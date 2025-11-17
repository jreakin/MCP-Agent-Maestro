"""
Tests for RAG memory tracker.
"""
import pytest
from datetime import datetime, timedelta
from agent_mcp.features.rag.memory_tracker import RAGMemoryTracker, get_memory_tracker


class TestRAGMemoryTracker:
    """Test RAG memory tracker functionality."""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh memory tracker for each test."""
        return RAGMemoryTracker()
    
    def test_record_access(self, tracker):
        """Test recording document access."""
        tracker.record_access("agent1", "vector_search", "doc1")
        accessed = tracker.get_accessed_docs("agent1")
        assert "vector_search:doc1" in accessed
    
    def test_has_accessed(self, tracker):
        """Test checking if agent has accessed a document."""
        tracker.record_access("agent1", "live_context", "context1")
        assert tracker.has_accessed("agent1", "live_context", "context1") is True
        assert tracker.has_accessed("agent1", "live_context", "context2") is False
    
    def test_get_new_docs(self, tracker):
        """Test filtering out already accessed documents."""
        tracker.record_access("agent1", "vector_search", "doc1")
        
        candidates = [
            {"source": "vector_search", "id": "doc1"},
            {"source": "vector_search", "id": "doc2"},
            {"source": "live_context", "id": "context1"},
        ]
        
        new_docs = tracker.get_new_docs("agent1", candidates)
        assert len(new_docs) == 2
        assert {"source": "vector_search", "id": "doc1"} not in new_docs
        assert {"source": "vector_search", "id": "doc2"} in new_docs
    
    def test_cache_expiration(self, tracker):
        """Test that cache entries expire after TTL."""
        # Manually set old timestamp
        tracker._cache["agent1"] = {
            "doc1": datetime.now() - timedelta(hours=25)  # Older than 24h TTL
        }
        
        accessed = tracker.get_accessed_docs("agent1")
        assert len(accessed) == 0  # Should be cleaned up
    
    def test_multiple_agents(self, tracker):
        """Test that different agents have separate caches."""
        tracker.record_access("agent1", "vector_search", "doc1")
        tracker.record_access("agent2", "vector_search", "doc1")
        
        assert tracker.has_accessed("agent1", "vector_search", "doc1") is True
        assert tracker.has_accessed("agent2", "vector_search", "doc1") is True
        
        # But they're tracked separately
        assert len(tracker.get_accessed_docs("agent1")) == 1
        assert len(tracker.get_accessed_docs("agent2")) == 1
    
    def test_get_memory_tracker_singleton(self):
        """Test that get_memory_tracker returns a singleton."""
        tracker1 = get_memory_tracker()
        tracker2 = get_memory_tracker()
        assert tracker1 is tracker2
    
    def test_record_access_no_agent_id(self, tracker):
        """Test that recording access with no agent_id is safe."""
        # Should not raise
        tracker.record_access(None, "vector_search", "doc1")
        tracker.record_access("", "vector_search", "doc1")

