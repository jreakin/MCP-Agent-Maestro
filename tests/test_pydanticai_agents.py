"""
Hypothesis tests for PydanticAI agents.
Tests RAG agent, task agent, and orchestrator with property-based testing.

NOTE: These tests require pydantic-ai to be installed.
Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai
"""

import pytest

# Check if pydantic-ai is available - skip entire module if not installed
try:
    import pydantic_ai
except ImportError:
    pytest.skip("pydantic-ai is required for PydanticAI agent tests. Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai", allow_module_level=True)

from hypothesis import given, strategies as st, assume, settings, example, HealthCheck
from hypothesis.strategies import text, lists, dictionaries, none, one_of, datetimes, composite
from typing import Dict, Any, Optional, List
from datetime import datetime

from agent_mcp.agents.pydanticai_rag_agent import (
    RAGAgent,
    AgentQueryContextDeps,
    RAGResponse
)
from agent_mcp.agents.pydanticai_task_agent import (
    TaskAgent,
    TaskManagerDeps,
    TaskOutput
)
from agent_mcp.agents.pydanticai_orchestrator import (
    AgentOrchestrator,
    OrchestrationRequest,
    OrchestrationResult
)
from agent_mcp.models.task import TaskCreate, TaskUpdate


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    # In real tests, this would mock the OpenAI client
    # For Hypothesis tests, we'll skip tests that require actual API calls
    pass


@composite
def agent_query_context_deps_strategy(draw):
    """Generate random AgentQueryContextDeps for testing."""
    return AgentQueryContextDeps(
        agent_id=draw(text(min_size=1, max_size=50)),
        agent_role=draw(one_of(none(), st.sampled_from(['worker', 'frontend', 'security', 'research', 'manager']))),
        current_task=draw(one_of(none(), text(min_size=1, max_size=50))),
        agent_mode=draw(one_of(none(), st.sampled_from(['simple', 'advanced', 'expert'])))
    )


@composite
def task_manager_deps_strategy(draw):
    """Generate random TaskManagerDeps for testing."""
    return TaskManagerDeps(
        agent_id=draw(text(min_size=1, max_size=50)),
        agent_role=draw(one_of(none(), st.sampled_from(['admin', 'worker', 'manager']))),
        project_dir=draw(one_of(none(), text(min_size=1, max_size=200)))
    )


