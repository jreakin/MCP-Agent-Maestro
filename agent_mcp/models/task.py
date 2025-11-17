# Agent-MCP Task Models
"""
Pydantic models for task management with validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Task(BaseModel):
    """Task model with all fields."""
    
    task_id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., min_length=1, max_length=300, description="Task title")
    description: Optional[str] = Field(None, max_length=5000, description="Task description")
    status: Literal['pending', 'in_progress', 'completed', 'blocked', 'cancelled', 'failed'] = Field(
        default='pending', description="Task status"
    )
    priority: Literal['low', 'medium', 'high', 'critical'] = Field(
        default='medium', description="Task priority"
    )
    assigned_to: Optional[str] = Field(None, description="Agent ID assigned to this task")
    created_by: str = Field(..., description="Agent ID that created this task")
    parent_task: Optional[str] = Field(None, description="Parent task ID")
    child_tasks: List[str] = Field(default_factory=list, description="Child task IDs")
    depends_on_tasks: List[str] = Field(default_factory=list, description="Task IDs this task depends on")
    notes: List[Dict[str, Any]] = Field(default_factory=list, description="Task notes/audit log")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    due_date: Optional[datetime] = Field(None, description="Optional due date")
    tags: List[str] = Field(default_factory=list, max_items=20, description="Task tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Ensure tags don't contain malicious content."""
        import re
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tag too long (max 50 characters)')
            if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                raise ValueError(f'Invalid tag format: {tag} (only alphanumeric, underscore, hyphen allowed)')
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty."""
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class TaskCreate(BaseModel):
    """Model for creating a new task."""
    
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=5000)
    priority: Literal['low', 'medium', 'high', 'critical'] = Field(default='medium')
    status: Literal['pending', 'in_progress', 'completed', 'blocked', 'cancelled'] = Field(default='pending')
    assigned_to: Optional[str] = None
    parent_task: Optional[str] = None
    depends_on_tasks: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list, max_items=20)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    due_date: Optional[datetime] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty."""
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class TaskUpdate(BaseModel):
    """Model for updating an existing task."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[Literal['pending', 'in_progress', 'completed', 'blocked', 'cancelled', 'failed']] = None
    priority: Optional[Literal['low', 'medium', 'high', 'critical']] = None
    assigned_to: Optional[str] = None
    parent_task: Optional[str] = None
    depends_on_tasks: Optional[List[str]] = None
    tags: Optional[List[str]] = Field(None, max_items=20)
    metadata: Optional[Dict[str, Any]] = None
    due_date: Optional[datetime] = None


class TaskReorder(BaseModel):
    """Model for reordering tasks."""
    
    task_id: str = Field(..., description="Task ID to reorder")
    new_position: int = Field(..., ge=0, description="New position index")
    status: Optional[str] = Field(None, description="Status column for kanban reordering")


class BulkOperation(BaseModel):
    """Model for bulk task operations."""
    
    task_ids: List[str] = Field(..., min_length=1, description="Task IDs to operate on")
    operation: Literal['update_status', 'update_priority', 'assign', 'add_tags', 'remove_tags', 'delete'] = Field(
        ..., description="Operation to perform"
    )
    value: Optional[Any] = Field(None, description="Value for the operation (status, priority, agent_id, tags, etc.)")

