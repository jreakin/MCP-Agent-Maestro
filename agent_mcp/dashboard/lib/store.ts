import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// No-op storage for SSR
const noOpStorage: Storage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
  length: 0,
  clear: () => {},
  key: () => null,
} as Storage

// SSR-safe storage for zustand persist
const getStorage = () => {
  // Always use no-op during module initialization to prevent SSR errors
  // Real storage will be set up on client side if needed
  return noOpStorage
}

interface ThemeState {
  theme: 'light' | 'dark' | 'system'
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  isDark: boolean
  toggleTheme: () => void
}

// Helper to get initial theme from localStorage (client-side only)
const getInitialTheme = (): 'light' | 'dark' | 'system' => {
  if (typeof window === 'undefined') return 'system'
  try {
    const stored = localStorage.getItem('theme-storage')
    if (stored) {
      const parsed = JSON.parse(stored)
      if (parsed?.state?.theme) {
        return parsed.state.theme
      }
    }
  } catch (e) {
    // Ignore localStorage errors
  }
  return 'system'
}

export const useTheme = create<ThemeState>()((set, get) => ({
  theme: 'system', // Default, will be hydrated on client
  isDark: false,
  setTheme: (theme) => {
    set({ theme })
    
    // Only run in browser environment
    if (typeof window !== 'undefined') {
      const isDark = theme === 'dark' || 
        (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
      set({ isDark })
      
      // Update document class
      if (isDark) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }

      // Save to localStorage
      try {
        localStorage.setItem('theme-storage', JSON.stringify({ state: { theme } }))
      } catch (e) {
        // Ignore localStorage errors
      }
    }
  },
  toggleTheme: () => {
    const currentTheme = get().theme
    const newTheme = currentTheme === 'light' ? 'dark' : 'light'
    get().setTheme(newTheme)
  }
}))

interface SidebarState {
  isCollapsed: boolean
  setCollapsed: (collapsed: boolean) => void
  toggle: () => void
}

export const useSidebar = create<SidebarState>()((set, get) => ({
  isCollapsed: false,
  setCollapsed: (collapsed) => set({ isCollapsed: collapsed }),
  toggle: () => set({ isCollapsed: !get().isCollapsed })
}))

interface DashboardState {
  currentView: 'overview' | 'agents' | 'tasks' | 'memories' | 'prompts' | 'mcp-setup' | 'system' | 'config'
  setCurrentView: (view: 'overview' | 'agents' | 'tasks' | 'memories' | 'prompts' | 'mcp-setup' | 'system' | 'config') => void
  isLoading: boolean
  setLoading: (loading: boolean) => void
  lastUpdated: Date | null
  setLastUpdated: (date: Date) => void
}

export const useDashboard = create<DashboardState>()((set) => ({
  currentView: 'overview',
  setCurrentView: (view) => {
    console.log('Store setCurrentView called with:', view)
    set({ currentView: view })
    console.log('Store state after set:', useDashboard.getState().currentView)
  },
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),
  lastUpdated: null,
  setLastUpdated: (date) => set({ lastUpdated: date })
}))

interface CommandPaletteState {
  isOpen: boolean
  setOpen: (open: boolean) => void
  toggle: () => void
}

export const useCommandPalette = create<CommandPaletteState>()((set, get) => ({
  isOpen: false,
  setOpen: (open) => set({ isOpen: open }),
  toggle: () => set({ isOpen: !get().isOpen })
}))

interface NotificationState {
  notifications: Array<{
    id: string
    title: string
    message: string
    type: 'info' | 'success' | 'warning' | 'error'
    timestamp: Date
    read: boolean
  }>
  addNotification: (notification: Omit<NotificationState['notifications'][0], 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  removeNotification: (id: string) => void
  clearAll: () => void
}

export const useNotifications = create<NotificationState>()((set, get) => ({
  notifications: [],
  addNotification: (notification) => {
    const newNotification = {
      ...notification,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
      read: false
    }
    set({ 
      notifications: [newNotification, ...get().notifications].slice(0, 50) // Keep only latest 50
    })
  },
  markAsRead: (id) => {
    set({
      notifications: get().notifications.map(n => 
        n.id === id ? { ...n, read: true } : n
      )
    })
  },
  removeNotification: (id) => {
    set({
      notifications: get().notifications.filter(n => n.id !== id)
    })
  },
  clearAll: () => set({ notifications: [] })
}))

interface SearchState {
  query: string
  setQuery: (query: string) => void
  results: unknown[]
  setResults: (results: unknown[]) => void
  isSearching: boolean
  setSearching: (searching: boolean) => void
}

export const useSearch = create<SearchState>()((set) => ({
  query: '',
  setQuery: (query) => set({ query }),
  results: [],
  setResults: (results) => set({ results }),
  isSearching: false,
  setSearching: (searching) => set({ isSearching: searching })
}))