class TestRAGAgent:
    """Test RAG agent with Hypothesis."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @given(
        query=text(min_size=1, max_size=500),
        context=agent_query_context_deps_strategy(),
        format_type=st.sampled_from(['json', 'toon'])
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_search_returns_rag_response(self, query: str, context: AgentQueryContextDeps, format_type: str, db_connection):
        """Search returns a RAGResponse."""
        agent = RAGAgent()
        response = await agent.search(query, context, format_type)
        
        assert isinstance(response, RAGResponse)
        assert isinstance(response.answer, str)
        assert 0.0 <= response.confidence <= 1.0
        assert isinstance(response.suggested_queries, list)
        assert isinstance(response.context_keys_used, list)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @given(
        context_key=text(min_size=1, max_size=100),
        agent_id=text(min_size=1, max_size=50)
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_get_memory_returns_dict_or_none(self, context_key: str, agent_id: str, db_connection):
        """Get memory returns a dict or None."""
        agent = RAGAgent()
        memory = await agent.get_memory(context_key, agent_id)
        
        if memory is not None:
            assert isinstance(memory, dict)
            assert 'context_key' in memory or 'value' in memory


class TestTaskAgent:
    """Test task agent with Hypothesis."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @given(
        title=text(min_size=1, max_size=300),
        description=one_of(none(), text(max_size=5000)),
        priority=st.sampled_from(['low', 'medium', 'high', 'critical']),
        deps=task_manager_deps_strategy()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_create_task_returns_task_output(self, title: str, description: Optional[str], priority: str, deps: TaskManagerDeps, db_connection):
        """Create task returns a TaskOutput."""
        # Filter out whitespace-only titles
        assume(title.strip())
        
        from agent_mcp.models.task import TaskCreate
        
        agent = TaskAgent()
        task_create = TaskCreate(
            title=title,
            description=description,
            priority=priority
        )
        
        output = await agent.create_task(task_create, deps)
        
        assert isinstance(output, TaskOutput)
        assert isinstance(output.success, bool)
        assert isinstance(output.message, str)
        if output.success:
            assert output.task_id is not None
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @given(
        task_id=text(min_size=1, max_size=100),
        description=one_of(none(), text(min_size=1, max_size=100)),
        status=one_of(none(), st.sampled_from(['pending', 'in_progress', 'completed', 'blocked', 'cancelled', 'failed'])),
        priority=one_of(none(), st.sampled_from(['low', 'medium', 'high', 'critical'])),
        deps=task_manager_deps_strategy()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_update_task_returns_task_output(self, task_id: str, description: Optional[str], status: Optional[str], priority: Optional[str], deps: TaskManagerDeps, db_connection):
        """Update task returns a TaskOutput."""
        from agent_mcp.models.task import TaskUpdate
        
        agent = TaskAgent()
        # Build fields dict with only non-None values
        fields = {}
        if description is not None:
            fields['description'] = description
        if status is not None:
            fields['status'] = status
        if priority is not None:
            fields['priority'] = priority
        
        # Skip if no fields to update
        if not fields:
            return
        
        task_update = TaskUpdate(**fields)
        
        output = await agent.update_task(task_id, task_update, deps)
        
        assert isinstance(output, TaskOutput)
        assert isinstance(output.success, bool)
        assert isinstance(output.message, str)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @given(
        deps=task_manager_deps_strategy(),
        status=one_of(none(), st.sampled_from(['pending', 'in_progress', 'completed'])),
        assigned_to=one_of(none(), text(min_size=1, max_size=50))
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_list_tasks_returns_list(self, deps: TaskManagerDeps, status: Optional[str], assigned_to: Optional[str], db_connection):
        """List tasks returns a list."""
        agent = TaskAgent()
        tasks = await agent.list_tasks(status=status, assigned_to=assigned_to, deps=deps)
        
        assert isinstance(tasks, list)
        # All items should be dicts if not empty
        if tasks:
            assert all(isinstance(task, dict) for task in tasks)


class TestAgentOrchestrator:
    """Test agent orchestrator with Hypothesis."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @given(
        query=text(min_size=1, max_size=500),
        agent_id=text(min_size=1, max_size=50),
        agent_role=one_of(none(), st.sampled_from(['admin', 'worker', 'manager']))
    )
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_orchestrate_returns_orchestration_result(self, query: str, agent_id: str, agent_role: Optional[str], db_connection):
        """Orchestrate returns an OrchestrationResult."""
        orchestrator = AgentOrchestrator()
        request = OrchestrationRequest(
            query=query,
            agent_id=agent_id,
            agent_role=agent_role
        )
        
        result = await orchestrator.orchestrate(request)
        
        assert isinstance(result, OrchestrationResult)
        assert isinstance(result.success, bool)
        assert isinstance(result.result, str)
        assert isinstance(result.coordination_log, list)
        assert isinstance(result.next_steps, list)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @given(
        rag_query=text(min_size=1, max_size=300),
        task_operation=one_of(none(), text(min_size=1, max_size=200)),
        agent_id=text(min_size=1, max_size=50)
    )
    @settings(max_examples=20, deadline=20000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_coordinate_rag_and_tasks_returns_result(self, rag_query: str, task_operation: Optional[str], agent_id: str, db_connection):
        """Coordinate RAG and tasks returns an OrchestrationResult."""
        orchestrator = AgentOrchestrator()
        result = await orchestrator.coordinate_rag_and_tasks(
            rag_query=rag_query,
            task_operation=task_operation,
            agent_id=agent_id
        )
        
        assert isinstance(result, OrchestrationResult)
        assert isinstance(result.success, bool)
        assert isinstance(result.result, str)

