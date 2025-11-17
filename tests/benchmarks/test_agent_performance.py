"""
Benchmark tests for agent creation and management performance.
"""
import pytest
import time
from agent_mcp.db.actions.agent_db import get_all_active_agents_from_db
from agent_mcp.core.settings import get_settings


@pytest.mark.benchmark
@pytest.mark.skip(reason="Agent creation is done via tools, not direct DB function")
def test_agent_creation_time(benchmark):
    """Benchmark agent creation time."""
    settings = get_settings()
    
    def create_agent():
        """Create a test agent."""
        # Agent creation is handled through create_agent_tool_impl
        # Not directly accessible via DB function
        pass
    
    result = benchmark(create_agent)
    assert result is not None


@pytest.mark.benchmark
def test_agent_listing_performance(benchmark):
    """Benchmark agent listing performance."""
    
    def list_agents():
        """List all active agents."""
        return get_all_active_agents_from_db()
    
    result = benchmark(list_agents)
    assert isinstance(result, list)


@pytest.mark.benchmark
@pytest.mark.skip(reason="Agent creation is done via tools, not direct DB function")
def test_concurrent_agent_creation(benchmark):
    """Benchmark concurrent agent creation."""
    import asyncio
    
    async def create_agents_concurrent():
        """Create multiple agents concurrently."""
        # Agent creation is handled through create_agent_tool_impl
        # Not directly accessible via DB function
        pass
    
    # Note: Benchmark may need adjustment for async functions
    result = benchmark.pedantic(
        lambda: asyncio.run(create_agents_concurrent()),
        iterations=3,
        rounds=5
    )
    assert result is not None

