"""
Tests for WebSocket manager.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from agent_mcp.app.websocket import WebSocketManager, ws_manager


class TestWebSocketManager:
    """Test WebSocket manager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh WebSocket manager for each test."""
        return WebSocketManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = Mock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.receive_text = AsyncMock(return_value="ping")
        ws.close = AsyncMock()
        return ws
    
    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """Test connecting a WebSocket."""
        await manager.connect(mock_websocket, "tasks")
        assert mock_websocket in manager.active_connections["tasks"]
        assert manager.get_connection_count("tasks") == 1
    
    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test disconnecting a WebSocket."""
        await manager.connect(mock_websocket, "tasks")
        await manager.disconnect(mock_websocket, "tasks")
        assert mock_websocket not in manager.active_connections["tasks"]
        assert manager.get_connection_count("tasks") == 0
    
    @pytest.mark.asyncio
    async def test_broadcast(self, manager, mock_websocket):
        """Test broadcasting to connections."""
        await manager.connect(mock_websocket, "tasks")
        
        message = {"type": "test", "data": "message"}
        await manager.broadcast("tasks", message)
        
        mock_websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_multiple_connections(self, manager):
        """Test broadcasting to multiple connections."""
        ws1 = Mock()
        ws1.send_json = AsyncMock()
        ws1.accept = AsyncMock()  # Make accept() async
        ws2 = Mock()
        ws2.send_json = AsyncMock()
        ws2.accept = AsyncMock()  # Make accept() async
        
        await manager.connect(ws1, "tasks")
        await manager.connect(ws2, "tasks")
        
        message = {"type": "test"}
        await manager.broadcast("tasks", message)
        
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected(self, manager, mock_websocket):
        """Test that broadcast handles disconnected sockets gracefully."""
        await manager.connect(mock_websocket, "tasks")
        
        # Simulate send failure
        mock_websocket.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        
        message = {"type": "test"}
        await manager.broadcast("tasks", message)
        
        # Should clean up disconnected socket
        assert manager.get_connection_count("tasks") == 0
    
    def test_get_connection_count(self, manager):
        """Test getting connection count."""
        assert manager.get_connection_count("tasks") == 0
        assert manager.get_connection_count("agents") == 0
        assert manager.get_connection_count("security") == 0
    
    def test_get_total_connections(self, manager):
        """Test getting total connections across all channels."""
        assert manager.get_total_connections() == 0
    
    @pytest.mark.asyncio
    async def test_unknown_channel(self, manager, mock_websocket):
        """Test connecting to unknown channel."""
        await manager.connect(mock_websocket, "unknown")
        # Should close connection
        mock_websocket.close.assert_called_once()

