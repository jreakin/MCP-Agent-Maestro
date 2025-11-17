"""
Structured logging utilities with request IDs and performance timing.
"""
import time
import uuid
import logging
import functools
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.config import logger


# Thread-local storage for request context
import threading
_context = threading.local()


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return getattr(_context, 'request_id', None)


def set_request_id(request_id: str):
    """Set the current request ID in context."""
    _context.request_id = request_id


def clear_request_id():
    """Clear the current request ID from context."""
    if hasattr(_context, 'request_id'):
        delattr(_context, 'request_id')


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


class StructuredFormatter(logging.Formatter):
    """Custom formatter that includes request ID and structured fields."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add request ID if available
        request_id = get_request_id()
        if request_id:
            record.request_id = request_id
        else:
            # Use "system" for logs without request context
            record.request_id = "system"
        
        # Format with structured fields
        return super().format(record)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request IDs to all requests and log API performance."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate and set request ID
        request_id = generate_request_id()
        set_request_id(request_id)
        
        # Add request ID to request state for access in routes
        request.state.request_id = request_id
        
        # Track request timing
        start_time = time.time()
        
        # Add request ID to response headers
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log API request
            log_api_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            duration = time.time() - start_time
            # Log failed request
            log_api_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration=duration,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
        finally:
            clear_request_id()


@contextmanager
def log_performance(operation: str, **context: Any):
    """
    Context manager for logging operation performance.
    
    Usage:
        with log_performance("database_query", table="tasks"):
            # ... operation ...
    """
    start_time = time.time()
    request_id = get_request_id()
    
    logger.info(
        f"Starting {operation}",
        extra={
            "operation": operation,
            "request_id": request_id,
            **context
        }
    )
    
    try:
        yield
        duration = time.time() - start_time
        logger.info(
            f"Completed {operation}",
            extra={
                "operation": operation,
                "duration_seconds": duration,
                "request_id": request_id,
                "status": "success",
                **context
            }
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Failed {operation}",
            extra={
                "operation": operation,
                "duration_seconds": duration,
                "request_id": request_id,
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                **context
            },
            exc_info=True
        )
        raise


def log_function_call(func: Callable = None, *, operation: Optional[str] = None):
    """
    Decorator to log function calls with performance timing.
    
    Usage:
        @log_function_call(operation="create_task")
        async def create_task(...):
            ...
    """
    def decorator(f: Callable) -> Callable:
        op_name = operation or f"{f.__module__}.{f.__name__}"
        
        @functools.wraps(f)
        async def async_wrapper(*args, **kwargs):
            with log_performance(op_name, function=f.__name__):
                return await f(*args, **kwargs)
        
        @functools.wraps(f)
        def sync_wrapper(*args, **kwargs):
            with log_performance(op_name, function=f.__name__):
                return f(*args, **kwargs)
        
        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(f):
            return async_wrapper
        else:
            return sync_wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def log_database_operation(operation: str, table: Optional[str] = None, **context: Any):
    """
    Log a database operation with context.
    
    Usage:
        log_database_operation("SELECT", table="tasks", task_id="123")
    """
    request_id = get_request_id()
    logger.debug(
        f"Database operation: {operation}",
        extra={
            "operation": operation,
            "table": table,
            "request_id": request_id,
            **context
        }
    )


def log_security_event(event_type: str, severity: str = "INFO", **context: Any):
    """
    Log a security-related event.
    
    Usage:
        log_security_event("threat_detected", severity="WARNING", threat_type="injection")
    """
    request_id = get_request_id()
    log_level = getattr(logging, severity.upper(), logging.INFO)
    
    logger.log(
        log_level,
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            "severity": severity,
            "request_id": request_id,
            **context
        }
    )


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration: float,
    **context: Any
):
    """
    Log an API request with timing and status.
    
    Usage:
        log_api_request("POST", "/api/tasks", 201, 0.123, task_id="123")
    """
    request_id = get_request_id()
    log_level = logging.INFO if status_code < 400 else logging.WARNING if status_code < 500 else logging.ERROR
    
    # Only log if duration is significant or there's an error
    if duration > 1.0 or status_code >= 400:
        logger.log(
            log_level,
            f"API {method} {path} {status_code} ({duration:.3f}s)",
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_seconds": duration,
                "request_id": request_id,
                **context
            }
        )

