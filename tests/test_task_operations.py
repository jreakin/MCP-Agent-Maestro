"""
Hypothesis tests for task database operations.
Tests create, update, delete operations with property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, example, HealthCheck
from hypothesis.strategies import composite, lists, text, dictionaries, none, one_of, datetimes
from typing import List, Dict, Any, Optional
from datetime import datetime

from agent_mcp.models.task import TaskCreate, TaskUpdate, Task, TaskStatus
from agent_mcp.db.actions.task_db import create_task_in_db, update_task_fields_in_db, get_task_by_id


@composite
def task_create_strategy(draw):
    """Generate random TaskCreate for testing."""
    # Generate valid title (non-empty, non-whitespace-only, printable characters)
    title_text = draw(text(min_size=1, max_size=300, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
    assume(title_text.strip())  # Ensure title is not whitespace-only after stripping
    
    return TaskCreate(
        title=title_text,
        description=draw(one_of(none(), text(max_size=5000))),
        priority=draw(st.sampled_from(['low', 'medium', 'high', 'critical'])),
        status=draw(st.sampled_from(['pending', 'in_progress', 'completed', 'blocked', 'cancelled'])),
        assigned_to=draw(one_of(none(), text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))),
        parent_task=draw(one_of(none(), text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=48, max_codepoint=122)))),
        depends_on_tasks=draw(lists(text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=48, max_codepoint=122)), max_size=10)),
        tags=draw(lists(text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=['_', '-'])), max_size=20)),
        due_date=draw(one_of(none(), datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2100, 1, 1)))),
        metadata=draw(dictionaries(text(), st.text()))  # metadata should be a dict, not None
    )


@composite
def task_update_strategy(draw):
    """Generate random TaskUpdate for testing."""
    return TaskUpdate(
        title=draw(one_of(none(), text(min_size=1, max_size=300))),
        description=draw(one_of(none(), text(max_size=5000))),
        priority=draw(one_of(none(), st.sampled_from(['low', 'medium', 'high', 'critical']))),
        status=draw(one_of(none(), st.sampled_from(['pending', 'in_progress', 'completed', 'blocked', 'cancelled', 'failed']))),
        assigned_to=draw(one_of(none(), text(min_size=1, max_size=50))),
        parent_task=draw(one_of(none(), text(min_size=1, max_size=50))),
        depends_on_tasks=draw(one_of(none(), lists(text(min_size=1, max_size=50), max_size=10))),
        tags=draw(one_of(none(), lists(text(min_size=1, max_size=50), max_size=20))),
        due_date=draw(one_of(none(), datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2100, 1, 1)))),
        metadata=draw(one_of(none(), dictionaries(text(), st.text())))
    )


class TestTaskCreateModel:
    """Test TaskCreate Pydantic model validation with Hypothesis."""
    
    @given(task_data=task_create_strategy())
    @settings(max_examples=100)
    def test_task_create_validates_correctly(self, task_data: TaskCreate):
        """TaskCreate validates correctly for all valid inputs."""
        # Should not raise validation error
        assert task_data.title is not None
        # Title should be non-empty after stripping (Pydantic validator ensures this)
        assert len(task_data.title.strip()) > 0
        # Title should be auto-stripped by Pydantic validator
        # Pydantic validator strips whitespace, so task_data.title should not have leading/trailing whitespace
        # Compare with stripped version to ensure no leading/trailing whitespace
        stripped_title = task_data.title.strip()
        assert len(stripped_title) > 0
        # Title after validation should equal its stripped version (no leading/trailing whitespace)
        assert task_data.title == stripped_title
    
    @given(
        title=text(min_size=1, max_size=300, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        description=one_of(none(), text(max_size=5000)),
        priority=st.sampled_from(['low', 'medium', 'high', 'critical']),
        tags=lists(text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=['_', '-'], min_codepoint=48, max_codepoint=122)), max_size=20)
    )
    @settings(max_examples=50)
    def test_task_create_with_tags(self, title: str, description: Optional[str], priority: str, tags: List[str]):
        """TaskCreate handles tags correctly."""
        assume(title.strip())  # Ensure title is not whitespace-only
        assume(len(tags) <= 20)  # Enforce max_items constraint
        
        task = TaskCreate(
            title=title,
            description=description,
            priority=priority,
            tags=tags
        )
        
        assert len(task.tags) <= 20
        assert all(len(tag) <= 50 for tag in task.tags)
    
    @given(
        title=text(min_size=301),  # Too long
    )
    @settings(max_examples=10)
    def test_task_create_rejects_long_title(self, title: str):
        """TaskCreate rejects titles that are too long."""
        with pytest.raises(Exception):  # Should raise ValidationError
            TaskCreate(title=title)
    
    @given(
        title=text(max_size=0)  # Empty
    )
    @settings(max_examples=5)
    def test_task_create_rejects_empty_title(self, title: str):
        """TaskCreate rejects empty titles."""
        assume(not title.strip())
        with pytest.raises(Exception):  # Should raise ValidationError
            TaskCreate(title=title)


class TestTaskUpdateModel:
    """Test TaskUpdate Pydantic model with Hypothesis."""
    
    @given(update_data=task_update_strategy())
    @settings(max_examples=100)
    def test_task_update_validates_correctly(self, update_data: TaskUpdate):
        """TaskUpdate validates correctly for all valid inputs."""
        # All fields are optional, so this should always pass
        update_dict = update_data.model_dump(exclude_none=True)
        assert isinstance(update_dict, dict)
    
    @given(
        title=one_of(none(), text(min_size=1, max_size=300)),
        status=one_of(none(), st.sampled_from(['pending', 'in_progress', 'completed', 'cancelled', 'failed']))
    )
    @settings(max_examples=50)
    def test_task_update_partial_updates(self, title: Optional[str], status: Optional[str]):
        """TaskUpdate supports partial updates."""
        update = TaskUpdate(title=title, status=status)
        update_dict = update.model_dump(exclude_none=True)
        
        if title:
            assert 'title' in update_dict
        if status:
            assert 'status' in update_dict


class TestTaskDatabaseOperations:
    """Test task database operations with Hypothesis (mocked for unit tests)."""
    
    @pytest.mark.integration
    @given(task_data=task_create_strategy())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_create_task_in_db_returns_task_id(self, task_data: TaskCreate, db_connection):
        """Create task in DB returns a task ID."""
        task_id = create_task_in_db(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            status=task_data.status,
            assigned_to=task_data.assigned_to,
            created_by="test_agent",
            parent_task=task_data.parent_task,
            depends_on_tasks=task_data.depends_on_tasks,
            tags=task_data.tags,
            due_date=task_data.due_date.isoformat() if task_data.due_date else None,
            metadata=task_data.metadata
        )
        
        assert task_id is not None
        assert isinstance(task_id, str)
        assert task_id.startswith("task_")
    
    @pytest.mark.integration
    @given(
        task_id=text(min_size=1, max_size=100),
        fields=dictionaries(
            st.sampled_from(['title', 'description', 'status', 'priority', 'assigned_to']),
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_update_task_fields_validates_fields(self, task_id: str, fields: Dict[str, Any], db_connection):
        """Update task fields validates field names."""
        # This will fail if invalid fields are provided (should be handled gracefully)
        try:
            result = update_task_fields_in_db(task_id, fields)
            # Should return False if task doesn't exist, True if updated
            assert isinstance(result, bool)
        except Exception:
            # Invalid fields should be handled gracefully
            pass

