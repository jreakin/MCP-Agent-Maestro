# Agent-MCP Standardized Response Helpers
"""
Standardized response formatting for API endpoints.
Ensures consistent response structure across all routes.
"""
from starlette.responses import JSONResponse
from typing import Any, Optional, Dict


def success_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200
) -> JSONResponse:
    """Create standardized success response."""
    response: Dict[str, Any] = {"success": True, "data": data}
    if message:
        response["message"] = message
    return JSONResponse(
        response,
        status_code=status_code,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )


def error_response(
    error: str,
    status_code: int = 400,
    details: Optional[dict] = None
) -> JSONResponse:
    """Create standardized error response."""
    response: Dict[str, Any] = {"success": False, "error": error}
    if details:
        response["details"] = details
    return JSONResponse(
        response,
        status_code=status_code,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )

