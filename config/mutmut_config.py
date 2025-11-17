"""
Mutmut configuration for mutation testing.
All mutation testing runs inside the Docker container.
"""

# Paths to mutate (Python files in agent_mcp package)
paths_to_mutate = [
    "agent_mcp/",
]

# Paths to exclude from mutation
exclude_paths = [
    # Dashboard (TypeScript/React code)
    "agent_mcp/dashboard/",
    # Node.js code
    "agent-mcp-node/",
    # Database migrations (generated code)
    "agent_mcp/db/migrations/",
    # Test files themselves
    "tests/",
    # Scripts
    "scripts/",
    # Documentation
    "docs/",
    # Template files
    "agent_mcp/templates/",
    # Hooks (JavaScript)
    "agent_mcp/hooks/",
]

# Test command to run (executes in container)
test_command = "uv run pytest {test_path} -v"

# Coverage command (for mutmut to use)
coverage_command = "uv run pytest --cov=agent_mcp --cov-report=term-missing {test_path} -v"

# Pre-mutation command (optional, can be used to set up test environment)
pre_mutation = None

# Post-mutation command (optional, can be used to clean up)
post_mutation = None

