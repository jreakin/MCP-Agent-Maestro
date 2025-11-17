# Agent-MCP WebSocket Manager
"""
WebSocket manager for real-time updates to dashboard clients.
Manages connections and broadcasts updates for tasks, agents, and security events.
"""
from typing import Dict, Set
from starlette.websockets import WebSocket
import json
import asyncio
from ..core.config import logger


class WebSocketManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "tasks": set(),
            "agents": set(),
            "security": set(),
        }
    
    async def connect(self, websocket: WebSocket, channel: str):
        """Connect a WebSocket to a channel."""
        await websocket.accept()
        if channel in self.active_connections:
            self.active_connections[channel].add(websocket)
            logger.info(f"WebSocket connected to {channel} channel")
        else:
            logger.warning(f"Unknown WebSocket channel: {channel}")
            await websocket.close(code=1008, reason=f"Unknown channel: {channel}")
    
    async def disconnect(self, websocket: WebSocket, channel: str):
        """Disconnect a WebSocket from a channel."""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            logger.info(f"WebSocket disconnected from {channel} channel")
    
    async def broadcast(self, channel: str, message: dict):
        """Broadcast message to all connections in a channel."""
        if channel not in self.active_connections:
            logger.warning(f"Attempted to broadcast to unknown channel: {channel}")
            return
        
        if not self.active_connections[channel]:
            # No connections, skip broadcast
            return
        
        disconnected = set()
        for websocket in self.active_connections[channel]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected sockets
        if disconnected:
            self.active_connections[channel] -= disconnected
            logger.info(f"Cleaned up {len(disconnected)} disconnected WebSocket(s) from {channel} channel")
    
    async def send_to_connection(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send to specific WebSocket: {e}")
    
    def get_connection_count(self, channel: str) -> int:
        """Get the number of active connections for a channel."""
        return len(self.active_connections.get(channel, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections across all channels."""
        return sum(len(connections) for connections in self.active_connections.values())


# Global instance
ws_manager = WebSocketManager()

