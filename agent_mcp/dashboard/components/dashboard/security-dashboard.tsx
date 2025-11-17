"use client"

import React, { useState, useEffect } from "react"
import { AlertTriangle, Shield, Activity, Clock, CheckCircle2, XCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { apiClient } from "@/lib/api"
import { useWebSocket } from "@/hooks/useWebSocket"

interface SecurityAlert {
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  message: string
  details: Record<string, any>
  timestamp: string
  agent_id?: string
  tool_name?: string
}

interface SecurityScan {
  id: string
  type: string
  status: 'safe' | 'threat_detected'
  timestamp: string
  threats?: Array<{ type: string; severity: string }>
}

export function SecurityDashboard() {
  const [alerts, setAlerts] = useState<SecurityAlert[]>([])
  const [scans, setScans] = useState<SecurityScan[]>([])
  const [loading, setLoading] = useState(true)

  const fetchAlerts = async () => {
    try {
      const data = await apiClient.getSecurityAlerts(50)
      setAlerts(data.alerts || [])
    } catch (error) {
      console.error('Failed to fetch security alerts:', error)
    }
  }

  const fetchScanHistory = async () => {
    try {
      const data = await apiClient.getSecurityScanHistory()
      setScans(data.scans || [])
    } catch (error) {
      console.error('Failed to fetch scan history:', error)
    }
  }

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([fetchAlerts(), fetchScanHistory()])
      setLoading(false)
    }
    loadData()
  }, [])

  // WebSocket for real-time security alerts
  useWebSocket<{ type: string; alert: SecurityAlert }>(
    '/ws/security',
    (message) => {
      if (message.type === 'security_alert' && message.alert) {
        setAlerts(prev => [message.alert, ...prev].slice(0, 50))
      }
    },
    { reconnect: true }
  )

  const getSeverityColor = (severity: SecurityAlert['severity']) => {
    switch (severity) {
      case 'CRITICAL': return 'bg-red-500 text-white'
      case 'HIGH': return 'bg-orange-500 text-white'
      case 'MEDIUM': return 'bg-yellow-500 text-black'
      case 'LOW': return 'bg-blue-500 text-white'
      default: return 'bg-gray-500 text-white'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString()
  }

  const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL').length
  const highAlerts = alerts.filter(a => a.severity === 'HIGH').length
  const totalAlerts = alerts.length

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">Security Dashboard</h1>
        <p className="text-muted-foreground">Monitor security alerts and scan history</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalAlerts}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Critical</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{criticalAlerts}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">High</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-500">{highAlerts}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Scans</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scans.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Recent Security Alerts</CardTitle>
            <Button variant="outline" size="sm" onClick={fetchAlerts}>
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            {alerts.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Shield className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No security alerts</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert, index) => (
                  <div
                    key={index}
                    className={cn(
                      "border rounded-lg p-4",
                      alert.severity === 'CRITICAL' && "border-red-500 bg-red-50 dark:bg-red-950",
                      alert.severity === 'HIGH' && "border-orange-500 bg-orange-50 dark:bg-orange-950",
                      alert.severity === 'MEDIUM' && "border-yellow-500 bg-yellow-50 dark:bg-yellow-950",
                      alert.severity === 'LOW' && "border-blue-500 bg-blue-50 dark:bg-blue-950"
                    )}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge className={getSeverityColor(alert.severity)}>
                          {alert.severity}
                        </Badge>
                        {alert.agent_id && (
                          <Badge variant="outline">Agent: {alert.agent_id}</Badge>
                        )}
                        {alert.tool_name && (
                          <Badge variant="outline">Tool: {alert.tool_name}</Badge>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {formatTimestamp(alert.timestamp)}
                      </span>
                    </div>
                    <p className="font-medium mb-1">{alert.message}</p>
                    {Object.keys(alert.details).length > 0 && (
                      <details className="mt-2">
                        <summary className="text-sm text-muted-foreground cursor-pointer">
                          Details
                        </summary>
                        <pre className="mt-2 text-xs bg-background p-2 rounded overflow-auto">
                          {JSON.stringify(alert.details, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Scan History */}
      <Card>
        <CardHeader>
          <CardTitle>Scan History</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px]">
            {scans.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No scan history available</p>
              </div>
            ) : (
              <div className="space-y-2">
                {scans.map((scan) => (
                  <div
                    key={scan.id}
                    className="flex items-center justify-between border rounded-lg p-3"
                  >
                    <div className="flex items-center gap-3">
                      {scan.status === 'safe' ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      <div>
                        <p className="font-medium">{scan.type}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatTimestamp(scan.timestamp)}
                        </p>
                      </div>
                    </div>
                    <Badge variant={scan.status === 'safe' ? 'default' : 'destructive'}>
                      {scan.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

