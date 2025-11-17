"use client"

import React, { useEffect, useState } from "react"
import { useServerStore } from "@/lib/stores/server-store"

interface DashboardWrapperProps {
  children: React.ReactNode
}

export function DashboardWrapper({ children }: DashboardWrapperProps) {
  const [isHydrated, setIsHydrated] = useState(false)
  const { activeServerId, servers } = useServerStore()
  
  // Hydrate store on client side only
  useEffect(() => {
    if (typeof window !== 'undefined') {
      useServerStore.persist.rehydrate()
      setIsHydrated(true)
    }
  }, [])
  
  const activeServer = servers.find(s => s.id === activeServerId)
  
  // Show server connection if no server is selected or selected server is not connected
  const isConnected = activeServerId && activeServer?.status === 'connected'
  
  // Debug: Log connection status - MUST be before any conditional returns
  useEffect(() => {
    if (isHydrated) {
      console.log('DashboardWrapper - isConnected:', isConnected, 'activeServerId:', activeServerId, 'activeServer:', activeServer)
    }
  }, [isHydrated, isConnected, activeServerId, activeServer])
  
  // Don't render until hydrated to avoid SSR mismatch
  if (!isHydrated) {
    return <div className="h-full w-full flex items-center justify-center">Loading...</div>
  }
  
  // Allow dashboard pages to render even without server connection
  // Individual pages can handle their own connection checks
  // Only show connection prompt on initial load or if user explicitly needs it
  return <div className="h-full w-full">{children}</div>
}