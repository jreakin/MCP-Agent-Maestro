"use client"

import { useEffect, useState } from 'react'
import { useServerStore } from '@/lib/stores/server-store'
import { apiClient } from '@/lib/api'

export function ApiClientInitializer() {
  const { activeServerId, servers } = useServerStore()
  const [isHydrated, setIsHydrated] = useState(false)

  // Hydrate the store on client side and switch to real localStorage storage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        // Switch from no-op storage to real localStorage storage
        const { createJSONStorage } = require('zustand/middleware')
        const clientStorage = createJSONStorage(() => {
          try {
            return window.localStorage
          } catch {
            // Return a no-op if localStorage fails
            return {
              getItem: () => null,
              setItem: () => {},
              removeItem: () => {},
              length: 0,
              clear: () => {},
              key: () => null,
            } as any
          }
        })
        
        // Update storage and rehydrate
        useServerStore.persist.setOptions({
          storage: clientStorage
        })
        useServerStore.persist.rehydrate()
        setIsHydrated(true)
      } catch (e) {
        // If localStorage fails, continue without persistence
        console.warn('Failed to initialize localStorage:', e)
        setIsHydrated(true)
      }
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