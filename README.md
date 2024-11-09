# YouTube Video Processor

A web application that processes YouTube videos using FastAPI, Celery, and Next.js. This application allows users to input a YouTube URL, download the video, and process it with real-time progress tracking.

## Features

- YouTube video processing with progress tracking
- Real-time status updates
- Video preview and download functionality
- Containerized development and production environments
- Asynchronous task processing with Celery
- Modern UI with Tailwind CSS
- Error handling and validation
- Progress bar for download and processing status
- Automatic video player preview

## Tech Stack

### Frontend

- **Next.js**: React framework for production
- **Tailwind CSS**: Utility-first CSS framework
- **React**: UI library
- **fetch API**: For handling HTTP requests

### Backend

- **FastAPI**: Modern Python web framework
- **Celery**: Distributed task queue
- **Redis**: Message broker and result backend
- **yt-dlp**: YouTube video downloader
- **uvicorn**: ASGI server
- **Python 3.9+**: Programming language

### Infrastructure

- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Production web server (optional)

## Prerequisites

- Docker and Docker Compose
- Node.js 16+ (for local frontend development)
- Python 3.9+ (for local backend development)
- Git

## Getting Started

### Development Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd youtube-video-processor
```

2. Create environment files:

```bash
# .env.development
REDIS_URL=redis://redis:6379/0
API_URL=http://localhost:8000
```

3. Start the development environment:

```bash
docker-compose up --build
```

The application will be available at:

- Frontend: <http://localhost:3456>
- Backend API: <http://localhost:8000>
- API Documentation: <http://localhost:8000/docs>

### Production Setup

1. Create production environment files:

```bash
# .env.production
REDIS_URL=redis://redis:6379/0
API_URL=https://your-domain.com/api
```

2. Build and run for production:

```bash
docker-compose -f docker-compose.prod.yml up --build
```

## Project Structure

```
.
├── frontend/                # Next.js frontend application
│   ├── src/
│   │   ├── components/     # React components
│   │   │   └── VideoForm.jsx  # Main video processing form
│   │   └── app/           # Next.js pages
│   ├── package.json
│   └── tailwind.config.js
├── backend/                # FastAPI backend application
│   ├── app/
│   │   ├── main.py        # FastAPI application
│   │   ├── tasks.py       # Celery tasks
│   │   └── celeryconfig.py # Celery configuration
│   ├── Dockerfile         # Development Dockerfile
│   ├── Dockerfile.prod    # Production Dockerfile
│   └── requirements.txt
├── docker-compose.yml     # Development compose file
└── docker-compose.prod.yml # Production compose file
```

## API Endpoints

### Process Video

```
POST /api/process-video
```

Start processing a YouTube video.

Request body:

```json
{
  "url": "https://youtube.com/watch?v=..."
}
```

Response:

```json
{
  "job_id": "task-uuid-here"
}
```

### Get Task Status

```
GET /api/task-status/{job_id}
```

Check the status of a processing task.

Response:

```json
{
  "status": "PROCESSING",
  "progress": 45,
  "result": {
    "download_url": "http://..."
  }
}
```

Status values:

- `STARTING`: Task is initializing
- `PROCESSING`: Task is in progress
- `SUCCESS`: Task completed successfully
- `ERROR`: Task failed

## Development

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Running Celery Worker

```bash
cd backend
celery -A app.tasks worker --loglevel=info
```

## Configuration

### Environment Variables

Frontend:

- `NEXT_PUBLIC_API_URL`: Backend API URL

Backend:

- `REDIS_URL`: Redis connection URL
- `CORS_ORIGINS`: Allowed CORS origins
- `MAX_WORKERS`: Maximum Celery workers

## Error Handling

The application handles various error cases:

- Invalid YouTube URLs
- Network connectivity issues
- Video processing failures
- Server errors

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

Common issues and solutions:

1. **Redis Connection Error**
   - Ensure Redis is running
   - Check Redis URL configuration

2. **Video Processing Fails**
   - Verify YouTube URL is valid
   - Check network connectivity
   - Ensure sufficient disk space

3. **Docker Issues**
   - Run `docker-compose down -v` to clean up
   - Rebuild containers with `docker-compose up --build`

## License

[MIT License](LICENSE)

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Celery](https://docs.celeryproject.org/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
