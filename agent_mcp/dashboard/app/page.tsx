"use client"

import { useEffect, useState } from "react"

// Force this page to be client-side only - no SSR at all
export const dynamic = 'force-dynamic'

// Simple client-only loader that doesn't import any stores during module load
function ClientOnlyLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100 mx-auto mb-4"></div>
        <p className="text-muted-foreground">Loading dashboard...</p>
      </div>
    </div>
  )
}

// This component loads all dashboard code dynamically after mount
function DashboardApp() {
  const [Component, setComponent] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Dynamically import everything after component mounts (client-side only)
    import("@/components/dashboard/dashboard-content")
      .then((mod) => {
        setComponent(() => mod.DashboardContent)
      })
      .catch((err) => {
        console.error("Failed to load dashboard:", err)
        setError(err.message)
      })
  }, [])

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Error loading dashboard</h2>
          <p className="text-muted-foreground">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded"
          >
            Reload
          </button>
        </div>
      </div>
    )
  }

  if (!Component) {
    return <ClientOnlyLoader />
  }

  return <Component />
}

export default function HomePage() {
  // Always render a loading state during SSR
  // Only load the actual dashboard on the client
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (!isClient) {
    return <ClientOnlyLoader />
  }

  return <DashboardApp />
}
