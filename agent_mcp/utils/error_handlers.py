"""
Centralized error handling utilities for MCP Agent Maestro.
Provides custom exceptions and consistent error response formatting.
"""
from typing import Dict, Any, Optional
from starlette.responses import JSONResponse
from starlette.requests import Request
import traceback

from ..core.config import logger


# Custom Exception Classes
class MaestroException(Exception):
    """Base exception for MCP Agent Maestro errors.
    
    All Maestro-specific exceptions inherit from this base class. It provides
    structured error information including status codes and contextual details
    for better debugging and error handling.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (default: 500)
        details: Dictionary with additional context for debugging
    """
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        # Add timestamp for debugging
        import time
        if "timestamp" not in self.details:
            self.details["timestamp"] = time.time()
        super().__init__(self.message)


# Backward compatibility alias
AgentMCPError = MaestroException


class AgentOrchestrationError(MaestroException):
    """Raised when agent coordination fails.
    
    This exception is raised when the Maestro orchestrator fails to coordinate
    multiple agents, manage agent lifecycle, or handle inter-agent communication.
    
    Attributes:
        message: Human-readable error message
        details: Dictionary with additional context (agent_ids, operation, etc.)
        status_code: HTTP status code (500 for server errors)
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        if details is None:
            details = {}
        # Add debugging context
        if "operation" not in details:
            details["operation"] = "agent_orchestration"
        if "error_type" not in details:
            details["error_type"] = "AgentOrchestrationError"
        super().__init__(message, status_code=500, details=details)


class TaskPlacementError(MaestroException):
    """Raised when task assignment fails.
    
    This exception is raised when the Maestro cannot assign a task to an agent,
    such as when all agents are busy, no suitable agent exists, or task
    validation fails.
    
    Attributes:
        message: Human-readable error message
        details: Dictionary with additional context (task_id, agent_id, reason, etc.)
        status_code: HTTP status code (500 for server errors)
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        if details is None:
            details = {}
        # Add debugging context
        if "operation" not in details:
            details["operation"] = "task_placement"
        if "error_type" not in details:
            details["error_type"] = "TaskPlacementError"
        super().__init__(message, status_code=500, details=details)


class DatabaseError(MaestroException):
    """Database operation errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class ValidationError(MaestroException):
    """Data validation errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class SecurityError(MaestroException):
    """Security-related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class NotFoundError(MaestroException):
    """Resource not found errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)


class AuthenticationError(MaestroException):
    """Authentication errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class ConflictError(MaestroException):
    """Resource conflict errors (e.g., duplicate entries)."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, details=details)


def format_error_response(
    error: Exception,
    status_code: int = 500,
    include_traceback: bool = False,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format a consistent error response.
    
    Args:
        error: The exception that occurred
        status_code: HTTP status code
        include_traceback: Whether to include traceback in response (for debugging)
        request_id: Optional request ID for tracing
        
    Returns:
        Formatted error response dictionary
    """
    response = {
        "error": str(error),
        "status_code": status_code,
    }
    
    if request_id:
        response["request_id"] = request_id
    
    # Add details if it's a MaestroException (or backward compat AgentMCPError)
    if isinstance(error, (MaestroException, AgentMCPError)):
        response["error"] = error.message
        response["status_code"] = error.status_code
        if error.details:
            response["details"] = error.details
    
    # Include traceback only in debug mode or if explicitly requested
    if include_traceback:
        response["traceback"] = traceback.format_exc()
    
    return response


def create_error_response(
    error: Exception,
    status_code: int = 500,
    include_traceback: bool = False,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create a JSONResponse with formatted error information.
    
    Args:
        error: The exception that occurred
        status_code: HTTP status code
        include_traceback: Whether to include traceback in response
        request_id: Optional request ID for tracing
        
    Returns:
        JSONResponse with error information
    """
    error_data = format_error_response(error, status_code, include_traceback, request_id)
    return JSONResponse(
        error_data,
        status_code=error_data["status_code"],
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
    )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None, request: Optional[Request] = None):
    """
    Log an error with context information.
    
    Args:
        error: The exception that occurred
        context: Additional context information
        request: Optional request object for logging request details
    """
    error_context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if context:
        error_context.update(context)
    
    if request:
        error_context.update({
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
        })
    
    # Log with appropriate level based on error type
    if isinstance(error, (ValidationError, NotFoundError, AuthenticationError)):
        logger.warning(f"Client error: {error_context}", exc_info=True)
    elif isinstance(error, SecurityError):
        logger.error(f"Security error: {error_context}", exc_info=True)
    elif isinstance(error, DatabaseError):
        logger.error(f"Database error: {error_context}", exc_info=True)
    else:
        logger.error(f"Unexpected error: {error_context}", exc_info=True)


async def error_handler_middleware(request: Request, call_next):
    """
    Middleware to catch and format errors consistently.
    This should be added to the Starlette app middleware stack.
    """
    try:
        response = await call_next(request)
        return response
    except (MaestroException, AgentMCPError) as e:
        log_error(e, request=request)
        return create_error_response(e, include_traceback=False)
    except Exception as e:
        log_error(e, request=request)
        return create_error_response(e, status_code=500, include_traceback=False)


def handle_database_error(error: Exception, operation: str, context: Optional[Dict[str, Any]] = None) -> DatabaseError:
    """
    Convert a database exception to a DatabaseError with context.
    
    Args:
        error: The database exception
        operation: Description of the operation that failed
        context: Additional context (e.g., task_id, agent_id)
        
    Returns:
        DatabaseError with formatted message
    """
    import psycopg2
    
    if isinstance(error, psycopg2.Error):
        error_msg = f"Database error during {operation}: {str(error)}"
    else:
        error_msg = f"Unexpected database error during {operation}: {str(error)}"
    
    details = context or {}
    details["operation"] = operation
    
    return DatabaseError(error_msg, details=details)


def handle_validation_error(field: str, value: Any, reason: str) -> ValidationError:
    """
    Create a ValidationError for a specific field.
    
    Args:
        field: The field that failed validation
        value: The invalid value
        reason: Reason for validation failure
        
    Returns:
        ValidationError with formatted message
    """
    message = f"Validation error for field '{field}': {reason}"
    details = {
        "field": field,
        "value": str(value),
        "reason": reason
    }
    return ValidationError(message, details=details)

