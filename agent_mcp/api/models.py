"""
Pydantic models for API request/response validation.
Provides type safety, automatic validation, and security checks.
"""
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
import re


# Security validators
def validate_no_injection(value: str) -> str:
    """Validate that a string doesn't contain common injection patterns."""
    if not isinstance(value, str):
        return value
    
    # Common injection patterns
    injection_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'data:text/html',
        r'vbscript:',
        r'<iframe',
        r'<object',
        r'<embed',
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError(f"Potential injection detected in field")
    
    return value


def validate_safe_string(value: str, max_length: int = 10000) -> str:
    """Validate string is safe and within length limits."""
    if not isinstance(value, str):
        raise ValueError("Must be a string")
    
    if len(value) > max_length:
        raise ValueError(f"String exceeds maximum length of {max_length}")
    
    # Check for null bytes
    if '\x00' in value:
        raise ValueError("String contains null bytes")
    
    return validate_no_injection(value)


# Task Models
class TaskCreate(BaseModel):
    """Model for creating a new task."""
    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    description: Optional[str] = Field(None, max_length=10000, description="Task description")
    priority: Literal["low", "medium", "high", "critical"] = Field(default="medium")
    status: Literal["pending", "in_progress", "completed", "blocked", "cancelled"] = Field(default="pending")
    assigned_to: Optional[str] = Field(None, max_length=100, description="Agent ID to assign task to")
    parent_task: Optional[str] = Field(None, max_length=100, description="Parent task ID")
    depends_on_tasks: Optional[List[str]] = Field(default_factory=list, description="List of task IDs this task depends on")
    tags: Optional[List[str]] = Field(default_factory=list, description="Task tags")
    due_date: Optional[str] = Field(None, description="Due date in ISO format")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty and strip whitespace."""
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return validate_safe_string(v.strip())
    
    @field_validator('description', 'assigned_to', 'parent_task')
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_safe_string(v)
    
    @field_validator('depends_on_tasks', 'tags')
    @classmethod
    def validate_string_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        return [validate_safe_string(item, max_length=200) for item in v]


class TaskUpdate(BaseModel):
    """Model for updating an existing task."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=10000)
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    status: Optional[Literal["pending", "in_progress", "completed", "blocked", "cancelled"]] = None
    assigned_to: Optional[str] = Field(None, max_length=100)
    parent_task: Optional[str] = Field(None, max_length=100)
    depends_on_tasks: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    due_date: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator('title', 'description', 'assigned_to', 'parent_task')
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_safe_string(v)
    
    @field_validator('depends_on_tasks', 'tags')
    @classmethod
    def validate_string_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        return [validate_safe_string(item, max_length=200) for item in v]


class TaskAssign(BaseModel):
    """Model for assigning a task to an agent."""
    agent_id: str = Field(..., max_length=100)
    
    @field_validator('agent_id')
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        return validate_safe_string(v, max_length=100)


class TaskStatusUpdate(BaseModel):
    """Model for updating task status."""
    status: Literal["pending", "in_progress", "completed", "blocked", "cancelled"] = Field(...)


class TaskPriorityUpdate(BaseModel):
    """Model for updating task priority."""
    priority: Literal["low", "medium", "high", "critical"] = Field(...)


# Bulk Operations
class BulkOperation(BaseModel):
    """Model for bulk task operations."""
    task_ids: List[str] = Field(..., min_items=1, description="List of task IDs to operate on")
    operation: Literal["update_status", "update_priority", "assign", "add_tags", "delete"] = Field(...)
    value: Optional[Any] = Field(None, description="Value for the operation (status, priority, agent_id, etc.)")
    
    @field_validator('task_ids')
    @classmethod
    def validate_task_ids(cls, v: List[str]) -> List[str]:
        if len(v) > 100:  # Limit bulk operations
            raise ValueError("Cannot operate on more than 100 tasks at once")
        return [validate_safe_string(task_id, max_length=100) for task_id in v]
    
    @model_validator(mode='after')
    def validate_operation_value(self):
        """Validate that value is provided when required."""
        if self.operation in ["update_status", "update_priority", "assign"] and self.value is None:
            raise ValueError(f"Operation '{self.operation}' requires a 'value' field")
        return self


class TaskReorder(BaseModel):
    """Model for reordering tasks."""
    task_ids: List[str] = Field(..., min_items=1, description="Ordered list of task IDs")
    
    @field_validator('task_ids')
    @classmethod
    def validate_task_ids(cls, v: List[str]) -> List[str]:
        if len(v) > 1000:  # Reasonable limit
            raise ValueError("Cannot reorder more than 1000 tasks at once")
        return [validate_safe_string(task_id, max_length=100) for task_id in v]


