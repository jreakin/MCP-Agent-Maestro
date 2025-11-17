# Agent-MCP RAG Memory Tracker
"""
Track which documentation agents have accessed to avoid repetition
and provide complementary information.
"""
from typing import Set, List, Dict, Optional
from datetime import datetime, timedelta
from ...db.connection_factory import db_connection
from ...core.config import logger


class RAGMemoryTracker:
    """Track which docs agents have accessed."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, datetime]] = {}  # agent_id -> {doc_id: timestamp}
        self._cache_ttl = timedelta(hours=24)  # Cache for 24 hours
    
    def record_access(self, agent_id: str, doc_source: str, doc_id: str):
        """
        Record that an agent accessed a specific document.
        
        Args:
            agent_id: ID of the agent
            doc_source: Source of the document (e.g., 'vector_search', 'live_context')
            doc_id: Unique identifier for the document
        """
        if not agent_id:
            return
        
        try:
            # Store in memory cache
            if agent_id not in self._cache:
                self._cache[agent_id] = {}
            
            # Use composite key: source:doc_id
            cache_key = f"{doc_source}:{doc_id}"
            self._cache[agent_id][cache_key] = datetime.now()
            
            # Optionally store in database for persistence
            # For now, just use in-memory cache
        except Exception as e:
            logger.warning(f"Failed to record RAG access: {e}")
    
    def get_accessed_docs(self, agent_id: str) -> Set[str]:
        """
        Get set of document IDs the agent has recently accessed.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Set of document identifiers (format: "source:doc_id")
        """
        if not agent_id or agent_id not in self._cache:
            return set()
        
        # Clean up old entries
        now = datetime.now()
        agent_cache = self._cache[agent_id]
        expired_keys = [
            key for key, timestamp in agent_cache.items()
            if now - timestamp > self._cache_ttl
        ]
        for key in expired_keys:
            del agent_cache[key]
        
        return set(agent_cache.keys())
    
    def has_accessed(self, agent_id: str, doc_source: str, doc_id: str) -> bool:
        """
        Check if agent has recently accessed a specific document.
        
        Args:
            agent_id: ID of the agent
            doc_source: Source of the document
            doc_id: Document identifier
            
        Returns:
            True if agent has accessed this document recently
        """
        cache_key = f"{doc_source}:{doc_id}"
        accessed = self.get_accessed_docs(agent_id)
        return cache_key in accessed
    
    def get_new_docs(
        self,
        agent_id: str,
        candidate_docs: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Filter out documents the agent has already accessed.
        
        Args:
            agent_id: ID of the agent
            candidate_docs: List of candidate documents with 'source' and 'id' keys
            
        Returns:
            List of documents the agent hasn't accessed yet
        """
        accessed = self.get_accessed_docs(agent_id)
        new_docs = []
        
        for doc in candidate_docs:
            doc_source = doc.get('source', 'unknown')
            doc_id = doc.get('id', doc.get('chunk_id', ''))
            cache_key = f"{doc_source}:{doc_id}"
            
            if cache_key not in accessed:
                new_docs.append(doc)
        
        return new_docs


# Global instance
_memory_tracker: Optional[RAGMemoryTracker] = None


def get_memory_tracker() -> RAGMemoryTracker:
    """Get or create global memory tracker instance."""
    global _memory_tracker
    if _memory_tracker is None:
        _memory_tracker = RAGMemoryTracker()
    return _memory_tracker

