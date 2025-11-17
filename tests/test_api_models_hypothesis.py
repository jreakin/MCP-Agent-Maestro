"""
Hypothesis property-based tests for API Pydantic models.
Tests all API request/response models with comprehensive property-based testing.
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import text, lists, dictionaries, one_of, none, integers
import string
from typing import Dict, Any, List, Optional

from agent_mcp.api.models import (
    TaskCreate,
    TaskUpdate,
    TaskAssign,
    TaskStatusUpdate,
    TaskPriorityUpdate,
    BulkOperation,
    TaskReorder,
    AgentCreate,
    MemoryCreate,
    MemoryUpdate,
    PromptCreate,
    PromptUpdate,
    PromptExecute,
    SecurityScanRequest,
    MCPConfigRequest,
    MCPInstallRequest,
)


class TestTaskModels:
    """Property-based tests for task-related models."""
    
    @given(
        title=text(min_size=1, max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>')),
        description=one_of(none(), text(max_size=10000, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>'))),
        priority=st.sampled_from(['low', 'medium', 'high', 'critical']),
        status=st.sampled_from(['pending', 'in_progress', 'completed', 'blocked', 'cancelled']),
        assigned_to=one_of(none(), text(max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>'))),
        parent_task=one_of(none(), text(max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>'))),
        depends_on=lists(text(max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>')), max_size=20),
        tags=lists(text(max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>')), max_size=50)
    )
    @settings(max_examples=100)
    def test_task_create_validates(self, title: str, description: Optional[str], priority: str,
                                   status: str, assigned_to: Optional[str], parent_task: Optional[str],
                                   depends_on: List[str], tags: List[str]):
        """TaskCreate validates correctly for all valid inputs."""
        assume(title.strip())  # Title must not be whitespace-only
        
        # Filter out tags that might contain injection patterns
        safe_tags = [tag for tag in tags if not any(pattern in tag.lower() for pattern in ['<script', '<object', '<iframe', 'javascript:', 'data:text/html', 'onerror'])]
        
        task = TaskCreate(
            title=title,
            description=description,
            priority=priority,
            status=status,
            assigned_to=assigned_to,
            parent_task=parent_task,
            depends_on_tasks=depends_on,
            tags=safe_tags
        )
        
        assert task.title == title.strip()
        assert task.priority == priority
        assert task.status == status
    
    @given(
        updates=dictionaries(
            keys=st.sampled_from(['title', 'description', 'priority', 'status', 'assigned_to']),
            values=one_of(
                text(min_size=1, max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))),  # title requires min_length=1 if provided
                st.sampled_from(['low', 'medium', 'high', 'critical']),
                st.sampled_from(['pending', 'in_progress', 'completed', 'blocked', 'cancelled'])
            ),
            max_size=5
        )
    )
    @settings(max_examples=50)
    def test_task_update_all_optional(self, updates: Dict[str, Any]):
        """TaskUpdate accepts all optional fields."""
        # Filter to valid combinations and exclude empty strings for title
        valid_updates = {}
        for key, value in updates.items():
            if key == 'title' and (not value or len(value.strip()) == 0):
                continue  # Skip empty titles (min_length=1 requirement)
            if key == 'priority' and value not in ['low', 'medium', 'high', 'critical']:
                continue
            if key == 'status' and value not in ['pending', 'in_progress', 'completed', 'blocked', 'cancelled']:
                continue
            valid_updates[key] = value
        
        if valid_updates:
            task_update = TaskUpdate(**valid_updates)
            assert isinstance(task_update.model_dump(exclude_none=True), dict)
    
    @given(
        task_ids=lists(text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>')), min_size=1, max_size=100),
        operation=st.sampled_from(['update_status', 'update_priority', 'assign', 'add_tags', 'delete']),
        value=one_of(
            st.sampled_from(['pending', 'in_progress', 'completed']),
            st.sampled_from(['low', 'medium', 'high', 'critical']),
            text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>'))
        )
    )
    @settings(max_examples=50)
    def test_bulk_operation_validates(self, task_ids: List[str], operation: str, value: Any):
        """BulkOperation validates correctly."""
        # Filter out any task_ids that might contain injection patterns
        safe_task_ids = [tid for tid in task_ids if not any(pattern in tid.lower() for pattern in ['<script', '<object', '<iframe', 'javascript:', 'onerror'])]
        if not safe_task_ids:
            return  # Skip if all task_ids were filtered out
        
        # Some operations require a value - skip if operation is 'delete' and value is provided
        # (delete doesn't need a value, but others do)
        if operation == 'delete':
            # For delete, value can be None
            bulk_op = BulkOperation(
                task_ids=safe_task_ids,
                operation=operation,
                value=None
            )
        else:
            # For other operations, value is required
            bulk_op = BulkOperation(
                task_ids=safe_task_ids,
                operation=operation,
                value=value
            )
        
        assert len(bulk_op.task_ids) == len(safe_task_ids)
        assert bulk_op.operation == operation


class TestSecurityModels:
    """Property-based tests for security-related models."""
    
    @given(
        text_content=text(min_size=1, max_size=100000, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))),
        context=one_of(none(), text(max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))))
    )
    @settings(max_examples=50)
    def test_security_scan_request(self, text_content: str, context: Optional[str]):
        """SecurityScanRequest validates correctly."""
        request = SecurityScanRequest(
            text=text_content,
            context=context
        )
        
        assert request.text == text_content
        assert request.context == context


class TestAgentModels:
    """Property-based tests for agent-related models."""
    
    @given(
        agent_id=one_of(none(), text(max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>\'"'))),
        capabilities=lists(text(max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>\'"')), max_size=20),
        working_directory=one_of(none(), text(max_size=500, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='<>\'"')))
    )
    @settings(max_examples=30)
    def test_agent_create(self, agent_id: Optional[str], capabilities: List[str], 
                         working_directory: Optional[str]):
        """AgentCreate validates correctly."""
        # Filter out any strings that might contain injection patterns
        safe_capabilities = [cap for cap in capabilities if not any(pattern in cap.lower() for pattern in ['<script', '<object', '<iframe', 'javascript:', 'onerror'])]
        
        agent = AgentCreate(
            agent_id=agent_id,
            capabilities=safe_capabilities,
            working_directory=working_directory
        )
        
        assert agent.agent_id == agent_id
        assert len(agent.capabilities) == len(safe_capabilities)


class TestMemoryModels:
    """Property-based tests for memory-related models."""
    
    @given(
        context_key=text(min_size=1, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))),
        context_value=one_of(
            text(max_size=10000, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))),
            integers(),
            lists(text(max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))), max_size=10),
            dictionaries(text(max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))), text(max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))), max_size=10)
        ),
        description=one_of(none(), text(max_size=1000, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))))
    )
    @settings(max_examples=50)
    def test_memory_create(self, context_key: str, context_value: Any, description: Optional[str]):
        """MemoryCreate validates correctly."""
        memory = MemoryCreate(
            context_key=context_key,
            context_value=context_value,
            description=description
        )
        
        assert memory.context_key == context_key
        assert memory.context_value == context_value


class TestPromptModels:
    """Property-based tests for prompt-related models."""
    
    @given(
        name=text(min_size=1, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))),
        description=one_of(none(), text(max_size=1000, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No')))),
        template=text(min_size=1, max_size=50000, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))),
        category=one_of(none(), text(max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No')))),
        tags=lists(text(max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))), max_size=20),
        variables=lists(text(max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126, whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'No'))), max_size=20)
    )
    @settings(max_examples=30)
    def test_prompt_create(self, name: str, description: Optional[str], template: str,
                          category: Optional[str], tags: List[str], variables: List[str]):
        """PromptCreate validates correctly."""
        prompt = PromptCreate(
            name=name,
            description=description,
            template=template,
            category=category,
            tags=tags,
            variables=variables
        )
        
        assert prompt.name == name
        assert prompt.template == template
        assert len(prompt.tags) == len(tags)

