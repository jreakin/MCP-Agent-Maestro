"use client"

import React from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { DashboardWrapper } from "@/components/dashboard/dashboard-wrapper"
import { OverviewDashboard } from "@/components/dashboard/overview-dashboard"
import { AgentsDashboard } from "@/components/dashboard/agents-dashboard"
import { TasksDashboard } from "@/components/dashboard/tasks-dashboard"
import { MemoriesDashboard } from "@/components/dashboard/memories-dashboard"
import { PromptBookDashboard } from "@/components/dashboard/prompt-book-dashboard"
import { SystemDashboard } from "@/components/dashboard/system-dashboard"
import { MCPSetupDashboard } from "@/components/dashboard/mcp-setup-dashboard"
import { ConfigDashboard } from "@/components/dashboard/config-dashboard"
import { useDashboard } from "@/lib/store"

export function DashboardContent() {
  // Use selector to ensure proper subscription
  const currentView = useDashboard((state) => state.currentView)
  const setCurrentView = useDashboard((state) => state.setCurrentView)

  // Debug: Log view changes
  React.useEffect(() => {
    console.log('DashboardContent - currentView changed to:', currentView)
  }, [currentView])

  // Force re-render on mount to check initial state
  React.useEffect(() => {
    console.log('DashboardContent mounted, currentView:', currentView)
    const store = useDashboard.getState()
    console.log('Store state on mount:', store.currentView)
  }, [])

  // Render the current view directly (not in a function) to ensure re-renders
  // Add key to force re-render when view changes
  let content: React.ReactNode
  switch (currentView) {
    case 'overview':
      content = <OverviewDashboard key="overview" />
      break
    case 'agents':
      content = <AgentsDashboard key="agents" />
      break
    case 'tasks':
      content = <TasksDashboard key="tasks" />
      break
    case 'memories':
      content = <MemoriesDashboard key="memories" />
      break
    case 'prompts':
      content = <PromptBookDashboard key="prompts" />
      break
    case 'mcp-setup':
      content = <MCPSetupDashboard key="mcp-setup" />
      break
    case 'system':
      content = <SystemDashboard key="system" />
      break
    case 'config':
      content = <ConfigDashboard key="config" />
      break
    default:
      content = <OverviewDashboard key="overview-default" />
  }

  console.log('DashboardContent rendering with currentView:', currentView)

  return (
    <MainLayout>
      <DashboardWrapper>
        <div key={currentView} style={{ minHeight: '100%', width: '100%' }}>
          {content}
        </div>
      </DashboardWrapper>
    </MainLayout>
  )
}

