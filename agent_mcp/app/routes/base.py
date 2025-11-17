"""Base utilities and shared handlers for routes."""
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response


async def handle_options(request: Request) -> Response:
    """Handle OPTIONS requests for CORS preflight"""
    return PlainTextResponse(
        '',
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Max-Age': '86400',
        }
    )

