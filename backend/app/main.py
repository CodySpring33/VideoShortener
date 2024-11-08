from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .tasks import process_video

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