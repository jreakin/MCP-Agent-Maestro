# Docker Setup for Agent-MCP

This document describes the containerized setup for Agent-MCP with PostgreSQL support.

## Architecture

Each project gets its own containerized Agent-MCP instance with:
- **Agent-MCP service**: The main application
- **PostgreSQL database**: Isolated database per project (with pgvector for embeddings)
- **Persistent volumes**: Data persists across container restarts

## Quick Start

### 1. Create a `.env` file

```bash
# Required - AI Provider (choose one)
OPENAI_API_KEY=your_openai_api_key_here

# Optional - Use Ollama instead of OpenAI (see docs/setup/OLLAMA_SETUP.md)
# EMBEDDING_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Optional - Database
DB_PASSWORD=your_secure_password_here
PORT=8080
DB_PORT=5433
```

### 2. Start the services

```bash
docker-compose up -d
```

### 3. Access the services

- **Agent-MCP API**: http://localhost:8080 (or PORT from .env)
- **PostgreSQL**: localhost:5433 (or DB_PORT from .env)
- **Dashboard**: Run separately or add to docker-compose

**Note**: The default port is `8080` (not 3000) to match the main README.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 3000 | Port for Agent-MCP service |
| `DB_TYPE` | `postgresql` | Database type (`sqlite` or `postgresql`) |
| `DB_HOST` | `postgres` | PostgreSQL host (use `postgres` in docker-compose) |
| `DB_PORT` | 5432 | PostgreSQL port |
| `DB_NAME` | `agent_mcp` | Database name |
| `DB_USER` | `agent_mcp` | Database user |
| `DB_PASSWORD` | `agent_mcp_password` | Database password |

### Using SQLite (Development)

To use SQLite instead of PostgreSQL, set:
```bash
DB_TYPE=sqlite
```

## Project-Specific Deployment

### Option 1: One container per project directory

```bash
# In your project directory
cd /path/to/your/project
docker-compose -f /path/to/Agent-MCP-fork/docker-compose.yml up -d
```

### Option 2: Custom docker-compose per project

Create a `docker-compose.yml` in your project:

```yaml
version: '3.8'
services:
  agent-mcp:
    image: your-registry/agent-mcp:latest
    ports:
      - "3000:3000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DB_PASSWORD=${DB_PASSWORD}
    volumes:
      - ./:/app/project-data
    depends_on:
      - postgres
  
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=agent_mcp
      - POSTGRES_USER=agent_mcp
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
```

## Database Migrations

The database schema is automatically initialized on first startup. For manual migrations:

```bash
docker-compose exec agent-mcp uv run -m agent_mcp.db.migrations
```

## Troubleshooting

### Check logs
```bash
docker-compose logs -f agent-mcp
docker-compose logs -f postgres
```

### Access PostgreSQL
```bash
docker-compose exec postgres psql -U agent_mcp -d agent_mcp
```

### Reset database
```bash
docker-compose down -v  # Removes volumes
docker-compose up -d    # Recreates with fresh database
```

## Production Considerations

1. **Security**: Change default passwords
2. **Backups**: Set up regular PostgreSQL backups
3. **Resource limits**: Add memory/CPU limits in docker-compose
4. **Networking**: Use Docker networks for service isolation
5. **Secrets**: Use Docker secrets or external secret management

## Next Steps

- [ ] Complete PostgreSQL schema migration
- [ ] Add database migration system
- [ ] Create production-ready docker-compose
- [ ] Add health checks and monitoring
- [ ] Document backup/restore procedures
