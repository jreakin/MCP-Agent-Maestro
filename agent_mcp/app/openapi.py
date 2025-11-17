"""
OpenAPI/Swagger documentation generation for Agent-MCP API.
"""
from typing import Dict, Any, List
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
import json

from ..core.config import VERSION, DESCRIPTION
from ..api.models import (
    TaskCreate,
    TaskUpdate,
    TaskAssign,
    TaskStatusUpdate,
    TaskPriorityUpdate,
    BulkOperation,
    TaskReorder,
    AgentCreate,
    MemoryCreate,
    MemoryUpdate,
    PromptCreate,
    PromptUpdate,
    PromptExecute,
    SecurityScanRequest,
    MCPConfigRequest,
    MCPInstallRequest,
)


def generate_openapi_schema() -> Dict[str, Any]:
    """Generate OpenAPI 3.0 schema from Pydantic models."""
    
    schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "MCP Agent Maestro API",
            "version": VERSION,
            "description": DESCRIPTION,
            "contact": {
                "name": "MCP Agent Maestro",
                "url": "https://github.com/jreakin/mcp-agent-maestro"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8080",
                "description": "Local development server"
            }
        ],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "description": "Check if the service is healthy",
                    "responses": {
                        "200": {
                            "description": "Service is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "timestamp": {"type": "number"},
                                            "checks": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/metrics": {
                "get": {
                    "summary": "Get metrics",
                    "description": "Get system and application metrics",
                    "responses": {
                        "200": {
                            "description": "Metrics data",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/tasks": {
                "get": {
                    "summary": "List all tasks",
                    "description": "Get a list of all tasks",
                    "responses": {
                        "200": {
                            "description": "List of tasks",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/tasks/{task_id}": {
                "get": {
                    "summary": "Get task by ID",
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Task details"},
                        "404": {"description": "Task not found"}
                    }
                },
                "put": {
                    "summary": "Update task",
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": TaskUpdate.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Task updated"},
                        "404": {"description": "Task not found"}
                    }
                },
                "delete": {
                    "summary": "Delete task",
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Task deleted"},
                        "404": {"description": "Task not found"}
                    }
                }
            },
            "/api/tasks/{task_id}/assign": {
                "post": {
                    "summary": "Assign task to agent",
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": TaskAssign.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Task assigned"},
                        "404": {"description": "Task not found"}
                    }
                }
            },
            "/api/tasks/{task_id}/status": {
                "put": {
                    "summary": "Update task status",
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": TaskStatusUpdate.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Status updated"},
                        "404": {"description": "Task not found"}
                    }
                }
            },
            "/api/tasks/{task_id}/priority": {
                "put": {
                    "summary": "Update task priority",
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": TaskPriorityUpdate.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Priority updated"},
                        "404": {"description": "Task not found"}
                    }
                }
            },
            "/api/tasks/bulk": {
                "post": {
                    "summary": "Bulk task operations",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": BulkOperation.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Bulk operation completed"}
                    }
                }
            },
            "/api/security/scan": {
                "post": {
                    "summary": "Scan text for security threats",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": SecurityScanRequest.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Scan results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "safe": {"type": "boolean"},
                                            "threats": {"type": "array"},
                                            "scan_timestamp": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/security/alerts": {
                "get": {
                    "summary": "Get recent security alerts",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 50}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Security alerts",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "alerts": {"type": "array"},
                                            "count": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/security/scan-history": {
                "get": {
                    "summary": "Get security scan history",
                    "responses": {
                        "200": {
                            "description": "Scan history",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "scans": {"type": "array"},
                                            "count": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/tasks/{task_id}/history": {
                "get": {
                    "summary": "Get task history",
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Task history",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "task_id": {"type": "string"},
                                            "history": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/tasks/reorder": {
                "put": {
                    "summary": "Reorder tasks",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": TaskReorder.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Tasks reordered"}
                    }
                }
            },
            "/api/all-data": {
                "get": {
                    "summary": "Get all data in one call",
                    "description": "Get all agents, tasks, context, actions, and file metadata",
                    "responses": {
                        "200": {
                            "description": "All system data",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/status": {
                "get": {
                    "summary": "Get simple system status",
                    "responses": {
                        "200": {
                            "description": "System status",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "server_running": {"type": "boolean"},
                                            "total_agents": {"type": "integer"},
                                            "active_agents": {"type": "integer"},
                                            "total_tasks": {"type": "integer"},
                                            "pending_tasks": {"type": "integer"},
                                            "completed_tasks": {"type": "integer"},
                                            "last_updated": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/graph-data": {
                "get": {
                    "summary": "Get graph data for visualization",
                    "responses": {
                        "200": {
                            "description": "Graph data",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/task-tree-data": {
                "get": {
                    "summary": "Get task tree data for visualization",
                    "responses": {
                        "200": {
                            "description": "Task tree data",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/node-details": {
                "get": {
                    "summary": "Get node details",
                    "parameters": [
                        {
                            "name": "node_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Node details"},
                        "404": {"description": "Node not found"}
                    }
                }
            },
            "/api/agents": {
                "get": {
                    "summary": "List all agents",
                    "responses": {
                        "200": {
                            "description": "List of agents",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/tokens": {
                "get": {
                    "summary": "Get authentication tokens",
                    "responses": {
                        "200": {
                            "description": "Tokens",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "admin_token": {"type": "string"},
                                            "agent_tokens": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/update-task-dashboard": {
                "post": {
                    "summary": "Update task details via dashboard",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "token": {"type": "string"},
                                        "task_id": {"type": "string"},
                                        "status": {"type": "string"},
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                        "priority": {"type": "string"},
                                        "notes": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Task updated"}
                    }
                }
            },
            "/api/create-agent": {
                "post": {
                    "summary": "Create an agent",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": AgentCreate.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Agent created"},
                        "401": {"description": "Unauthorized"},
                        "409": {"description": "Agent already exists"}
                    }
                }
            },
            "/api/terminate-agent": {
                "post": {
                    "summary": "Terminate an agent",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "token": {"type": "string"},
                                        "agent_id": {"type": "string"}
                                    },
                                    "required": ["token", "agent_id"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Agent terminated"},
                        "401": {"description": "Unauthorized"},
                        "404": {"description": "Agent not found"}
                    }
                }
            },
            "/api/memories": {
                "post": {
                    "summary": "Create a memory entry",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": MemoryCreate.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Memory created"},
                        "409": {"description": "Memory already exists"}
                    }
                }
            },
            "/api/memories/{context_key}": {
                "put": {
                    "summary": "Update a memory entry",
                    "parameters": [
                        {
                            "name": "context_key",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": MemoryUpdate.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Memory updated"},
                        "404": {"description": "Memory not found"}
                    }
                },
                "delete": {
                    "summary": "Delete a memory entry",
                    "parameters": [
                        {
                            "name": "context_key",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "token": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Memory deleted"},
                        "404": {"description": "Memory not found"}
                    }
                }
            },
            "/api/context-data": {
                "get": {
                    "summary": "Get context data",
                    "responses": {
                        "200": {
                            "description": "Context data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/create-sample-memories": {
                "post": {
                    "summary": "Create sample memory entries for testing",
                    "responses": {
                        "200": {
                            "description": "Sample memories created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "created_count": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/mcp/config": {
                "post": {
                    "summary": "Generate MCP configuration for a client",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": MCPConfigRequest.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "MCP configuration generated"},
                        "400": {"description": "Unsupported client"}
                    }
                }
            },
            "/api/mcp/install": {
                "post": {
                    "summary": "Install MCP configuration to a client",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": MCPInstallRequest.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "MCP configuration installed"},
                        "400": {"description": "Invalid request"}
                    }
                }
            },
            "/api/mcp/verify-all": {
                "get": {
                    "summary": "Verify all MCP client configurations",
                    "responses": {
                        "200": {
                            "description": "Verification results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "results": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/prompts": {
                "get": {
                    "summary": "List all prompts",
                    "responses": {
                        "200": {
                            "description": "List of prompts",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create a prompt",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": PromptCreate.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Prompt created"}
                    }
                }
            },
            "/api/prompts/{prompt_id}": {
                "get": {
                    "summary": "Get prompt by ID",
                    "parameters": [
                        {
                            "name": "prompt_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Prompt details"},
                        "404": {"description": "Prompt not found"}
                    }
                },
                "put": {
                    "summary": "Update a prompt",
                    "parameters": [
                        {
                            "name": "prompt_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": PromptUpdate.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Prompt updated"},
                        "404": {"description": "Prompt not found"}
                    }
                },
                "delete": {
                    "summary": "Delete a prompt",
                    "parameters": [
                        {
                            "name": "prompt_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Prompt deleted"},
                        "404": {"description": "Prompt not found"}
                    }
                }
            },
            "/api/prompts/{prompt_id}/execute": {
                "post": {
                    "summary": "Execute a prompt",
                    "parameters": [
                        {
                            "name": "prompt_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": PromptExecute.model_json_schema()
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Prompt executed"}
                    }
                }
            },
            "/api/prompts/{prompt_id}/analytics": {
                "get": {
                    "summary": "Get prompt analytics",
                    "parameters": [
                        {
                            "name": "prompt_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Prompt analytics"}
                    }
                }
            },
            "/api/prompts/export": {
                "get": {
                    "summary": "Export prompts",
                    "responses": {
                        "200": {"description": "Prompts exported"}
                    }
                }
            },
            "/api/prompts/import": {
                "post": {
                    "summary": "Import prompts",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Prompts imported"}
                    }
                }
            },
            "/ws/tasks": {
                "get": {
                    "summary": "WebSocket connection for real-time task updates",
                    "description": "Establishes a WebSocket connection for receiving real-time task updates",
                    "responses": {
                        "101": {
                            "description": "Switching Protocols - WebSocket connection established"
                        }
                    }
                }
            },
            "/ws/agents": {
                "get": {
                    "summary": "WebSocket connection for real-time agent updates",
                    "description": "Establishes a WebSocket connection for receiving real-time agent updates",
                    "responses": {
                        "101": {
                            "description": "Switching Protocols - WebSocket connection established"
                        }
                    }
                }
            },
            "/ws/security": {
                "get": {
                    "summary": "WebSocket connection for real-time security alerts",
                    "description": "Establishes a WebSocket connection for receiving real-time security alerts",
                    "responses": {
                        "101": {
                            "description": "Switching Protocols - WebSocket connection established"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "TaskCreate": TaskCreate.model_json_schema(),
                "TaskUpdate": TaskUpdate.model_json_schema(),
                "TaskAssign": TaskAssign.model_json_schema(),
                "TaskStatusUpdate": TaskStatusUpdate.model_json_schema(),
                "TaskPriorityUpdate": TaskPriorityUpdate.model_json_schema(),
                "BulkOperation": BulkOperation.model_json_schema(),
                "TaskReorder": TaskReorder.model_json_schema(),
                "AgentCreate": AgentCreate.model_json_schema(),
                "MemoryCreate": MemoryCreate.model_json_schema(),
                "MemoryUpdate": MemoryUpdate.model_json_schema(),
                "PromptCreate": PromptCreate.model_json_schema(),
                "PromptUpdate": PromptUpdate.model_json_schema(),
                "PromptExecute": PromptExecute.model_json_schema(),
                "SecurityScanRequest": SecurityScanRequest.model_json_schema(),
                "MCPConfigRequest": MCPConfigRequest.model_json_schema(),
                "MCPInstallRequest": MCPInstallRequest.model_json_schema(),
            }
        }
    }
    
    return schema


async def openapi_json_route(request: Request) -> JSONResponse:
    """Serve OpenAPI schema as JSON."""
    schema = generate_openapi_schema()
    return JSONResponse(schema)


async def swagger_ui_route(request: Request) -> HTMLResponse:
    """Serve Swagger UI for API documentation."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Agent-MCP API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui.css" />
        <style>
            html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
            *, *:before, *:after { box-sizing: inherit; }
            body { margin:0; background: #fafafa; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: "/docs/openapi.json",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                });
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

