# Agent-MCP Setup Guide

Complete setup guide for Agent-MCP multi-agent orchestration system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Installation Methods](#installation-methods)
4. [Configuration](#configuration)
5. [First Run](#first-run)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

- **Python 3.10+** - Check with `python3 --version`
- **Node.js 18+** - Check with `node --version`
- **PostgreSQL 14+** - For database storage
- **OpenAI API Key** - For embeddings and LLM features

### Optional

- **Docker & Docker Compose** - For containerized deployment
- **Git** - For cloning the repository

## Quick Start

### One-Command Setup (Recommended)

```bash
./scripts/setup.sh
```

This script will:
- Check prerequisites
- Install Python dependencies
- Set up PostgreSQL database
- Configure environment variables
- Run verification checks

### Manual Setup

See [Installation Methods](#installation-methods) below for detailed steps.

## Installation Methods

### Method 1: Using npm Package (Recommended for Users)

```bash
# Install globally
npm install -g @rinadelph/agent-mcp

# Or install locally in your project
npm install @rinadelph/agent-mcp

# Run the setup
agent-mcp setup
```

### Method 2: From Source (For Developers)

```bash
# Clone the repository
git clone https://github.com/rinadelph/Agent-MCP.git
cd Agent-MCP

# Install Python dependencies
uv sync

# Install Node.js dependencies (for dashboard)
cd agent_mcp/dashboard
npm install
cd ../..

# Run setup script
./scripts/setup.sh
```

### Method 3: Docker Compose (For Production)

```bash
# Clone repository
git clone https://github.com/rinadelph/Agent-MCP.git
cd Agent-MCP

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-api-key-here

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agent_mcp
DB_USER=agent_mcp
DB_PASSWORD=your-password

# Connection Pool Settings
DB_POOL_MIN=1
DB_POOL_MAX=10

# Server Configuration
MCP_SERVER_PORT=8080
MCP_DEBUG=false

# Security Settings
AGENT_MCP_SECURITY_ENABLED=true
AGENT_MCP_SCAN_TOOL_SCHEMAS=true
AGENT_MCP_SCAN_TOOL_RESPONSES=true
AGENT_MCP_SANITIZATION_MODE=remove
```

### PostgreSQL Setup

1. **Install PostgreSQL** (if not already installed):
   ```bash
   # macOS
   brew install postgresql@14
   
   # Ubuntu/Debian
   sudo apt-get install postgresql-14
   
   # Or use Docker
   docker run -d --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:14
   ```

2. **Create Database and User**:
   ```sql
   CREATE DATABASE agent_mcp;
   CREATE USER agent_mcp WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE agent_mcp TO agent_mcp;
   ```

3. **Enable pgvector Extension**:
   ```sql
   \c agent_mcp
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

## First Run

### 1. Start the Server

```bash
# Using uv
uv run agent-mcp server --project-dir .

# Or using Python directly
python -m agent_mcp.cli server --project-dir .
```

### 2. Access the Dashboard

Open your browser to:
- **Dashboard**: http://localhost:3847
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

### 3. Get Admin Token

The admin token is displayed in the server logs on startup. You can also retrieve it:

```bash
# From logs
grep "Admin token" mcp_server.log

# Or via API (if server is running)
curl http://localhost:8080/api/status
```

## Verification

### Run Verification Script

```bash
python scripts/verify_setup.py
```

This will check:
- ✅ Python version
- ✅ Node.js version
- ✅ PostgreSQL connection
- ✅ Database schema
- ✅ OpenAI API key
- ✅ Required dependencies
- ✅ Server health

### Manual Verification

1. **Check Server Health**:
   ```bash
   curl http://localhost:8080/health
   ```

2. **Check Database Connection**:
   ```bash
   psql -h localhost -U agent_mcp -d agent_mcp -c "SELECT 1;"
   ```

3. **Test API Endpoints**:
   ```bash
   # List tasks
   curl http://localhost:8080/api/tasks
   
   # Get metrics
   curl http://localhost:8080/metrics
   ```

## Troubleshooting

### Common Issues

#### 1. PostgreSQL Connection Failed

**Error**: `Failed to connect to PostgreSQL`

**Solutions**:
- Verify PostgreSQL is running: `pg_isready` or `docker ps`
- Check connection settings in `.env`
- Verify database and user exist
- Check firewall settings

#### 2. OpenAI API Key Invalid

**Error**: `OpenAI client failed to initialize`

**Solutions**:
- Verify API key in `.env` file
- Check API key has sufficient credits
- Verify network connectivity to OpenAI

#### 3. Port Already in Use

**Error**: `Address already in use`

**Solutions**:
- Change port in `.env`: `MCP_SERVER_PORT=8081`
- Or stop the process using the port:
  ```bash
  # Find process
  lsof -i :8080
  # Kill process
  kill -9 <PID>
  ```

#### 4. Database Schema Errors

**Error**: `Failed to initialize database schema`

**Solutions**:
- Run schema migration manually:
  ```python
  from agent_mcp.db.postgres_schema import init_database
  init_database()
  ```
- Check database permissions
- Verify pgvector extension is installed

#### 5. Module Not Found

**Error**: `ModuleNotFoundError`

**Solutions**:
- Reinstall dependencies: `uv sync`
- Verify virtual environment is activated
- Check Python path

### Getting Help

- **GitHub Issues**: https://github.com/rinadelph/Agent-MCP/issues
- **Documentation**: https://github.com/rinadelph/Agent-MCP/tree/main/docs
- **Logs**: Check `mcp_server.log` for detailed error messages

## Next Steps

After setup, explore:

1. **Create Your First Agent**: Use the dashboard or API
2. **Add Tasks**: Create and assign tasks to agents
3. **Configure RAG**: Index your project for better context
4. **Set Up MCP Client**: Connect Cursor, Claude Desktop, or Windsurf
5. **Review Security**: Configure security scanning and monitoring

## Advanced Configuration

See [CONFIGURATION.md](../CONFIGURATION.md) for:
- Custom embedding models
- Advanced security settings
- Performance tuning
- Multi-project setup
- Production deployment

