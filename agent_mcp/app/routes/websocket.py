"""WebSocket routes for real-time updates."""
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket

from ...core.config import logger
from ..websocket import ws_manager


async def task_updates_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time task updates."""
    await ws_manager.connect(websocket, "tasks")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except Exception as e:
        logger.debug(f"WebSocket connection closed: {e}")
    finally:
        await ws_manager.disconnect(websocket, "tasks")


async def agent_updates_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates."""
    await ws_manager.connect(websocket, "agents")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except Exception as e:
        logger.debug(f"WebSocket connection closed: {e}")
    finally:
        await ws_manager.disconnect(websocket, "agents")


async def security_updates_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time security alerts."""
    await ws_manager.connect(websocket, "security")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except Exception as e:
        logger.debug(f"WebSocket connection closed: {e}")
    finally:
        await ws_manager.disconnect(websocket, "security")


# Route definitions
routes = [
    WebSocketRoute('/ws/tasks', endpoint=task_updates_websocket, name="task_updates_ws"),
    WebSocketRoute('/ws/agents', endpoint=agent_updates_websocket, name="agent_updates_ws"),
    WebSocketRoute('/ws/security', endpoint=security_updates_websocket, name="security_updates_ws"),
]

