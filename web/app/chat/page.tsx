'use client'

import { useState, useEffect, useRef } from 'react'
import { useSession } from 'next-auth/react'
import { redirect } from 'next/navigation'
import { Send, ThumbsUp, ThumbsDown, FileText, X } from 'lucide-react'

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
  const { data: session, status } = useSession()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackRating, setFeedbackRating] = useState<'up' | 'down' | null>(null)
  const [feedbackReason, setFeedbackReason] = useState('')
  const [selectedCitations, setSelectedCitations] = useState<number[]>([])
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const lastMessageRef = useRef<Message | null>(null)

  useEffect(() => {
    if (status === 'loading') return
    if (!session) {
      redirect('/auth/signin')
    }
  }, [session, status])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/proxy/answer/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken}`
        },
        body: JSON.stringify({
          query: input,
          top_k: 10,
          rerank: true,
          max_ctx_tokens: 2000
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      let assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
      lastMessageRef.current = assistantMessage

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'chunk') {
                assistantMessage.content += data.text
                setMessages(prev => [...prev.slice(0, -1), { ...assistantMessage }])
              } else if (data.type === 'done') {
                assistantMessage.citations = data.citations
                setMessages(prev => [...prev.slice(0, -1), { ...assistantMessage }])
                setShowFeedback(true)
              }
            } catch (error) {
              console.error('Error parsing SSE data:', error)
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleCitationClick = async (citation: Citation) => {
    if (citation.text) {
      setSelectedCitation(citation)
    } else {
      // Fetch citation text if not available
      try {
        const response = await fetch(`/api/proxy/chunks/${citation.chunk_id}`, {
          headers: {
            'Authorization': `Bearer ${session?.accessToken}`
          }
        })
        if (response.ok) {
          const data = await response.json()
          setSelectedCitation({ ...citation, text: data.text })
        }
      } catch (error) {
        console.error('Error fetching citation:', error)
      }
    }
  }

  const handleFeedback = async (rating: 'up' | 'down') => {
    setFeedbackRating(rating)
    
    if (rating === 'down') {
      // Show feedback modal for negative feedback
      return
    }

    await submitFeedback(rating)
  }

  const submitFeedback = async (rating: 'up' | 'down', reason?: string) => {
    if (!lastMessageRef.current) return

    try {
      await fetch('/api/proxy/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken}`
        },
        body: JSON.stringify({
          answer_id: lastMessageRef.current.id,
          rating,
          reason,
          selected_citation_ids: selectedCitations
        })
      })

      setShowFeedback(false)
      setFeedbackRating(null)
      setFeedbackReason('')
      setSelectedCitations([])
    } catch (error) {
      console.error('Error submitting feedback:', error)
    }
  }

  const handleCitationSelect = (citationId: number) => {
    setSelectedCitations(prev => 
      prev.includes(citationId) 
        ? prev.filter(id => id !== citationId)
        : [...prev, citationId]
    )
  }

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">Chat with Your Documents</h1>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-lg px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
              
              {/* Citations */}
              {message.citations && message.citations.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Sources:</h4>
                  <div className="space-y-2">
                    {message.citations.map((citation, index) => (
                      <button
                        key={index}
                        onClick={() => handleCitationClick(citation)}
                        className={`block w-full text-left p-2 rounded text-sm transition-colors ${
                          selectedCitations.includes(citation.chunk_id)
                            ? 'bg-blue-100 border-blue-300'
                            : 'bg-gray-50 hover:bg-gray-100'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-gray-700">
                            Document {citation.doc_id}
                            {citation.page && ` (Page ${citation.page})`}
                          </span>
                          <span className="text-gray-500">
                            Score: {citation.score.toFixed(2)}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Feedback */}
              {message.role === 'assistant' && showFeedback && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">Was this helpful?</span>
                    <button
                      onClick={() => handleFeedback('up')}
                      className={`p-1 rounded ${
                        feedbackRating === 'up' ? 'text-green-600' : 'text-gray-400'
                      } hover:text-green-600`}
                    >
                      <ThumbsUp className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleFeedback('down')}
                      className={`p-1 rounded ${
                        feedbackRating === 'down' ? 'text-red-600' : 'text-gray-400'
                      } hover:text-red-600`}
                    >
                      <ThumbsDown className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="bg-white border-t border-gray-200 p-6">
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
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg transition duration-200"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>

      {/* Citation Modal */}
      {selectedCitation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Citation Details</h3>
                <button
                  onClick={() => setSelectedCitation(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="space-y-2 mb-4">
                <p><strong>Document ID:</strong> {selectedCitation.doc_id}</p>
                <p><strong>Chunk ID:</strong> {selectedCitation.chunk_id}</p>
                {selectedCitation.page && <p><strong>Page:</strong> {selectedCitation.page}</p>}
                <p><strong>Score:</strong> {selectedCitation.score.toFixed(2)}</p>
              </div>
              {selectedCitation.text && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">Text:</h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{selectedCitation.text}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Feedback Modal */}
      {feedbackRating === 'down' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">What went wrong?</h3>
              <textarea
                value={feedbackReason}
                onChange={(e) => setFeedbackReason(e.target.value)}
                placeholder="Please describe the issue..."
                className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
              <div className="flex space-x-2">
                <button
                  onClick={() => submitFeedback('down', feedbackReason)}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
                >
                  Submit
                </button>
                <button
                  onClick={() => {
                    setFeedbackRating(null)
                    setFeedbackReason('')
                  }}
                  className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-lg"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
