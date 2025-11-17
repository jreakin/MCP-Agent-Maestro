"""
Benchmark tests for task assignment and management performance.
"""
import pytest
import time
from agent_mcp.db.actions.task_db import create_task_in_db, get_all_tasks_from_db, update_task_fields_in_db
from agent_mcp.core.settings import get_settings


@pytest.mark.benchmark
def test_task_creation_time(benchmark):
    """Benchmark task creation time."""
    
    def create_task():
        """Create a test task."""
        task_data = {
            "title": "Test Task",
            "description": "Benchmark task creation",
            "priority": "medium",
            "status": "pending"
        }
        return create_task_in_db(**task_data)
    
    result = benchmark(create_task)
    assert result is not None
    assert isinstance(result, str)  # create_task_in_db returns task_id as string


@pytest.mark.benchmark
def test_task_assignment_latency(benchmark):
    """Benchmark task assignment latency."""
    from agent_mcp.db.actions.agent_db import get_agent_by_id
    
    # Setup: Get an existing agent (or skip if none exist)
    agents = get_all_active_agents_from_db()
    if not agents:
        pytest.skip("No active agents available for assignment test")
    
    agent_id = agents[0]["agent_id"]
    
    # Setup: Create a task
    task_data = {
        "title": "Assignment Test",
        "description": "Benchmark task assignment",
        "priority": "medium",
        "status": "pending"
    }
    task_id = create_task_in_db(**task_data)
    
    def assign_task():
        """Assign task to agent."""
        return update_task_fields_in_db(task_id, {'assigned_to': agent_id})
    
    result = benchmark(assign_task)
    assert result is True


@pytest.mark.benchmark
def test_task_listing_performance(benchmark):
    """Benchmark task listing performance."""
    
    def list_tasks():
        """List all tasks."""
        return get_all_tasks_from_db()
    
    result = benchmark(list_tasks)
    assert isinstance(result, list)


@pytest.mark.benchmark
def test_bulk_task_creation(benchmark):
    """Benchmark bulk task creation."""
    
    def create_bulk_tasks():
        """Create 10 tasks."""
        tasks = []
        for i in range(10):
            task_data = {
                "title": f"Bulk Task {i}",
                "description": f"Benchmark bulk task {i}",
                "priority": "medium",
                "status": "pending"
            }
            task_id = create_task_in_db(**task_data)
            tasks.append(task_id)
        return tasks
    
    result = benchmark(create_bulk_tasks)
    assert len(result) == 10

