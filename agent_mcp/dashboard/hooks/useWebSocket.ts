import { useEffect, useRef, useState, useCallback } from 'react'

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export function useWebSocket<T extends WebSocketMessage>(
  url: string | null,
  onMessage: (data: T) => void,
  options?: {
    reconnect?: boolean
    reconnectInterval?: number
    onOpen?: () => void
    onClose?: () => void
    onError?: (error: Event) => void
  }
) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  
  const {
    reconnect = true,
    reconnectInterval = 3000,
    onOpen,
    onClose,
    onError
  } = options || {}

  const connect = useCallback(() => {
    if (!url) return

    try {
      // Determine WebSocket URL based on current location
      const wsUrl = url.startsWith('ws://') || url.startsWith('wss://')
        ? url
        : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${url}`
      
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setReconnectAttempts(0)
        onOpen?.()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as T
          onMessage(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        onError?.(error)
      }

      ws.onclose = () => {
        setIsConnected(false)
        onClose?.()

        // Attempt to reconnect if enabled
        if (reconnect && reconnectAttempts < 10) {
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1)
            connect()
          }, reconnectInterval)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }, [url, onMessage, reconnect, reconnectInterval, reconnectAttempts, onOpen, onClose, onError])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])

  const send = useCallback((message: string | object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message)
      wsRef.current.send(data)
    } else {
      console.warn('WebSocket is not connected. Cannot send message.')
    }
  }, [])

  return {
    ws: wsRef.current,
    isConnected,
    send,
    reconnectAttempts
  }
}

