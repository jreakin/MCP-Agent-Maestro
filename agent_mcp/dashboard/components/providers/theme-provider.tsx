"use client"

import React, { useEffect, useState } from 'react'
import { useTheme } from '@/lib/store'

interface ThemeProviderProps {
  children: React.ReactNode
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [mounted, setMounted] = useState(false)
  const { theme, setTheme } = useTheme()

  useEffect(() => {
    setMounted(true)
    
    // Hydrate theme from localStorage on mount
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('theme-storage')
        if (stored) {
          const parsed = JSON.parse(stored)
          if (parsed?.state?.theme && parsed.state.theme !== theme) {
            setTheme(parsed.state.theme)
            return // setTheme will trigger the theme initialization
          }
        }
      } catch (e) {
        // Ignore localStorage errors
      }
    }
    
    // Initialize theme on mount
    const initializeTheme = () => {
      const currentTheme = theme
      const isDark = currentTheme === 'dark' || 
        (currentTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
      
      if (isDark) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    }
    
    initializeTheme()
    
    // Listen for system theme changes
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handleChange = () => {
        setTheme('system') // This will re-trigger the theme calculation
      }
      
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme, setTheme])

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return (
      <div className="min-h-screen bg-background" suppressHydrationWarning>
        {children}
      </div>
    )
  }

  return <>{children}</>
}