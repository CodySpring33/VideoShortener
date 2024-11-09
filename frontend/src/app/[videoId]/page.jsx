'use client'

import { useEffect } from 'react'
import VideoForm from '../../components/VideoForm'

export default function AutoProcessPage({ params }) {
  useEffect(() => {
    if (params.videoId) {
      // Construct YouTube URL from video ID
      const youtubeUrl = `https://youtube.com/watch?v=${params.videoId}`
      
      // Create and dispatch the auto-process event
      const event = new CustomEvent('auto-process-video', {
        detail: {
          url: youtubeUrl,
          mediaType: 'audio'
        }
      })
      window.dispatchEvent(event)
    }
  }, [params.videoId])

  return <VideoForm />
} 