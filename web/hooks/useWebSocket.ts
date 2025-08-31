import { useState, useEffect, useRef } from 'react'
import { useSession } from 'next-auth/react'

export function useWebSocket(url: string) {
  const { data: session } = useSession()
  const [messages, setMessages] = useState<string[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!session?.accessToken) {
      setConnected(false)
      return
    }

    const connect = () => {
      try {
        const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}${url}?token=${session.accessToken}`
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
          reconnectTimeoutRef.current = setTimeout(() => {
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
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [url, session?.accessToken])

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
