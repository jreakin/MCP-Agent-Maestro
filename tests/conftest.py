"""
Pytest configuration and fixtures for Agent-MCP tests.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ.setdefault("MCP_DEBUG", "true")
os.environ.setdefault("TESTING", "true")
# Set dummy OpenAI API key to prevent settings validation errors during test collection
# This must be set before any imports that trigger settings initialization
os.environ.setdefault("AGENT_MCP_OPENAI_API_KEY", "sk-test123456789012345678901234567890")


def _is_database_available() -> bool:
    """Check if database is available for integration tests."""
    try:
        from agent_mcp.db.connection_factory import get_db_connection
        from agent_mcp.db.postgres_connection import return_connection
        
        # Try to get a connection
        conn = get_db_connection()
        if conn:
            # Test the connection
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    conn.commit()
                return_connection(conn)
                return True
            except Exception:
                return_connection(conn)
                return False
        return False
    except Exception:
        # Database not available
        return False


# Pytest fixture to check database availability
@pytest.fixture(scope="session")
def db_available():
    """Check if database is available for integration tests."""
    return _is_database_available()


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temporary database path for testing."""
    return tmp_path_factory.mktemp("test_db")


@pytest.fixture(autouse=True)
def reset_test_environment():
    """Reset test environment before each test."""
    # Add any global test setup/teardown here
    yield
    # Cleanup after test
    pass


@pytest.fixture
def db_connection():
    """Provide a database connection for integration tests."""
    from agent_mcp.db.connection_factory import get_db_connection
    from agent_mcp.db.postgres_connection import return_connection
    
    if not _is_database_available():
        pytest.skip("Database not available")
    
    conn = get_db_connection()
    yield conn
    return_connection(conn)


def _is_openai_available() -> bool:
    """Check if OpenAI API is available for integration tests."""
    try:
        # If using Ollama, we don't need OpenAI
        if os.getenv("EMBEDDING_PROVIDER", "openai").lower() == "ollama":
            return True  # Ollama is handled separately
        from agent_mcp.external.openai_service import get_openai_client
        client = get_openai_client()
        return client is not None
    except Exception:
        return False


def _is_ollama_available() -> bool:
    """Check if Ollama is available for integration tests."""
    try:
        import httpx
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        # Try to connect to Ollama API
        response = httpx.get(f"{ollama_url}/api/tags", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def openai_available():
    """Check if OpenAI API is available for integration tests."""
    return _is_openai_available()


@pytest.fixture(scope="session")
def ollama_available():
    """Check if Ollama is available for integration tests."""
    return _is_ollama_available()


# Pytest hook to skip integration tests if database/OpenAI unavailable
def pytest_collection_modifyitems(config, items):
    """
    Automatically skip integration tests if database/OpenAI unavailable.
    
    NOTE: All tests should be run in-container for consistency.
    Run tests using: ./scripts/run_tests_docker.sh or uv run test
    """
    db_available = _is_database_available()
    openai_available = _is_openai_available()
    ollama_available = _is_ollama_available()
    embedding_provider = os.environ.get("EMBEDDING_PROVIDER", "openai").lower()
    
    # Check if we're running in a container (DB_HOST will be 'postgres' in Docker)
    in_container = os.environ.get("DB_HOST") == "postgres" or os.path.exists("/.dockerenv")
    
    # Determine which AI provider is available based on configuration
    ai_provider_available = False
    if embedding_provider == "ollama":
        ai_provider_available = ollama_available
    else:
        ai_provider_available = openai_available
    
    for item in items:
        # Check if test is marked with integration marker
        if item.get_closest_marker("integration"):
            # Skip if database not available (most integration tests need DB)
            if not db_available:
                skip_marker = pytest.mark.skip(
                    reason="Database not available - run tests in Docker container: ./scripts/run_tests_docker.sh"
                )
                item.add_marker(skip_marker)
            elif not in_container:
                # Warn if running integration tests outside container
                import warnings
                warnings.warn(
                    f"Integration test '{item.name}' is running outside Docker container. "
                    "For consistency, run all tests in-container: ./scripts/run_tests_docker.sh",
                    UserWarning
                )
            # Skip if AI provider required but not available
            # Check if test is in a PydanticAI-related class or has OpenAI-related name
            test_path = str(item.fspath) if hasattr(item, 'fspath') else ""
            test_cls = item.cls.__name__ if item.cls else ""
            test_name = item.name.lower()
            
            # Check if pydantic-ai is installed
            pydanticai_available = False
            try:
                import pydantic_ai
                pydanticai_available = True
            except ImportError:
                pass
            
            needs_ai_provider = (
                "pydanticai" in test_name or 
                "pydanticai" in test_cls.lower() or
                "pydanticai" in test_path.lower() or
                "rag_agent" in test_name or
                "ragagent" in test_cls.lower() or
                "orchestrat" in test_name or
                "orchestrat" in test_cls.lower() or
                "taskagent" in test_cls.lower()
            )
            
            # Skip PydanticAI tests if pydantic-ai is not installed
            if needs_ai_provider and not pydanticai_available:
                skip_marker = pytest.mark.skip(
                    reason="pydantic-ai is required for PydanticAI agent tests. Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai"
                )
                item.add_marker(skip_marker)
            elif needs_ai_provider and not ai_provider_available:
                if embedding_provider == "ollama":
                    skip_marker = pytest.mark.skip(
                        reason=f"Ollama not available - ensure Ollama is running and accessible at {os.environ.get('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')}"
                    )
                else:
                    skip_marker = pytest.mark.skip(
                        reason="OpenAI API not available - set OPENAI_API_KEY environment variable or use EMBEDDING_PROVIDER=ollama"
                    )
                item.add_marker(skip_marker)

