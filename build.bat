@echo off

:: Set your Docker Hub username (or registry URL)
set REGISTRY_USER=cjspring33
:: Set the version/tag
set VERSION=1.0.0

:: Build the images
echo Building frontend image...
docker build -f frontend/Dockerfile.prod -t %REGISTRY_USER%/video-processor-frontend:%VERSION% ./frontend
docker tag %REGISTRY_USER%/video-processor-frontend:%VERSION% %REGISTRY_USER%/video-processor-frontend:latest

echo Building backend image...
docker build -f backend/Dockerfile.prod -t %REGISTRY_USER%/video-processor-backend:%VERSION% ./backend
docker tag %REGISTRY_USER%/video-processor-backend:%VERSION% %REGISTRY_USER%/video-processor-backend:latest

:: Push the images to registry
echo Pushing images to registry...
docker push %REGISTRY_USER%/video-processor-frontend:%VERSION%
docker push %REGISTRY_USER%/video-processor-frontend:latest
docker push %REGISTRY_USER%/video-processor-backend:%VERSION%
docker push %REGISTRY_USER%/video-processor-backend:latest 