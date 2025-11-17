"use client"

import React, { useState, useEffect } from "react"
import { BarChart3, TrendingUp, Clock, CheckCircle2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api"

interface PromptAnalyticsProps {
  promptId: string
}

interface AnalyticsData {
  prompt_id: string
  usage_count: number
  success_rate: number
  created_at?: string
  updated_at?: string
}

export function PromptAnalytics({ promptId }: PromptAnalyticsProps) {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true)
        // Note: This assumes the API client has a method for prompt analytics
        // You may need to add this method to apiClient
        const response = await fetch(`/api/prompts/${promptId}/analytics`)
        const data = await response.json()
        if (data.prompt_id) {
          setAnalytics(data)
        }
      } catch (error) {
        console.error('Failed to fetch prompt analytics:', error)
      } finally {
        setLoading(false)
      }
    }

    if (promptId) {
      fetchAnalytics()
    }
  }, [promptId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
        <p>No analytics data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Usage Count
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.usage_count}</div>
            <p className="text-xs text-muted-foreground mt-1">Total executions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(analytics.success_rate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">Success rate</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Last Updated
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">
              {analytics.updated_at
                ? new Date(analytics.updated_at).toLocaleDateString()
                : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Last execution</p>
          </CardContent>
        </Card>
      </div>

      {analytics.created_at && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Metadata</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created:</span>
              <span>{new Date(analytics.created_at).toLocaleString()}</span>
            </div>
            {analytics.updated_at && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Updated:</span>
                <span>{new Date(analytics.updated_at).toLocaleString()}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

