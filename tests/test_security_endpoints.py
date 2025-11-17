"""
Tests for security dashboard endpoints.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from starlette.requests import Request
from agent_mcp.app.routes.security import security_alerts_api_route, security_scan_history_api_route
from agent_mcp.app.responses import success_response


class TestSecurityEndpoints:
    """Test security dashboard API endpoints."""
    
    @pytest.mark.asyncio
    async def test_security_alerts_api_route(self):
        """Test getting security alerts."""
        # Mock the SecurityMonitor
        mock_security_monitor = Mock()
        mock_security_monitor.get_recent_alerts = AsyncMock(return_value=[])
        
        # Patch SecurityMonitor where it's imported (in agent_mcp.security)
        # and patch the globals module where it's imported as 'g' inside the route function
        with patch('agent_mcp.security.SecurityMonitor', return_value=mock_security_monitor):
            # Patch the globals module that gets imported as 'g' inside the function
            with patch('agent_mcp.core.globals') as mock_globals:
                # Set up the mock globals to have security_monitor attribute
                mock_globals.security_monitor = mock_security_monitor
                # Make hasattr return True for security_monitor
                original_hasattr = hasattr
                def mock_hasattr(obj, name):
                    if obj is mock_globals and name == 'security_monitor':
                        return True
                    return original_hasattr(obj, name)
                
                # Patch hasattr in the route's namespace
                import builtins
                with patch.object(builtins, 'hasattr', side_effect=mock_hasattr):
                    request = Mock(spec=Request)
                    request.method = "GET"
                    request.query_params = Mock(get=Mock(return_value="50"))
                    
                    response = await security_alerts_api_route(request)
                    assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_security_scan_history_api_route(self):
        """Test getting scan history."""
        request = Mock(spec=Request)
        request.method = "GET"
        
        response = await security_scan_history_api_route(request)
        assert response.status_code == 200
        # Should return empty scans for now
        assert "scans" in str(response.body)

