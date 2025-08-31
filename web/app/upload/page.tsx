'use client'

import { useState, useRef, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react'
import { useWebSocket } from '@/lib/websocket'

interface JobStatus {
  event: string
  job_id: number
  document_id: number
  type: string
  progress: number
  ts: string
}

export default function UploadPage() {
  const { data: session } = useSession()
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [jobs, setJobs] = useState<Map<number, JobStatus>>(new Map())
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const { messages } = useWebSocket('/ws/jobs', session?.accessToken)

  // Handle WebSocket messages
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      try {
        const jobStatus: JobStatus = JSON.parse(lastMessage)
        setJobs(prev => new Map(prev.set(jobStatus.job_id, jobStatus)))
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
  }, [messages])

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFile = async (file: File) => {
    if (!session?.accessToken) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/proxy/ingest', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.accessToken}`
        },
        body: formData
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const result = await response.json()
      console.log('Upload successful:', result)
    } catch (error) {
      console.error('Upload error:', error)
    } finally {
      setUploading(false)
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const getJobStatusIcon = (status: JobStatus) => {
    switch (status.event) {
      case 'done':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />
      default:
        return <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold mb-8">Upload Documents</h1>
          
          {/* Upload Area */}
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-lg text-gray-600 mb-4">
              Drag and drop your document here, or{' '}
              <button
                className="text-blue-500 hover:text-blue-700 underline"
                onClick={() => fileInputRef.current?.click()}
              >
                browse files
              </button>
            </p>
            <p className="text-sm text-gray-500">
              Supports PDF, Word, Excel, CSV, and text files
            </p>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileInput}
              accept=".pdf,.docx,.xlsx,.csv,.txt,.md,.html"
            />
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div className="mt-8 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-3" />
                <span className="text-blue-700">Uploading document...</span>
              </div>
            </div>
          )}

          {/* Job Status */}
          {jobs.size > 0 && (
            <div className="mt-8">
              <h2 className="text-xl font-semibold mb-4">Processing Status</h2>
              <div className="space-y-4">
                {Array.from(jobs.values()).map((job) => (
                  <div key={job.job_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      {getJobStatusIcon(job)}
                      <div>
                        <p className="font-medium">
                          {job.type.charAt(0).toUpperCase() + job.type.slice(1)} Job #{job.job_id}
                        </p>
                        <p className="text-sm text-gray-600">
                          Document #{job.document_id}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{job.event}</p>
                      {job.progress > 0 && job.progress < 100 && (
                        <div className="w-32 bg-gray-200 rounded-full h-2 mt-1">
                          <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
