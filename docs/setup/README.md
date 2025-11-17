# Agent-MCP Setup Guide

Welcome to Agent-MCP! This guide will help you get up and running quickly.

## Quick Start (5 minutes)

For experienced users who want to get running fast:

```bash
# 1. Clone the repository
git clone https://github.com/rinadelph/Agent-MCP.git
cd Agent-MCP

# 2. Install dependencies
uv venv && source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key: OPENAI_API_KEY=sk-...

# 4. Start the server
uv run -m agent_mcp.cli --port 8080 --project-dir /path/to/your/project

# 5. Launch dashboard (optional)
cd agent_mcp/dashboard && npm install && npm run dev
```

**Verify:** You should see the admin token in the server output and the dashboard at `http://localhost:3000`.

---

## Full Setup Guide (20 minutes)

### Prerequisites

#### Required
- **Python 3.10+** - [Install Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Install Node.js](https://nodejs.org/)
- **uv package manager** - [Install uv](https://docs.astral.sh/uv/)
- **OpenAI API key** - [Get API key](https://platform.openai.com/api-keys)

#### Optional
- **Docker** - For containerized deployment ([Docker Setup Guide](./DOCKER.md))
- **Git** - For development setup
- **PostgreSQL** - For production use (SQLite is used by default)

#### System Requirements
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 2GB free
- **OS**: macOS, Linux, or Windows with WSL2

### Step-by-Step Installation

#### Step 1: Clone the Repository

```bash
git clone https://github.com/rinadelph/Agent-MCP.git
cd Agent-MCP
```

**Verify:** You should see the project files:
```bash
ls
# Expected output: agent_mcp/ dashboard/ docs/ README.md pyproject.toml ...
```

#### Step 2: Install Python Dependencies

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows

# Install the package
uv pip install -e .
```

**Verify:** Check installation:
```bash
python -c "import agent_mcp; print('✓ Installed')"
```

#### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

**Required variables:**
- `OPENAI_API_KEY=sk-...` - Get from [platform.openai.com](https://platform.openai.com/api-keys)

**Optional variables:**
- `AGENT_MCP_SECURITY_ENABLED=true` - Enable security scanning (default: true)
- `AGENT_MCP_PORT=8080` - Server port (default: 8080)
- `AGENT_MCP_PROJECT_DIR=/path/to/project` - Default project directory

#### Step 4: Install Dashboard Dependencies

```bash
cd agent_mcp/dashboard
npm install
cd ../..
```

**Verify:** Check Node.js installation:
```bash
node --version  # Should be >=18.0.0
npm --version   # Should be >=9.0.0
```

#### Step 5: Start the MCP Server

```bash
# Start the server with your project directory
uv run -m agent_mcp.cli --port 8080 --project-dir /path/to/your/project
```

**Verify:** You should see:
```
🤖 Admin Token: abc123def456...
📡 Server running on http://localhost:8080
```

**Note:** Save the admin token - you'll need it to create agents!

#### Step 6: Launch the Dashboard (Optional but Recommended)

In a new terminal:

```bash
cd agent_mcp/dashboard
npm run dev
```

**Verify:** Open `http://localhost:3000` in your browser. You should see the Agent-MCP dashboard.

---

## Setup Options

### Option A: Development Setup

For contributors and those wanting to modify code:

```bash
# Full git clone with editable install
git clone https://github.com/rinadelph/Agent-MCP.git
cd Agent-MCP
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"  # Includes dev dependencies
```

### Option B: User Setup

For users who want to use Agent-MCP as-is:

```bash
# Using pip (when published)
pip install agent-mcp

# OR using uv
uv pip install agent-mcp
```

### Option C: Docker Setup

For containerized deployment:

See [Docker Setup Guide](./DOCKER.md) for detailed instructions.

```bash
docker-compose up -d
```

### Option D: Cloud Deployment

For production use on cloud platforms:

- **AWS**: Use EC2 with Docker or ECS
- **GCP**: Use Cloud Run or Compute Engine
- **Azure**: Use Container Instances or App Service

See [Configuration Guide](./CONFIGURATION.md) for production settings.

---

## Your First Agent Task

Let's create a simple task to verify everything works:

1. **Start the MCP server:**
   ```bash
   uv run -m agent_mcp.cli --project-dir ./example-project
   ```

2. **In another terminal, start the dashboard:**
   ```bash
   cd agent_mcp/dashboard && npm run dev
   ```

3. **Open http://localhost:3000** in your browser

4. **Create your first task:**
   - Click "New Task"
   - Enter: "Create a hello.py file that prints 'Hello from Agent-MCP!'"
   - Click "Assign to Agent"

5. **Watch the agent work in the dashboard!**

---

## Verification

Run the setup verification script to check your installation:

```bash
python scripts/verify_setup.py
```

This will check:
- ✓ Python version (3.10+)
- ✓ Dependencies installed
- ✓ API keys configured
- ✓ Ports available
- ✓ Database connectivity

---

## Next Steps

- Read the [Configuration Guide](./CONFIGURATION.md) for advanced settings
- Check the [Troubleshooting Guide](./TROUBLESHOOTING.md) if you encounter issues
- Explore the [Getting Started Guide](../getting-started.md) for usage examples
- Join our [Discord Community](https://discord.gg/7Jm7nrhjGn) for support

---

## Troubleshooting

If you encounter issues, see the [Troubleshooting Guide](./TROUBLESHOOTING.md) for common problems and solutions.

Common issues:
- **"Admin token not found"** - Check server startup logs
- **"Port already in use"** - Change port with `--port 8001`
- **"OpenAI API Error"** - Verify API key in `.env` file
- **"Dashboard connection failed"** - Ensure MCP server is running first

---

## Support

- **Documentation**: [docs/](../)
- **Discord**: [Join our community](https://discord.gg/7Jm7nrhjGn)
- **GitHub Issues**: [Report bugs](https://github.com/rinadelph/Agent-MCP/issues)
- **Discussions**: [Ask questions](https://github.com/rinadelph/Agent-MCP/discussions)

