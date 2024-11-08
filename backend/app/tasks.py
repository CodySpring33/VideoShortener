from celery import Celery
import yt_dlp
import os
import logging
import random
from moviepy.editor import VideoFileClip, concatenate_videoclips

# Initialize Celery
celery = Celery('tasks', broker='redis://redis:6379/0')

@celery.task
def process_video(youtube_url: str):
    try:
        os.makedirs('/tmp/videos', exist_ok=True)
        
        # Download video (existing code)
        ydl_opts = {
            'format': 'best',
            'outtmpl': '/tmp/videos/%(id)s.%(ext)s',
            'verbose': True
        }

        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            video_path = ydl.prepare_filename(info)

        # Process the video
        output_path = create_random_clips(video_path)

        return {
            "status": "success",
            "video_path": output_path,
            "title": info.get('title', 'Unknown')
        }

    except Exception as e:
        logging.error(f"Error processing video: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

def create_random_clips(input_path: str, target_duration: int = 1500) -> str:
    """
    Creates a 25-minute video from random clips
    target_duration is in seconds (25 minutes = 1500 seconds)
    """
    video = VideoFileClip(input_path)
    total_duration = video.duration
    
    clips = []
    current_duration = 0
    used_segments = []

    while current_duration < target_duration:
        # Calculate remaining duration needed
        remaining_duration = target_duration - current_duration
        
        # Generate random clip duration (between 30 and 120 seconds)
        clip_duration = min(random.randint(30, 120), remaining_duration)
        
        # Find a non-overlapping segment
        while True:
            # Random start time
            max_start = total_duration - clip_duration
            start_time = random.uniform(0, max_start)
            
            # Check if this segment overlaps with any used segments
            overlap = False
            for used_start, used_end in used_segments:
                if not (start_time + clip_duration <= used_start or start_time >= used_end):
                    overlap = True
                    break
            
            if not overlap:
                break
        
        # Extract the clip
        clip = video.subclip(start_time, start_time + clip_duration)
        clips.append(clip)
        used_segments.append((start_time, start_time + clip_duration))
        current_duration += clip_duration

    # Concatenate all clips
    final_video = concatenate_videoclips(clips)
    
    # Generate output path
    output_path = input_path.rsplit('.', 1)[0] + '_processed.mp4'
    
    # Write the final video
    final_video.write_videofile(output_path)
    
    # Close all clips to free up resources
    final_video.close()
    for clip in clips:
        clip.close()
    video.close()
    
    return output_path

@celery.task
def cleanup_s3_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"status": "success", "message": f"Cleaned up {file_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}