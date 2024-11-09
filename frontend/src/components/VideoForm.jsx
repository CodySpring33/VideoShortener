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

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (jobId) {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`http://localhost:8123/api/task-status/${jobId}`)
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setStatus('STARTING')
    setProgress(0)
    setDownloadUrl(null)
    
    try {
      const response = await fetch('http://localhost:8123/api/process-video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setJobId(data.job_id)
    } catch (error) {
      setError('Error: ' + error.message)
      setStatus('')
    }
  }

  if (!mounted) return null

  return (
    <div className="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow-md">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">YouTube Video Processor</h1>
      
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
        
        <button
          type="submit"
          disabled={status === 'PROCESSING'}
          className="w-full bg-blue-500 text-white py-3 px-4 rounded-md hover:bg-blue-600 transition-colors duration-200 disabled:bg-gray-400"
        >
          Process Video
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
          <div className="aspect-video w-full">
            <video 
              className="w-full rounded-lg"
              controls
              src={downloadUrl}
            >
              Your browser does not support the video tag.
            </video>
          </div>
          
          <a
            href={downloadUrl}
            className="w-full block text-center bg-green-500 text-white py-3 px-4 rounded-md hover:bg-green-600 transition-colors duration-200"
            target="_blank"
            rel="noopener noreferrer"
          >
            Download Processed Video
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