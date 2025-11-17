"""
Assessment Agent - Analyzes requests and routes to appropriate agents/models.
Intelligently selects the best agent and model for each request.

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
        f"pydantic-ai is required for Assessment Agent. "
        f"Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai. "
        f"Original error: {e}"
    )

from ..core.config import logger
from ..external.openai_service import get_openai_client
from ..external.ollama_service import (
    get_best_chat_model,
    get_best_code_model,
    get_available_ollama_models
)


class AssessmentRequest(BaseModel):
    """Request for assessment."""
    query: str = Field(..., description="The user query to assess")
    agent_id: str = Field(..., description="ID of requesting agent")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class AgentSelection(BaseModel):
    """Selected agents and models for the request."""
    primary_agent: str = Field(..., description="Primary agent type: 'rag', 'task', 'code', 'chat', 'orchestrate'")
    model_name: str = Field(..., description="Model to use for this request")
    secondary_agents: List[str] = Field(default_factory=list, description="Additional agents to involve")
    reasoning: str = Field(..., description="Why these agents were selected")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in selection")
    use_parallel: bool = Field(default=False, description="Whether to run agents in parallel")


class AssessmentAgent:
    """Agent that assesses requests and selects appropriate agents/models."""
    
    def __init__(self, assessment_model: Optional[str] = None):
        """
        Initialize assessment agent.
        
        Args:
            assessment_model: Model to use for assessment (defaults to fast/lightweight model)
        """
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        
        if embedding_provider == "ollama":
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            provider = OpenAIProvider(
                base_url=f"{ollama_base_url}/v1",
                api_key="ollama"
            )
            # Use lightweight model for fast assessment
            model_name = assessment_model or os.getenv("OLLAMA_ASSESSMENT_MODEL", "llama3.2")
            model = OpenAIModel(model_name, provider=provider)
        else:
            openai_client = get_openai_client()
            if not openai_client:
                raise ValueError("OpenAI client not available")
            # Use fast, cheap model for assessment
            model = OpenAIModel(assessment_model or "gpt-4o-mini")
        
        self.agent = Agent(
            model,
            system_prompt="""You are an assessment agent that analyzes user requests and determines the best way to handle them.

Your job is to:
1. Analyze the request type (code generation, RAG query, task management, general chat, etc.)
2. Select the most appropriate agent type(s) to handle it
3. Choose the best model for the task (code model for code, chat model for general, etc.)
4. Determine if multiple agents should work in parallel

Agent types:
- 'rag': For questions about project knowledge, documentation, codebase understanding
- 'task': For creating, updating, or managing tasks
- 'code': For code generation, code analysis, programming questions
- 'chat': For general conversation, explanations, help
- 'orchestrate': For complex requests requiring multiple agents

Model selection:
- Use code models (codellama, deepseek-coder) for code-related tasks
- Use chat models (llama3.2, mistral) for general tasks
- Use embedding models for RAG queries (handled separately)

Be precise and efficient. Consider:
- Code keywords: function, class, def, import, code, implement, write, parse, sql, query
- Task keywords: create task, assign, update task, task status
- RAG keywords: what, how, explain, find, search, information, documentation
- General: questions, help, explain, describe

