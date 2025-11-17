"""
PydanticAI RAG Agent for structured query handling.
Provides type-safe RAG operations with Pydantic models.

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
        f"pydantic-ai is required for PydanticAI RAG Agent. "
        f"Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai. "
        f"Original error: {e}"
    )

from ..core.config import logger, CHAT_MODEL
from ..external.openai_service import get_openai_client
from ..features.rag.query import query_rag_system
from ..features.rag.context import AgentQueryContext
from ..db.actions.context_db import get_context_by_key


class AgentQueryContextDeps(BaseModel):
    """Dependencies for RAG agent queries."""
    agent_id: str = Field(..., description="ID of the agent making the query")
    agent_role: Optional[str] = Field(None, description="Agent role for context-aware responses")
    current_task: Optional[str] = Field(None, description="Current task ID for task-specific context")
    agent_mode: Optional[str] = Field(None, description="Agent mode (simple, advanced, etc.)")


class RAGResponse(BaseModel):
    """Structured response from RAG query."""
    answer: str = Field(..., description="The answer to the query")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source references")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score (0-1)")
    suggested_queries: List[str] = Field(default_factory=list, description="Suggested follow-up queries")
    context_keys_used: List[str] = Field(default_factory=list, description="Context keys referenced")


class RAGAgent:
    """PydanticAI agent for RAG operations."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize RAG agent.
        
        Args:
            model_name: Model name (defaults to CHAT_MODEL from config or Ollama model)
        """
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        
        # Configure model based on provider
        if embedding_provider == "ollama":
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
            # Model will be auto-detected on first use if not specified
            self.model_name = model_name or os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
            self._ollama_base_url = ollama_base_url
            self._model_detected = False
            
            # Use Ollama's OpenAI-compatible endpoint
            # Model will be auto-detected on first use if needed
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
            system_prompt="""You are a specialized RAG (Retrieval-Augmented Generation) agent.
You help answer questions by querying project context, documentation, and indexed knowledge.
Always provide accurate, context-aware answers based on the retrieved information.
When appropriate, suggest related queries or context keys that might be helpful.""",
            output_type=RAGResponse,
        )
    
    async def _ensure_model_detected(self):
        """Ensure Ollama model is detected if using Ollama."""
        if not self._model_detected and os.getenv("EMBEDDING_PROVIDER", "openai").lower() == "ollama":
            from ..external.ollama_service import get_best_chat_model
            try:
                detected_model = await get_best_chat_model()
                if detected_model:
                    self.model_name = detected_model
                    logger.info(f"Auto-detected Ollama chat model: {detected_model}")
                    # Recreate provider with detected model
                    provider = OpenAIProvider(
                        base_url=f"{self._ollama_base_url}/v1",
                        api_key="ollama"
                    )
                    model = OpenAIModel(self.model_name, provider=provider)
                    self.agent = Agent(
                        model,
                        system_prompt=self.agent.system_prompt,
                        output_type=self.agent.output_type
                    )
            except Exception as e:
                logger.warning(f"Could not auto-detect Ollama model: {e}, using {self.model_name}")
            finally:
                self._model_detected = True
    
    async def search(
        self,
        query: str,
        agent_context: AgentQueryContextDeps,
        format_type: str = "json"
    ) -> RAGResponse:
        """
        Search the RAG system for information.
        
        Args:
            query: The search query
            agent_context: Agent context dependencies
            format_type: Serialization format ('json' or 'toon')
            
        Returns:
            Structured RAG response
        """
        try:
            # Auto-detect model if needed
            await self._ensure_model_detected()
            
            # Get agent context if needed
            from ..features.rag.context import get_agent_context
            
            context_obj = None
            if agent_context.agent_id:
                context_obj = get_agent_context(agent_context.agent_id)
                if context_obj:
                    # Update context with provided values
                    if agent_context.agent_role:
                        context_obj.agent_role = agent_context.agent_role
                    if agent_context.current_task:
                        context_obj.current_task = agent_context.current_task
                    if agent_context.agent_mode:
                        context_obj.agent_mode = agent_context.agent_mode
            
            # Query RAG system
            answer_text = await query_rag_system(
                query_text=query,
                agent_id=agent_context.agent_id,
                agent_context=context_obj,
                format_type=format_type
            )
            
            # Build structured response
            response = RAGResponse(
                answer=answer_text,
                confidence=0.8,  # Default confidence, could be enhanced with actual scoring
                suggested_queries=self._generate_suggested_queries(query, answer_text),
                context_keys_used=await self._extract_context_keys(query)
            )
            
            return response
        except Exception as e:
            logger.error(f"Error in RAG agent search: {e}", exc_info=True)
            return RAGResponse(
                answer=f"Error processing query: {str(e)}",
                confidence=0.0,
                suggested_queries=[],
                context_keys_used=[]
            )
    
    async def get_memory(
        self,
        context_key: str,
        agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory/context entry.
        
        Args:
            context_key: The context key to retrieve
            agent_id: Agent ID for authorization
            
        Returns:
            Context entry or None
        """
        try:
            context_entry = get_context_by_key(context_key)
            if context_entry:
                return {
                    "context_key": context_entry.get("context_key"),
                    "value": context_entry.get("value"),
                    "description": context_entry.get("description"),
                    "last_updated": context_entry.get("last_updated")
                }
            return None
        except Exception as e:
            logger.error(f"Error getting memory: {e}", exc_info=True)
            return None
    
    def _generate_suggested_queries(self, query: str, answer: str) -> List[str]:
        """Generate suggested follow-up queries."""
        # Simple heuristic-based suggestions
        suggestions = []
        
        # Suggest related topics if answer mentions specific concepts
        if "API" in answer or "endpoint" in answer.lower():
            suggestions.append("What are all the API endpoints in this project?")
        
        if "database" in answer.lower() or "schema" in answer.lower():
            suggestions.append("What is the database schema structure?")
        
        if "configuration" in answer.lower() or "config" in answer.lower():
            suggestions.append("What configuration options are available?")
        
        # General query suggestions
        if not suggestions:
            suggestions.append(f"Tell me more about {query.split()[0] if query.split() else 'this'}")
            suggestions.append("What are the main components of this system?")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    async def _extract_context_keys(self, query: str) -> List[str]:
        """Extract relevant context keys from query."""
        # Simple keyword-based extraction
        # In a real implementation, this could use NLP or keyword matching
        context_keys = []
        
        query_lower = query.lower()
        if "api" in query_lower:
            context_keys.append("api.config")
        if "database" in query_lower or "db" in query_lower:
            context_keys.append("db.config")
        if "auth" in query_lower or "authentication" in query_lower:
            context_keys.append("auth.config")
        
        return context_keys


# Tool definitions for PydanticAI agent
async def search_tool(query: str, deps: AgentQueryContextDeps) -> RAGResponse:
    """Search tool for PydanticAI agent."""
    agent = RAGAgent()
    return await agent.search(query, deps)


async def get_memory_tool(context_key: str, deps: AgentQueryContextDeps) -> Optional[Dict[str, Any]]:
    """Get memory tool for PydanticAI agent."""
    agent = RAGAgent()
    return await agent.get_memory(context_key, deps.agent_id)

