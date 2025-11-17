"use client"

import React, { useState, useEffect, useCallback } from "react"
import { 
  Settings, CheckCircle2, AlertCircle, XCircle, Copy, Download, 
  RefreshCw, Zap, Info, Code, ChevronRight, ChevronDown
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from "@/components/ui/select"
import { 
  Tabs, TabsContent, TabsList, TabsTrigger 
} from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { apiClient } from "@/lib/api"
import { useServerStore } from "@/lib/stores/server-store"
import { ServerConnection } from "@/components/server/server-connection"
import { cn } from "@/lib/utils"

type ClientType = 'cursor' | 'claude' | 'windsurf' | 'vscode'

interface VerificationResult {
  exists: boolean
  valid: boolean
  path?: string
  config?: any
  errors?: string[]
}

export function MCPSetupDashboard() {
  const { activeServerId, servers } = useServerStore()
  const activeServer = servers.find(s => s.id === activeServerId)
  const isConnected = !!activeServerId && activeServer?.status === 'connected'

  const [selectedClient, setSelectedClient] = useState<ClientType>('cursor')
  const [configOptions, setConfigOptions] = useState({
    host: 'localhost',
    port: 8080,
    command: 'agent-mcp'
  })
  const [generatedConfig, setGeneratedConfig] = useState<any>(null)
  const [configJson, setConfigJson] = useState('')
  const [verificationResults, setVerificationResults] = useState<Record<string, VerificationResult>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [copied, setCopied] = useState(false)
  const [installResults, setInstallResults] = useState<Record<string, { success: boolean; message?: string; error?: string }>>({})
  const [expandedClients, setExpandedClients] = useState<Set<ClientType>>(new Set())

  // Load verification results on mount
  useEffect(() => {
    if (isConnected) {
      verifyAllConfigs()
    }
  }, [isConnected])

  const generateConfig = useCallback(async () => {
    if (!isConnected) return

    setIsLoading(true)
    try {
      const result = await apiClient.getMCPConfig(selectedClient, configOptions)
      setGeneratedConfig(result.config)
      setConfigJson(JSON.stringify(result.config, null, 2))
    } catch (error) {
      console.error('Failed to generate config:', error)
    } finally {
      setIsLoading(false)
    }
  }, [selectedClient, configOptions, isConnected])

  const verifyAllConfigs = useCallback(async () => {
    if (!isConnected) return

    setIsVerifying(true)
    try {
      const result = await apiClient.verifyMCPConfigs()
      setVerificationResults(result.results)
    } catch (error) {
      console.error('Failed to verify configs:', error)
    } finally {
      setIsVerifying(false)
    }
  }, [isConnected])

  const installConfig = useCallback(async (client: ClientType) => {
    if (!isConnected) return

    setIsLoading(true)
    try {
      const result = await apiClient.installMCPConfig(client, {
        ...configOptions,
        backup: true
      })
      
      setInstallResults(prev => ({
        ...prev,
        [client]: result
      }))

      // Refresh verification after install
      await verifyAllConfigs()
    } catch (error) {
      console.error('Failed to install config:', error)
      setInstallResults(prev => ({
        ...prev,
        [client]: {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      }))
    } finally {
      setIsLoading(false)
    }
  }, [configOptions, isConnected, verifyAllConfigs])

  const copyToClipboard = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }, [])

  const downloadConfig = useCallback((config: any, filename: string) => {
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [])

  const toggleClient = (client: ClientType) => {
    setExpandedClients(prev => {
      const next = new Set(prev)
      if (next.has(client)) {
        next.delete(client)
      } else {
        next.add(client)
      }
      return next
    })
  }

  const getVerificationIcon = (result: VerificationResult) => {
    if (!result.exists) {
      return <XCircle className="h-4 w-4 text-muted-foreground" />
    }
    if (result.valid) {
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    }
    return <AlertCircle className="h-4 w-4 text-amber-500" />
  }

  const getVerificationStatus = (result: VerificationResult) => {
    if (!result.exists) {
      return { label: 'Not Installed', className: 'text-muted-foreground' }
    }
    if (result.valid) {
      return { label: 'Installed & Valid', className: 'text-green-500' }
    }
    return { label: 'Has Errors', className: 'text-amber-500' }
  }

  if (!isConnected) {
    return (
      <div className="h-full w-full">
        <ServerConnection />
      </div>
    )
  }

  return (
    <div className="relative w-full space-y-[var(--space-fluid-lg)]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-fluid-2xl font-bold text-foreground">MCP Client Setup</h1>
          <p className="text-slate-400 dark:text-slate-400 text-slate-600 text-fluid-base mt-1">
            Configure and install MCP Maestro for Cursor, Claude Desktop, Windsurf, or VS Code
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={verifyAllConfigs}
            disabled={isVerifying}
          >
            <RefreshCw className={cn("h-3.5 w-3.5 mr-1.5", isVerifying && "animate-spin")} />
            Verify All
          </Button>
        </div>
      </div>

      <Tabs defaultValue="automatic" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="automatic">Automatic Setup</TabsTrigger>
          <TabsTrigger value="manual">Manual Setup</TabsTrigger>
        </TabsList>

        <TabsContent value="automatic" className="space-y-4">
          {/* Configuration Options */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Server Configuration</CardTitle>
              <CardDescription>
                Configure server connection settings (used for all clients)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="host">Host</Label>
                  <Input
                    id="host"
                    value={configOptions.host}
                    onChange={(e) => setConfigOptions(prev => ({ ...prev, host: e.target.value }))}
                    placeholder="localhost"
                  />
                </div>
                <div>
                  <Label htmlFor="port">Port</Label>
                  <Input
                    id="port"
                    type="number"
                    value={configOptions.port}
                    onChange={(e) => setConfigOptions(prev => ({ ...prev, port: parseInt(e.target.value) || 8080 }))}
                    placeholder="8080"
                  />
                </div>
                <div>
                  <Label htmlFor="command">Command</Label>
                  <Input
                    id="command"
                    value={configOptions.command}
                    onChange={(e) => setConfigOptions(prev => ({ ...prev, command: e.target.value }))}
                    placeholder="agent-mcp"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Client Verification Panel */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Client Status</CardTitle>
              <CardDescription>
                Current installation status for each supported client
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {(['cursor', 'claude', 'windsurf', 'vscode'] as ClientType[]).map(client => {
                const result = verificationResults[client] || { exists: false, valid: false }
                const status = getVerificationStatus(result)
                const isExpanded = expandedClients.has(client)

                return (
                  <div key={client} className="border rounded-lg">
                    <button
                      onClick={() => toggleClient(client)}
                      className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {getVerificationIcon(result)}
                        <div className="text-left">
                          <div className="font-medium capitalize">{client}</div>
                          <div className={cn("text-xs", status.className)}>{status.label}</div>
                        </div>
                      </div>
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>

                    {isExpanded && (
                      <div className="px-4 pb-4 space-y-3 border-t pt-3">
                        {result.path && (
                          <div className="text-sm">
                            <span className="text-muted-foreground">Config Path:</span>
                            <code className="ml-2 text-xs bg-muted px-2 py-1 rounded">{result.path}</code>
                          </div>
                        )}

                        {result.errors && result.errors.length > 0 && (
                          <div className="text-sm space-y-1">
                            <div className="text-amber-500 font-medium">Issues:</div>
                            {result.errors.map((error, idx) => (
                              <div key={idx} className="text-xs text-muted-foreground ml-2">• {error}</div>
                            ))}
                          </div>
                        )}

                        {result.config && (
                          <div className="text-sm">
                            <div className="text-muted-foreground mb-1">Current Configuration:</div>
                            <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                              {JSON.stringify(result.config, null, 2)}
                            </pre>
                          </div>
                        )}

                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => installConfig(client)}
                            disabled={isLoading}
                            variant={result.valid ? "outline" : "default"}
                          >
                            {result.valid ? "Reinstall" : "Install"}
                          </Button>
                          {installResults[client] && (
                            <Badge variant={installResults[client].success ? "default" : "destructive"}>
                              {installResults[client].success ? "Installed" : "Failed"}
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manual" className="space-y-4">
          {/* Manual Configuration Generator */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Generate Configuration</CardTitle>
              <CardDescription>
                Generate configuration file for manual installation
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Label htmlFor="client-select">Client</Label>
                  <Select
                    value={selectedClient}
                    onValueChange={(value: ClientType) => setSelectedClient(value)}
                  >
                    <SelectTrigger id="client-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cursor">Cursor</SelectItem>
                      <SelectItem value="claude">Claude Desktop</SelectItem>
                      <SelectItem value="windsurf">Windsurf</SelectItem>
                      <SelectItem value="vscode">VS Code</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end gap-2">
                  <Button
                    onClick={generateConfig}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4 mr-2" />
                        Generate
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {configJson && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Configuration JSON</Label>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(configJson)}
                      >
                        {copied ? (
                          <>
                            <CheckCircle2 className="h-4 w-4 mr-2" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4 mr-2" />
                            Copy
                          </>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadConfig(generatedConfig, `agent-mcp-${selectedClient}-config.json`)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    </div>
                  </div>
                  <Textarea
                    value={configJson}
                    readOnly
                    className="font-mono text-xs min-h-[200px]"
                  />
                </div>
              )}

              {!configJson && (
                <div className="flex items-center justify-center p-8 text-center border-2 border-dashed rounded-lg">
                  <div className="space-y-2">
                    <Info className="h-8 w-8 text-muted-foreground mx-auto" />
                    <p className="text-sm text-muted-foreground">
                      Select a client and click Generate to create a configuration
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Installation Instructions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Installation Instructions</CardTitle>
              <CardDescription>
                Manual installation steps for each client
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Cursor</h4>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground ml-2">
                    <li>Open Cursor Settings (Cmd/Ctrl + ,)</li>
                    <li>Search for "Claude" or "MCP"</li>
                    <li>Find the MCP Servers configuration</li>
                    <li>Copy the generated configuration into the settings file</li>
                    <li>Restart Cursor</li>
                  </ol>
                </div>
                <Separator />
                <div>
                  <h4 className="font-medium mb-2">Claude Desktop</h4>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground ml-2">
                    <li>Locate the Claude configuration file at: <code className="bg-muted px-1 rounded">~/Library/Application Support/Claude/claude_desktop_config.json</code> (macOS)</li>
                    <li>Open the file in a text editor</li>
                    <li>Add the generated configuration under the <code className="bg-muted px-1 rounded">mcpServers</code> key</li>
                    <li>Restart Claude Desktop</li>
                  </ol>
                </div>
                <Separator />
                <div>
                  <h4 className="font-medium mb-2">Windsurf</h4>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground ml-2">
                    <li>Open Windsurf Settings</li>
                    <li>Navigate to MCP Configuration</li>
                    <li>Paste the generated configuration</li>
                    <li>Restart Windsurf</li>
                  </ol>
                </div>
                <Separator />
                <div>
                  <h4 className="font-medium mb-2">VS Code</h4>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground ml-2">
                    <li>Install the Claude extension for VS Code</li>
                    <li>Open VS Code Settings (Cmd/Ctrl + ,)</li>
                    <li>Find MCP Servers configuration</li>
                    <li>Add the generated configuration</li>
                    <li>Reload VS Code</li>
                  </ol>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

