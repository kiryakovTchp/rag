import { useState, useEffect, useRef } from 'react'

export function useWebSocket(url: string) {
  const [messages, setMessages] = useState<string[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)

  useEffect(() => {
    const connect = () => {
      try {
        const base = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
        const token = localStorage.getItem('auth_token')
        const authQuery = token ? `?token=${encodeURIComponent(token)}` : ''
        const wsUrl = `${base}${url}${authQuery}`
        const ws = new WebSocket(wsUrl)
        
        ws.onopen = () => {
          console.log('WebSocket connected')
          setConnected(true)
        }

        ws.onmessage = (event) => {
          setMessages(prev => [...prev, event.data])
        }

        ws.onclose = () => {
          console.log('WebSocket disconnected')
          setConnected(false)
          
          // Reconnect after 5 seconds
          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect()
          }, 5000)
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          setConnected(false)
        }

        wsRef.current = ws
      } catch (error) {
        console.error('Failed to connect WebSocket:', error)
        setConnected(false)
      }
    }

    connect()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current !== null) window.clearTimeout(reconnectTimeoutRef.current)
    }
  }, [url])

  const sendMessage = (message: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(message)
    }
  }

  return {
    messages,
    connected,
    sendMessage
  }
}
