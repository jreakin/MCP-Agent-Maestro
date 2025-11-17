# Data Persistence in Agent-MCP

## Overview

Agent-MCP uses **Docker named volumes** to persist all database data across container restarts. Your context, agents, tasks, RAG embeddings, and all other data are automatically saved and restored.

## How It Works

### PostgreSQL Data Volume

In `docker-compose.yml`, the PostgreSQL service uses a named volume:

```yaml
postgres:
  volumes:
    - postgres-data:/var/lib/postgresql/data  # Named volume persists data
```

The volume `postgres-data` is defined at the bottom:

```yaml
volumes:
  postgres-data:
    driver: local  # Stored on your local machine
```

### What Gets Persisted

✅ **All database data persists**, including:
- **Agents**: All agent records, tokens, capabilities, status
- **Tasks**: All tasks, assignments, dependencies, notes
- **Project Context**: All context keys and values
- **RAG Data**: All indexed chunks, embeddings, metadata
- **Agent Messages**: Inter-agent communication history
- **File Metadata**: File tracking and change detection
- **Prompt Book**: All saved prompt templates
- **Security Logs**: Security alerts and monitoring data

## Container Lifecycle

### Normal Restart (Data Preserved)

```bash
# Stop containers (data stays in volume)
docker-compose stop

# Start containers (data is restored)
docker-compose start

# Or restart
docker-compose restart
```

**Result**: ✅ All your data is still there!

### Full Rebuild (Data Preserved)

```bash
# Rebuild and restart (data stays in volume)
docker-compose up -d --build
```

**Result**: ✅ All your data is still there!

### Remove Containers (Data Preserved)

```bash
# Remove containers but keep volumes
docker-compose down

# Start again
docker-compose up -d
```

**Result**: ✅ All your data is still there!

### Complete Reset (Data Deleted)

```bash
# ⚠️ WARNING: This deletes ALL data!
docker-compose down -v

# Start fresh
docker-compose up -d
```

**Result**: ❌ All data is deleted - fresh start

## Volume Location

Docker stores named volumes on your system:

- **Linux**: `/var/lib/docker/volumes/agent-mcp-fork_postgres-data/_data`
- **macOS/Windows**: Managed by Docker Desktop in a VM

### View Volume Info

```bash
# List all volumes
docker volume ls

# Inspect the volume
docker volume inspect agent-mcp-fork_postgres-data

# See volume size
docker system df -v
```

## Backup & Restore

### Manual Backup

```bash
# Create a backup
docker-compose exec postgres pg_dump -U agent_mcp agent_mcp > backup_$(date +%Y%m%d_%H%M%S).sql

# Or backup the entire volume
docker run --rm -v agent-mcp-fork_postgres-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore from Backup

```bash
# Restore from SQL dump
docker-compose exec -T postgres psql -U agent_mcp agent_mcp < backup_20240101_120000.sql

# Or restore from volume backup
docker run --rm -v agent-mcp-fork_postgres-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup-20240101.tar.gz -C /
```

### Automated Backups

You can set up automated backups using a cron job or scheduled task:

```bash
#!/bin/bash
# backup.sh - Run daily via cron
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
docker-compose exec -T postgres pg_dump -U agent_mcp agent_mcp | \
  gzip > "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz"

# Keep only last 7 days
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete
```

## Migration Between Systems

### Export Data

```bash
# Export to SQL file
docker-compose exec postgres pg_dump -U agent_mcp agent_mcp > agent_mcp_export.sql
```

### Import on New System

```bash
# Copy export file to new system, then:
docker-compose up -d postgres
# Wait for postgres to be ready
docker-compose exec -T postgres psql -U agent_mcp agent_mcp < agent_mcp_export.sql
```

## Project Data Directory

In addition to the database, the `project-data` directory is also persisted:

```yaml
agent-mcp:
  volumes:
    - ./project-data:/app/project-data  # Mounted from host
```

This directory contains:
- Agent working directories
- Temporary files
- Project-specific data

**Note**: This is a bind mount (not a volume), so it's stored in `./project-data` on your host machine.

## Troubleshooting

### Data Not Persisting?

1. **Check volume exists:**
   ```bash
   docker volume ls | grep postgres-data
   ```

2. **Check volume is mounted:**
   ```bash
   docker-compose exec postgres df -h /var/lib/postgresql/data
   ```

3. **Verify data is there:**
   ```bash
   docker-compose exec postgres psql -U agent_mcp -d agent_mcp -c "SELECT COUNT(*) FROM agents;"
   ```

### Volume Full?

```bash
# Check volume size
docker system df -v

# Clean up unused volumes (be careful!)
docker volume prune
```

### Reset Specific Table

If you need to reset just one table while keeping the rest:

```bash
docker-compose exec postgres psql -U agent_mcp -d agent_mcp -c "TRUNCATE TABLE tasks CASCADE;"
```

## Best Practices

1. **Regular Backups**: Set up automated daily backups
2. **Version Control**: Don't commit the `project-data` directory
3. **Monitor Size**: Keep an eye on database growth
4. **Test Restores**: Periodically test that your backups work
5. **Document Changes**: Note any schema changes for migration

## Summary

✅ **Data persists automatically** - No action needed  
✅ **Survives container restarts** - Your context is always there  
✅ **Survives rebuilds** - Data stays in the volume  
⚠️ **`docker-compose down -v` deletes everything** - Use with caution  
💾 **Backup regularly** - Especially before major changes

