"use client"

import { useEffect, useState } from 'react'
import { useServerStore } from '@/lib/stores/server-store'
import { apiClient } from '@/lib/api'

export function ApiClientInitializer() {
  const { activeServerId, servers } = useServerStore()
  const [isHydrated, setIsHydrated] = useState(false)

  // Hydrate the store on client side
  useEffect(() => {
    if (typeof window !== 'undefined') {
      useServerStore.persist.rehydrate()
      setIsHydrated(true)
    }
  }, [])

  useEffect(() => {
    if (!isHydrated) return
    
    console.debug('ApiClientInitializer: Hydrating API client...')
    if (activeServerId) {
      const activeServer = servers.find(s => s.id === activeServerId)
      if (activeServer) {
        console.debug(`ApiClientInitializer: Setting API server to ${activeServer.host}:${activeServer.port}`)
        apiClient.setServer(activeServer.host, activeServer.port)
      }
    }
  }, [activeServerId, servers, isHydrated])

  return null
} 