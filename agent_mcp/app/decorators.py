# Agent-MCP Route Decorators
"""
Decorators for API routes to handle CORS, authentication, and error handling.
Eliminates repetitive code in route handlers.
"""
from functools import wraps
from typing import Callable, Optional, Literal, Any
from starlette.requests import Request
from starlette.responses import JSONResponse
from ..core.auth import verify_token
from ..utils.error_handlers import create_error_response, AuthenticationError, log_error
from ..core.config import logger


def handle_cors(func: Callable) -> Callable:
    """Handle CORS preflight requests."""
    @wraps(func)
    async def wrapper(request: Request, *args: Any, **kwargs: Any) -> JSONResponse:
        if request.method == "OPTIONS":
            return JSONResponse(
                {},
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                }
            )
        return await func(request, *args, **kwargs)
    return wrapper


def require_auth(required_role: Literal["admin", "agent"] = "agent") -> Callable:
    """Require authentication for route."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @handle_cors
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> JSONResponse:
            # Extract token from body or query params
            token = None
            if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                try:
                    body = await request.json()
                    token = body.get("token")
                except Exception:
                    pass
            if not token:
                token = request.query_params.get("token")
            
            if not verify_token(token or "", required_role):
                raise AuthenticationError(f"Invalid {required_role} token")
            
            # Inject token into kwargs
            kwargs["token"] = token
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def api_route(
    methods: Optional[list[str]] = None,
    require_auth_role: Optional[Literal["admin", "agent"]] = None
) -> Callable:
    """Combined decorator for API routes with CORS, auth, and error handling."""
    def decorator(func: Callable) -> Callable:
        wrapped = func
        if require_auth_role:
            wrapped = require_auth(require_auth_role)(wrapped)
        else:
            wrapped = handle_cors(wrapped)
        
        @wraps(wrapped)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> JSONResponse:
            try:
                return await wrapped(request, *args, **kwargs)
            except Exception as e:
                log_error(e, request=request)
                return create_error_response(e)
        return wrapper
    return decorator

