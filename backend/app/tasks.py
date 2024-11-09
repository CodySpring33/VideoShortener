from celery import Celery
import yt_dlp
import os
import logging
import random
import time
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
from .utils.s3 import S3Handler

app = Celery('tasks')
app.config_from_object('app.celeryconfig')

class ProgressHook:
    def __init__(self, task_id):
        self.task_id = task_id

    def __call__(self, d):
        if d['status'] == 'downloading':
            try:
                percentage = float(d.get('_percent_str', '0%').replace('%', ''))
                app.backend.store_result(
                    self.task_id,
                    {
                        'status': 'DOWNLOADING',
                        'progress': percentage,
                        'message': f"Downloading: {percentage:.1f}%"
                    },
                    'DOWNLOADING'
                )
            except (ValueError, TypeError):
                pass

class ProgressLogger:
    def __init__(self, task, start_progress, end_progress):
        self.task = task
        self.start_progress = float(start_progress)
        self.end_progress = float(end_progress)
        self.last_progress = float(start_progress)
        self.duration = None  # Will store total duration
        self.current_time = 0

    def __call__(self, t=None, message=None):
        if t is not None:
            self.current_time = t
            if self.duration is None:
                # First call usually includes the total duration
                self.duration = t
            
            # Calculate progress as percentage of completion
            progress = self.start_progress + (
                (self.current_time / max(self.duration, 0.0001)) * 
                (self.end_progress - self.start_progress)
            )
        else:
            # If no time provided, use message only
            progress = self.last_progress

        # Ensure progress stays within bounds
        progress = max(min(progress, self.end_progress), self.start_progress)

        if progress - self.last_progress >= 1:
            self.task.update_state(
                state='PROCESSING',
                meta={
                    'progress': progress,
                    'message': message if message else f'Rendering: {progress:.1f}%'
                }
            )
            self.last_progress = progress

    def iter_bar(self, chunk=None, t=None):
        """Handle both audio chunks and video frame iterations"""
        if chunk is not None:
            # Audio processing
            total = max(len(chunk), 1)
            for i, item in enumerate(chunk):
                progress = self.start_progress + (
                    (i / total) * (self.end_progress - self.start_progress)
                )
                progress = max(min(progress, self.end_progress), self.start_progress)
                
                if progress - self.last_progress >= 1:
                    self.task.update_state(
                        state='PROCESSING',
                        meta={
                            'progress': progress,
                            'message': f'Processing audio: {progress:.1f}%'
                        }
                    )
                    self.last_progress = progress
                yield item
        elif t is not None:
            # Video processing
            for frame_time in t:
                if self.duration:  # Only update progress if we have a duration
                    progress = self.start_progress + (
                        (frame_time / self.duration) * 
                        (self.end_progress - self.start_progress)
                    )
                    progress = max(min(progress, self.end_progress), self.start_progress)
                    
                    if progress - self.last_progress >= 1:
                        self.task.update_state(
                            state='PROCESSING',
                            meta={
                                'progress': progress,
                                'message': f'Processing video: {progress:.1f}%'
                            }
                        )
                        self.last_progress = progress
                yield frame_time

