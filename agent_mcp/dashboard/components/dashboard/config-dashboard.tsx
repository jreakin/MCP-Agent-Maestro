"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, Save, CheckCircle2, AlertCircle, Eye, EyeOff } from "lucide-react"
import { api } from "@/lib/api"

interface ConfigValues {
  [key: string]: string
}

export function ConfigDashboard() {
  const [config, setConfig] = useState<ConfigValues>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showPasswords, setShowPasswords] = useState<{ [key: string]: boolean }>({})
  const [changes, setChanges] = useState<ConfigValues>({})

  // Load configuration on mount
  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.getConfig()
      if (response.success) {
        setConfig(response.config || {})
        setChanges({})
      } else {
        setError("Failed to load configuration")
      }
    } catch (err: any) {
      setError(err.message || "Failed to load configuration")
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (key: string, value: string) => {
    setChanges(prev => ({ ...prev, [key]: value }))
    setConfig(prev => ({ ...prev, [key]: value }))
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      setError(null)
      setSuccess(null)

      const response = await api.updateConfig(changes)
      
      if (response.success) {
        setSuccess(response.message || "Configuration saved successfully")
        setChanges({})
        // Reload to get updated masked values
        setTimeout(() => loadConfig(), 1000)
      } else {
        setError(response.message || "Failed to save configuration")
      }
    } catch (err: any) {
      setError(err.message || "Failed to save configuration")
    } finally {
      setSaving(false)
    }
  }

  const togglePasswordVisibility = (key: string) => {
    setShowPasswords(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const isPasswordField = (key: string) => {
    return key.includes("API_KEY") || key.includes("PASSWORD") || key.includes("SECRET")
  }

  const isMasked = (value: string) => {
    return typeof value === "string" && value.startsWith("***")
  }

  const hasChanges = Object.keys(changes).length > 0

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full w-full p-6 space-y-6 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Configuration</h1>
          <p className="text-muted-foreground mt-1">
            Manage API keys and environment variables
          </p>
        </div>
        {hasChanges && (
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        )}
      </div>

      {/* Alerts */}
      {error && (
        <Alert className="border-red-500 bg-red-50 dark:bg-red-950">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800 dark:text-red-200">{error}</AlertDescription>
        </Alert>
      )}
      {success && (
        <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800 dark:text-green-200">
            {success}
          </AlertDescription>
        </Alert>
      )}

      {/* Configuration Tabs */}
      <Tabs defaultValue="api-keys" className="w-full">
        <TabsList>
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          <TabsTrigger value="database">Database</TabsTrigger>
          <TabsTrigger value="server">Server</TabsTrigger>
          <TabsTrigger value="ollama">Ollama</TabsTrigger>
        </TabsList>

        {/* API Keys Tab */}
        <TabsContent value="api-keys" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>OpenAI Configuration</CardTitle>
              <CardDescription>
                Configure your OpenAI API key for embeddings and chat completion
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="openai_api_key">OpenAI API Key</Label>
                <div className="flex gap-2">
                  <Input
                    id="openai_api_key"
                    type={showPasswords["AGENT_MCP_OPENAI_API_KEY"] ? "text" : "password"}
                    value={config["AGENT_MCP_OPENAI_API_KEY"] || config["OPENAI_API_KEY"] || ""}
                    onChange={(e) => handleChange("AGENT_MCP_OPENAI_API_KEY", e.target.value)}
                    placeholder="sk-..."
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => togglePasswordVisibility("AGENT_MCP_OPENAI_API_KEY")}
                  >
                    {showPasswords["AGENT_MCP_OPENAI_API_KEY"] ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Optional if using Ollama. Get your key from{" "}
                  <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="underline">
                    OpenAI Platform
                  </a>
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Embedding Provider</CardTitle>
              <CardDescription>
                Choose your embedding provider (OpenAI or Ollama)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="embedding_provider">Provider</Label>
                <select
                  id="embedding_provider"
                  value={config["EMBEDDING_PROVIDER"] || "openai"}
                  onChange={(e) => handleChange("EMBEDDING_PROVIDER", e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                >
                  <option value="openai">OpenAI</option>
                  <option value="ollama">Ollama (Local)</option>
                </select>
                <p className="text-xs text-muted-foreground">
                  Use Ollama for local models, or OpenAI for cloud-based embeddings
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Database Tab */}
        <TabsContent value="database" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Database Configuration</CardTitle>
              <CardDescription>
                Configure PostgreSQL database connection settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="db_host">Host</Label>
                  <Input
                    id="db_host"
                    value={config["AGENT_MCP_DB_HOST"] || ""}
                    onChange={(e) => handleChange("AGENT_MCP_DB_HOST", e.target.value)}
                    placeholder="localhost or postgres"
                  />
                  <p className="text-xs text-muted-foreground">
                    Use "postgres" for Docker, "localhost" for local
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="db_port">Port</Label>
                  <Input
                    id="db_port"
                    type="number"
                    value={config["AGENT_MCP_DB_PORT"] || ""}
                    onChange={(e) => handleChange("AGENT_MCP_DB_PORT", e.target.value)}
                    placeholder="5432"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="db_name">Database Name</Label>
                  <Input
                    id="db_name"
                    value={config["AGENT_MCP_DB_NAME"] || ""}
                    onChange={(e) => handleChange("AGENT_MCP_DB_NAME", e.target.value)}
                    placeholder="agent_mcp"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="db_user">User</Label>
                  <Input
                    id="db_user"
                    value={config["AGENT_MCP_DB_USER"] || ""}
                    onChange={(e) => handleChange("AGENT_MCP_DB_USER", e.target.value)}
                    placeholder="agent_mcp"
                  />
                </div>
                <div className="space-y-2 col-span-2">
                  <Label htmlFor="db_password">Password</Label>
                  <div className="flex gap-2">
                    <Input
                      id="db_password"
                      type={showPasswords["AGENT_MCP_DB_PASSWORD"] ? "text" : "password"}
                      value={config["AGENT_MCP_DB_PASSWORD"] || ""}
                      onChange={(e) => handleChange("AGENT_MCP_DB_PASSWORD", e.target.value)}
                      placeholder="Enter database password"
                      className="flex-1"
                    />
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => togglePasswordVisibility("AGENT_MCP_DB_PASSWORD")}
                    >
                      {showPasswords["AGENT_MCP_DB_PASSWORD"] ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Server Tab */}
        <TabsContent value="server" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Server Configuration</CardTitle>
              <CardDescription>
                Configure API server and logging settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="api_port">API Port</Label>
                  <Input
                    id="api_port"
                    type="number"
                    value={config["AGENT_MCP_API_PORT"] || ""}
                    onChange={(e) => handleChange("AGENT_MCP_API_PORT", e.target.value)}
                    placeholder="8080"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="log_level">Log Level</Label>
                  <select
                    id="log_level"
                    value={config["AGENT_MCP_LOG_LEVEL"] || "INFO"}
                    onChange={(e) => handleChange("AGENT_MCP_LOG_LEVEL", e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                  >
                    <option value="DEBUG">DEBUG</option>
                    <option value="INFO">INFO</option>
                    <option value="WARNING">WARNING</option>
                    <option value="ERROR">ERROR</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Ollama Tab */}
        <TabsContent value="ollama" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Ollama Configuration</CardTitle>
              <CardDescription>
                Configure Ollama for local model usage
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="ollama_base_url">Ollama Base URL</Label>
                  <Input
                    id="ollama_base_url"
                    value={config["OLLAMA_BASE_URL"] || ""}
                    onChange={(e) => handleChange("OLLAMA_BASE_URL", e.target.value)}
                    placeholder="http://localhost:11434"
                  />
                  <p className="text-xs text-muted-foreground">
                    For Docker: use http://host.docker.internal:11434
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ollama_embedding_model">Embedding Model</Label>
                  <Input
                    id="ollama_embedding_model"
                    value={config["OLLAMA_EMBEDDING_MODEL"] || ""}
                    onChange={(e) => handleChange("OLLAMA_EMBEDDING_MODEL", e.target.value)}
                    placeholder="nomic-embed-text"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ollama_chat_model">Chat Model</Label>
                  <Input
                    id="ollama_chat_model"
                    value={config["OLLAMA_CHAT_MODEL"] || ""}
                    onChange={(e) => handleChange("OLLAMA_CHAT_MODEL", e.target.value)}
                    placeholder="llama3.2"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

