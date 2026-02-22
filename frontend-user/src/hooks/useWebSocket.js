import { useState, useEffect, useRef, useCallback } from 'react'

const CONNECTING = 0
const OPEN = 1
const CLOSING = 2
const CLOSED = 3

export function useWebSocket({ url, token }) {
  const [readyState, setReadyState] = useState(CLOSED)
  const [lastMessage, setLastMessage] = useState(null)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectDelay = 30000

  const connect = useCallback(() => {
    if (!url || !token) {
      setReadyState(CLOSED)
      return
    }
    const separator = url.includes('?') ? '&' : '?'
    const fullUrl = `${url}${separator}token=${encodeURIComponent(token)}`
    setError(null)
    setReadyState(CONNECTING)
    const ws = new WebSocket(fullUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setReadyState(OPEN)
      reconnectAttempts.current = 0
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setLastMessage(data)
      } catch {
        setLastMessage(event.data)
      }
    }

    ws.onerror = (event) => {
      setError(event)
    }

    ws.onclose = () => {
      setReadyState(CLOSED)
      wsRef.current = null
      if (!url || !token) return
      const delay = Math.min(1000 * 2 ** reconnectAttempts.current, maxReconnectDelay)
      reconnectAttempts.current += 1
      reconnectTimeoutRef.current = setTimeout(connect, delay)
    }
  }, [url, token])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      setReadyState(CLOSED)
    }
  }, [connect])

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [readyState])

  return { readyState, lastMessage, error, send }
}
