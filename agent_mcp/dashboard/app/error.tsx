"use client"

import { useEffect } from "react"
import { Button } from "@/components/ui/button"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log error but don't crash - localStorage errors during SSR are expected
    if (error.message.includes('local storage') || error.message.includes('localStorage')) {
      console.warn('SSR localStorage error (expected):', error.message)
      // Auto-retry after a short delay
      setTimeout(() => {
        window.location.reload()
      }, 1000)
      return
    }
    console.error('Dashboard error:', error)
  }, [error])

  // For localStorage errors, show a loading state and auto-reload
  if (error.message.includes('local storage') || error.message.includes('localStorage')) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p>Initializing dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-4">Something went wrong!</h2>
        <p className="text-muted-foreground mb-4">{error.message}</p>
        <Button onClick={reset}>Try again</Button>
      </div>
    </div>
  )
}

