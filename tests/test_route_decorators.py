"""
Tests for route decorators (CORS, auth, error handling).
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from starlette.requests import Request
from starlette.responses import JSONResponse
from agent_mcp.app.decorators import handle_cors, require_auth, api_route
from agent_mcp.app.responses import success_response, error_response


class TestHandleCORS:
    """Test CORS handling decorator."""
    
    @pytest.mark.asyncio
    async def test_handle_cors_options(self):
        """Test that OPTIONS requests are handled."""
        @handle_cors
        async def test_handler(request: Request):
            return JSONResponse({"data": "test"})
        
        request = Mock(spec=Request)
        request.method = "OPTIONS"
        
        response = await test_handler(request)
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
    
    @pytest.mark.asyncio
    async def test_handle_cors_normal_request(self):
        """Test that normal requests pass through."""
        @handle_cors
        async def test_handler(request: Request):
            return JSONResponse({"data": "test"})
        
        request = Mock(spec=Request)
        request.method = "GET"
        
        response = await test_handler(request)
        assert response.status_code == 200
        data = response.body.decode()
        assert "test" in data


class TestRequireAuth:
    """Test authentication decorator."""
    
    @pytest.mark.asyncio
    async def test_require_auth_valid_token(self):
        """Test with valid token."""
        with patch('agent_mcp.app.decorators.verify_token', return_value=True):
            @require_auth("admin")
            async def test_handler(request: Request, token: str):
                return success_response({"authenticated": True})
            
            request = Mock(spec=Request)
            request.method = "POST"
            request.json = AsyncMock(return_value={"token": "valid-token"})
            
            response = await test_handler(request)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_require_auth_invalid_token(self):
        """Test with invalid token."""
        with patch('agent_mcp.app.decorators.verify_token', return_value=False):
            @require_auth("admin")
            async def test_handler(request: Request, token: str):
                return success_response({"authenticated": True})
            
            request = Mock(spec=Request)
            request.method = "POST"
            request.json = AsyncMock(return_value={"token": "invalid-token"})
            
            with pytest.raises(Exception):  # Should raise AuthenticationError
                await test_handler(request)
    
    @pytest.mark.asyncio
    async def test_require_auth_no_token(self):
        """Test with no token."""
        with patch('agent_mcp.app.decorators.verify_token', return_value=False):
            @require_auth("admin")
            async def test_handler(request: Request, token: str):
                return success_response({"authenticated": True})
            
            request = Mock(spec=Request)
            request.method = "POST"
            request.json = AsyncMock(return_value={})
            request.query_params = Mock(get=Mock(return_value=None))
            
            with pytest.raises(Exception):  # Should raise AuthenticationError
                await test_handler(request)


class TestAPIRoute:
    """Test combined API route decorator."""
    
    @pytest.mark.asyncio
    async def test_api_route_success(self):
        """Test successful API route."""
        @api_route()
        async def test_handler(request: Request):
            return success_response({"data": "test"})
        
        request = Mock(spec=Request)
        request.method = "GET"
        
        response = await test_handler(request)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_api_route_error_handling(self):
        """Test error handling in API route."""
        @api_route()
        async def test_handler(request: Request):
            raise ValueError("Test error")
        
        request = Mock(spec=Request)
        request.method = "GET"
        # Make query_params behave like a dict for error handler
        request.query_params = {}
        request.path_params = {}
        request.url = Mock()
        request.url.path = "/test"
        request.url.query = ""
        
        response = await test_handler(request)
        # Should return error response, not raise
        assert response.status_code >= 400


class TestResponseHelpers:
    """Test response helper functions."""
    
    def test_success_response(self):
        """Test success response creation."""
        response = success_response({"data": "test"}, message="Success", status_code=200)
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
    
    def test_error_response(self):
        """Test error response creation."""
        response = error_response("Error message", status_code=400, details={"field": "value"})
        assert response.status_code == 400
        assert "Access-Control-Allow-Origin" in response.headers

