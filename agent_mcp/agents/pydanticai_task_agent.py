"""
PydanticAI Task Agent for structured task management.
Provides type-safe task operations with Pydantic models.

NOTE: This module requires pydantic-ai to be installed.
Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai
"""

import os
from typing import List, Optional, Dict, Any

# Check if pydantic-ai is available
try:
    from pydantic import BaseModel, Field
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIModel
    from pydantic_ai.providers.openai import OpenAIProvider
except ImportError as e:
    raise ImportError(
        f"pydantic-ai is required for PydanticAI Task Agent. "
        f"Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai. "
        f"Original error: {e}"
    )

from ..core.config import logger, CHAT_MODEL
from ..external.openai_service import get_openai_client
from ..db.actions.task_db import (
    get_all_tasks_from_db,
    get_task_by_id,
    update_task_fields_in_db,
    create_task_in_db
)
from ..models.task import Task, TaskCreate, TaskUpdate


class TaskManagerDeps(BaseModel):
    """Dependencies for task management operations."""
    agent_id: str = Field(..., description="ID of the agent managing tasks")
    agent_role: Optional[str] = Field(None, description="Agent role (admin, worker, etc.)")
    project_dir: Optional[str] = Field(None, description="Project directory for context")


class TaskOutput(BaseModel):
    """Structured output from task operations."""
    success: bool = Field(..., description="Whether the operation succeeded")
    task_id: Optional[str] = Field(None, description="Task ID if applicable")
    message: str = Field(..., description="Operation result message")
    task: Optional[Dict[str, Any]] = Field(None, description="Task data if applicable")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested next actions")


