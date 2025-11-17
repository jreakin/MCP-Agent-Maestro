"""
Hypothesis tests for task Pydantic models.
Tests Task, TaskCreate, TaskUpdate validation with property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.strategies import text, lists, dictionaries, none, one_of, datetimes, sampled_from
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from agent_mcp.models.task import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskStatus,
    TaskReorder,
    BulkOperation
)


class TestTaskModel:
    """Test Task model validation with Hypothesis."""
    
    @given(
        task_id=text(min_size=1, max_size=100),
        title=text(min_size=1, max_size=300, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        created_by=text(min_size=1, max_size=50),
        description=one_of(none(), text(max_size=5000)),
        status=sampled_from(['pending', 'in_progress', 'completed', 'blocked', 'cancelled', 'failed']),
        priority=sampled_from(['low', 'medium', 'high', 'critical']),
        tags=lists(text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=['_', '-'], min_codepoint=48, max_codepoint=122)), max_size=20)
    )
    @settings(max_examples=100)
    def test_task_validates_correctly(self, task_id: str, title: str, created_by: str, description: Optional[str], 
                                      status: str, priority: str, tags: List[str]):
        """Task validates correctly for all valid inputs."""
        assume(title.strip())  # Ensure title is not whitespace-only
        assume(len(tags) <= 20)
        assume(all(len(tag) <= 50 for tag in tags))
        
        task = Task(
            task_id=task_id,
            title=title,
            created_by=created_by,
            description=description,
            status=status,  # type: ignore
            priority=priority,  # type: ignore
            tags=tags
        )
        
        assert task.task_id == task_id
        # Pydantic validator strips the title, so task.title should equal title.strip()
        assert task.title == title.strip()
        assert len(task.tags) <= 20
        assert all(len(tag) <= 50 for tag in task.tags)
    
    @given(
        title=text(min_size=301)  # Too long
    )
    @settings(max_examples=10)
    def test_task_rejects_long_title(self, title: str):
        """Task rejects titles that are too long."""
        with pytest.raises(Exception):  # Should raise ValidationError
            Task(
                task_id="test_task",
                title=title,
                created_by="test_agent"
            )
    
    @given(
        tags=lists(text(min_size=51), min_size=1)  # Tags too long
    )
    @settings(max_examples=5)
    def test_task_rejects_long_tags(self, tags: List[str]):
        """Task rejects tags that are too long."""
        with pytest.raises(Exception):  # Should raise ValidationError
            Task(
                task_id="test_task",
                title="Test Task",
                created_by="test_agent",
                tags=tags
            )
    
    @given(
        tags=lists(text(), min_size=21)  # Too many tags
    )
    @settings(max_examples=5)
    def test_task_rejects_too_many_tags(self, tags: List[str]):
        """Task rejects more than 20 tags."""
        assume(len(tags) > 20)
        with pytest.raises(Exception):  # Should raise ValidationError
            Task(
                task_id="test_task",
                title="Test Task",
                created_by="test_agent",
                tags=tags[:25]  # Take first 25 to ensure > 20
            )


class TestTaskCreateModel:
    """Test TaskCreate model with Hypothesis."""
    
    @given(
        title=text(min_size=1, max_size=300, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
        description=one_of(none(), text(max_size=5000)),
        priority=sampled_from(['low', 'medium', 'high', 'critical']),
        status=sampled_from(['pending', 'in_progress', 'completed', 'blocked', 'cancelled'])
    )
    @settings(max_examples=100)
    def test_task_create_minimal_fields(self, title: str, description: Optional[str], priority: str, status: str):
        """TaskCreate validates with minimal required fields."""
        assume(title.strip())  # Ensure title is not whitespace-only
        
        task = TaskCreate(
            title=title,
            description=description,
            priority=priority,  # type: ignore
            status=status  # type: ignore
        )
        
        assert task.title == title.strip()  # Pydantic validator auto-strips titles
        assert task.priority == priority
        assert task.status == status


class TestTaskUpdateModel:
    """Test TaskUpdate model with Hypothesis."""
    
    @given(
        updates=dictionaries(
            st.sampled_from(['title', 'description', 'status', 'priority', 'assigned_to']),
            one_of(
                text(min_size=1, max_size=300),  # For title/description
                st.sampled_from(['pending', 'in_progress', 'completed', 'cancelled', 'failed']),  # For status
                st.sampled_from(['low', 'medium', 'high', 'critical']),  # For priority
                text(min_size=1, max_size=50)  # For assigned_to
            ),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=50)
    def test_task_update_all_optional(self, updates: Dict[str, Any]):
        """TaskUpdate accepts all optional fields."""
        # Filter out invalid combinations - map keys to valid values
        filtered_updates = {}
        for key, value in updates.items():
            if key == 'status' and value not in ['pending', 'in_progress', 'completed', 'blocked', 'cancelled', 'failed']:
                continue  # Skip invalid status values
            elif key == 'priority' and value not in ['low', 'medium', 'high', 'critical']:
                continue  # Skip invalid priority values
            else:
                filtered_updates[key] = value
        
        # Convert dict to TaskUpdate (only with valid combinations)
        task_update = TaskUpdate(**filtered_updates)
        
        update_dict = task_update.model_dump(exclude_none=True)
        assert isinstance(update_dict, dict)


class TestTaskReorderModel:
    """Test TaskReorder model with Hypothesis."""
    
    @given(
        task_id=text(min_size=1, max_size=100),
        new_position=st.integers(min_value=0, max_value=1000),
        status=one_of(none(), text(min_size=1, max_size=50))
    )
    @settings(max_examples=50)
    def test_task_reorder_validates(self, task_id: str, new_position: int, status: Optional[str]):
        """TaskReorder validates correctly."""
        reorder = TaskReorder(
            task_id=task_id,
            new_position=new_position,
            status=status
        )
        
        assert reorder.task_id == task_id
        assert reorder.new_position == new_position
        assert reorder.new_position >= 0  # ge=0 constraint
    
    @given(
        task_id=text(min_size=1, max_size=100),
        negative_position=st.integers(max_value=-1)
    )
    @settings(max_examples=10)
    def test_task_reorder_rejects_negative_position(self, task_id: str, negative_position: int):
        """TaskReorder rejects negative positions."""
        assume(negative_position < 0)
        with pytest.raises(Exception):  # Should raise ValidationError
            TaskReorder(
                task_id=task_id,
                new_position=negative_position
            )


class TestBulkOperationModel:
    """Test BulkOperation model with Hypothesis."""
    
    @given(
        task_ids=lists(text(min_size=1, max_size=100), min_size=1, max_size=50),
        operation=sampled_from(['update_status', 'update_priority', 'assign', 'add_tags', 'remove_tags', 'delete']),
        value=one_of(none(), text(), lists(text()), st.integers())
    )
    @settings(max_examples=50)
    def test_bulk_operation_validates(self, task_ids: List[str], operation: str, value):
        """BulkOperation validates correctly."""
        bulk_op = BulkOperation(
            task_ids=task_ids,
            operation=operation,  # type: ignore
            value=value
        )
        
        assert len(bulk_op.task_ids) >= 1  # min_length=1 constraint
        assert bulk_op.operation == operation
    
    @given(
        empty_list=lists(text(), max_size=0)  # Empty list
    )
    @settings(max_examples=5)
    def test_bulk_operation_rejects_empty_task_ids(self, empty_list: List[str]):
        """BulkOperation rejects empty task_ids list."""
        assume(len(empty_list) == 0)
        with pytest.raises(Exception):  # Should raise ValidationError
            BulkOperation(
                task_ids=empty_list,
                operation='update_status'
            )

