from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .tasks import process_video
from celery.result import AsyncResult

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoURL(BaseModel):
    url: str

@app.post("/api/process-video")
async def create_video_process(video: VideoURL):
    # Send task to Celery
    task = process_video.delay(video.url)
    return {"job_id": str(task.id)}

@app.get("/")
async def root():
    return {"message": "Video processing API is running"}

@app.get("/api/task-status/{task_id}")
async def get_task_status(task_id: str):
    task = AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'status': task.state,
            'progress': 0,
        }
    elif task.state == 'SUCCESS':
        response = {
            'status': task.state,
            'progress': 100,
            'result': task.result
        }
    else:
        # Handle DOWNLOADING, PROCESSING, and UPLOADING states
        response = {
            'status': task.state,
            'progress': task.info.get('progress', 0) if isinstance(task.info, dict) else 0,
            'message': task.info.get('message', '') if isinstance(task.info, dict) else str(task.info)
        }
    return response 