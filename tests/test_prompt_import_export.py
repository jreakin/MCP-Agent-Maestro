"""
Tests for prompt import/export functionality.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from starlette.requests import Request
from agent_mcp.api.prompts import export_prompts_api_route, import_prompts_api_route
from agent_mcp.app.responses import success_response, error_response


class TestPromptImportExport:
    """Test prompt import/export endpoints."""
    
    @pytest.mark.asyncio
    async def test_export_prompts(self):
        """Test exporting prompts."""
        with patch('agent_mcp.api.prompts.get_prompt_storage') as mock_storage:
            mock_storage_instance = Mock()
            mock_storage_instance.list_prompts = Mock(return_value=[
                {"prompt_id": "test1", "template": "Test template 1"},
                {"prompt_id": "test2", "template": "Test template 2"},
            ])
            mock_storage.return_value = mock_storage_instance
            
            request = Mock(spec=Request)
            request.method = "GET"
            request.query_params = {"token": "valid-admin-token"}  # Token comes from query params
            request.path_params = {}
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            
            with patch('agent_mcp.app.decorators.verify_token', return_value=True):
                response = await export_prompts_api_route(request)
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_import_prompts_valid(self):
        """Test importing valid prompts."""
        with patch('agent_mcp.api.prompts.get_prompt_storage') as mock_storage:
            mock_storage_instance = Mock()
            mock_storage_instance.get_prompt = Mock(return_value=None)  # New prompt
            mock_storage_instance.create_prompt = Mock(return_value="new_id")
            mock_storage.return_value = mock_storage_instance
            
            request = Mock(spec=Request)
            request.method = "POST"
            request.json = AsyncMock(return_value={
                "token": "valid-admin-token",
                "prompts": [
                    {"prompt_id": "test1", "template": "Test template 1"},
                    {"prompt_id": "test2", "template": "Test template 2"},
                ]
            })
            request.query_params = {}
            request.path_params = {}
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            
            with patch('agent_mcp.app.decorators.verify_token', return_value=True):
                response = await import_prompts_api_route(request)
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_import_prompts_invalid_format(self):
        """Test importing with invalid format."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.json = AsyncMock(return_value={
            "token": "valid-admin-token",
            "prompts": "not a list"
        })
        request.query_params = {}
        request.path_params = {}
        request.url = Mock()
        request.url.path = "/test"
        request.url.query = ""
        
        with patch('agent_mcp.app.decorators.verify_token', return_value=True):
            response = await import_prompts_api_route(request)
            assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_import_prompts_update_existing(self):
        """Test importing prompts that already exist (should update)."""
        with patch('agent_mcp.api.prompts.get_prompt_storage') as mock_storage:
            mock_storage_instance = Mock()
            mock_storage_instance.get_prompt = Mock(return_value={"prompt_id": "test1"})  # Exists
            mock_storage_instance.update_prompt = Mock()
            mock_storage.return_value = mock_storage_instance
            
            request = Mock(spec=Request)
            request.method = "POST"
            request.json = AsyncMock(return_value={
                "token": "valid-admin-token",
                "prompts": [
                    {"prompt_id": "test1", "template": "Updated template"},
                ]
            })
            request.query_params = {}
            request.path_params = {}
            request.url = Mock()
            request.url.path = "/test"
            request.url.query = ""
            
            with patch('agent_mcp.app.decorators.verify_token', return_value=True):
                response = await import_prompts_api_route(request)
                assert response.status_code == 200
                mock_storage_instance.update_prompt.assert_called_once()