@app.task(bind=True)
def process_video(self, youtube_url: str, media_type: str = 'video'):
    original_file = None
    processed_file = None
    
    try:
        self.update_state(
            state='DOWNLOADING',
            meta={'progress': 0, 'message': 'Starting download...'}
        )
        
        os.makedirs('/tmp/videos', exist_ok=True)
        
        ydl_opts = {
            'format': 'best' if media_type == 'video' else 'bestaudio',
            'outtmpl': '/tmp/videos/%(id)s.%(ext)s',
            'progress_hooks': [ProgressHook(self.request.id)],
        }

        if media_type == 'audio':
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            video_id = info['id']
            
            if media_type == 'audio':
                original_file = f'/tmp/videos/{video_id}.mp3'
            else:
                original_file = f'/tmp/videos/{video_id}.mp4'

        self.update_state(
            state='PROCESSING',
            meta={'progress': 0, 'message': 'Starting processing...'}
        )
        
        processed_file = create_random_clips(original_file, self, media_type=media_type)
        
        self.update_state(
            state='UPLOADING',
            meta={'progress': 0, 'message': 'Uploading to S3...'}
        )
        
        s3_handler = S3Handler()
        download_url = s3_handler.upload_file(processed_file)
        
        # Clean up files
        for file in [original_file, processed_file]:
            if file and os.path.exists(file):
                os.remove(file)
        
        return {
            "status": "SUCCESS",
            "download_url": download_url,
            "title": info.get('title', 'Unknown')
        }

    except Exception as e:
        for file in [original_file, processed_file]:
            if file and os.path.exists(file):
                os.remove(file)
        raise Exception(f"Error processing {media_type}: {str(e)}")

def create_random_clips(input_path: str, task, target_duration: int = 1500, media_type: str = 'video') -> str:
    try:
        task.update_state(
            state='PROCESSING',
            meta={'progress': 0, 'message': f'Loading {media_type} file...'}
        )
        
        clip = VideoFileClip(input_path, audio=True) if media_type == 'video' else AudioFileClip(input_path)
        total_duration = clip.duration
        
        task.update_state(
            state='PROCESSING',
            meta={'progress': 10, 'message': 'File loaded, creating chunks...'}
        )
        
        # Adjust chunk duration based on total video length
        if total_duration < 330:
            chunk_duration = total_duration / 3
            total_chunks = 3
        else:
            chunk_duration = random.randint(270, 330)
            total_chunks = min(int(target_duration / chunk_duration), 10)
            total_chunks = min(total_chunks, int(total_duration / chunk_duration))
        
        clips = []
        used_segments = []
        max_attempts = 50  # Prevent infinite loops
        
        for chunk_num in range(total_chunks):
            progress = 10 + (chunk_num / total_chunks) * 40
            task.update_state(
                state='PROCESSING',
                meta={
                    'progress': progress,
                    'message': f'Creating chunk {chunk_num + 1} of {total_chunks}'
                }
            )
            
            attempts = 0
            while attempts < max_attempts:
                max_start = max(0, total_duration - chunk_duration)
                start_time = random.uniform(0, max_start)
                end_time = min(start_time + chunk_duration, total_duration)
                
                # Check for overlap with existing segments
                overlap = any(
                    not (end_time <= used_start or start_time >= used_end) 
                    for used_start, used_end in used_segments
                )
                
                if not overlap:
                    subclip = clip.subclip(start_time, end_time)
                    clips.append(subclip)
                    used_segments.append((start_time, end_time))
                    break
                    
                attempts += 1
            
            if attempts >= max_attempts:
                # If we can't find a non-overlapping segment, break the loop
                break
        
        if not clips:
            raise Exception("Failed to create any valid clips")
            
        if media_type == 'video':
            final_clip = concatenate_videoclips(clips, method="compose")
            output_path = input_path.replace('.mp4', '_processed.mp4')
            
            progress_logger = ProgressLogger(task, 50, 90)
            
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                logger=progress_logger
            )
        else:
            final_clip = concatenate_audioclips(clips)
            output_path = input_path.replace('.mp3', '_processed.mp3')
            
            progress_logger = ProgressLogger(task, 50, 90)
            
            final_clip.write_audiofile(
                output_path,
                codec='libmp3lame',
                bitrate='192k',
                logger=progress_logger
            )

        clip.close()
        for c in clips:
            c.close()
        final_clip.close()

        return output_path
        
    except Exception as e:
        logging.error(f"Error in create_random_clips: {str(e)}")
        if 'clip' in locals():
            clip.close()
        if 'clips' in locals():
            for c in clips:
                c.close()
        if 'final_clip' in locals():
            final_clip.close()
        raise e

@app.task
def cleanup_s3_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"status": "success", "message": f"Cleaned up {file_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}