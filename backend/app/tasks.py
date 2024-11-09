from celery import Celery, states
from celery.result import AsyncResult
import yt_dlp
import os
import logging
import random
from moviepy.editor import VideoFileClip, concatenate_videoclips
from .utils.s3 import S3Handler

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
def process_video(self, youtube_url: str):
    try:
        # Initialize download state
        self.update_state(
            state='DOWNLOADING',
            meta={'progress': 0, 'message': 'Starting download...'}
        )
        
        os.makedirs('/tmp/videos', exist_ok=True)
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': '/tmp/videos/%(id)s.%(ext)s',
            'progress_hooks': [ProgressHook(self.request.id)]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            video_path = ydl.prepare_filename(info)

        # Update to processing state
        self.update_state(
            state='PROCESSING',
            meta={'progress': 0, 'message': 'Processing video...'}
        )
        
        output_path = create_random_clips(video_path, self)
        
        # Update to uploading state
        self.update_state(
            state='UPLOADING',
            meta={'progress': 0, 'message': 'Uploading to S3...'}
        )
        
        s3_handler = S3Handler()
        download_url = s3_handler.upload_file(output_path)
        
        # Clean up the original downloaded video
        if os.path.exists(video_path):
            os.remove(video_path)
        
        return {
            "status": "SUCCESS",
            "download_url": download_url,
            "title": info.get('title', 'Unknown')
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }

def create_random_clips(input_path: str, task, target_duration: int = 1500) -> str:
    video = VideoFileClip(input_path)
    total_duration = video.duration
    clips = []
    current_duration = 0
    used_segments = []

    # Allocate progress percentages for different stages
    CLIP_SELECTION_PROGRESS = 10  # 0-30% for selecting clips
    CLIP_CREATION_PROGRESS = 20   # 30-70% for creating clips
    CONCATENATION_PROGRESS = 20   # 70-85% for concatenating
    WRITING_PROGRESS = 50         # 85-100% for writing file

    while current_duration < target_duration:
        # Calculate progress for clip selection
        selection_progress = (current_duration / target_duration) * CLIP_SELECTION_PROGRESS
        task.update_state(
            state='PROCESSING',
            meta={
                'progress': selection_progress,
                'message': f'Selecting clips: {selection_progress:.1f}%'
            }
        )
        
        remaining_duration = target_duration - current_duration
        # Set clip duration to around 5 minutes (300 seconds)
        clip_duration = min(random.randint(270, 330), remaining_duration)
        
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

        # Update progress for clip creation
        creation_progress = CLIP_SELECTION_PROGRESS + ((current_duration / target_duration) * CLIP_CREATION_PROGRESS)
        task.update_state(
            state='PROCESSING',
            meta={
                'progress': creation_progress,
                'message': f'Creating clip {len(clips) + 1}: {creation_progress:.1f}%'
            }
        )
        
        clip = video.subclip(start_time, start_time + clip_duration)
        clips.append(clip)
        used_segments.append((start_time, start_time + clip_duration))
        current_duration += clip_duration

    # Update progress for concatenation start
    task.update_state(
        state='PROCESSING',
        meta={
            'progress': CLIP_SELECTION_PROGRESS + CLIP_CREATION_PROGRESS,
            'message': 'Starting concatenation...'
        }
    )
    
    final_video = concatenate_videoclips(clips)
    output_path = input_path.rsplit('.', 1)[0] + '_processed.mp4'

    # Update progress for writing start
    task.update_state(
        state='PROCESSING',
        meta={
            'progress': CLIP_SELECTION_PROGRESS + CLIP_CREATION_PROGRESS + CONCATENATION_PROGRESS,
            'message': 'Writing final video...'
        }
    )
    
    # Write the final video
    final_video.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )

    # Clean up
    final_video.close()
    for clip in clips:
        clip.close()
    video.close()

    return output_path

@app.task
def cleanup_s3_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"status": "success", "message": f"Cleaned up {file_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}