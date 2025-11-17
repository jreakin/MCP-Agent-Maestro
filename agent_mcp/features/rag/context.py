# Agent-MCP RAG Context Models
"""
Agent context metadata for context-aware RAG queries.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AgentQueryContext(BaseModel):
    """Context metadata for agent RAG queries."""
    
    agent_id: str = Field(..., description="ID of the agent making the query")
    agent_role: str = Field(
        default="worker",
        description="Agent role: 'worker', 'frontend', 'security', 'research', 'manager'"
    )
    agent_mode: str = Field(
        default="",
        description="Agent mode flags like --worker, --playwright, --memory"
    )
    current_task: Optional[str] = Field(
        None, description="Current task ID the agent is working on"
    )
    task_history: List[str] = Field(
        default_factory=list, description="List of recent task IDs"
    )
    accessed_files: List[str] = Field(
        default_factory=list, description="List of recently accessed file paths"
    )
    agent_capabilities: List[str] = Field(
        default_factory=list, description="Available tools/permissions"
    )
    query_intent: str = Field(
        default="general",
        description="Query intent: 'implementation', 'debugging', 'architecture', 'security', 'planning'"
    )
    working_directory: Optional[str] = Field(
        None, description="Agent's current working directory"
    )


def get_agent_context(agent_id: str) -> Optional[AgentQueryContext]:
    """
    Retrieve agent context from database.
    
    Args:
        agent_id: ID of the agent
        
    Returns:
        AgentQueryContext if agent exists, None otherwise
    """
    from ...db.actions.agent_db import get_agent_by_id
    from ...db.actions.task_db import get_tasks_by_agent_id
    
    if not agent_id:
        return None
    
    agent = get_agent_by_id(agent_id)
    if not agent:
        return None
    
    # Determine agent role from capabilities or agent_id
    capabilities = agent.get('capabilities', [])
    if isinstance(capabilities, str):
        import json
        try:
            capabilities = json.loads(capabilities) if capabilities else []
        except json.JSONDecodeError:
            capabilities = []
    
    # Infer role from agent_id or capabilities
    agent_id_lower = agent_id.lower()
    if 'frontend' in agent_id_lower or 'ui' in agent_id_lower:
        role = 'frontend'
    elif 'security' in agent_id_lower or 'sec' in agent_id_lower:
        role = 'security'
    elif 'research' in agent_id_lower or 'analysis' in agent_id_lower:
        role = 'research'
    elif 'manager' in agent_id_lower or 'admin' in agent_id_lower:
        role = 'manager'
    else:
        role = 'worker'
    
    # Get current task
    current_task = agent.get('current_task')
    
    # Get recent task history
    recent_tasks = get_tasks_by_agent_id(agent_id, status_filter=None)
    task_history = [t['task_id'] for t in recent_tasks[:10]]  # Last 10 tasks
    
    # Get agent mode from status or capabilities
    agent_mode = ""
    if 'playwright' in capabilities or 'browser' in capabilities:
        agent_mode += "--playwright "
    if 'memory' in capabilities or 'rag' in capabilities:
        agent_mode += "--memory "
    if role == 'worker':
        agent_mode += "--worker"
    
    return AgentQueryContext(
        agent_id=agent_id,
        agent_role=role,
        agent_mode=agent_mode.strip(),
        current_task=current_task,
        task_history=task_history,
        accessed_files=[],  # TODO: Track from file_metadata table
        agent_capabilities=capabilities,
        working_directory=agent.get('working_directory')
    )

