# MCP Agent Maestro - Production Deployment Guide

## Overview

This guide covers deploying MCP Agent Maestro in production environments. The Maestro system can be deployed using Docker Compose (recommended) or as separate services.

## Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- PostgreSQL 14+ with pgvector extension
- OpenAI API key (or Ollama for local embeddings)
- Minimum 4GB RAM (8GB+ recommended)
- Minimum 2 CPU cores (4+ recommended)

## Docker Compose Deployment (Recommended)

### Quick Start

1. **Clone the repository**:
```bash
git clone https://github.com/jreakin/mcp-agent-maestro.git
cd mcp-agent-maestro
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services**:
```bash
docker-compose up -d
```

4. **Verify deployment**:
```bash
curl http://localhost:8080/health
```

### Environment Configuration

Key environment variables for production:

```bash
# Database
AGENT_MCP_DB_HOST=postgres
AGENT_MCP_DB_PORT=5432
AGENT_MCP_DB_NAME=agent_mcp
AGENT_MCP_DB_USER=agent_mcp
AGENT_MCP_DB_PASSWORD=<secure_password>

# OpenAI (or use Ollama)
AGENT_MCP_OPENAI_API_KEY=sk-...
EMBEDDING_PROVIDER=openai

# Or Ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434

# Security
AGENT_MCP_SECURITY_ENABLED=true
AGENT_MCP_SECURITY_POISON_DETECTION_ENABLED=true

# Logging
AGENT_MCP_LOG_LEVEL=INFO
AGENT_MCP_MCP_DEBUG=false
```

## Production Best Practices

### Database Configuration

1. **Use managed PostgreSQL** (AWS RDS, Google Cloud SQL, Azure Database):
   - Enable pgvector extension
   - Configure connection pooling
   - Set up automated backups
   - Enable monitoring

2. **Database Connection Pooling**:
```bash
AGENT_MCP_DB_POOL_MIN=5
AGENT_MCP_DB_POOL_MAX=20
AGENT_MCP_DB_MAX_OVERFLOW=10
```

### Security Configuration

1. **Enable all security features**:
```bash
AGENT_MCP_SECURITY_ENABLED=true
AGENT_MCP_SECURITY_POISON_DETECTION_ENABLED=true
AGENT_MCP_SECURITY_SCAN_TOOL_SCHEMAS=true
AGENT_MCP_SECURITY_SCAN_TOOL_RESPONSES=true
```

2. **Configure security webhook** (optional):
```bash
AGENT_MCP_SECURITY_ALERT_WEBHOOK=https://your-webhook-url
```

3. **Use secure authentication**:
   - Generate strong admin tokens
   - Rotate tokens regularly
   - Use environment variables for secrets

### Performance Optimization

1. **Agent Limits**:
```bash
AGENT_MCP_MAX_WORKERS=10  # Adjust based on resources
AGENT_MCP_AGENT_TIMEOUT=3600  # 1 hour timeout
```

2. **RAG Configuration**:
```bash
AGENT_MCP_RAG_ENABLED=true
AGENT_MCP_RAG_MAX_RESULTS=13  # Balance between relevance and performance
```

3. **Embedding Mode**:
   - Simple mode (1536 dimensions): Better performance, lower cost
   - Advanced mode (3072 dimensions): Better accuracy, higher cost

### Monitoring & Logging

1. **Health Checks**:
   - Use `/health` endpoint for load balancer checks
   - Use `/health/ready` for Kubernetes readiness probes
   - Use `/health/live` for Kubernetes liveness probes

2. **Metrics**:
   - Use `/metrics` endpoint for Prometheus scraping
   - Monitor agent count, task completion rates
   - Track database connection pool stats

3. **Logging**:
   - Set appropriate log level (`INFO` for production)
   - Configure log aggregation (ELK, Loki, etc.)
   - Enable structured logging with trace IDs

## Kubernetes Deployment

### Deployment Manifest Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-agent-maestro
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-agent-maestro
  template:
    metadata:
      labels:
        app: mcp-agent-maestro
    spec:
      containers:
      - name: backend
        image: mcp-agent-maestro:latest
        ports:
        - containerPort: 8080
        env:
        - name: AGENT_MCP_DB_HOST
          value: "postgres-service"
        - name: AGENT_MCP_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: maestro-secrets
              key: openai-api-key
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
```

## Scaling Considerations

### Horizontal Scaling

- Multiple conductor instances can coordinate
- Use shared PostgreSQL database
- Implement sticky sessions if needed
- Monitor resource usage per instance

### Vertical Scaling

- Increase agent limits based on CPU/RAM
- Adjust database connection pool size
- Tune embedding batch sizes
- Monitor memory usage

## Backup & Recovery

### Database Backups

1. **Automated Backups**:
   - Use PostgreSQL native backup tools
   - Schedule regular backups (daily recommended)
   - Test restore procedures

2. **Knowledge Graph Backup**:
   - Backup `rag_embeddings` table
   - Backup `project_context` table
   - Backup `agents` and `tasks` tables

### Disaster Recovery

1. **Backup Strategy**:
   - Daily full backups
   - Point-in-time recovery capability
   - Off-site backup storage

2. **Recovery Procedures**:
   - Document recovery steps
   - Test recovery regularly
   - Maintain recovery runbooks

## Troubleshooting

### Common Issues

1. **Database Connection Failures**:
   - Check connection pool settings
   - Verify database is accessible
   - Check credentials

2. **Agent Creation Failures**:
   - Check agent limits
   - Verify resources available
   - Check OpenAI API quota

3. **RAG System Issues**:
   - Verify pgvector extension is installed
   - Check embedding service availability
   - Verify rag_embeddings table exists

### Debug Mode

For troubleshooting, enable debug mode:

```bash
AGENT_MCP_MCP_DEBUG=true
AGENT_MCP_LOG_LEVEL=DEBUG
```

**Note**: Disable debug mode in production for performance and security.

## SSL/TLS Configuration

### Reverse Proxy (Nginx)

```nginx
server {
    listen 443 ssl;
    server_name maestro.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Checklist

- [ ] Change default passwords
- [ ] Enable all security features
- [ ] Configure security webhook
- [ ] Use HTTPS/TLS
- [ ] Rotate API keys regularly
- [ ] Limit network access
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Monitor for security alerts

## Performance Monitoring

### Key Metrics

- Agent creation/termination rates
- Task completion times
- Database query performance
- RAG query latency
- Memory usage
- CPU usage
- Request latency

### Alerts

Set up alerts for:
- Health check failures
- High error rates
- Resource exhaustion
- Agent capacity limits
- Database connection pool exhaustion

