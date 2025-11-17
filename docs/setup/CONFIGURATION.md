# Configuration Guide

Complete reference for configuring Agent-MCP.

## Configuration Methods

Agent-MCP can be configured through:

1. **Environment Variables** (`.env` file or system environment)
2. **Command-line Arguments** (CLI flags)
3. **Configuration Files** (`.agent-mcp.json` in project root)

Priority order: CLI arguments > Environment variables > Config file > Defaults

---

## Environment Variables

### Required

#### `OPENAI_API_KEY`
- **Description:** Your OpenAI API key for embeddings and chat completions
- **Example:** `OPENAI_API_KEY=sk-proj-...`
- **Required:** Yes
- **Get it:** [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Server Configuration

#### `AGENT_MCP_PORT`
- **Description:** Port for the MCP server
- **Default:** `8080`
- **Example:** `AGENT_MCP_PORT=8080`

#### `AGENT_MCP_HOST`
- **Description:** Host address to bind to
- **Default:** `0.0.0.0` (all interfaces)
- **Example:** `AGENT_MCP_HOST=localhost` (local only)

#### `AGENT_MCP_PROJECT_DIR`
- **Description:** Default project directory path
- **Default:** Current working directory
- **Example:** `AGENT_MCP_PROJECT_DIR=/path/to/project`

#### `MCP_DEBUG`
- **Description:** Enable debug logging
- **Default:** `false`
- **Example:** `MCP_DEBUG=true`

### Database Configuration

#### `DATABASE_URL`
- **Description:** PostgreSQL connection string (optional, uses SQLite by default)
- **Format:** `postgresql://user:password@host:port/database`
- **Example:** `DATABASE_URL=postgresql://user:pass@localhost:5432/agent_mcp`

#### `DB_FILE_NAME`
- **Description:** SQLite database filename (if using SQLite)
- **Default:** `mcp_state.db`
- **Example:** `DB_FILE_NAME=my_project.db`

### Security Configuration

#### `AGENT_MCP_SECURITY_ENABLED`
- **Description:** Enable security scanning for prompt injection
- **Default:** `true`
- **Example:** `AGENT_MCP_SECURITY_ENABLED=true`

#### `AGENT_MCP_SCAN_TOOL_SCHEMAS`
- **Description:** Scan tool schemas for malicious content
- **Default:** `true`
- **Example:** `AGENT_MCP_SCAN_TOOL_SCHEMAS=true`

#### `AGENT_MCP_SCAN_TOOL_RESPONSES`
- **Description:** Scan tool responses for injected content
- **Default:** `true`
- **Example:** `AGENT_MCP_SCAN_TOOL_RESPONSES=true`

#### `AGENT_MCP_SANITIZATION_MODE`
- **Description:** How to handle detected threats
- **Options:** `remove`, `neutralize`, `block`
- **Default:** `remove`
- **Example:** `AGENT_MCP_SANITIZATION_MODE=neutralize`

#### `AGENT_MCP_SECURITY_ALERT_WEBHOOK`
- **Description:** Webhook URL for security alerts
- **Default:** None
- **Example:** `AGENT_MCP_SECURITY_ALERT_WEBHOOK=https://your-alerts.com/webhook`

#### `AGENT_MCP_USE_ML_DETECTION`
- **Description:** Use ML-based threat detection (experimental)
- **Default:** `false`
- **Example:** `AGENT_MCP_USE_ML_DETECTION=false`

### RAG Configuration

#### `ENABLE_TASK_PLACEMENT_RAG`
- **Description:** Enable RAG for task placement decisions
- **Default:** `true`
- **Example:** `ENABLE_TASK_PLACEMENT_RAG=true`

#### `TASK_DUPLICATION_THRESHOLD`
- **Description:** Similarity threshold for detecting duplicate tasks (0.0-1.0)
- **Default:** `0.8`
- **Example:** `TASK_DUPLICATION_THRESHOLD=0.8`

#### `ALLOW_RAG_OVERRIDE`
- **Description:** Allow manual override of RAG task placement
- **Default:** `true`
- **Example:** `ALLOW_RAG_OVERRIDE=true`

#### `TASK_PLACEMENT_RAG_TIMEOUT`
- **Description:** Timeout for RAG queries in seconds
- **Default:** `5`
- **Example:** `TASK_PLACEMENT_RAG_TIMEOUT=5`

### OpenAI Model Configuration

#### `ADVANCED_EMBEDDINGS`
- **Description:** Use advanced embedding model (higher dimension)
- **Default:** `false`
- **Example:** `ADVANCED_EMBEDDINGS=true`

#### `DISABLE_AUTO_INDEXING`
- **Description:** Disable automatic RAG indexing
- **Default:** `false`
- **Example:** `DISABLE_AUTO_INDEXING=false`

---

## Configuration File

Create `.agent-mcp.json` in your project root:

```json
{
  "project_name": "my-project",
  "server": {
    "port": 8080,
    "host": "0.0.0.0"
  },
  "agents": {
    "max_workers": 5,
    "default_mode": "worker"
  },
  "rag": {
    "enabled": true,
    "embedding_model": "text-embedding-3-large",
    "embedding_dimension": 1536
  },
  "dashboard": {
    "port": 3000,
    "host": "localhost"
  },
  "security": {
    "enabled": true,
    "scan_tool_schemas": true,
    "scan_tool_responses": true,
    "sanitization_mode": "remove",
    "alert_webhook": null
  },
  "database": {
    "type": "sqlite",
    "path": ".agent/mcp_state.db"
  }
}
```

---

## Command-Line Arguments

### Server Options

```bash
uv run -m agent_mcp.cli --port 8080 --project-dir /path/to/project
```

#### `--port`
- **Description:** Server port
- **Default:** `8080`
- **Example:** `--port 8080`

#### `--project-dir`
- **Description:** Project directory path
- **Required:** Yes
- **Example:** `--project-dir /path/to/project`

#### `--host`
- **Description:** Host address
- **Default:** `0.0.0.0`
- **Example:** `--host localhost`

#### `--debug`
- **Description:** Enable debug mode
- **Default:** `false`
- **Example:** `--debug`

---

## Production Configuration

### Recommended Settings

```bash
# .env for production
OPENAI_API_KEY=sk-proj-...
AGENT_MCP_PORT=8080
AGENT_MCP_HOST=0.0.0.0
MCP_DEBUG=false

# Security (strict)
AGENT_MCP_SECURITY_ENABLED=true
AGENT_MCP_SCAN_TOOL_SCHEMAS=true
AGENT_MCP_SCAN_TOOL_RESPONSES=true
AGENT_MCP_SANITIZATION_MODE=block
AGENT_MCP_SECURITY_ALERT_WEBHOOK=https://your-alerts.com/webhook

# Database (PostgreSQL recommended)
DATABASE_URL=postgresql://user:password@db-host:5432/agent_mcp

# Performance
ADVANCED_EMBEDDINGS=true
TASK_PLACEMENT_RAG_TIMEOUT=10
```

### Docker Configuration

See [Docker Setup Guide](./DOCKER.md) for containerized deployment.

### Cloud Deployment

#### AWS (EC2/ECS)
- Use environment variables in task definition
- Store secrets in AWS Secrets Manager
- Use RDS for PostgreSQL

#### GCP (Cloud Run)
- Use environment variables in service config
- Store secrets in Secret Manager
- Use Cloud SQL for PostgreSQL

#### Azure (Container Instances)
- Use environment variables in container group
- Store secrets in Key Vault
- Use Azure Database for PostgreSQL

---

## Security Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use strong API keys** - Rotate regularly
3. **Enable security scanning** - Keep defaults enabled
4. **Monitor alerts** - Set up webhook for production
5. **Use PostgreSQL** - More secure than SQLite for production
6. **Restrict network access** - Use firewall rules
7. **Enable HTTPS** - Use reverse proxy (nginx/traefik)
8. **Regular updates** - Keep dependencies updated

---

## Performance Tuning

### For Large Projects

```bash
# Increase embedding dimension for better accuracy
ADVANCED_EMBEDDINGS=true

# Increase RAG timeout for complex queries
TASK_PLACEMENT_RAG_TIMEOUT=15

# Use PostgreSQL for better performance
DATABASE_URL=postgresql://...
```

### For High Throughput

```bash
# Reduce RAG timeout for faster responses
TASK_PLACEMENT_RAG_TIMEOUT=3

# Disable auto-indexing if not needed
DISABLE_AUTO_INDEXING=true

# Use simpler embeddings
ADVANCED_EMBEDDINGS=false
```

---

## Troubleshooting Configuration

### Check Current Configuration

```bash
# Print all environment variables
env | grep AGENT_MCP

# Check config file
cat .agent-mcp.json

# Verify in Python
python -c "from agent_mcp.core.config import *; print(f'Port: {AGENT_MCP_PORT}')"
```

### Common Issues

1. **Config not loading:** Restart server after changes
2. **Wrong values:** Check for typos in variable names
3. **Conflicts:** CLI args override env vars
4. **Missing values:** Check defaults in config.py

---

## Advanced Configuration

### Custom Security Patterns

Add custom patterns to `agent_mcp/security/patterns.py`:

```python
CUSTOM_PATTERNS = [
    (r'your-custom-pattern', 'CUSTOM_THREAT_TYPE'),
]
```

### Custom Models

Override model selection in `agent_mcp/core/config.py`:

```python
CHAT_MODEL = "gpt-4-turbo"
EMBEDDING_MODEL = "text-embedding-3-large"
```

---

For more information, see:
- [Setup Guide](./README.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Main Documentation](../)

