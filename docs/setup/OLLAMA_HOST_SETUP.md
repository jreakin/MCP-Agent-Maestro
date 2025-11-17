# Using Ollama on Host Machine with Docker Container

This guide explains how to configure Agent-MCP running in Docker to use Ollama running natively on your host machine.

## Why Host-Based Ollama?

Running Ollama on your host machine (instead of in a container) provides:

- ✅ **Better Performance**: Direct GPU access, no container overhead
- ✅ **Easier Model Management**: Use `ollama pull/list` directly on host
- ✅ **Shared Resources**: Multiple containers can use the same Ollama instance
- ✅ **Persistent Models**: Models stored on host, survive container restarts
- ✅ **Resource Efficiency**: Ollama can use system resources directly

## Quick Setup

### 1. Install Ollama on Host

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai/download
```

### 2. Start Ollama on Host

```bash
# Start Ollama service (runs on http://localhost:11434)
ollama serve

# In another terminal, pull models
ollama pull nomic-embed-text  # For embeddings
ollama pull llama3.2          # For chat
```

### 3. Configure Agent-MCP

Update your `.env` file:

```bash
# Use Ollama instead of OpenAI
EMBEDDING_PROVIDER=ollama

# Connect to host Ollama (macOS/Windows/Linux with Docker Desktop)
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Model names
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.2

# Database (unchanged)
DB_PASSWORD=your_secure_password
PORT=8080
DB_PORT=5433
```

### 4. Start Agent-MCP

```bash
docker-compose up -d
```

The container will automatically connect to your host's Ollama instance.

## Platform-Specific Configuration

### macOS / Windows (Docker Desktop)

Docker Desktop automatically provides `host.docker.internal`:

```bash
# .env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

**No additional configuration needed!**

### Linux (Docker Desktop)

Same as macOS/Windows:

```bash
# .env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

The `docker-compose.yml` includes `extra_hosts` to ensure this works.

### Linux (Docker Engine - Native)

If `host.docker.internal` doesn't work, use the Docker bridge gateway:

```bash
# Find your Docker bridge gateway IP
docker network inspect bridge | grep Gateway

# Usually 172.17.0.1, use in .env:
OLLAMA_BASE_URL=http://172.17.0.1:11434
```

**Alternative**: Use host network mode (see below).

## Testing the Connection

### From Host Machine

```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Should return JSON with available models
```

### From Docker Container

```bash
# Test connection from container
docker-compose exec agent-mcp curl http://host.docker.internal:11434/api/tags

# Or test with the gateway IP (Linux)
docker-compose exec agent-mcp curl http://172.17.0.1:11434/api/tags
```

If successful, you'll see your available models in JSON format.

## Troubleshooting

### Container Can't Reach Host Ollama

**Problem**: `curl: (7) Failed to connect to host.docker.internal`

**Solutions**:

1. **Verify Ollama is running on host**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Check Ollama is listening on all interfaces**:
   ```bash
   # Should show 0.0.0.0:11434 or *:11434
   netstat -an | grep 11434  # Linux/macOS
   lsof -i :11434            # macOS alternative
   ```

3. **For Linux, ensure extra_hosts is in docker-compose.yml**:
   ```yaml
   services:
     agent-mcp:
       extra_hosts:
         - "host.docker.internal:host-gateway"
   ```

4. **For Linux, try bridge gateway IP**:
   ```bash
   # Find gateway
   ip addr show docker0 | grep inet
   
   # Use in .env
   OLLAMA_BASE_URL=http://172.17.0.1:11434
   ```

### Ollama Connection Timeout

**Problem**: Connection works but times out

**Solutions**:

1. **Check firewall rules** (Linux):
   ```bash
   # Allow connections from Docker network
   sudo ufw allow from 172.17.0.0/16 to any port 11434
   ```

2. **Verify Ollama is accessible**:
   ```bash
   # From host
   curl http://localhost:11434/api/tags
   
   # From container
   docker-compose exec agent-mcp curl http://host.docker.internal:11434/api/tags
   ```

### Models Not Found

**Problem**: Agent-MCP can't find models

**Solutions**:

1. **Verify models are pulled on host**:
   ```bash
   ollama list
   ```

2. **Check model names match exactly**:
   ```bash
   # In .env, use exact model name from ollama list
   OLLAMA_EMBEDDING_MODEL=nomic-embed-text  # Not "nomic-embed" or "nomic"
   ```

## Advanced: Host Network Mode (Linux Only)

For Linux, you can use host network mode to simplify networking:

```yaml
# docker-compose.yml
services:
  agent-mcp:
    network_mode: "host"  # Use host network
    environment:
      - OLLAMA_BASE_URL=http://localhost:11434  # Now localhost works
      # ... other env vars ...
    # Remove ports mapping (not needed in host mode)
    # ports:
    #   - "${PORT:-8080}:8080"
```

**Note**: Host network mode has security implications and may conflict with other services using the same ports.

## Recommended Models

### For Embeddings

- **nomic-embed-text** (768 dimensions) - Best general purpose
- **mxbai-embed-large** (1024 dimensions) - Higher quality, larger

### For Chat Completions

- **llama3.2** - Fast and efficient
- **codellama** - Specialized for code
- **mistral** - Good balance
- **qwen2.5** - Excellent multilingual support

## Performance Tips

1. **GPU Acceleration**: Install GPU drivers on host for better performance
2. **Model Size**: Use smaller models for faster responses (llama3.2 vs llama3.1)
3. **Concurrent Requests**: Ollama handles multiple requests, but monitor resource usage
4. **Memory**: Ensure host has enough RAM for models (8GB+ recommended)

## Security Considerations

- Ollama on host is accessible from containers - ensure firewall rules if needed
- Consider binding Ollama to specific interface if security is a concern
- Use Docker networks to isolate container-to-host communication

## Next Steps

- See [OLLAMA_SETUP.md](./OLLAMA_SETUP.md) for implementation details
- Check [QUICK_START.md](./QUICK_START.md) for general setup
- Join [Discord](https://discord.gg/7Jm7nrhjGn) for help

