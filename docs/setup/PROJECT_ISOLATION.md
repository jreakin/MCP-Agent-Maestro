# Project Isolation in Agent-MCP

## How Project Isolation Works

Agent-MCP provides **complete isolation per project** through Docker-level separation. Each project gets its own:

- ✅ **Separate Docker Compose instance**
- ✅ **Separate PostgreSQL database**
- ✅ **Separate PostgreSQL volume**
- ✅ **Separate container network**

## Current Architecture: One Database Per Project

### How It Works

**Each project runs its own Agent-MCP instance** with a dedicated database:

```
Project A (vep-phone-bank-app)
├── docker-compose.yml
├── agent-mcp container
└── agent-mcp-postgres container
    └── postgres-data volume (isolated)

Project B (another-project)
├── docker-compose.yml  
├── agent-mcp container
└── agent-mcp-postgres container
    └── postgres-data volume (isolated)
```

### Database Schema

The current database schema **does NOT include a `project_id` field**. This means:

- ✅ **One project per database** = Complete isolation (current design)
- ⚠️ **Multiple projects per database** = Data would be shared (not recommended)

## Setting Up Multiple Projects

### Option 1: Separate Docker Compose Per Project (Recommended)

Each project has its own `docker-compose.yml`:

**Project A (`/path/to/project-a/docker-compose.yml`):**
```yaml
services:
  agent-mcp:
    volumes:
      - ./:/app/project-data  # Project A's code
    environment:
      - MCP_PROJECT_DIR=/app/project-data
  
  postgres:
    container_name: project-a-postgres
    volumes:
      - project-a-postgres-data:/var/lib/postgresql/data

volumes:
  project-a-postgres-data:  # Isolated volume for Project A
```

**Project B (`/path/to/project-b/docker-compose.yml`):**
```yaml
services:
  agent-mcp:
    volumes:
      - ./:/app/project-data  # Project B's code
    environment:
      - MCP_PROJECT_DIR=/app/project-data
  
  postgres:
    container_name: project-b-postgres
    volumes:
      - project-b-postgres-data:/var/lib/postgresql/data

volumes:
  project-b-postgres-data:  # Isolated volume for Project B
```

**Result**: ✅ Complete isolation - each project has its own database and data.

### Option 2: Shared Docker Compose (Not Recommended)

If you try to run multiple projects against the same database:

```yaml
# This would share data between projects - NOT recommended
services:
  postgres:
    volumes:
      - shared-postgres-data:/var/lib/postgresql/data  # Shared!
```

**Result**: ⚠️ Projects would share agents, tasks, and context - **not isolated**.

## What Gets Isolated

When each project has its own database, the following are completely isolated:

- ✅ **Agents**: Each project has its own agent fleet
- ✅ **Tasks**: Task lists are separate per project
- ✅ **Project Context**: Context keys are project-specific
- ✅ **RAG Data**: Embeddings and indexed content are separate
- ✅ **Agent Messages**: Communication history is isolated
- ✅ **File Metadata**: File tracking is per-project
- ✅ **Prompt Book**: Saved prompts are project-specific
- ✅ **Security Logs**: Security events are isolated

## Integration Example

See `INTEGRATION_EXAMPLE.yml` for how to add Agent-MCP to an existing project:

```yaml
# In your project's docker-compose.yml
services:
  agent-mcp:
    volumes:
      - ./:/app/project-data  # Your project directory
    environment:
      - MCP_PROJECT_DIR=/app/project-data
  
  agent-mcp-postgres:
    container_name: your-project-postgres
    volumes:
      - your-project-postgres-data:/var/lib/postgresql/data

volumes:
  your-project-postgres-data:  # Isolated to this project
```

## Verifying Isolation

### Check Volume Isolation

```bash
# List all volumes
docker volume ls

# You should see separate volumes:
# project-a-postgres-data
# project-b-postgres-data
```

### Check Database Isolation

```bash
# Connect to Project A's database
docker-compose -f /path/to/project-a/docker-compose.yml exec postgres \
  psql -U agent_mcp -d agent_mcp -c "SELECT COUNT(*) FROM agents;"

# Connect to Project B's database  
docker-compose -f /path/to/project-b/docker-compose.yml exec postgres \
  psql -U agent_mcp -d agent_mcp -c "SELECT COUNT(*) FROM agents;"

# These should show different counts
```

## Port Configuration

Each project can use different ports:

**Project A:**
```yaml
ports:
  - "8080:8080"  # Project A on port 8080
```

**Project B:**
```yaml
ports:
  - "8081:8080"  # Project B on port 8081
```

## Best Practices

1. **One docker-compose.yml per project** - Ensures complete isolation
2. **Unique container names** - Use project-specific names
3. **Unique volume names** - Prevents accidental data sharing
4. **Unique ports** - Avoid port conflicts
5. **Separate .env files** - Each project has its own configuration

## Future: Multi-Project Database Support

If you need to support multiple projects in a single database (for centralized management), you would need to:

1. Add `project_id` field to all tables
2. Update all queries to filter by `project_id`
3. Add project management API endpoints
4. Update authentication to include project context

**Current recommendation**: Use separate databases per project (current design) for better isolation and simpler architecture.

## Summary

✅ **Yes, information is isolated per-project**  
✅ **Each project gets its own database and volume**  
✅ **Complete separation of agents, tasks, context, and RAG data**  
✅ **No data sharing between projects**  
✅ **Persistent across container restarts**

The isolation is achieved through **Docker-level separation** (separate containers, volumes, and databases) rather than application-level separation (project_id fields).