Return your assessment with clear reasoning.""",
            output_type=AgentSelection
        )
        
        self._available_models_cache: Optional[Dict[str, List[str]]] = None
    
    async def _get_available_models(self, force_refresh: bool = False) -> Dict[str, List[str]]:
        """Get available models by type."""
        if self._available_models_cache is None or force_refresh:
            models = await get_available_ollama_models()
            model_names = [m.get("name", "") for m in models if m.get("name")]
            
            self._available_models_cache = {
                "chat": [],
                "code": [],
                "embedding": []
            }
            
            for name in model_names:
                name_lower = name.lower()
                if any(kw in name_lower for kw in ["code", "coder", "deepseek"]):
                    self._available_models_cache["code"].append(name)
                elif any(kw in name_lower for kw in ["embed", "nomic", "mxbai"]):
                    self._available_models_cache["embedding"].append(name)
                else:
                    self._available_models_cache["chat"].append(name)
        
        return self._available_models_cache
    
    async def assess_request(self, request: AssessmentRequest) -> AgentSelection:
        """
        Assess request and select appropriate agents/models.
        
        Args:
            request: Assessment request
            
        Returns:
            Agent selection with reasoning
        """
        try:
            # Get available models
            available = await self._get_available_models()
            
            # Build context about available models
            available_info = []
            if available["chat"]:
                available_info.append(f"Chat models: {', '.join(available['chat'][:3])}")
            if available["code"]:
                available_info.append(f"Code models: {', '.join(available['code'][:3])}")
            if available["embedding"]:
                available_info.append(f"Embedding models: {', '.join(available['embedding'][:3])}")
            
            context = f"""
Available models:
{chr(10).join(available_info) if available_info else 'No models available'}

User query: {request.query}
Requesting agent: {request.agent_id}
"""
            
            if request.context:
                context += f"\nAdditional context: {request.context}"
            
            # Use LLM to assess
            result = await self.agent.run(context)
            selection = result.data
            
            # Validate and adjust based on actual availability
            if selection.primary_agent == "code" and available["code"]:
                selection.model_name = available["code"][0]
                logger.info(f"Assessment: Using code model {selection.model_name} for code request")
            elif selection.primary_agent in ["rag", "chat", "orchestrate"] and available["chat"]:
                selection.model_name = available["chat"][0]
                logger.info(f"Assessment: Using chat model {selection.model_name} for {selection.primary_agent} request")
            else:
                # Fallback to chat model
                if available["chat"]:
                    selection.model_name = available["chat"][0]
                    if selection.primary_agent == "code":
                        selection.primary_agent = "chat"
                        selection.reasoning += " (Code model not available, using chat model)"
                    logger.warning(f"Assessment: Fallback to chat model {selection.model_name}")
            
            # If no model found, use defaults
            if not selection.model_name:
                chat_model = await get_best_chat_model() or "llama3.2"
                selection.model_name = chat_model
                logger.warning(f"Assessment: Using default model {chat_model}")
            
            return selection
            
        except Exception as e:
            logger.error(f"Error in assessment: {e}", exc_info=True)
            # Fallback to default
            chat_model = await get_best_chat_model() or "llama3.2"
            return AgentSelection(
                primary_agent="chat",
                model_name=chat_model,
                reasoning=f"Assessment failed, using default: {str(e)}",
                confidence=0.5
            )
    
    async def route_request(
        self,
        query: str,
        agent_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assess and route request to appropriate agent(s).
        
        Args:
            query: User query
            agent_id: Requesting agent ID
            context: Additional context
            
        Returns:
            Dictionary with selected agents and execution plan
        """
        assessment = await self.assess_request(
            AssessmentRequest(query=query, agent_id=agent_id, context=context)
        )
        
        # Create execution plan
        execution_plan = {
            "primary_agent": assessment.primary_agent,
            "model": assessment.model_name,
            "secondary_agents": assessment.secondary_agents,
            "reasoning": assessment.reasoning,
            "confidence": assessment.confidence,
            "use_parallel": assessment.use_parallel
        }
        
        logger.info(f"Assessment result: {execution_plan}")
        return execution_plan


# Global assessment agent instance
_assessment_agent: Optional[AssessmentAgent] = None


def get_assessment_agent() -> AssessmentAgent:
    """Get or create global assessment agent."""
    global _assessment_agent
    if _assessment_agent is None:
        _assessment_agent = AssessmentAgent()
    return _assessment_agent


async def assess_and_route(
    query: str,
    agent_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Assess request and get routing plan.
    
    Args:
        query: User query
        agent_id: Requesting agent ID
        context: Additional context
        
    Returns:
        Execution plan dictionary
    """
    agent = get_assessment_agent()
    return await agent.route_request(query, agent_id, context)
