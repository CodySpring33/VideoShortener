'use client'
import { useState, useEffect } from 'react'
import React from 'react'
export default function VideoForm() {
  const [mounted, setMounted] = useState(false)
  const [url, setUrl] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setStatus('Processing...')
    
    try {
      const response = await fetch('http://localhost:8000/api/process-video', {
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
      setStatus(`Job ID: ${data.job_id}`)
    } catch (error) {
      setError('Error: ' + (error as Error).message)
      setStatus('')
    }
  }

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
          className="w-full bg-blue-500 text-white py-3 px-4 rounded-md hover:bg-blue-600 transition-colors duration-200"
        >
          Process Video
        </button>
      </form>

      {status && (
        <div className="mt-4 p-4 bg-green-50 text-green-700 rounded-md">
          {status}
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