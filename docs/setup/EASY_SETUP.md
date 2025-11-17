# Easy Setup Guide

Agent-MCP now includes **interactive setup tools** that make configuration simple and automatic.

## One-Command Setup (Recommended)

### Option 1: Interactive Setup Script (Bash)

```bash
# Run the interactive setup script
./scripts/setup.sh
```

This script will:
- ✅ Check all prerequisites (Docker, Docker Compose)
- ✅ Detect available AI providers (OpenAI or Ollama)
- ✅ Auto-configure Ollama if detected and running
- ✅ Prompt for any missing configuration
- ✅ Create `.env` file automatically
- ✅ Start services with Docker Compose
- ✅ Verify everything is working

**Example output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agent-MCP Setup Wizard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Checking Prerequisites
✓ Docker is installed (Docker version 24.0.0)
✓ Docker daemon is running
✓ Docker Compose is available

Step 2: Choose AI Provider
✓ Ollama is installed and running
  Detected models: nomic-embed-text, llama3.2
Choose provider (1 or 2) [1]: 2

Step 3: Database Configuration
Database password [agent_mcp_password]: 
Agent-MCP port [8080]: 
PostgreSQL port (host) [5433]: 

Step 4: Creating Configuration
✓ Configuration saved to .env

Step 5: Starting Services
✓ Services started successfully
✓ Agent-MCP is running on http://localhost:8080
✓ PostgreSQL is healthy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Setup Complete! 🎉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Option 2: Interactive Setup Command (Python CLI)

```bash
# Install Agent-MCP first
uv pip install -e .

# Run interactive setup
uv run -m agent_mcp.cli setup
```

This Python command provides the same interactive experience with automatic detection.

### Option 3: Non-Interactive Setup (CI/CD)

```bash
# For automation, use non-interactive mode with defaults
uv run -m agent_mcp.cli setup \
  --provider ollama \
  --non-interactive \
  --db-password my-secure-password
```

## Quick Setup Commands

### Detect and Configure Everything Automatically

```bash
# Auto-detect and configure (interactive)
./scripts/setup.sh

# Or with Python CLI
uv run -m agent_mcp.cli setup --provider auto
```

### Check Your Setup

After setup, verify everything is working:

```bash
# Run diagnostics
uv run -m agent_mcp.cli doctor

# Check specific components
uv run -m agent_mcp.cli doctor --check-ollama
uv run -m agent_mcp.cli doctor --check-openai
uv run -m agent_mcp.cli doctor --check-services
```

**Example output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agent-MCP Doctor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Docker:
  ✓ Installed: Docker version 24.0.0
  ✓ Daemon is running
  ✓ Docker Compose available: docker compose

Ollama:
  ✓ Installed
  ✓ Service is running
  ✓ Models detected:
    • Embedding: nomic-embed-text
    • Chat: llama3.2

OpenAI:
  ✗ API key not found

Services:
  ✓ Agent-MCP is running on port 8080
  ✓ PostgreSQL is running

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found 1 issue(s):
  • OpenAI API key not found

Run 'agent-mcp setup' to configure Agent-MCP
```

## What Gets Configured Automatically

### ✅ Automatic Detection

The setup tools automatically detect:

1. **Docker & Docker Compose** - Checks if installed and running
2. **Ollama Installation** - Detects if Ollama is installed
3. **Ollama Service** - Checks if Ollama is running
4. **Ollama Models** - Lists available models and suggests defaults
5. **OpenAI API Key** - Checks for existing keys in `.env` or environment
6. **Service Status** - Verifies Agent-MCP and PostgreSQL are running

### ✅ Smart Defaults

- **Ports**: 8080 for Agent-MCP, 5433 for PostgreSQL (avoids conflicts)
- **Database Password**: Generates secure default
- **Ollama Models**: Auto-detects best models (nomic-embed-text, llama3.2)
- **Network Configuration**: Automatically configures `host.docker.internal` for your OS

### ✅ Platform-Specific Configuration

The setup automatically handles:

- **macOS/Windows**: Uses `host.docker.internal` for Ollama
- **Linux**: Configures `host.docker.internal` via Docker Compose `extra_hosts`
- **Docker Desktop vs Engine**: Detects and configures appropriately

## Common Setup Scenarios

### Scenario 1: New User with Ollama

```bash
# 1. Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama
ollama serve

# 3. Pull models (in another terminal)
ollama pull nomic-embed-text
ollama pull llama3.2

# 4. Run setup script
./scripts/setup.sh
# Choose option 2 (Ollama) when prompted

# Done! Agent-MCP is now configured and running.
```

### Scenario 2: New User with OpenAI

```bash
# 1. Get OpenAI API key from https://platform.openai.com/api-keys

# 2. Run setup script
./scripts/setup.sh
# Choose option 1 (OpenAI) when prompted
# Enter your API key when asked

# Done! Agent-MCP is now configured and running.
```

### Scenario 3: Existing User Updating Configuration

```bash
# 1. Check current setup
uv run -m agent_mcp.cli doctor

# 2. Run setup to update configuration
./scripts/setup.sh
# Script will detect existing .env and ask if you want to update it

# Done! Configuration updated.
```

## Troubleshooting Setup Issues

### Setup Script Can't Find Docker

```bash
# Check if Docker is installed
docker --version

# Check if Docker daemon is running
docker info

# On macOS/Windows, ensure Docker Desktop is running
# On Linux, ensure Docker service is running:
sudo systemctl status docker
```

### Setup Script Can't Connect to Ollama

```bash
# Check if Ollama is installed
ollama --version

# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve

# The setup script will wait for Ollama if you choose to wait
```

### Services Won't Start

```bash
# Check Docker Compose logs
docker-compose logs

# Check if ports are already in use
lsof -i :8080  # macOS/Linux
netstat -an | grep 8080  # Linux

# Try different ports
./scripts/setup.sh
# When prompted, enter different ports
```

## Next Steps After Setup

1. **Configure MCP Client**: 
   - Use `uv run -m agent_mcp.cli mcp-setup show-config` to see configuration
   - Use `uv run -m agent_mcp.cli mcp-setup install-config` to auto-install

2. **Start Dashboard**:
   ```bash
   cd agent_mcp/dashboard
   npm install
   npm run dev
   ```

3. **Test the API**:
   ```bash
   curl http://localhost:8080/api/status
   ```

4. **Read Documentation**:
   - [Quick Start Guide](./QUICK_START.md)
   - [Configuration Guide](./CONFIGURATION.md)
   - [Ollama Setup](./OLLAMA_SETUP.md)

## Manual Setup (Advanced Users)

If you prefer manual setup, see:
- [Quick Start Guide](./QUICK_START.md) for step-by-step manual setup
- [Configuration Guide](./CONFIGURATION.md) for all configuration options

## Getting Help

- **Run diagnostics**: `uv run -m agent_mcp.cli doctor`
- **Check logs**: `docker-compose logs -f agent-mcp`
- **Join Discord**: [Get help from the community](https://discord.gg/7Jm7nrhjGn)
- **GitHub Issues**: [Report bugs or ask questions](https://github.com/rinadelph/Agent-MCP/issues)