# Agent Models
class AgentCreate(BaseModel):
    """Model for creating a new agent."""
    agent_id: Optional[str] = Field(None, max_length=100, description="Optional agent ID (auto-generated if not provided)")
    capabilities: Optional[List[str]] = Field(default_factory=list, description="List of agent capabilities")
    working_directory: Optional[str] = Field(None, max_length=500, description="Working directory for the agent")
    
    @field_validator('agent_id', 'working_directory')
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_safe_string(v, max_length=500)
    
    @field_validator('capabilities')
    @classmethod
    def validate_capabilities(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        return [validate_safe_string(cap, max_length=200) for cap in v]


# Memory/Context Models
class MemoryCreate(BaseModel):
    """Model for creating a memory entry."""
    context_key: str = Field(..., min_length=1, max_length=200, description="Context key")
    context_value: Any = Field(..., description="Context value (can be any JSON-serializable type)")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the memory entry")
    
    @field_validator('context_key', 'description')
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_safe_string(v)


class MemoryUpdate(BaseModel):
    """Model for updating a memory entry."""
    context_value: Optional[Any] = Field(None, description="New context value")
    description: Optional[str] = Field(None, max_length=1000, description="New description")
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_safe_string(v)


# Prompt Book Models
class PromptCreate(BaseModel):
    """Model for creating a prompt template."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    template: str = Field(..., min_length=1, max_length=50000, description="Prompt template text")
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(default_factory=list)
    variables: Optional[List[str]] = Field(default_factory=list, description="List of variable names used in template")
    
    @field_validator('name', 'description', 'category')
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_safe_string(v)
    
    @field_validator('template')
    @classmethod
    def validate_template(cls, v: str) -> str:
        # Templates can be longer, but still check for injection
        if len(v) > 50000:
            raise ValueError("Template exceeds maximum length of 50000 characters")
        return validate_no_injection(v)
    
    @field_validator('tags', 'variables')
    @classmethod
    def validate_string_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        return [validate_safe_string(item, max_length=200) for item in v]


class PromptUpdate(BaseModel):
    """Model for updating a prompt template."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    template: Optional[str] = Field(None, min_length=1, max_length=50000)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    variables: Optional[List[str]] = None
    
    @field_validator('name', 'description', 'category')
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_safe_string(v)
    
    @field_validator('template')
    @classmethod
    def validate_template(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) > 50000:
            raise ValueError("Template exceeds maximum length of 50000 characters")
        return validate_no_injection(v)
    
    @field_validator('tags', 'variables')
    @classmethod
    def validate_string_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        return [validate_safe_string(item, max_length=200) for item in v]


class PromptExecute(BaseModel):
    """Model for executing a prompt template."""
    prompt_id: str = Field(..., description="ID of the prompt to execute")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variable values to substitute in template")
    
    @field_validator('prompt_id')
    @classmethod
    def validate_prompt_id(cls, v: str) -> str:
        return validate_safe_string(v, max_length=100)


# Security Scan Models
class SecurityScanRequest(BaseModel):
    """Model for security scan requests."""
    text: str = Field(..., description="Text to scan for security threats")
    context: Optional[str] = Field(None, max_length=500, description="Context about where the text came from")
    
    @field_validator('text', 'context')
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_safe_string(v, max_length=100000)  # Allow longer text for scanning


# MCP Setup Models
class MCPConfigRequest(BaseModel):
    """Model for MCP configuration requests."""
    client: Literal["cursor", "claude", "windsurf", "vscode"] = Field(..., description="MCP client type")
    server_name: Optional[str] = Field(None, max_length=100, description="Custom server name")
    
    @field_validator('server_name')
    @classmethod
    def validate_server_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_safe_string(v, max_length=100)


class MCPInstallRequest(BaseModel):
    """Model for MCP installation requests."""
    client: Literal["cursor", "claude", "windsurf", "vscode"] = Field(..., description="MCP client type")
    config_path: Optional[str] = Field(None, max_length=500, description="Custom config file path")
    
    @field_validator('config_path')
    @classmethod
    def validate_config_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Validate path format (basic check)
        if not re.match(r'^[a-zA-Z0-9_/\.\-]+$', v):
            raise ValueError("Invalid path format")
        return v


# Common Response Models
class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = Field(True)
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

