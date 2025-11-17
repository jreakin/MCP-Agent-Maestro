# Using Agent-MCP with Ollama

## Overview

Agent-MCP currently supports **OpenAI** for embeddings and chat completions in the Python implementation. The Node.js version includes Ollama support, but the Python version does not yet have native Ollama integration.

## Current Status

### Python Implementation (This Repository)
- ✅ **OpenAI**: Full support for embeddings and chat completions
- ❌ **Ollama**: Not yet implemented (requires development)

### Node.js Implementation
- ✅ **OpenAI**: Supported
- ✅ **Ollama**: Supported (see `agent-mcp-node` directory)

## How to Use Ollama (Future Implementation)

The recommended approach is to run Ollama **natively on your host machine** and connect the Agent-MCP container to it. This provides better performance and easier model management.

### 1. Install Ollama on Your Host Machine

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai/download
# Windows: Download installer from https://ollama.ai/download
```

### 2. Start Ollama Service on Host

```bash
# Start Ollama (runs on http://localhost:11434 by default)
ollama serve

# In another terminal, pull suitable models
ollama pull nomic-embed-text  # Recommended for embeddings (768 dimensions)
ollama pull llama3.2          # For chat completions
```

### 3. Configure Agent-MCP to Connect to Host Ollama

The key is using the correct host address from within the Docker container:

**For macOS/Windows:**
- Use `host.docker.internal` to access the host machine
- This is automatically available in Docker Desktop

**For Linux:**
- Use `host.docker.internal` (Docker Desktop) OR
- Use `172.17.0.1` (default Docker bridge gateway) OR
- Use `host` network mode (see below)

### 4. Environment Configuration

Update your `.env` file:

```bash
# .env file
EMBEDDING_PROVIDER=ollama

# For macOS/Windows Docker Desktop (recommended)
OLLAMA_BASE_URL=http://host.docker.internal:11434

# For Linux (if host.docker.internal doesn't work)
# OLLAMA_BASE_URL=http://172.17.0.1:11434

OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.2

# Database configuration (unchanged)
DB_PASSWORD=your_secure_password
PORT=8080
DB_PORT=5433
```

### 5. Docker Compose Configuration

The `docker-compose.yml` doesn't need an Ollama service - it connects to your host:

```yaml
version: '3.8'

services:
  agent-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: agent-mcp
    ports:
      - "${PORT:-8080}:8080"
    environment:
      - PORT=${PORT:-8080}
      # Ollama configuration (connects to host)
      - EMBEDDING_PROVIDER=${EMBEDDING_PROVIDER:-openai}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://host.docker.internal:11434}
      - OLLAMA_EMBEDDING_MODEL=${OLLAMA_EMBEDDING_MODEL:-nomic-embed-text}
      - OLLAMA_CHAT_MODEL=${OLLAMA_CHAT_MODEL:-llama3.2}
      # Database configuration
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=agent_mcp
      - DB_USER=agent_mcp
      - DB_PASSWORD=${DB_PASSWORD:-agent_mcp_password}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - agent-mcp-network
    # Optional: Add extra_hosts for Linux compatibility
    extra_hosts:
      - "host.docker.internal:host-gateway"

  postgres:
    image: pgvector/pgvector:pg16
    container_name: agent-mcp-postgres
    environment:
      - POSTGRES_DB=agent_mcp
      - POSTGRES_USER=agent_mcp
      - POSTGRES_PASSWORD=${DB_PASSWORD:-agent_mcp_password}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "${DB_PORT:-5433}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agent_mcp -d agent_mcp"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - agent-mcp-network

volumes:
  postgres-data:

networks:
  agent-mcp-network:
    driver: bridge
```

### 6. Linux Alternative: Host Network Mode

If `host.docker.internal` doesn't work on Linux, you can use host network mode:

```yaml
services:
  agent-mcp:
    # ... other config ...
    network_mode: "host"  # Use host network
    environment:
      - OLLAMA_BASE_URL=http://localhost:11434  # Now localhost works
      # ... other env vars ...
    # Remove ports mapping (not needed in host mode)
    # ports:
    #   - "${PORT:-8080}:8080"
```

**Note**: Host network mode has security implications and may conflict with other services.

### 7. Verify Connection

Test that the container can reach your host Ollama:

```bash
# Start services
docker-compose up -d

# Test connection from container
docker-compose exec agent-mcp curl http://host.docker.internal:11434/api/tags

# Should return list of available models
```

### Benefits of Host-Based Ollama

1. **Better Performance**: No container overhead for model inference
2. **Easier Model Management**: Manage models directly on host with `ollama pull/list`
3. **Shared Resources**: Multiple containers can use the same Ollama instance
4. **Persistent Models**: Models stored on host, not in container volumes
5. **Resource Efficiency**: Ollama can use GPU directly from host

## Network Configuration Details

### Understanding Docker Networking

When Agent-MCP runs in a Docker container, it needs to connect to Ollama running on your host machine. The connection method depends on your OS:

| Platform | Method | Address |
|----------|--------|---------|
| **macOS** (Docker Desktop) | `host.docker.internal` | `http://host.docker.internal:11434` |
| **Windows** (Docker Desktop) | `host.docker.internal` | `http://host.docker.internal:11434` |
| **Linux** (Docker Desktop) | `host.docker.internal` | `http://host.docker.internal:11434` |
| **Linux** (Docker Engine) | Bridge gateway | `http://172.17.0.1:11434` |
| **Linux** (Alternative) | Host network mode | `http://localhost:11434` |

