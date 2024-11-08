FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including FFmpeg and imagemagick
RUN apt-get update && \
    apt-get install -y ffmpeg imagemagick && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create videos directory and set permissions
RUN mkdir -p /tmp/videos && \
    chmod 777 /tmp/videos

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 