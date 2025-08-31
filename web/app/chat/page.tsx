'use client'

import { useState, useRef, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Send, MessageSquare, ThumbsUp, ThumbsDown } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  timestamp: Date
}

interface Citation {
  doc_id: number
  chunk_id: number
  page?: number
  score: number
  text?: string
}

export default function ChatPage() {
  const { data: session } = useSession()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !session?.accessToken) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setStreamingMessage('')

    try {
      // Start SSE stream
      const eventSource = new EventSource(`/api/proxy/answer/stream?query=${encodeURIComponent(input)}`, {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`
        }
      })

      eventSourceRef.current = eventSource
      let citations: Citation[] = []
      let usage: any = null

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'chunk') {
          setStreamingMessage(prev => prev + data.text)
        } else if (data.type === 'done') {
          citations = data.citations || []
          usage = data.usage
          
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: streamingMessage,
            citations,
            timestamp: new Date()
          }
          
          setMessages(prev => [...prev, assistantMessage])
          setStreamingMessage('')
          setIsLoading(false)
          eventSource.close()
        }
      }

      eventSource.onerror = (error) => {
        console.error('SSE error:', error)
        setIsLoading(false)
        eventSource.close()
      }

    } catch (error) {
      console.error('Chat error:', error)
      setIsLoading(false)
    }
  }

  const handleFeedback = async (messageId: string, rating: 'up' | 'down') => {
    if (!session?.accessToken) return

    try {
      const message = messages.find(m => m.id === messageId)
      if (!message) return

      await fetch('/api/proxy/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.accessToken}`
        },
        body: JSON.stringify({
          answer_id: messageId,
          rating,
          reason: rating === 'down' ? 'User feedback' : null,
          selected_citation_ids: message.citations?.map(c => c.chunk_id) || []
        })
      })
    } catch (error) {
      console.error('Feedback error:', error)
    }
  }

  const handleCitationClick = async (citation: Citation) => {
    if (!session?.accessToken) return

    try {
      // Fetch citation text from backend
      const response = await fetch(`/api/proxy/citations/${citation.chunk_id}`, {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setSelectedCitation({ ...citation, text: data.text })
      }
    } catch (error) {
      console.error('Citation error:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-sm border-b px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold">Chat with Documents</h1>
          <div className="flex items-center space-x-4">
            <a href="/upload" className="text-blue-600 hover:text-blue-800">
              Upload Documents
            </a>
            <a href="/settings" className="text-gray-600 hover:text-gray-800">
              Settings
            </a>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 max-w-4xl mx-auto w-full p-6">
        <div className="bg-white rounded-lg shadow-lg h-full flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-3xl ${message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100'} rounded-lg p-4`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Citations */}
                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-sm font-medium mb-2">Sources:</p>
                      <div className="space-y-2">
                        {message.citations.map((citation, index) => (
                          <button
                            key={index}
                            onClick={() => handleCitationClick(citation)}
                            className="block text-left text-sm text-blue-600 hover:text-blue-800 underline"
                          >
                            Document {citation.doc_id}, Page {citation.page || 'N/A'} (Score: {citation.score.toFixed(3)})
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Feedback */}
                  {message.role === 'assistant' && (
                    <div className="mt-4 pt-4 border-t border-gray-200 flex space-x-2">
                      <button
                        onClick={() => handleFeedback(message.id, 'up')}
                        className="flex items-center space-x-1 text-sm text-gray-600 hover:text-green-600"
                      >
                        <ThumbsUp className="w-4 h-4" />
                        <span>Helpful</span>
                      </button>
                      <button
                        onClick={() => handleFeedback(message.id, 'down')}
                        className="flex items-center space-x-1 text-sm text-gray-600 hover:text-red-600"
                      >
                        <ThumbsDown className="w-4 h-4" />
                        <span>Not helpful</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {/* Streaming message */}
            {streamingMessage && (
              <div className="flex justify-start">
                <div className="max-w-3xl bg-gray-100 rounded-lg p-4">
                  <p className="whitespace-pre-wrap">{streamingMessage}</p>
                  <div className="mt-2 w-2 h-4 bg-gray-400 animate-pulse"></div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t p-6">
            <form onSubmit={handleSubmit} className="flex space-x-4">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question about your documents..."
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <Send className="w-4 h-4" />
                <span>Send</span>
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Citation Modal */}
      {selectedCitation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Citation Details</h3>
                <button
                  onClick={() => setSelectedCitation(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <p><strong>Document ID:</strong> {selectedCitation.doc_id}</p>
                <p><strong>Chunk ID:</strong> {selectedCitation.chunk_id}</p>
                <p><strong>Page:</strong> {selectedCitation.page || 'N/A'}</p>
                <p><strong>Score:</strong> {selectedCitation.score.toFixed(3)}</p>
              </div>
              {selectedCitation.text && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm">{selectedCitation.text}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
