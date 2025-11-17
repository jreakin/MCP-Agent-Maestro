# Load environment variables as the very first thing
import os
from pathlib import Path
from dotenv import load_dotenv

# Simple function to ensure .env file exists (avoid circular imports)
def ensure_env_file_simple(project_dir=None):
    """Simple version of ensure_env_file that doesn't require logger."""
    from pathlib import Path
    
    if project_dir:
        env_path = Path(project_dir) / ".env"
    else:
        # Search for .env in current directory and up to 3 parent directories
        current = Path.cwd()
        for level in range(4):
            candidate = current / (".." * level) / ".env"
            candidate = candidate.resolve()
            if candidate.exists():
                return candidate
        # If not found, create in current directory
        env_path = Path.cwd() / ".env"
    
    # Create .env file if it doesn't exist
    if not env_path.exists():
        print(f"Creating default .env file at: {env_path}")
        
        default_env_content = """# MCP Agent Maestro Configuration
# This file was automatically generated. Edit as needed.

# API & Server Configuration
AGENT_MCP_API_HOST=localhost
AGENT_MCP_API_PORT=8080
AGENT_MCP_DASHBOARD_PORT=3000

# Database Configuration
# For Docker: use 'postgres' as host, for local: use 'localhost'
AGENT_MCP_DB_HOST=localhost
AGENT_MCP_DB_PORT=5432
AGENT_MCP_DB_NAME=agent_mcp
AGENT_MCP_DB_USER=agent_mcp
AGENT_MCP_DB_PASSWORD=
AGENT_MCP_DB_POOL_MIN=1
AGENT_MCP_DB_POOL_MAX=10

# OpenAI Configuration (optional - leave empty if using Ollama)
# AGENT_MCP_OPENAI_API_KEY=sk-your-api-key-here
AGENT_MCP_OPENAI_MODEL=gpt-4.1-2025-04-14
AGENT_MCP_EMBEDDING_MODEL=text-embedding-3-large
AGENT_MCP_EMBEDDING_DIMENSION=1536

# Embedding Provider (openai or ollama)
# Set to 'ollama' to use local Ollama models instead of OpenAI
EMBEDDING_PROVIDER=openai

# Ollama Configuration (if using EMBEDDING_PROVIDER=ollama)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_EMBEDDING_MODEL=nomic-embed-text
# OLLAMA_CHAT_MODEL=llama3.2

# Security Configuration
AGENT_MCP_SECURITY_ENABLED=true
AGENT_MCP_SECURITY_POISON_DETECTION_ENABLED=true
AGENT_MCP_SECURITY_SCAN_TOOL_SCHEMAS=true
AGENT_MCP_SECURITY_SCAN_TOOL_RESPONSES=true
AGENT_MCP_SECURITY_SANITIZATION_MODE=remove

# RAG Configuration
AGENT_MCP_RAG_ENABLED=true
AGENT_MCP_RAG_MAX_RESULTS=13
AGENT_MCP_DISABLE_AUTO_INDEXING=false

# Logging Configuration
AGENT_MCP_LOG_LEVEL=INFO
AGENT_MCP_MCP_DEBUG=false
AGENT_MCP_LOG_FILE=mcp_server.log

# Agent Management
AGENT_MCP_MAX_WORKERS=5
AGENT_MCP_AGENT_TIMEOUT=3600

# Task Analysis
AGENT_MCP_TASK_ANALYSIS_MODEL=gpt-4.1-2025-04-14
AGENT_MCP_TASK_ANALYSIS_MAX_TOKENS=1000000

# Task Placement
AGENT_MCP_ENABLE_TASK_PLACEMENT_RAG=true
AGENT_MCP_TASK_DUPLICATION_THRESHOLD=0.8
AGENT_MCP_ALLOW_RAG_OVERRIDE=true
AGENT_MCP_TASK_PLACEMENT_RAG_TIMEOUT=5
"""
        
        try:
            env_path.parent.mkdir(parents=True, exist_ok=True)
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(default_env_content)
            print(f"Created default .env file at: {env_path}")
        except Exception as e:
            print(f"Warning: Failed to create .env file at {env_path}: {e}. Continuing with environment variables only.")
    else:
        print(f"Using existing .env file at: {env_path}")
    
    return env_path

# Find and ensure .env file exists
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent  # Go up to MCP Agent Maestro directory

# Ensure .env file exists (will create with defaults if missing)
env_file = ensure_env_file_simple(project_root)
print(f"Using .env file at: {env_file}")

# Load environment variables from .env file
load_dotenv(dotenv_path=str(env_file))
print(f"OPENAI_API_KEY in environment: {os.environ.get('OPENAI_API_KEY', 'NOT FOUND')[:20]}...")

# Now import and run the CLI
from .cli import main_cli

if __name__ == "__main__":
    main_cli()