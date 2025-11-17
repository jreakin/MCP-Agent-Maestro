# agent_mcp/tools/pydanticai_tools.py
"""
PydanticAI-based tools for structured, type-safe operations.
These tools provide enhanced responses with confidence scores, suggestions, and orchestration.

NOTE: This module requires pydantic-ai to be installed.
Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai
"""
from typing import List, Dict, Any
import mcp.types as mcp_types

# Check if pydantic-ai is available
try:
    import pydantic_ai
except ImportError:
    raise ImportError(
        "pydantic-ai is required for PydanticAI tools. "
        "Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai"
    )

from .registry import register_tool
from ..core.config import logger
from ..core.auth import get_agent_id
from ..utils.audit_utils import log_audit

# Import PydanticAI agents (these will also check for pydantic-ai)
try:
    from ..agents.pydanticai_rag_agent import RAGAgent, AgentQueryContextDeps
    from ..agents.pydanticai_task_agent import TaskAgent, TaskManagerDeps
    from ..agents.pydanticai_orchestrator import AgentOrchestrator, OrchestrationRequest
    from ..agents.assessment_agent import assess_and_route
    from ..models.task import TaskCreate
except ImportError as e:
    logger.error(f"Failed to import PydanticAI agents: {e}")
    raise


# --- Structured RAG Query Tool ---
async def ask_project_rag_structured_tool_impl(arguments: Dict[str, Any]) -> List[mcp_types.TextContent]:
    """
    Ask a question using the structured PydanticAI RAG agent.
    Returns structured response with confidence, sources, and suggestions.
    """
    agent_auth_token = arguments.get("token")
    query_text = arguments.get("query")
    agent_role = arguments.get("agent_role")  # Optional

    requesting_agent_id = get_agent_id(agent_auth_token)
    if not requesting_agent_id:
        return [mcp_types.TextContent(
            type="text",
            text="Unauthorized: Valid agent token required"
        )]

    if not query_text or not isinstance(query_text, str):
        return [mcp_types.TextContent(
            type="text",
            text="Error: query text is required and must be a string."
        )]

    log_audit(requesting_agent_id, "ask_project_rag_structured", {"query": query_text})
    logger.info(f"Agent '{requesting_agent_id}' using structured RAG: '{query_text[:100]}...'")

    try:
        # Use PydanticAI RAG agent
        rag_agent = RAGAgent()
        agent_context = AgentQueryContextDeps(
            agent_id=requesting_agent_id,
            agent_role=agent_role
        )
        
        response = await rag_agent.search(query=query_text, agent_context=agent_context)
        
        # Format structured response
        result_text = f"""Answer: {response.answer}

Confidence: {response.confidence:.2%}
Sources Found: {len(response.sources)}
Context Keys Used: {', '.join(response.context_keys_used) if response.context_keys_used else 'None'}

Suggested Follow-up Queries:
{chr(10).join(f"  - {q}" for q in response.suggested_queries[:3])}
"""
        
        return [mcp_types.TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error in structured RAG tool: {e}", exc_info=True)
        return [mcp_types.TextContent(
            type="text",
            text=f"Error processing structured RAG query: {str(e)}"
        )]


# --- Structured Task Creation Tool ---
async def create_task_structured_tool_impl(arguments: Dict[str, Any]) -> List[mcp_types.TextContent]:
    """
    Create a task using the structured PydanticAI Task agent.
    Returns structured response with suggested actions.
    """
    agent_auth_token = arguments.get("token")
    title = arguments.get("title")
    description = arguments.get("description", "")
    priority = arguments.get("priority", "medium")
    status = arguments.get("status", "created")
    assigned_to = arguments.get("assigned_to")
    parent_task = arguments.get("parent_task")
    depends_on_tasks = arguments.get("depends_on_tasks", [])

    requesting_agent_id = get_agent_id(agent_auth_token)
    if not requesting_agent_id:
        return [mcp_types.TextContent(
            type="text",
            text="Unauthorized: Valid agent token required"
        )]

    if not title:
        return [mcp_types.TextContent(
            type="text",
            text="Error: title is required"
        )]

    log_audit(requesting_agent_id, "create_task_structured", {"title": title})
    logger.info(f"Agent '{requesting_agent_id}' creating structured task: '{title}'")

    try:
        # Use PydanticAI Task agent
        task_agent = TaskAgent()
        task_deps = TaskManagerDeps(
            agent_id=requesting_agent_id,
            agent_role=arguments.get("agent_role")
        )
        
        task_create = TaskCreate(
            title=title,
            description=description,
            priority=priority,
            status=status,
            assigned_to=assigned_to,
            parent_task=parent_task,
            depends_on_tasks=depends_on_tasks if isinstance(depends_on_tasks, list) else []
        )
        
        output = await task_agent.create_task(task_create, task_deps)
        
        if output.success:
            result_text = f"""✅ Task Created Successfully

Task ID: {output.task_id}
Title: {title}
Status: {output.task.get('status') if output.task else status}
Priority: {output.task.get('priority') if output.task else priority}

Suggested Next Actions:
{chr(10).join(f"  - {action}" for action in output.suggested_actions[:3])}
"""
        else:
            result_text = f"❌ Failed to create task: {output.message}"
        
        return [mcp_types.TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error in structured task creation: {e}", exc_info=True)
        return [mcp_types.TextContent(
            type="text",
            text=f"Error creating structured task: {str(e)}"
        )]


# --- Assessment Tool ---
async def assess_request_tool_impl(arguments: Dict[str, Any]) -> List[mcp_types.TextContent]:
    """
    Assess a request and determine which agents/models to use.
    Returns routing plan with reasoning.
    """
    agent_auth_token = arguments.get("token")
    query = arguments.get("query")
    context = arguments.get("context")

    requesting_agent_id = get_agent_id(agent_auth_token)
    if not requesting_agent_id:
        return [mcp_types.TextContent(
            type="text",
            text="Unauthorized: Valid agent token required"
        )]

    if not query or not isinstance(query, str):
        return [mcp_types.TextContent(
            type="text",
            text="Error: query is required and must be a string"
        )]

    log_audit(requesting_agent_id, "assess_request", {"query": query[:100]})
    logger.info(f"Agent '{requesting_agent_id}' assessing request: '{query[:100]}...'")

    try:
        # Assess request
        plan = await assess_and_route(
            query=query,
            agent_id=requesting_agent_id,
            context=context
        )
        
        # Format assessment result
        result_text = f"""🎯 Request Assessment

Primary Agent: {plan['primary_agent']}
Model: {plan['model']}
Confidence: {plan['confidence']:.2%}

Reasoning:
{plan['reasoning']}

Execution Plan:
- Primary: {plan['primary_agent']} using {plan['model']}
"""
        
        if plan.get('secondary_agents'):
            result_text += f"- Secondary: {', '.join(plan['secondary_agents'])}\n"
        
        if plan.get('use_parallel'):
            result_text += "- Execution: Parallel (multiple agents simultaneously)\n"
        else:
            result_text += "- Execution: Sequential\n"
        
        return [mcp_types.TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error in assessment: {e}", exc_info=True)
        return [mcp_types.TextContent(
            type="text",
            text=f"Error assessing request: {str(e)}"
        )]


# --- Orchestration Tool ---
async def orchestrate_workflow_tool_impl(arguments: Dict[str, Any]) -> List[mcp_types.TextContent]:
    """
    Orchestrate complex workflows using RAG + Task agents.
    Automatically determines which agents to use based on the query.
    """
    agent_auth_token = arguments.get("token")
    query = arguments.get("query")
    agent_role = arguments.get("agent_role")

    requesting_agent_id = get_agent_id(agent_auth_token)
    if not requesting_agent_id:
        return [mcp_types.TextContent(
            type="text",
            text="Unauthorized: Valid agent token required"
        )]

    if not query or not isinstance(query, str):
        return [mcp_types.TextContent(
            type="text",
            text="Error: query is required and must be a string"
        )]

    log_audit(requesting_agent_id, "orchestrate_workflow", {"query": query[:100]})
    logger.info(f"Agent '{requesting_agent_id}' orchestrating workflow: '{query[:100]}...'")

    try:
        # Use PydanticAI Orchestrator
        orchestrator = AgentOrchestrator()
        request = OrchestrationRequest(
            query=query,
            agent_id=requesting_agent_id,
            agent_role=agent_role,
            context=arguments.get("context")
        )
        
        # Use assessment by default unless explicitly disabled
        use_assessment = arguments.get("use_assessment", True)
        result = await orchestrator.orchestrate(request, use_assessment=use_assessment)
        
        # Format orchestration result
        result_text = f"""🎯 Orchestration Result

Status: {'✅ Success' if result.success else '❌ Failed'}
Result: {result.result}

Coordination Log:
{chr(10).join(f"  • {log}" for log in result.coordination_log)}

Next Steps:
{chr(10).join(f"  - {step}" for step in result.next_steps[:5])}
"""
        
        if result.rag_response:
            result_text += f"\nRAG Response Confidence: {result.rag_response.confidence:.2%}\n"
        
        if result.task_outputs:
            result_text += f"\nTask Operations Completed: {len(result.task_outputs)}\n"
            for task_output in result.task_outputs:
                result_text += f"  • {task_output.message}\n"
        
        return [mcp_types.TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error in orchestration: {e}", exc_info=True)
        return [mcp_types.TextContent(
            type="text",
            text=f"Error orchestrating workflow: {str(e)}"
        )]


# --- Register Tools ---
def register_pydanticai_tools():
    """Register all PydanticAI-based tools."""
    
    # Structured RAG tool
    register_tool(
        name="ask_project_rag_structured",
        description="Ask a question using structured RAG with confidence scores, sources, and suggestions. Returns detailed structured response.",
        input_schema={
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "Authentication token for the agent making the query."},
                "query": {"type": "string", "description": "The natural language question to ask about the project."},
                "agent_role": {"type": "string", "description": "Optional agent role for context-aware responses"}
            },
            "required": ["token", "query"],
            "additionalProperties": False
        },
        implementation=ask_project_rag_structured_tool_impl
    )
    
    # Structured task creation tool
    register_tool(
        name="create_task_structured",
        description="Create a task using structured task management with suggested actions. Returns detailed structured response.",
        input_schema={
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "Authentication token for the agent."},
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium", "description": "Task priority"},
                "status": {"type": "string", "default": "created", "description": "Initial task status"},
                "assigned_to": {"type": "string", "description": "Agent ID to assign task to"},
                "parent_task": {"type": "string", "description": "Parent task ID"},
                "depends_on_tasks": {"type": "array", "items": {"type": "string"}, "description": "Task IDs this depends on"},
                "agent_role": {"type": "string", "description": "Optional agent role"}
            },
            "required": ["token", "title"],
            "additionalProperties": False
        },
        implementation=create_task_structured_tool_impl
    )
    
    # Assessment tool
    register_tool(
        name="assess_request",
        description="Assess a request and determine which agents and models should handle it. Returns routing plan with reasoning about agent/model selection.",
        input_schema={
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "Authentication token for the agent."},
                "query": {"type": "string", "description": "The request to assess"},
                "context": {"type": "object", "description": "Additional context for assessment"}
            },
            "required": ["token", "query"],
            "additionalProperties": False
        },
        implementation=assess_request_tool_impl
    )
    
    # Orchestration tool
    register_tool(
        name="orchestrate_workflow",
        description="Orchestrate complex workflows that may require both RAG queries and task operations. Automatically coordinates multiple agents based on query content. Uses assessment agent for intelligent routing.",
        input_schema={
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "Authentication token for the agent."},
                "query": {"type": "string", "description": "The orchestration query (e.g., 'What do we know about auth and create a task to implement OAuth2')"},
                "agent_role": {"type": "string", "description": "Optional agent role"},
                "context": {"type": "object", "description": "Additional context for orchestration"},
                "use_assessment": {"type": "boolean", "default": True, "description": "Whether to use assessment agent for intelligent routing"}
            },
            "required": ["token", "query"],
            "additionalProperties": False
        },
        implementation=orchestrate_workflow_tool_impl
    )


# Register tools when module is imported
register_pydanticai_tools()
