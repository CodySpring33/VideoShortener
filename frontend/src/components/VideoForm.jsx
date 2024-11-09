'use client'
import { useState, useEffect } from 'react'
import React from 'react'

export default function VideoForm() {
  const [mounted, setMounted] = useState(false)
  const [url, setUrl] = useState('')
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [progress, setProgress] = useState(0)
  const [downloadUrl, setDownloadUrl] = useState(null)
  const [isAudioOnly, setIsAudioOnly] = useState(false)
  const [mediaType, setMediaType] = useState('video')

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (jobId) {
      const interval = setInterval(async () => {
        try {
          const statusUrl = `http://${window.location.hostname}:8123/api/task-status/${jobId}`
          const response = await fetch(statusUrl)
          const data = await response.json()
          
          setProgress(data.progress || 0)
          setStatus(data.status)

          if (data.status === 'SUCCESS') {
            clearInterval(interval)
            setDownloadUrl(data.result.download_url)
          } else if (data.status === 'ERROR') {
            clearInterval(interval)
            setError(data.message)
          }
        } catch (error) {
          console.error('Error checking status:', error)
        }
      }, 1000)

      return () => clearInterval(interval)
    }
  }, [jobId])

  const pollStatus = (jobId) => {
    setJobId(jobId);
    // The useEffect hook will handle the actual polling
    // when jobId changes
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setStatus('STARTING');
    setProgress(0);
    setDownloadUrl('');

    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8123';
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 300000); // 5 minutes

      const response = await fetch(`${backendUrl}/api/process-video`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url,
          mediaType: mediaType
        }),
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const jobId = data.job_id;

      // Start polling for status
      pollStatus(jobId);
    } catch (err) {
      setError(err.name === 'AbortError' ? 'Request timed out' : err.message);
      setStatus('ERROR');
    }
  };

  if (!mounted) return null

  return (
    <div className="max-w-2xl mx-auto p-4 bg-white rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-4">YouTube Video Processor</h1>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
            YouTube URL
          </label>
          <input
            type="text"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="https://youtube.com/watch?v=..."
          />
        </div>

        <div className="flex items-center space-x-4">
          <label className="inline-flex items-center">
            <input
              type="radio"
              className="form-radio text-blue-500"
              name="mediaType"
              value="video"
              checked={mediaType === 'video'}
              onChange={(e) => setMediaType(e.target.value)}
            />
            <span className="ml-2">Video</span>
          </label>
          <label className="inline-flex items-center">
            <input
              type="radio"
              className="form-radio text-blue-500"
              name="mediaType"
              value="audio"
              checked={mediaType === 'audio'}
              onChange={(e) => setMediaType(e.target.value)}
            />
            <span className="ml-2">Audio Only</span>
          </label>
        </div>
        
        <button
          type="submit"
          disabled={status === 'PROCESSING'}
          className="w-full bg-blue-500 text-white py-3 px-4 rounded-md hover:bg-blue-600 transition-colors duration-200 disabled:bg-gray-400"
        >
          Process {mediaType === 'audio' ? 'Audio' : 'Video'}
        </button>
      </form>

      {status && status !== 'SUCCESS' && (
        <div className="mt-6">
          <div className="mb-2 flex justify-between">
            <span className="text-sm font-medium text-gray-700">{status}</span>
            <span className="text-sm font-medium text-gray-700">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {downloadUrl && (
        <div className="mt-6 space-y-4">
          {mediaType === 'video' ? (
            <div className="aspect-video w-full">
              <video 
                className="w-full rounded-lg"
                controls
                src={downloadUrl}
              >
                Your browser does not support the video tag.
              </video>
            </div>
          ) : (
            <div className="w-full">
              <audio 
                className="w-full"
                controls
                src={downloadUrl}
              >
                Your browser does not support the audio tag.
              </audio>
            </div>
          )}
          
          <a
            href={downloadUrl}
            className="w-full block text-center bg-green-500 text-white py-3 px-4 rounded-md hover:bg-green-600 transition-colors duration-200"
            target="_blank"
            rel="noopener noreferrer"
          >
            Download Processed {mediaType === 'audio' ? 'Audio' : 'Video'}
          </a>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}
    </div>
  )
} 