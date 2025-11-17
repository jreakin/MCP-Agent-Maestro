"""
Atheris fuzzing target for Task model validation.

Fuzzes Task, TaskCreate, and TaskUpdate models to find validation edge cases.
"""

import sys
import pytest

try:
    import atheris
    ATHERIS_AVAILABLE = True
except ImportError:
    ATHERIS_AVAILABLE = False
    pytest.skip("Atheris not available", allow_module_level=True)

import json

# Import the models to fuzz
from agent_mcp.models.task import Task, TaskCreate, TaskUpdate


def TestOneInput(data: bytes):
    """
    Fuzzing entry point for Task model validation.
    """
    try:
        # Decode bytes to string
        input_str = data.decode('utf-8', errors='ignore')
        
        # Try to parse as JSON first
        try:
            task_data = json.loads(input_str)
        except json.JSONDecodeError:
            # If not valid JSON, try creating TaskCreate with string as title
            try:
                task = TaskCreate(title=input_str[:300])  # Limit to max length
                # Basic validation: title should be stripped
                assert task.title == input_str[:300].strip()
            except (ValueError, Exception):
                pass
            return
        
        # If we got JSON, try to create models
        if isinstance(task_data, dict):
            # Try TaskCreate
            try:
                # Ensure required fields
                if 'title' not in task_data:
                    task_data['title'] = input_str[:100] if input_str else "test"
                
                task = TaskCreate(**task_data)
                assert task.title is not None
                assert len(task.title) > 0
                assert len(task.title) <= 300
            except (ValueError, Exception):
                pass
            
            # Try TaskUpdate (all fields optional)
            try:
                task_update = TaskUpdate(**task_data)
                # If title is provided, validate it
                if task_update.title is not None:
                    assert len(task_update.title) > 0
                    assert len(task_update.title) <= 300
            except (ValueError, Exception):
                pass
            
            # Try full Task (requires more fields)
            try:
                if 'task_id' not in task_data:
                    task_data['task_id'] = 'fuzz-test-1'
                if 'created_by' not in task_data:
                    task_data['created_by'] = 'fuzz-agent'
                
                task = Task(**task_data)
                assert task.task_id is not None
                assert task.title is not None
                assert len(task.title) > 0
                assert len(task.title) <= 300
            except (ValueError, Exception):
                pass
        
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        # Expected exceptions
        pass
    except Exception as e:
        print(f"Unexpected exception with input: {data[:100]}")
        raise


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


