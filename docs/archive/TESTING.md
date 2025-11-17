# Testing Guide

## Quick Test

To test the PostgreSQL setup, run the test script inside the Docker container:

```bash
# Build and start the containers
docker-compose up -d --build

# Run the test script
docker-compose exec agent-mcp python3 test_postgres_setup.py
```

## Manual Testing

### 1. Check Container Status

```bash
docker-compose ps
```

Both `agent-mcp` and `agent-mcp-postgres` should be running.

### 2. Check Logs

```bash
# Agent-MCP logs
docker-compose logs agent-mcp

# PostgreSQL logs
docker-compose logs postgres
```

### 3. Test Database Connection

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U agent_mcp -d agent_mcp

# Inside psql, check tables
\dt

# Check pgvector extension
\dx vector

# Exit
\q
```

### 4. Test API Endpoints

```bash
# Health check
curl http://localhost:8080/api/status

# Should return JSON with status information
```

### 5. Test RAG Functionality

The RAG indexing should start automatically. Check logs for:

```
RAG indexing cycle started
Successfully inserted X new chunks/embeddings
```

## Troubleshooting

### Connection Issues

If you see connection errors:

1. Check that PostgreSQL is healthy:
   ```bash
   docker-compose ps postgres
   ```

2. Check environment variables:
   ```bash
   docker-compose exec agent-mcp env | grep DB_
   ```

3. Test connection manually:
   ```bash
   docker-compose exec agent-mcp python3 -c "from agent_mcp.db import get_db_connection; conn = get_db_connection(); print('Connected!')"
   ```

### Schema Issues

If tables are missing:

1. Check initialization logs:
   ```bash
   docker-compose logs agent-mcp | grep -i schema
   ```

2. Manually initialize:
   ```bash
   docker-compose exec agent-mcp python3 -c "from agent_mcp.db.postgres_schema import init_database; init_database()"
   ```

### pgvector Issues

If pgvector is not working:

1. Check if extension is installed:
   ```bash
   docker-compose exec postgres psql -U agent_mcp -d agent_mcp -c "\dx vector"
   ```

2. Install manually if needed:
   ```bash
   docker-compose exec postgres psql -U agent_mcp -d agent_mcp -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

## Integration Testing

To test integration with your project:

1. Add Agent-MCP to your project's `docker-compose.yml` (see `INTEGRATION_EXAMPLE.yml`)

2. Start all services:
   ```bash
   docker-compose up -d
   ```

3. Verify Agent-MCP is accessible:
   ```bash
   curl http://localhost:8080/api/status
   ```

4. Check that databases are isolated:
   - Agent-MCP uses its own PostgreSQL instance
   - Your Supabase database is separate
   - No conflicts on ports or data
