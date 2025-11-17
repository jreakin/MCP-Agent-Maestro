# Agent-MCP RAG Response Personalizer
"""
Personalize RAG responses based on agent context.
"""

from typing import List, Dict, Any, Optional
from .context import AgentQueryContext
from ...core.config import logger


class ResponsePersonalizer:
    """Personalize RAG responses for specific agent contexts."""
    
    # Role-specific keywords for filtering
    ROLE_KEYWORDS = {
        'frontend': ['ui', 'component', 'react', 'vue', 'angular', 'css', 'html', 'frontend', 'client', 'browser'],
        'security': ['security', 'vulnerability', 'auth', 'encryption', 'secure', 'safe', 'attack', 'exploit'],
        'research': ['architecture', 'design', 'pattern', 'structure', 'analysis', 'overview'],
        'manager': ['overview', 'status', 'progress', 'summary', 'coordination'],
        'worker': ['implementation', 'code', 'function', 'class', 'method', 'api'],
    }
    
    def personalize_response(
        self,
        raw_results: List[Dict[str, Any]],
        agent_context: AgentQueryContext
    ) -> List[Dict[str, Any]]:
        """
        Filter and personalize RAG results based on agent context.
        
        Args:
            raw_results: Raw RAG retrieval results
            agent_context: Agent context metadata
            
        Returns:
            Personalized and filtered results
        """
        if not raw_results:
            return []
        
        # Filter by role relevance
        filtered = self._filter_by_role(raw_results, agent_context.agent_role)
        
        # Adjust complexity based on agent mode
        adjusted = self._adjust_complexity(filtered, agent_context.agent_mode)
        
        # Re-rank based on task context
        reranked = self._rerank_by_task_context(adjusted, agent_context)
        
        return reranked
    
    def _filter_by_role(
        self,
        results: List[Dict[str, Any]],
        agent_role: str
    ) -> List[Dict[str, Any]]:
        """Filter results by relevance to agent role."""
        if agent_role not in self.ROLE_KEYWORDS:
            return results
        
        keywords = self.ROLE_KEYWORDS[agent_role]
        scored_results = []
        
        for result in results:
            score = 0
            content = str(result.get('content', '') + ' ' + result.get('title', '')).lower()
            
            # Score based on keyword matches
            for keyword in keywords:
                if keyword in content:
                    score += 1
            
            if score > 0 or agent_role == 'worker':  # Workers get all results
                scored_results.append({
                    **result,
                    '_role_score': score
                })
        
        # Sort by role score
        scored_results.sort(key=lambda x: x.get('_role_score', 0), reverse=True)
        
        # Return top results (at least 3, up to original count)
        return scored_results[:max(3, len(results))]
    
    def _adjust_complexity(
        self,
        results: List[Dict[str, Any]],
        agent_mode: str
    ) -> List[Dict[str, Any]]:
        """Adjust result complexity based on agent mode."""
        # For now, just return as-is
        # Future: could filter out advanced concepts for simpler modes
        return results
    
    def _rerank_by_task_context(
        self,
        results: List[Dict[str, Any]],
        agent_context: AgentQueryContext
    ) -> List[Dict[str, Any]]:
        """Re-rank results based on current task context."""
        if not agent_context.current_task:
            return results
        
        # Boost results that mention task-related keywords
        # This is a simple implementation - could be enhanced with actual task content
        for result in results:
            content = str(result.get('content', '')).lower()
            # Simple boost if content seems relevant to task context
            if agent_context.current_task.lower() in content:
                result['_task_boost'] = result.get('_task_boost', 0) + 1
        
        # Sort by task boost if available
        results.sort(key=lambda x: x.get('_task_boost', 0), reverse=True)
        
        return results
    
    def add_role_guidance(
        self,
        response_text: str,
        agent_context: AgentQueryContext
    ) -> str:
        """
        Add role-specific guidance to response.
        
        Args:
            response_text: Base response text
            agent_context: Agent context
            
        Returns:
            Response with role-specific guidance
        """
        guidance_prefix = ""
        
        if agent_context.agent_role == 'frontend':
            guidance_prefix = "As a frontend specialist, focus on UI/UX patterns and component architecture. "
        elif agent_context.agent_role == 'security':
            guidance_prefix = "As a security reviewer, pay special attention to security implications. "
        elif agent_context.agent_role == 'research':
            guidance_prefix = "As a research agent, focus on understanding architecture and design patterns. "
        
        if guidance_prefix:
            return guidance_prefix + response_text
        
        return response_text
    
    def format_response(
        self,
        response_text: str,
        agent_context: AgentQueryContext
    ) -> str:
        """
        Format response with task-specific context.
        
        Args:
            response_text: Response text
            agent_context: Agent context
            
        Returns:
            Formatted response
        """
        # Add context about current task if available
        if agent_context.current_task:
            task_context = f"\n\n[Note: You are currently working on task: {agent_context.current_task}]"
            response_text += task_context
        
        return response_text

