# How to Use PydanticAI Agents in Agent-MCP

## 🎯 **Overview**

This guide shows you how to integrate and use the PydanticAI agents that are already in the codebase but not yet connected to the system.

---

## 📋 **Three Integration Approaches**

1. **Add New MCP Tools** (Recommended) - Add new tools alongside existing ones
2. **Replace Existing Tools** - Swap current implementations with PydanticAI versions
3. **Add API Endpoints** - Expose PydanticAI agents via HTTP API

---

## 🛠️ **Approach 1: Add New MCP Tools (Recommended)**

### **Step 1: Create New Tool File**

Create `agent_mcp/tools/pydanticai_tools.py`:

```python
# agent_mcp/tools/pydanticai_tools.py
from typing import List, Dict, Any
import mcp.types as mcp_types
import json

from .registry import register_tool
from ..core.config import logger
from ..core.auth import get_agent_id
from ..utils.audit_utils import log_audit
from ..agents.pydanticai_rag_agent import RAGAgent, AgentQueryContextDeps
from ..agents.pydanticai_task_agent import TaskAgent, TaskManagerDeps
from ..agents.pydanticai_orchestrator import AgentOrchestrator, OrchestrationRequest
from ..models.task import TaskCreate, TaskUpdate


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
        
        result = await orchestrator.orchestrate(request)
        
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
                "token": {"type": "string", "description": "Authentication token"},
                "query": {"type": "string", "description": "The question to ask"},
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
                "token": {"type": "string", "description": "Authentication token"},
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                "status": {"type": "string", "default": "created"},
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
    
    # Orchestration tool
    register_tool(
        name="orchestrate_workflow",
        description="Orchestrate complex workflows that may require both RAG queries and task operations. Automatically coordinates multiple agents.",
        input_schema={
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "Authentication token"},
                "query": {"type": "string", "description": "The orchestration query (e.g., 'What do we know about auth and create a task to implement OAuth2')"},
                "agent_role": {"type": "string", "description": "Optional agent role"},
                "context": {"type": "object", "description": "Additional context"}
            },
            "required": ["token", "query"],
            "additionalProperties": False
        },
        implementation=orchestrate_workflow_tool_impl
    )


# Register tools when module is imported
register_pydanticai_tools()
```

### **Step 2: Import the Tools**

Add to `agent_mcp/tools/__init__.py`:

```python
# agent_mcp/tools/__init__.py
# ... existing imports ...

# Import PydanticAI tools to register them
from . import pydanticai_tools  # This will call register_pydanticai_tools()
```

---

## 🔄 **Approach 2: Replace Existing Tools**

### **Option A: Replace RAG Tool**

Modify `agent_mcp/tools/rag_tools.py`:

```python
# In ask_project_rag_tool_impl, replace the direct call:
# OLD:
answer_text = await query_rag_system(query_text, agent_id=requesting_agent_id, format_type=format_type)
return [mcp_types.TextContent(type="text", text=answer_text)]

# NEW:
from ..agents.pydanticai_rag_agent import RAGAgent, AgentQueryContextDeps

rag_agent = RAGAgent()
agent_context = AgentQueryContextDeps(agent_id=requesting_agent_id)
response = await rag_agent.search(query=query_text, agent_context=agent_context)

# Return structured response
result_text = f"{response.answer}\n\nConfidence: {response.confidence:.2%}"
if response.suggested_queries:
    result_text += f"\n\nSuggested queries: {', '.join(response.suggested_queries[:3])}"

return [mcp_types.TextContent(type="text", text=result_text)]
```

### **Option B: Replace Task Creation Tool**

Modify `agent_mcp/tools/task_tools.py` - find `create_task_tool_impl` and replace with PydanticAI version.

---

## 🌐 **Approach 3: Add API Endpoints**

### **Step 1: Create API Route File**

Create `agent_mcp/app/routes/pydanticai.py`:

