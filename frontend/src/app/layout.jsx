import { Inter } from 'next/font/google'
import './globals.css'
import React from 'react'
const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'YouTube Video Processor',
  description: 'Process YouTube videos into shorter clips',
}

export default function RootLayout({
  children
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
