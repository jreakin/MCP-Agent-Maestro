# Integrating Agent-MCP into Your Project

## Quick Answers to Your Questions

### 1. **Isolation: YES ✅**

The Agent-MCP PostgreSQL database is **completely isolated** from your Supabase database:

- **Different containers**: `agent-mcp-postgres` vs your Supabase instance
- **Different volumes**: `agent-mcp-postgres-data` vs Supabase's data
- **Different networks**: Can be on same Docker network but separate services
- **No connection**: Agent-MCP never touches your Supabase database

### 2. **Port Configuration: Flexible ✅**

You have full control over port mapping:

```yaml
ports:
  - "8080:3000"  # Host:Container
```

- **Inside container**: Agent-MCP runs on port 3000 (or 8080 if you change it)
- **From host**: Access via `localhost:8080` (or any port you choose)
- **Your app**: Still uses port 8000, no conflicts

## Integration Steps

### Step 1: Add to your `.env` file

```bash
# Agent-MCP Configuration
OPENAI_API_KEY=your_key_here
AGENT_MCP_DB_PASSWORD=secure_password_here
```

### Step 2: Add services to your `docker-compose.yml`

Copy the Agent-MCP services from `docs/examples/INTEGRATION_EXAMPLE.yml` into your existing docker-compose.yml.

### Step 3: Start everything

```bash
docker-compose up -d
```

### Step 4: Access Agent-MCP

- **API**: http://localhost:8080
- **SSE Endpoint**: http://localhost:8080/sse
- **Dashboard**: Run separately or add to docker-compose

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│  Your Project (vep-phone-bank-app)      │
│                                         │
│  ┌─────────────┐  ┌──────────────┐    │
│  │   App       │  │   Redis      │    │
│  │  :8000      │  │  :6379       │    │
│  └──────┬──────┘  └──────────────┘    │
│         │                              │
│         │ Connects to                  │
│         ▼                              │
│  ┌──────────────────────────────┐     │
│  │  Supabase (on host machine)  │     │
│  │  :54322                      │     │
│  └──────────────────────────────┘     │
│                                         │
│  ┌──────────────────────────────┐     │
│  │  Agent-MCP Services          │     │
│  │                              │     │
│  │  ┌──────────────┐            │     │
│  │  │ Agent-MCP    │            │     │
│  │  │ :3000 (int)  │            │     │
│  │  │ :8080 (host) │            │     │
│  │  └──────┬───────┘            │     │
│  │         │                    │     │
│  │         │ Connects to        │     │
│  │         ▼                    │     │
│  │  ┌──────────────┐            │     │
│  │  │ PostgreSQL   │            │     │
│  │  │ :5432        │            │     │
│  │  │ (ISOLATED)   │            │     │
│  │  └──────────────┘            │     │
│  └──────────────────────────────┘     │
└─────────────────────────────────────────┘
```

## Key Points

1. **Complete Isolation**: Agent-MCP's PostgreSQL never touches Supabase
2. **Port Flexibility**: Map container port 3000 to any host port (8080, 3000, etc.)
3. **Same Network**: Services can communicate via Docker service names
4. **Separate Volumes**: Each database has its own persistent storage
5. **Easy Cleanup**: `docker-compose down -v` removes Agent-MCP data, leaves Supabase untouched

## Port Options

### Option 1: Use 8080 on host (as you suggested)
```yaml
ports:
  - "8080:3000"  # Host:Container
```
Access: `http://localhost:8080`

### Option 2: Keep 3000 on host
```yaml
ports:
  - "3000:3000"
```
Access: `http://localhost:3000`

### Option 3: Use different port
```yaml
ports:
  - "9000:3000"  # Any port you want
```
Access: `http://localhost:9000`

## Connecting from Your App

If your app needs to call Agent-MCP:

```python
# From within your app container
AGENT_MCP_URL = "http://agent-mcp:3000"  # Docker service name

# From host machine
AGENT_MCP_URL = "http://localhost:8080"  # Host port
```

## Troubleshooting

### Check if services are running
```bash
docker-compose ps
```

### View Agent-MCP logs
```bash
docker-compose logs -f agent-mcp
```

### Access Agent-MCP PostgreSQL
```bash
docker-compose exec agent-mcp-postgres psql -U agent_mcp -d agent_mcp
```

### Verify isolation
```bash
# List all databases in Agent-MCP PostgreSQL
docker-compose exec agent-mcp-postgres psql -U agent_mcp -d agent_mcp -c "\l"

# Should only show agent_mcp database, not your Supabase databases
```
