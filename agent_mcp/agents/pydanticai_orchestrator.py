"""
PydanticAI Orchestrator for multi-agent coordination.
Coordinates RAG and task agents for complex workflows.

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
        f"pydantic-ai is required for PydanticAI Orchestrator. "
        f"Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai. "
        f"Original error: {e}"
    )

from ..core.config import logger, CHAT_MODEL
from ..external.openai_service import get_openai_client
from .pydanticai_rag_agent import RAGAgent, AgentQueryContextDeps, RAGResponse
from .pydanticai_task_agent import TaskAgent, TaskManagerDeps, TaskOutput
from .assessment_agent import assess_and_route


class OrchestrationRequest(BaseModel):
    """Request for agent orchestration."""
    query: str = Field(..., description="The orchestration query or request")
    agent_id: str = Field(..., description="ID of the requesting agent")
    agent_role: Optional[str] = Field(None, description="Agent role")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class OrchestrationResult(BaseModel):
    """Result from agent orchestration."""
    success: bool = Field(..., description="Whether orchestration succeeded")
    result: str = Field(..., description="Result description")
    rag_response: Optional[RAGResponse] = Field(None, description="RAG agent response if used")
    task_outputs: List[TaskOutput] = Field(default_factory=list, description="Task operation outputs")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next steps")
    coordination_log: List[str] = Field(default_factory=list, description="Coordination activity log")


class AgentOrchestrator:
    """PydanticAI orchestrator for multi-agent workflows."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize orchestrator.
        
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
        
        # Initialize sub-agents
        self.rag_agent = RAGAgent(model_name)
        self.task_agent = TaskAgent(model_name)
        
        # Create orchestrator agent
        self.orchestrator = Agent(
            model,
            system_prompt="""You are a multi-agent orchestrator.
You coordinate between RAG (Retrieval-Augmented Generation) and task management agents.
Your role is to:
1. Understand complex requests that require multiple agent capabilities
2. Coordinate sequential or parallel agent operations
3. Combine results from multiple agents into coherent responses
4. Suggest next steps based on agent outputs

Always break down complex requests into steps and coordinate agent operations efficiently.
Provide clear coordination logs of what each agent did.""",
            output_type=OrchestrationResult,
        )
    
    async def orchestrate(
        self,
        request: OrchestrationRequest,
        use_assessment: bool = True
    ) -> OrchestrationResult:
        """
        Orchestrate multi-agent workflow.
        
        Args:
            request: Orchestration request
            use_assessment: Whether to use assessment agent for routing
            
        Returns:
            Orchestration result
        """
        coordination_log = []
        task_outputs = []
        rag_response = None
        assessment_plan = None  # Initialize for scope
        
        try:
            # Use assessment agent if enabled
            if use_assessment:
                try:
                    assessment_plan = await assess_and_route(
                        query=request.query,
                        agent_id=request.agent_id,
                        context=request.context
                    )
                    coordination_log.append(f"Assessment: {assessment_plan['reasoning']}")
                    coordination_log.append(f"Selected: {assessment_plan['primary_agent']} with model {assessment_plan['model']}")
                    
                    # Use assessment to determine what to do
                    primary_agent = assessment_plan['primary_agent']
                    use_parallel = assessment_plan.get('use_parallel', False)
                    secondary_agents = assessment_plan.get('secondary_agents', [])
                    
                    # Determine needs based on assessment
                    needs_rag = primary_agent in ["rag", "orchestrate"] or "rag" in secondary_agents
                    needs_tasks = primary_agent in ["task", "orchestrate"] or "task" in secondary_agents
                    needs_code = primary_agent == "code" or "code" in secondary_agents
                    
                except Exception as e:
                    logger.warning(f"Assessment failed, using keyword-based detection: {e}")
                    use_assessment = False
                    assessment_plan = None
            
            # Fallback to keyword-based detection if assessment not used or failed
            if not use_assessment or assessment_plan is None:
                query_lower = request.query.lower()
                
                # Determine if RAG query is needed
                rag_keywords = ["what", "how", "explain", "find", "search", "information", "documentation"]
                needs_rag = any(keyword in query_lower for keyword in rag_keywords)
                
                # Determine if task operations are needed
                task_keywords = ["create", "update", "task", "assign", "status", "priority", "complete"]
                needs_tasks = any(keyword in query_lower for keyword in task_keywords)
                needs_code = False
                use_parallel = False
            
            # Execute agents (in parallel if requested)
            import asyncio
            
            async def execute_rag():
                """Execute RAG query."""
                coordination_log.append("Querying RAG agent for information...")
                try:
                    rag_deps = AgentQueryContextDeps(
                        agent_id=request.agent_id,
                        agent_role=request.agent_role
                    )
                    # Use model from assessment if available
                    if use_assessment and assessment_plan:
                        rag_agent = RAGAgent(model_name=assessment_plan.get('model'))
                    else:
                        rag_agent = self.rag_agent
                    
                    response = await rag_agent.search(
                        query=request.query,
                        agent_context=rag_deps
                    )
                    coordination_log.append(f"RAG agent returned answer with {len(response.sources)} sources")
                    return response
                except Exception as e:
                    coordination_log.append(f"RAG agent error: {str(e)}")
                    logger.error(f"RAG agent error in orchestration: {e}", exc_info=True)
                    return None
            
            async def execute_tasks():
                """Execute task operations."""
                coordination_log.append("Executing task management operations...")
                try:
                    task_deps = TaskManagerDeps(
                        agent_id=request.agent_id,
                        agent_role=request.agent_role
                    )
                    
                    # Use model from assessment if available
                    if use_assessment and assessment_plan:
                        task_agent = TaskAgent(model_name=assessment_plan.get('model'))
                    else:
                        task_agent = self.task_agent
                    
                    # Try to parse task creation from query
                    query_lower = request.query.lower()
                    if "create task" in query_lower or "new task" in query_lower:
                        from ..models.task import TaskCreate
                        task_create = TaskCreate(
                            title=request.query.split(":")[-1].strip() if ":" in request.query else "New Task",
                            description=request.query,
                            priority="medium"
                        )
                        output = await task_agent.create_task(task_create, task_deps)
                        return [output]
                    elif "list tasks" in query_lower or "show tasks" in query_lower:
                        tasks = await task_agent.list_tasks(deps=task_deps)
                        coordination_log.append(f"Retrieved {len(tasks)} tasks")
                        from .pydanticai_task_agent import TaskOutput
                        return [TaskOutput(
                            success=True,
                            message=f"Found {len(tasks)} tasks",
                            task={"count": len(tasks), "tasks": tasks}
                        )]
                    return []
                except Exception as e:
                    coordination_log.append(f"Task agent error: {str(e)}")
                    logger.error(f"Task agent error in orchestration: {e}", exc_info=True)
                    return []
            
            # Execute in parallel if requested, otherwise sequential
            if use_parallel and (needs_rag and needs_tasks):
                coordination_log.append("Executing agents in parallel...")
                rag_task = execute_rag() if needs_rag else None
                task_task = execute_tasks() if needs_tasks else None
                
                results = await asyncio.gather(
                    rag_task if rag_task else asyncio.sleep(0),
                    task_task if task_task else asyncio.sleep(0),
                    return_exceptions=True
                )
                
                if needs_rag and results[0] and not isinstance(results[0], Exception):
                    rag_response = results[0]
                if needs_tasks and results[1] and not isinstance(results[1], Exception):
                    task_outputs = results[1] if isinstance(results[1], list) else [results[1]]
            else:
                # Sequential execution
                if needs_rag:
                    rag_response = await execute_rag()
                if needs_tasks:
                    task_results = await execute_tasks()
                    task_outputs = task_results if isinstance(task_results, list) else [task_results] if task_results else []
            
            # Combine results
            result_text = ""
            if rag_response:
                result_text += f"RAG Response: {rag_response.answer}\n\n"
            if task_outputs:
                result_text += f"Task Operations: {len(task_outputs)} operations completed\n"
                for output in task_outputs:
                    result_text += f"- {output.message}\n"
            
            if not result_text:
                result_text = "No specific operations were performed based on the query."
            
            # Generate next steps
            next_steps = []
            if rag_response and rag_response.suggested_queries:
                next_steps.extend(rag_response.suggested_queries[:2])
            if task_outputs:
                for output in task_outputs:
                    next_steps.extend(output.suggested_actions[:2])
            
            return OrchestrationResult(
                success=True,
                result=result_text,
                rag_response=rag_response,
                task_outputs=task_outputs,
                next_steps=next_steps[:5],  # Limit to 5 next steps
                coordination_log=coordination_log
            )
            
        except Exception as e:
            logger.error(f"Error in orchestration: {e}", exc_info=True)
            return OrchestrationResult(
                success=False,
                result=f"Orchestration error: {str(e)}",
                rag_response=rag_response,
                task_outputs=task_outputs,
                next_steps=["Review error logs", "Retry with simpler query"],
                coordination_log=coordination_log + [f"Error: {str(e)}"]
            )
    
    async def coordinate_rag_and_tasks(
        self,
        rag_query: str,
        task_operation: Optional[str] = None,
        agent_id: str = "orchestrator",
        agent_role: Optional[str] = None
    ) -> OrchestrationResult:
        """
        Coordinate RAG query with optional task operation.
        
        Args:
            rag_query: RAG query string
            task_operation: Optional task operation description
            agent_id: Agent ID
            agent_role: Agent role
            
        Returns:
            Orchestration result
        """
        query = rag_query
        if task_operation:
            query += f"\nAlso: {task_operation}"
        
        request = OrchestrationRequest(
            query=query,
            agent_id=agent_id,
            agent_role=agent_role
        )
        
        return await self.orchestrate(request)


# Convenience function for orchestrating workflows
async def orchestrate_workflow(
    query: str,
    agent_id: str,
    agent_role: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> OrchestrationResult:
    """
    Orchestrate a multi-agent workflow.
    
    Args:
        query: The orchestration query
        agent_id: Agent ID
        agent_role: Agent role
        context: Additional context
        
    Returns:
        Orchestration result
    """
    orchestrator = AgentOrchestrator()
    request = OrchestrationRequest(
        query=query,
        agent_id=agent_id,
        agent_role=agent_role,
        context=context
    )
    return await orchestrator.orchestrate(request)

