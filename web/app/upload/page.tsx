'use client'

import { useState, useRef, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { redirect } from 'next/navigation'
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react'
import { useWebSocket } from '@/hooks/useWebSocket'

interface JobStatus {
  job_id: number
  document_id: number
  type: string
  progress: number
  status: 'started' | 'progress' | 'done' | 'failed'
  error?: string
}

export default function UploadPage() {
  const { data: session, status } = useSession()
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [jobStatuses, setJobStatuses] = useState<Map<number, JobStatus>>(new Map())
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // WebSocket connection for realtime status
  const { messages, connected } = useWebSocket('/ws/jobs')

  useEffect(() => {
    if (status === 'loading') return
    if (!session) {
      redirect('/auth/signin')
    }
  }, [session, status])

  useEffect(() => {
    // Process WebSocket messages
    messages.forEach((message) => {
      try {
        const data = JSON.parse(message)
        if (data.event && data.job_id) {
          setJobStatuses(prev => {
            const newMap = new Map(prev)
            newMap.set(data.job_id, {
              job_id: data.job_id,
              document_id: data.document_id,
              type: data.type,
              progress: data.progress || 0,
              status: data.event.split('_')[1] as JobStatus['status'],
              error: data.error
            })
            return newMap
          })
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    })
  }, [messages])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || [])
    setFiles(prev => [...prev, ...selectedFiles])
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setUploading(true)
    
    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        
        const response = await fetch('/api/proxy/ingest', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session?.accessToken}`
          },
          body: formData
        })

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`)
        }

        const result = await response.json()
        console.log('Upload result:', result)
      }

      // Clear files after successful upload
      setFiles([])
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const getStatusIcon = (status: JobStatus['status']) => {
    switch (status) {
      case 'done':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />
      default:
        return <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    }
  }

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Upload Documents</h1>
          
          {/* WebSocket Status */}
          <div className="mb-6">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${
              connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              <div className={`w-2 h-2 rounded-full mr-2 ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              {connected ? 'Connected' : 'Disconnected'} to realtime updates
            </div>
          </div>

          {/* File Upload Area */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6">
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-lg text-gray-600 mb-4">
              Drag and drop files here, or click to select
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt"
              onChange={handleFileSelect}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
            >
              Select Files
            </button>
          </div>

          {/* Selected Files */}
          {files.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Selected Files</h3>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                    <div className="flex items-center">
                      <File className="w-5 h-5 text-gray-400 mr-3" />
                      <span className="text-gray-700">{file.name}</span>
                      <span className="text-gray-500 text-sm ml-2">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload Button */}
          {files.length > 0 && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition duration-200"
            >
              {uploading ? 'Uploading...' : `Upload ${files.length} file${files.length > 1 ? 's' : ''}`}
            </button>
          )}

          {/* Job Status */}
          {jobStatuses.size > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Status</h3>
              <div className="space-y-3">
                {Array.from(jobStatuses.values()).map((job) => (
                  <div key={job.job_id} className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center">
                        {getStatusIcon(job.status)}
                        <span className="ml-2 font-medium">
                          {job.type.charAt(0).toUpperCase() + job.type.slice(1)} Job {job.job_id}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">
                        {job.progress}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${job.progress}%` }}
                      ></div>
                    </div>
                    {job.error && (
                      <p className="text-red-600 text-sm mt-2">{job.error}</p>
                    )}
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