```python
# agent_mcp/app/routes/pydanticai.py
from typing import Optional, Dict, Any
from starlette.responses import JSONResponse
from starlette.requests import Request

from ..decorators import api_route, require_auth
from ..responses import success_response, error_response
from ...agents.pydanticai_rag_agent import RAGAgent, AgentQueryContextDeps
from ...agents.pydanticai_task_agent import TaskAgent, TaskManagerDeps
from ...agents.pydanticai_orchestrator import AgentOrchestrator, OrchestrationRequest
from ...models.task import TaskCreate, TaskUpdate
from ...core.auth import get_agent_id_from_token


@api_route("POST", "/api/pydanticai/rag")
@require_auth
async def structured_rag_endpoint(request: Request):
    """Structured RAG query endpoint."""
    try:
        data = await request.json()
        query = data.get("query")
        agent_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not query:
            return error_response("query is required", status_code=400)
        
        agent_id = get_agent_id_from_token(agent_token)
        if not agent_id:
            return error_response("Invalid token", status_code=401)
        
        rag_agent = RAGAgent()
        agent_context = AgentQueryContextDeps(
            agent_id=agent_id,
            agent_role=data.get("agent_role")
        )
        
        response = await rag_agent.search(query=query, agent_context=agent_context)
        
        return success_response({
            "answer": response.answer,
            "confidence": response.confidence,
            "sources": response.sources,
            "suggested_queries": response.suggested_queries,
            "context_keys_used": response.context_keys_used
        })
        
    except Exception as e:
        return error_response(str(e), status_code=500)


@api_route("POST", "/api/pydanticai/tasks")
@require_auth
async def structured_task_endpoint(request: Request):
    """Structured task creation endpoint."""
    try:
        data = await request.json()
        agent_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        agent_id = get_agent_id_from_token(agent_token)
        if not agent_id:
            return error_response("Invalid token", status_code=401)
        
        task_agent = TaskAgent()
        task_deps = TaskManagerDeps(
            agent_id=agent_id,
            agent_role=data.get("agent_role")
        )
        
        task_create = TaskCreate(**data)
        output = await task_agent.create_task(task_create, task_deps)
        
        return success_response({
            "success": output.success,
            "task_id": output.task_id,
            "message": output.message,
            "task": output.task,
            "suggested_actions": output.suggested_actions
        })
        
    except Exception as e:
        return error_response(str(e), status_code=500)


@api_route("POST", "/api/pydanticai/orchestrate")
@require_auth
async def orchestrate_endpoint(request: Request):
    """Orchestration endpoint."""
    try:
        data = await request.json()
        query = data.get("query")
        agent_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not query:
            return error_response("query is required", status_code=400)
        
        agent_id = get_agent_id_from_token(agent_token)
        if not agent_id:
            return error_response("Invalid token", status_code=401)
        
        orchestrator = AgentOrchestrator()
        orchestration_request = OrchestrationRequest(
            query=query,
            agent_id=agent_id,
            agent_role=data.get("agent_role"),
            context=data.get("context")
        )
        
        result = await orchestrator.orchestrate(orchestration_request)
        
        return success_response({
            "success": result.success,
            "result": result.result,
            "rag_response": result.rag_response.model_dump() if result.rag_response else None,
            "task_outputs": [output.model_dump() for output in result.task_outputs],
            "next_steps": result.next_steps,
            "coordination_log": result.coordination_log
        })
        
    except Exception as e:
        return error_response(str(e), status_code=500)
```

### **Step 2: Register Routes**

Add to `agent_mcp/app/routes/__init__.py`:

```python
# agent_mcp/app/routes/__init__.py
# ... existing imports ...

from . import pydanticai  # This registers the routes
```

---

## 🧪 **Testing Your Integration**

### **Test MCP Tools (in Cursor)**

1. **Restart Agent-MCP server**
2. **In Cursor, try the new tools:**

```
# Test structured RAG
"Use ask_project_rag_structured to find out how authentication works"

# Test structured task creation
"Use create_task_structured to create a task for implementing OAuth2"

# Test orchestration
"Use orchestrate_workflow to find authentication info and create a task for OAuth2"
```

### **Test API Endpoints**

```bash
# Structured RAG
curl -X POST http://localhost:8080/api/pydanticai/rag \
  -H "Authorization: Bearer YOUR_AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "How does authentication work?"}'

# Structured Task Creation
curl -X POST http://localhost:8080/api/pydanticai/tasks \
  -H "Authorization: Bearer YOUR_AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement OAuth2",
    "description": "Add OAuth2 authentication",
    "priority": "high"
  }'

# Orchestration
curl -X POST http://localhost:8080/api/pydanticai/orchestrate \
  -H "Authorization: Bearer YOUR_AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What do we know about auth and create a task for OAuth2"}'
```

---

## 📊 **Comparison: Old vs New**

### **Old (Direct Function Call):**
```python
# Returns plain string
answer = await query_rag_system("How does auth work?")
# "Based on your codebase, authentication uses JWT tokens..."
```

### **New (PydanticAI Agent):**
```python
# Returns structured response
rag_agent = RAGAgent()
response = await rag_agent.search("How does auth work?", ...)
# RAGResponse(
#     answer="...",
#     confidence=0.91,
#     sources=[...],
#     suggested_queries=[...]
# )
```

---

## 🎯 **Benefits of Using PydanticAI Agents**

1. **Type Safety** - Pydantic validation catches errors early
2. **Structured Responses** - JSON models instead of plain text
3. **Better Error Handling** - Structured error responses
4. **Orchestration** - Coordinate multiple agents automatically
5. **Metadata** - Confidence scores, suggestions, context keys
6. **Extensibility** - Easy to add new fields to models

---

## 🚀 **Quick Start**

1. **Create the tool file** (`agent_mcp/tools/pydanticai_tools.py`) with code from Approach 1
2. **Import it** in `agent_mcp/tools/__init__.py`
3. **Restart Agent-MCP**
4. **Use in Cursor** - New tools will be available!

---

## 📝 **Example Usage in Cursor**

**With structured RAG:**
```
You: "Use ask_project_rag_structured to find authentication patterns"

Cursor: [Calls tool]
Result: 
Answer: Based on your codebase, authentication uses JWT tokens...
Confidence: 91%
Sources Found: 5
Suggested Follow-up Queries:
  - How are JWT tokens validated?
  - What is the token expiration policy?
```

**With orchestration:**
```
You: "Use orchestrate_workflow to find auth info and create a task for OAuth2"

Cursor: [Calls orchestrator]
Result:
🎯 Orchestration Result
Status: ✅ Success
Coordination Log:
  • Querying RAG agent for information...
  • RAG agent returned answer with 5 sources
  • Executing task management operations...
  • Created task: task_123
Next Steps:
  - Review authentication patterns
  - Assign task to backend agent
```

---

## ✅ **Summary**

**To use PydanticAI agents:**

1. **Add new tools** (recommended) - Create `pydanticai_tools.py` and register them
2. **Or replace existing tools** - Modify current implementations
3. **Or add API endpoints** - Expose via HTTP API

**The PydanticAI agents provide:**
- Structured, type-safe responses
- Confidence scores and metadata
- Orchestration capabilities
- Better error handling

**They're ready to use - just need to be connected!** 🚀
