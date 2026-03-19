import { useEffect, useState } from 'react'
import { api, ENDPOINTS } from '../services/api'

export function useApi<T>(endpoint: string, params?: Record<string, any>) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refetch = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get(endpoint, { params })
      setData(response.data)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refetch()
  }, [endpoint])

  return { data, loading, error, refetch }
}

export function useWebSocket(url: string) {
  const [connected, setConnected] = useState(false)
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    const ws = new WebSocket(url)

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (event) => {
      setData(JSON.parse(event.data))
    }

    return () => ws.close()
  }, [url])

  return { connected, data }
}
