"""
Tests for MCP Agent Maestro exception hierarchy.
"""
import pytest
from agent_mcp.utils.error_handlers import (
    MaestroException,
    AgentMCPError,  # Backward compatibility
    AgentOrchestrationError,
    TaskPlacementError,
    DatabaseError,
    ValidationError,
    SecurityError,
    NotFoundError,
    AuthenticationError,
    ConflictError,
)


class TestMaestroException:
    """Test MaestroException base class."""
    
    def test_base_exception_creation(self):
        """Test creating a basic MaestroException."""
        exc = MaestroException("Test error", status_code=500)
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert isinstance(exc.details, dict)
        assert "timestamp" in exc.details
    
    def test_exception_with_details(self):
        """Test creating exception with details."""
        details = {"agent_id": "test-123", "operation": "test"}
        exc = MaestroException("Test error", status_code=400, details=details)
        assert exc.details["agent_id"] == "test-123"
        assert exc.details["operation"] == "test"
        assert "timestamp" in exc.details
    
    def test_exception_string_representation(self):
        """Test exception string representation."""
        exc = MaestroException("Test error message")
        assert str(exc) == "Test error message"


class TestAgentOrchestrationError:
    """Test AgentOrchestrationError."""
    
    def test_orchestration_error_creation(self):
        """Test creating an AgentOrchestrationError."""
        exc = AgentOrchestrationError("Failed to coordinate agents")
        assert exc.message == "Failed to coordinate agents"
        assert exc.status_code == 500
        assert exc.details["operation"] == "agent_orchestration"
        assert exc.details["error_type"] == "AgentOrchestrationError"
    
    def test_orchestration_error_with_details(self):
        """Test creating orchestration error with custom details."""
        details = {"agent_ids": ["agent1", "agent2"], "reason": "conflict"}
        exc = AgentOrchestrationError("Coordination failed", details=details)
        assert exc.details["agent_ids"] == ["agent1", "agent2"]
        assert exc.details["reason"] == "conflict"
        assert exc.details["operation"] == "agent_orchestration"


class TestTaskPlacementError:
    """Test TaskPlacementError."""
    
    def test_placement_error_creation(self):
        """Test creating a TaskPlacementError."""
        exc = TaskPlacementError("Failed to assign task")
        assert exc.message == "Failed to assign task"
        assert exc.status_code == 500
        assert exc.details["operation"] == "task_placement"
        assert exc.details["error_type"] == "TaskPlacementError"
    
    def test_placement_error_with_details(self):
        """Test creating placement error with custom details."""
        details = {"task_id": "task-123", "reason": "no available agents"}
        exc = TaskPlacementError("Assignment failed", details=details)
        assert exc.details["task_id"] == "task-123"
        assert exc.details["reason"] == "no available agents"
        assert exc.details["operation"] == "task_placement"


class TestExceptionInheritance:
    """Test exception inheritance and backward compatibility."""
    
    def test_backward_compatibility(self):
        """Test that AgentMCPError still works."""
        exc1 = AgentMCPError("Test")
        exc2 = MaestroException("Test")
        assert isinstance(exc1, MaestroException)
        assert type(exc1) == type(exc2)
    
    def test_specialized_exceptions_inherit_from_base(self):
        """Test that specialized exceptions inherit from MaestroException."""
        assert issubclass(AgentOrchestrationError, MaestroException)
        assert issubclass(TaskPlacementError, MaestroException)
        assert issubclass(DatabaseError, MaestroException)
        assert issubclass(ValidationError, MaestroException)
        assert issubclass(SecurityError, MaestroException)
    
    def test_exception_isinstance_checks(self):
        """Test isinstance checks work correctly."""
        exc = AgentOrchestrationError("Test")
        assert isinstance(exc, MaestroException)
        assert isinstance(exc, AgentMCPError)  # Backward compatibility


class TestExceptionErrorHandlers:
    """Test exception error handling utilities."""
    
    def test_format_error_response(self):
        """Test formatting error responses."""
        from agent_mcp.utils.error_handlers import format_error_response
        
        exc = MaestroException("Test error", status_code=400, details={"field": "test"})
        response = format_error_response(exc)
        
        assert response["error"] == "Test error"
        assert response["status_code"] == 400
        assert response["details"]["field"] == "test"
    
    def test_format_error_response_with_request_id(self):
        """Test formatting error with request ID."""
        from agent_mcp.utils.error_handlers import format_error_response
        
        exc = ValidationError("Validation failed")
        response = format_error_response(exc, request_id="req-123")
        
        assert response["error"] == "Validation failed"
        assert response["request_id"] == "req-123"
    
    def test_handle_validation_error(self):
        """Test handle_validation_error utility."""
        from agent_mcp.utils.error_handlers import handle_validation_error
        
        exc = handle_validation_error("email", "invalid-email", "Must be a valid email")
        assert isinstance(exc, ValidationError)
        assert exc.details["field"] == "email"
        assert exc.details["reason"] == "Must be a valid email"
        assert exc.status_code == 400

