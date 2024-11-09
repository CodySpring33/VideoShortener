from celery import Celery, states
from celery.result import AsyncResult
import yt_dlp
import os
import logging
import random
from moviepy.editor import (
    VideoFileClip, 
    AudioFileClip,
    concatenate_videoclips,
    concatenate_audioclips
)
from .utils.s3 import S3Handler
import time

# Initialize Celery with explicit config module
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
        
        format_option = 'bestaudio' if media_type == 'audio' else 'best'
        
        # For audio, let yt-dlp handle the initial download without extension
        base_output_template = '/tmp/videos/%(id)s'
            
        ydl_opts = {
            'format': format_option,
            'outtmpl': base_output_template,
            'progress_hooks': [ProgressHook(self.request.id)]
        }

        if media_type == 'audio':
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })

        # Add transition state for download completion
        self.update_state(
            state='DOWNLOADING',
            meta={'progress': 95, 'message': 'Download completing...'}
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            video_id = info['id']
            
            if media_type == 'audio':
                original_file = f'/tmp/videos/{video_id}.mp3'
            else:
                original_file = f'/tmp/videos/{video_id}.mp4'

            # Add post-download verification state
            self.update_state(
                state='VERIFYING DOWNLOAD',
                meta={'progress': 98, 'message': 'Verifying download...'}
            )

            # Wait for file to be fully written (max 10 seconds)
            max_wait = 10
            wait_time = 0
            while not os.path.exists(original_file) and wait_time < max_wait:
                time.sleep(0.5)
                wait_time += 0.5

            # Verify the file exists
            if not os.path.exists(original_file):
                raise FileNotFoundError(f"Downloaded file not found at {original_file} after {max_wait} seconds")

            # Verify file size
            file_size = os.path.getsize(original_file)
            if file_size == 0:
                raise ValueError(f"Downloaded file is empty: {original_file}")

        processed_file = create_random_clips(original_file, self, media_type=media_type)
        
        self.update_state(
            state='UPLOADING',
            meta={'progress': 0, 'message': 'Uploading to S3...'}
        )
        
        s3_handler = S3Handler()
        download_url = s3_handler.upload_file(processed_file)
        
        # Clean up both original and processed files
        if original_file and os.path.exists(original_file):
            os.remove(original_file)
        if processed_file and os.path.exists(processed_file):
            os.remove(processed_file)
        
        return {
            "status": "SUCCESS",
            "download_url": download_url,
            "title": info.get('title', 'Unknown')
        }

    except Exception as e:
        # Clean up files in case of error
        if original_file and os.path.exists(original_file):
            os.remove(original_file)
        if processed_file and os.path.exists(processed_file):
            os.remove(processed_file)
            
        error_msg = f"Error processing {media_type}: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        
        return {
            "status": "ERROR",
            "message": error_msg
        }

def create_random_clips(input_path: str, task, target_duration: int = 1500, media_type: str = 'video') -> str:
    try:
        if media_type == 'video':
            clip = VideoFileClip(input_path)
        else:
            clip = AudioFileClip(input_path)
        
        total_duration = clip.duration
        clips = []
        current_duration = 0
        used_segments = []

        # Calculate number of chunks needed (5-minute segments)
        chunk_duration = random.randint(270, 330)  # 4.5-5.5 minutes
        estimated_chunks = target_duration / chunk_duration
        chunks_processed = 0

        while current_duration < target_duration:
            # Calculate progress based on chunks processed
            chunks_processed += 1
            progress = min(95, (chunks_processed / estimated_chunks) * 95)  # Leave 5% for final concatenation
            
            task.update_state(
                state='PROCESSING',
                meta={
                    'progress': progress,
                    'message': f'Processing chunk {chunks_processed} of {int(estimated_chunks)}'
                }
            )
            
            remaining_duration = target_duration - current_duration
            clip_duration = min(chunk_duration, remaining_duration)
            
            while True:
                max_start = total_duration - clip_duration
                start_time = random.uniform(0, max_start)
                
                overlap = False
                for used_start, used_end in used_segments:
                    if not (start_time + clip_duration <= used_start or start_time >= used_end):
                        overlap = True
                        break
                
                if not overlap:
                    break

            subclip = clip.subclip(start_time, start_time + clip_duration)
            clips.append(subclip)
            used_segments.append((start_time, start_time + clip_duration))
            current_duration += clip_duration

        task.update_state(
            state='PROCESSING',
            meta={
                'progress': 95,
                'message': f'Finalizing {media_type}...'
            }
        )

        if media_type == 'video':
            final_clip = concatenate_videoclips(clips)
            output_path = input_path.replace('.mp4', '_processed.mp4')
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
        else:
            final_clip = concatenate_audioclips(clips)
            output_path = input_path.replace('.mp3', '_processed.mp3')
            final_clip.write_audiofile(
                output_path,
                codec='libmp3lame',
                bitrate='192k'
            )

        # Final progress update
        task.update_state(
            state='PROCESSING',
            meta={
                'progress': 100,
                'message': f'Processing complete'
            }
        )

        # Clean up
        clip.close()
        for c in clips:
            c.close()
        final_clip.close()

        return output_path
        
    except Exception as e:
        import traceback
        print(f"Error in create_random_clips: {str(e)}")
        print(traceback.format_exc())
        raise e

@app.task
def cleanup_s3_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"status": "success", "message": f"Cleaned up {file_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}