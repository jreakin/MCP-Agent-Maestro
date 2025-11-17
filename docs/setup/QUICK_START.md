# Quick Start Guide

This guide will help you get Agent-MCP up and running quickly.

> **💡 New to Agent-MCP?** Try the **[Easy Setup Guide](./EASY_SETUP.md)** first - it's a one-command interactive setup that detects everything automatically!

This guide covers manual setup for advanced users or CI/CD environments.

## Prerequisites

- **Docker** and **Docker Compose** installed
- **Git** installed
- **OpenAI API key** (or Ollama setup - see [OLLAMA_SETUP.md](./OLLAMA_SETUP.md))

## Step 1: Clone the Repository

```bash
git clone https://github.com/rinadelph/Agent-MCP.git
cd Agent-MCP
```

## Step 2: Choose Setup Method

### Option A: Interactive Setup (Recommended)

```bash
# Run the interactive setup wizard
./scripts/setup.sh
```

This will automatically detect your system and configure everything. Skip to Step 5 if using this method.

### Option B: Manual Setup

Continue with the steps below for manual configuration.

## Step 3: Create Environment File

Create a `.env` file in the project root:

```bash
# Required - AI Provider (choose one)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional - Use Ollama instead of OpenAI (runs on your host machine)
# EMBEDDING_PROVIDER=ollama
# OLLAMA_BASE_URL=http://host.docker.internal:11434
# OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Optional - Database
DB_PASSWORD=your_secure_password_here
PORT=8080
DB_PORT=5433
```

**Get your OpenAI API key**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

**Or use Ollama**: Install Ollama on your host machine, then set `EMBEDDING_PROVIDER=ollama` in `.env`. See [OLLAMA_SETUP.md](./OLLAMA_SETUP.md) for details.

## Step 4: Start with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f agent-mcp

# Check service status
docker-compose ps
```

This starts:
- **Agent-MCP service** on port 8080 (or your configured PORT)
- **PostgreSQL database** with pgvector on port 5433 (or your configured DB_PORT)

## Step 5: Verify Installation

```bash
# Check if the API is responding
curl http://localhost:8080/api/status

# Access PostgreSQL (optional)
docker-compose exec postgres psql -U agent_mcp -d agent_mcp
```

## Step 6: Access the Dashboard (Optional)

The dashboard runs separately. To start it:

```bash
cd agent_mcp/dashboard
npm install
npm run dev
```

Then open http://localhost:3847 in your browser.

## Step 7: Start Using Agent-MCP

### Option A: Via MCP Client (Recommended)

Configure your MCP client (Cursor, Claude Desktop, etc.) to connect to:

```
http://localhost:8080/mcp
```

See the [MCP Integration Guide](../README.md#mcp-integration-guide) in the main README for details.

### Option B: Via API

```bash
# Create an agent
curl -X POST http://localhost:8080/api/agents/create \
  -H "Content-Type: application/json" \
  -d '{
    "role": "backend",
    "specialization": "API development"
  }'

# Query project RAG
curl -X POST http://localhost:8080/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current architecture?",
    "agent_id": "your_agent_id"
  }'
```

## Troubleshooting

### Services won't start

```bash
# Check logs for errors
docker-compose logs

# Restart services
docker-compose restart

# Rebuild if needed
docker-compose up -d --build
```

### Database connection issues

```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### OpenAI API errors

```bash
# Verify API key is set
docker-compose exec agent-mcp env | grep OPENAI_API_KEY

# Check if key is valid
docker-compose exec agent-mcp python -c "from agent_mcp.external.openai_service import get_openai_client; print('OK' if get_openai_client() else 'FAILED')"
```

## Next Steps

- **Read the full documentation**: [README.md](../../README.md)
- **Configure MCP client**: [MCP Integration Guide](../../README.md#mcp-integration-guide)
- **Set up Ollama** (optional): [OLLAMA_SETUP.md](./OLLAMA_SETUP.md)
- **Explore the dashboard**: Start the dashboard and explore the UI
- **Create your first agent**: Use the MCP tools or API to create specialized agents

## Running Tests

```bash
# Run tests in Docker container
docker-compose exec agent-mcp uv run pytest tests/ -v

# Run only integration tests (requires database)
docker-compose exec agent-mcp uv run pytest tests/ -m integration

# Skip integration tests
docker-compose exec agent-mcp uv run pytest tests/ -m "not integration"
```

## Stopping Services

```bash
# Stop services (keeps data)
docker-compose stop

# Stop and remove containers (keeps data)
docker-compose down

# Stop and remove everything including data volumes
docker-compose down -v
```

## Production Deployment

For production:

1. **Change default passwords** in `.env`
2. **Use Docker secrets** or external secret management
3. **Set resource limits** in `docker-compose.yml`
4. **Configure backups** for PostgreSQL
5. **Set up monitoring** and logging
6. **Use reverse proxy** (nginx/traefik) for HTTPS

See [DOCKER_SETUP.md](../../DOCKER_SETUP.md) for more production considerations.

## Getting Help

- **Discord**: [Join the community](https://discord.gg/7Jm7nrhjGn)
- **GitHub Issues**: [Report bugs or ask questions](https://github.com/rinadelph/Agent-MCP/issues)
- **Documentation**: Check the [docs](../) directory for detailed guides

