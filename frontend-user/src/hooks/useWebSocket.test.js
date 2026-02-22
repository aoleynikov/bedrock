import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWebSocket } from './useWebSocket'

describe('useWebSocket', () => {
  let mockWs

  beforeEach(() => {
    mockWs = {
      readyState: 0,
      close: vi.fn(),
      send: vi.fn(),
    }
    vi.stubGlobal('WebSocket', vi.fn(() => mockWs))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('does not connect when url or token is missing', () => {
    const { result } = renderHook(() => useWebSocket({ url: '', token: 'x' }))
    expect(result.current.readyState).toBe(3)
  })

  it('connects when url and token are provided', () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: 'ws://localhost/ws', token: 'token1' })
    )
    expect(WebSocket).toHaveBeenCalledWith(
      'ws://localhost/ws?token=token1'
    )
    expect(result.current.readyState).toBe(0)
  })

  it('updates readyState to OPEN when connection opens', () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: 'ws://localhost/ws', token: 't' })
    )
    act(() => {
      mockWs.readyState = 1
      if (mockWs.onopen) mockWs.onopen()
    })
    expect(result.current.readyState).toBe(1)
  })

  it('updates lastMessage when message is received', () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: 'ws://localhost/ws', token: 't' })
    )
    act(() => {
      if (mockWs.onmessage) mockWs.onmessage({ data: '{"x":1}' })
    })
    expect(result.current.lastMessage).toEqual({ x: 1 })
  })

  it('calls close on unmount', () => {
    const { unmount } = renderHook(() =>
      useWebSocket({ url: 'ws://localhost/ws', token: 't' })
    )
    unmount()
    expect(mockWs.close).toHaveBeenCalled()
  })
})
