"""
Tests for task history tracking.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from starlette.requests import Request
from agent_mcp.app.routes.tasks import get_task_history_api_route


class TestTaskHistory:
    """Test task history API endpoint."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_task_history(self):
        """Test getting task history."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.path_params = {"task_id": "test-task-123"}
        
        with patch('agent_mcp.app.routes.tasks.db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            # Set up cursor as a context manager
            mock_cursor.__enter__ = Mock(return_value=mock_cursor)
            mock_cursor.__exit__ = Mock(return_value=None)
            mock_conn.cursor.return_value = mock_cursor
            
            # Set up connection as a context manager
            mock_db.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_db.return_value.__exit__ = Mock(return_value=None)
            
            # Mock database response - cursor.fetchall() returns list of dict-like objects
            mock_cursor.fetchall.return_value = [
                type('Row', (), {
                    "agent_id": "agent1",
                    "action_type": "task_update",
                    "timestamp": "2024-01-01T00:00:00",
                    "details": '{"status": "completed"}'
                })()
            ]
            
            response = await get_task_history_api_route(request)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_task_history_no_task_id(self):
        """Test getting history without task_id."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.path_params = {}
        
        response = await get_task_history_api_route(request)
        assert response.status_code == 400