### Testing Host Connectivity

Before configuring Agent-MCP, verify your container can reach the host:

```bash
# Start Agent-MCP container
docker-compose up -d

# Test from inside container (macOS/Windows)
docker-compose exec agent-mcp curl http://host.docker.internal:11434/api/tags

# Test from inside container (Linux - bridge gateway)
docker-compose exec agent-mcp curl http://172.17.0.1:11434/api/tags

# If successful, you'll see JSON with available models
```

### Troubleshooting Host Connection

**Problem**: Container can't reach host Ollama

**Solutions**:

1. **Check Ollama is running on host**:
   ```bash
   # On host machine
   curl http://localhost:11434/api/tags
   ```

2. **Verify Ollama is listening on all interfaces** (not just localhost):
   ```bash
   # Check if Ollama is bound to 0.0.0.0 or 127.0.0.1
   # Ollama should bind to 0.0.0.0:11434 by default
   netstat -an | grep 11434  # Linux/macOS
   ```

3. **For Linux, add extra_hosts to docker-compose.yml**:
   ```yaml
   services:
     agent-mcp:
       extra_hosts:
         - "host.docker.internal:host-gateway"
   ```

4. **For Linux, find Docker bridge gateway IP**:
   ```bash
   # Find the gateway IP
   docker network inspect bridge | grep Gateway
   # Use that IP in OLLAMA_BASE_URL
   ```

## What Would Need to Be Implemented

To add Ollama support to the Python implementation, you would need to:

### 1. Create Ollama Service Module

Create `agent_mcp/external/ollama_service.py`:

```python
"""
Ollama service for embeddings and chat completions.
"""
import httpx
from typing import Optional, List, Dict, Any
from ..core.config import logger

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")

async def get_ollama_embeddings(text: str, model: str = OLLAMA_EMBEDDING_MODEL) -> Optional[List[float]]:
    """Get embeddings from Ollama."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={"model": model, "prompt": text},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding")
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            return None

async def get_ollama_chat_completion(
    messages: List[Dict[str, str]],
    model: str = OLLAMA_CHAT_MODEL
) -> Optional[str]:
    """Get chat completion from Ollama."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={"model": model, "messages": messages},
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content")
        except Exception as e:
            logger.error(f"Ollama chat completion error: {e}")
            return None
```

### 2. Update Embedding Provider Logic

Modify `agent_mcp/features/rag/indexing.py` to support provider selection:

```python
from ...core.config import EMBEDDING_PROVIDER

async def get_embeddings(text: str) -> Optional[List[float]]:
    """Get embeddings using configured provider."""
    if EMBEDDING_PROVIDER == "ollama":
        return await get_ollama_embeddings(text)
    elif EMBEDDING_PROVIDER == "openai":
        # Existing OpenAI code
        ...
    else:
        logger.error(f"Unknown embedding provider: {EMBEDDING_PROVIDER}")
        return None
```

### 3. Update Chat Completion Logic

Modify `agent_mcp/features/rag/query.py` to support Ollama for chat completions.

### 4. Configuration Updates

Add to `agent_mcp/core/config.py`:

```python
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
```

## Using Node.js Version for Ollama Support

The Node.js implementation already has Ollama support. To use it:

```bash
cd agent-mcp-node

# Set environment variables
export EMBEDDING_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=nomic-embed-text

# Install and run
npm install
npm start
```

## Recommended Ollama Models

### For Embeddings
- **nomic-embed-text**: Best general-purpose embedding model (768 dimensions)
- **mxbai-embed-large**: Higher quality (1024 dimensions, larger model)

### For Chat Completions
- **llama3.2**: Fast and efficient for code generation
- **codellama**: Specialized for code tasks
- **mistral**: Good balance of speed and quality
- **qwen2.5**: Excellent for multilingual and code tasks

## Benefits of Using Ollama

1. **No API Costs**: Run locally without per-token pricing
2. **Privacy**: All processing happens on your machine
3. **Offline Support**: Works without internet connection
4. **Custom Models**: Use fine-tuned or specialized models
5. **No Rate Limits**: Process as much as your hardware allows

## Considerations

1. **Hardware Requirements**: Ollama requires sufficient RAM (8GB+ recommended)
2. **Embedding Dimensions**: Different models produce different vector sizes (need to match PostgreSQL schema)
3. **Performance**: Local models may be slower than cloud APIs depending on hardware
4. **Model Management**: Need to pull and manage model files locally

## Future Work

To implement Ollama support in the Python version:

1. Create `ollama_service.py` module
2. Add provider abstraction layer
3. Update embedding and chat completion functions
4. Add configuration and environment variable handling
5. Update Docker Compose example
6. Add tests for Ollama integration

## Getting Help

- Check [Node.js implementation](../agent-mcp-node) for Ollama integration reference
- See [Ollama documentation](https://ollama.ai/docs) for API details
- Join [Discord community](https://discord.gg/7Jm7nrhjGn) for discussions