class TaskAgent:
    """PydanticAI agent for task management."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize task agent.
        
        Args:
            model_name: Model name (defaults to CHAT_MODEL from config or Ollama model)
        """
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        
        # Configure model based on provider
        if embedding_provider == "ollama":
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
            ollama_chat_model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
            self.model_name = model_name or ollama_chat_model
            
            # Use Ollama's OpenAI-compatible endpoint
            provider = OpenAIProvider(
                base_url=f"{ollama_base_url}/v1",
                api_key="ollama"  # Ollama doesn't require real API keys
            )
            model = OpenAIModel(self.model_name, provider=provider)
        else:
            self.model_name = model_name or CHAT_MODEL
            openai_client = get_openai_client()
            if not openai_client:
                raise ValueError("OpenAI client not available")
            model = OpenAIModel(self.model_name)
        
        # Create PydanticAI agent
        self.agent = Agent(
            model,
            system_prompt="""You are a specialized task management agent.
You help create, update, and manage tasks in a multi-agent system.
Always ensure tasks are well-structured, have clear descriptions, and appropriate priorities.
Consider task dependencies and agent assignments when creating or updating tasks.""",
            output_type=TaskOutput,
        )
    
    async def create_task(
        self,
        task_data: TaskCreate,
        deps: TaskManagerDeps
    ) -> TaskOutput:
        """
        Create a new task.
        
        Args:
            task_data: Task creation data
            deps: Task manager dependencies
            
        Returns:
            Task operation output
        """
        try:
            # Create task in database
            task_id = create_task_in_db(
                title=task_data.title,
                description=task_data.description,
                priority=task_data.priority,
                status=task_data.status,
                assigned_to=task_data.assigned_to,
                created_by=deps.agent_id,
                parent_task=task_data.parent_task,
                depends_on_tasks=task_data.depends_on_tasks,
                tags=task_data.tags,
                due_date=task_data.due_date,
                metadata=task_data.metadata
            )
            
            if task_id:
                task = get_task_by_id(task_id)
                return TaskOutput(
                    success=True,
                    task_id=task_id,
                    message=f"Task '{task_data.title}' created successfully",
                    task=task,
                    suggested_actions=[
                        f"Assign task to an agent",
                        "Set task dependencies if needed",
                        "Update task priority if urgent"
                    ]
                )
            else:
                return TaskOutput(
                    success=False,
                    message="Failed to create task",
                    suggested_actions=["Check task data validity", "Verify database connection"]
                )
        except Exception as e:
            logger.error(f"Error creating task: {e}", exc_info=True)
            return TaskOutput(
                success=False,
                message=f"Error creating task: {str(e)}",
                suggested_actions=["Review error logs", "Check task data format"]
            )
    
    async def update_task(
        self,
        task_id: str,
        updates: TaskUpdate,
        deps: TaskManagerDeps
    ) -> TaskOutput:
        """
        Update an existing task.
        
        Args:
            task_id: Task ID to update
            updates: Task update data
            deps: Task manager dependencies
            
        Returns:
            Task operation output
        """
        try:
            # Check if task exists
            task = get_task_by_id(task_id)
            if not task:
                return TaskOutput(
                    success=False,
                    task_id=task_id,
                    message=f"Task {task_id} not found",
                    suggested_actions=["Verify task ID", "Check task list"]
                )
            
            # Convert updates to dict
            update_dict = updates.model_dump(exclude_none=True)
            
            if not update_dict:
                return TaskOutput(
                    success=False,
                    task_id=task_id,
                    message="No fields to update",
                    task=task,
                    suggested_actions=["Provide update fields", "Check update data"]
                )
            
            # Update task
            success = update_task_fields_in_db(task_id, update_dict)
            
            if success:
                updated_task = get_task_by_id(task_id)
                return TaskOutput(
                    success=True,
                    task_id=task_id,
                    message=f"Task {task_id} updated successfully",
                    task=updated_task,
                    suggested_actions=[
                        "Review updated task",
                        "Notify assigned agent if status changed",
                        "Check dependencies if task completed"
                    ]
                )
            else:
                return TaskOutput(
                    success=False,
                    task_id=task_id,
                    message="Failed to update task",
                    task=task,
                    suggested_actions=["Check update validity", "Verify database connection"]
                )
        except Exception as e:
            logger.error(f"Error updating task: {e}", exc_info=True)
            return TaskOutput(
                success=False,
                task_id=task_id,
                message=f"Error updating task: {str(e)}",
                suggested_actions=["Review error logs", "Check update data format"]
            )
    
    async def get_task(
        self,
        task_id: str,
        deps: TaskManagerDeps
    ) -> TaskOutput:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            deps: Task manager dependencies
            
        Returns:
            Task operation output
        """
        try:
            task = get_task_by_id(task_id)
            if task:
                return TaskOutput(
                    success=True,
                    task_id=task_id,
                    message="Task retrieved successfully",
                    task=task,
                    suggested_actions=[
                        "Update task status if needed",
                        "Review task dependencies",
                        "Assign to agent if unassigned"
                    ]
                )
            else:
                return TaskOutput(
                    success=False,
                    task_id=task_id,
                    message=f"Task {task_id} not found",
                    suggested_actions=["Verify task ID", "Check task list"]
                )
        except Exception as e:
            logger.error(f"Error getting task: {e}", exc_info=True)
            return TaskOutput(
                success=False,
                task_id=task_id,
                message=f"Error retrieving task: {str(e)}",
                suggested_actions=["Review error logs", "Check database connection"]
            )
    
    async def list_tasks(
        self,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        deps: Optional[TaskManagerDeps] = None
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filtering.
        
        Args:
            status: Filter by status
            assigned_to: Filter by assigned agent
            deps: Task manager dependencies
            
        Returns:
            List of tasks
        """
        try:
            all_tasks = get_all_tasks_from_db()
            
            # Apply filters
            filtered_tasks = all_tasks
            if status:
                filtered_tasks = [t for t in filtered_tasks if t.get("status") == status]
            if assigned_to:
                filtered_tasks = [t for t in filtered_tasks if t.get("assigned_to") == assigned_to]
            
            return filtered_tasks
        except Exception as e:
            logger.error(f"Error listing tasks: {e}", exc_info=True)
            return []


# Tool definitions for PydanticAI agent
async def create_task_tool(task_data: Dict[str, Any], deps: TaskManagerDeps) -> TaskOutput:
    """Create task tool for PydanticAI agent."""
    agent = TaskAgent()
    task_create = TaskCreate(**task_data)
    return await agent.create_task(task_create, deps)


async def update_task_tool(task_id: str, updates: Dict[str, Any], deps: TaskManagerDeps) -> TaskOutput:
    """Update task tool for PydanticAI agent."""
    agent = TaskAgent()
    task_update = TaskUpdate(**updates)
    return await agent.update_task(task_id, task_update, deps)


async def get_task_tool(task_id: str, deps: TaskManagerDeps) -> TaskOutput:
    """Get task tool for PydanticAI agent."""
    agent = TaskAgent()
    return await agent.get_task(task_id, deps)


async def list_tasks_tool(deps: TaskManagerDeps, status: Optional[str] = None, assigned_to: Optional[str] = None) -> List[Dict[str, Any]]:
    """List tasks tool for PydanticAI agent."""
    agent = TaskAgent()
    return await agent.list_tasks(status=status, assigned_to=assigned_to, deps=deps)

