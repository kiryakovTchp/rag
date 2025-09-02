import { useState, useEffect, useRef, useCallback } from 'react'
import { Job, WebSocketMessage, WebSocketError } from '@/types'

interface UseJobsWebSocketOptions {
  tenantId?: string
  wsUrl?: string
  maxReconnectAttempts?: number
  reconnectDelay?: number
  onError?: (error: WebSocketError) => void
  onJobUpdate?: (job: Job) => void
}

interface WebSocketState {
  status: 'connecting' | 'connected' | 'reconnecting' | 'disconnected' | 'error'
  lastMessage: WebSocketMessage | null
  reconnectAttempts: number
  errors: WebSocketError[]
  isReconnecting: boolean
}

export function useJobsWebSocket({
  tenantId,
  wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  maxReconnectAttempts = 10,
  reconnectDelay = 1000,
  onError,
  onJobUpdate
}: UseJobsWebSocketOptions) {
  const [jobs, setJobs] = useState<Map<string, Job>>(new Map())
  const [events, setEvents] = useState<WebSocketMessage[]>([])
  const [state, setState] = useState<WebSocketState>({
    status: 'disconnected',
    lastMessage: null,
    reconnectAttempts: 0,
    errors: [],
    isReconnecting: false
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      setState(prev => ({ ...prev, status: 'connecting' }))
      
      const url = tenantId ? `${wsUrl}/ws/jobs?tenant_id=${tenantId}` : `${wsUrl}/ws/jobs`
      const ws = new WebSocket(url)
      
      ws.onopen = () => {
        setState(prev => ({ 
          ...prev, 
          status: 'connected', 
          reconnectAttempts: 0,
          isReconnecting: false 
        }))
        reconnectAttemptsRef.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setState(prev => ({ ...prev, lastMessage: message }))
          setEvents(prev => [message, ...prev.slice(0, 99)]) // Keep last 100 events

          // Handle job updates
          if (message.job_id && message.event) {
            const existingJob = jobs.get(message.job_id)
            if (existingJob) {
              const updatedJob: Job = {
                ...existingJob,
                status: message.event === 'parse_done' ? 'done' : 
                        message.event === 'failed' ? 'failed' : 'running',
                progress: message.progress || existingJob.progress,
                error: message.error,
                completed_at: message.event === 'parse_done' ? message.ts : existingJob.completed_at
              }
              
              setJobs(prev => new Map(prev.set(message.job_id!, updatedJob)))
              onJobUpdate?.(updatedJob)
            }
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        const error: WebSocketError = {
          code: event.code,
          reason: event.reason || 'Connection closed',
          timestamp: new Date().toISOString()
        }

        setState(prev => ({ 
          ...prev, 
          status: 'disconnected',
          errors: [...prev.errors, error]
        }))

        // Handle specific error codes
        if (event.code === 4000) {
          console.error('Redis unavailable')
        } else if (event.code === 4001) {
          console.error('Unauthorized')
        } else if (event.code === 4002) {
          console.error('No tenant_id provided')
        }

        onError?.(error)

        // Attempt to reconnect if not manually closed
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          scheduleReconnect()
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setState(prev => ({ ...prev, status: 'error' }))
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      setState(prev => ({ ...prev, status: 'error' }))
    }
  }, [wsUrl, tenantId, maxReconnectAttempts, onError, onJobUpdate, jobs])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }

    setState(prev => ({ 
      ...prev, 
      status: 'disconnected',
      isReconnecting: false 
    }))
    reconnectAttemptsRef.current = 0
  }, [])

  const scheduleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      setState(prev => ({ ...prev, status: 'error' }))
      return
    }

    setState(prev => ({ 
      ...prev, 
      status: 'reconnecting',
      isReconnecting: true 
    }))

    const delay = reconnectDelay * Math.pow(2, reconnectAttemptsRef.current)
    reconnectAttemptsRef.current++

    reconnectTimeoutRef.current = setTimeout(() => {
      connect()
    }, delay)
  }, [connect, maxReconnectAttempts, reconnectDelay])

  const reconnect = useCallback(() => {
    disconnect()
    reconnectAttemptsRef.current = 0
    connect()
  }, [disconnect, connect])

  const clearErrors = useCallback(() => {
    setState(prev => ({ ...prev, errors: [] }))
  }, [])

  // Auto-connect on mount and when tenantId changes
  useEffect(() => {
    if (tenantId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [tenantId, connect, disconnect])

  // Helper functions
  const getJobsArray = useCallback(() => Array.from(jobs.values()), [jobs])
  const activeJobs = useCallback(() => getJobsArray().filter(job => job.status === 'running'), [getJobsArray])
  const completedJobs = useCallback(() => getJobsArray().filter(job => job.status === 'done'), [getJobsArray])
  const failedJobs = useCallback(() => getJobsArray().filter(job => job.status === 'failed'), [getJobsArray])
  const pendingJobs = useCallback(() => getJobsArray().filter(job => job.status === 'queued'), [getJobsArray])
  
  const getJob = useCallback((id: string) => jobs.get(id), [jobs])
  const getJobsByType = useCallback((type: Job['kind']) => getJobsArray().filter(job => job.kind === type), [getJobsArray])
  const getJobsByTenant = useCallback((tenant: string) => getJobsArray().filter(job => job.tenant_id === tenant), [getJobsArray])

  return {
    jobs: getJobsArray(),
    events,
    state,
    connect,
    disconnect,
    reconnect,
    clearErrors,
    activeJobs: activeJobs(),
    completedJobs: completedJobs(),
    failedJobs: failedJobs(),
    pendingJobs: pendingJobs(),
    getJob,
    getJobsByType,
    getJobsByTenant
  }
}
