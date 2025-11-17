# Setting Up Agent-MCP in Cursor/VS Code

This guide will help you set up Agent-MCP to work with Cursor or VS Code using the Model Context Protocol (MCP).

## Prerequisites

- **Python 3.8+** with `uv` or `pip`
- **PostgreSQL** (or Docker for running PostgreSQL)
- **Cursor** or **VS Code** installed
- **OpenAI API key** (for embeddings/RAG) - optional if using Ollama

## Quick Setup (Recommended)

### Step 1: Install Agent-MCP

```bash
# Clone the repository
git clone https://github.com/rinadelph/Agent-MCP.git
cd Agent-MCP

# Install dependencies
uv pip install -e .
# OR if using pip:
# pip install -e .
```

### Step 2: Set Up Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your configuration:
# - OPENAI_API_KEY (or configure Ollama)
# - Database connection settings (if not using defaults)
```

### Step 3: Set Up Database

**Option A: Using Docker (Easiest)**
```bash
docker-compose up -d postgres
```

**Option B: Local PostgreSQL**
```bash
# Create database
createdb agent_mcp

# Or use the setup script
./scripts/setup.sh
```

### Step 4: Install MCP Configuration

**Automatic Setup (Easiest):**

```bash
# For Cursor (using uv)
uv run -m agent_mcp.cli mcp-setup install --client cursor --command "uv"

# For VS Code (using uv)
uv run -m agent_mcp.cli mcp-setup install --client vscode --command "uv"

# If using python instead of uv:
uv run -m agent_mcp.cli mcp-setup install --client cursor --command "python3"
```

**Note:** The `--command` flag specifies how to run Agent-MCP. Use `"uv"` if you installed with `uv`, or `"python3"` if using pip.

This command will:
- ✅ Generate the correct configuration
- ✅ Find your editor's config file location
- ✅ Back up your existing config
- ✅ Install Agent-MCP configuration
- ✅ Show you the config path

**⚠️ Important:** After automatic installation, you may need to manually edit the config file to ensure the `args` array includes `"run"`, `"-m"`, and `"agent_mcp.cli"` when using `uv`. See the [Manual Configuration](#manual-configuration) section for the correct format.

**Manual Setup:**

If you prefer to set it up manually (recommended for first-time setup), see the [Manual Configuration](#manual-configuration) section below.

### Step 5: Restart Your Editor

**Important:** You must restart Cursor or VS Code for the MCP configuration to take effect.

### Step 6: Verify Connection

1. Open Cursor/VS Code
2. Open the chat/assistant interface
3. Look for "🔌 agent-mcp" indicator (should appear automatically)
4. Try asking: "List all available tools" or "What agents are available?"

---

## Manual Configuration

If you prefer to configure manually or the automatic setup didn't work:

### Cursor Configuration

**Config File Location:**
- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/claude_desktop_config.json`
- **Linux**: `~/.config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/claude_desktop_config.json`
  - Expands to: `/home/your-username/.config/Cursor/...` (for regular users)
  - ⚠️ **Note:** If you see `/root/.config/...`, you're running as root. Use your regular user account instead.
- **Windows**: `%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\claude_desktop_config.json`

**Configuration Format (using uv):**
```json
{
  "mcpServers": {
    "agent-mcp": {
      "command": "uv",
      "args": [
        "run",
        "-m",
        "agent_mcp.cli",
        "--transport",
        "stdio",
        "--project-dir",
        "${workspaceFolder}"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

**Important:** The `args` array must include `"run"`, `"-m"`, and `"agent_mcp.cli"` before the transport and project-dir options when using `uv`.

**If using `python` instead of `uv`:**
```json
{
  "mcpServers": {
    "agent-mcp": {
      "command": "python3",
      "args": [
        "-m",
        "agent_mcp.cli",
        "--transport",
        "stdio",
        "--project-dir",
        "${workspaceFolder}"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

### VS Code Configuration

**Config File Location:**
- **macOS**: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/claude_desktop_config.json`
- **Linux**: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\claude_desktop_config.json`

**Configuration Format:** (Same as Cursor above)

---

## Configuration Options

### Using Custom Command Paths

If `uv` or `python` aren't in your PATH, use full paths:

```json
{
  "mcpServers": {
    "agent-mcp": {
      "command": "/full/path/to/uv",
      "args": [
        "run",
        "-m",
        "agent_mcp.cli",
        "--transport",
        "stdio",
        "--project-dir",
        "${workspaceFolder}"
      ]
    }
  }
}
```

### Environment Variables

You can pass environment variables in the config:

```json
{
  "mcpServers": {
    "agent-mcp": {
      "command": "uv",
      "args": [...],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "agent_mcp",
        "DB_USER": "agent_mcp",
        "DB_PASSWORD": "your-password"
      }
    }
  }
}
```

**Note:** Agent-MCP will also automatically load variables from a `.env` file in your project root.

### Using Ollama Instead of OpenAI

If you're using Ollama for embeddings:

```json
{
  "mcpServers": {
    "agent-mcp": {
      "command": "uv",
      "args": [...],
      "env": {
        "EMBEDDING_PROVIDER": "ollama",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_EMBEDDING_MODEL": "nomic-embed-text"
      }
    }
  }
}
```

---

## How It Works

### stdio Transport Mode

When configured with `--transport stdio`:
- Cursor/VS Code launches Agent-MCP as a subprocess
- Communication happens via stdin/stdout (JSON-RPC protocol)
- One server instance per workspace
- Automatic lifecycle (starts/stops with your editor)
- No network ports needed

### Project Directory

The `${workspaceFolder}` variable is automatically replaced with:
- Your current workspace root directory
- Example: `/Users/johneakin/PyCharmProjects/Agent-MCP-fork`

Agent-MCP uses this for:
- Database connections
- RAG indexing (scans files in this directory)
- Agent working directories
- Project context storage

**Important:** Each workspace gets its own Agent-MCP instance with separate agents, tasks, and context.

---

## Available Tools

Once connected, your AI assistant can use these Agent-MCP tools:

### Agent Management
- `create_agent` - Create specialized agents (backend, frontend, testing, etc.)
- `list_agents` - View all active agents
- `terminate_agent` - Shut down agents
- `get_agent_tokens` - Get agent authentication tokens

### Task Management
- `assign_task` - Assign tasks to agents
- `view_tasks` - View all tasks
- `update_task_status` - Update task status
- `create_task` - Create new tasks
- `bulk_update_tasks` - Update multiple tasks

### Knowledge & Context
- `ask_project_rag` - Query the knowledge graph
- `update_project_context` - Add project information
- `view_project_context` - View stored context
- `query_project_context` - Search context

### Communication
- `send_agent_message` - Send messages between agents
- `broadcast_message` - Broadcast to all agents
- `get_agent_messages` - Retrieve messages

### File Management
- `claim_file` - Claim file for editing
- `release_file` - Release file
- `get_file_metadata` - Get file information

---

## Troubleshooting

### Issue: "agent-mcp not found" or "command not found"

**Solution:**
```bash
# Check if command is in PATH
which uv
which python3

# Use full path in config, or ensure the command is in your PATH
```

### Issue: Connection failed or tools not showing

**Solutions:**
1. **Restart your editor** - MCP configs only load on startup
2. **Check PostgreSQL is running:**
   ```bash
   # If using Docker
   docker-compose ps
   
   # If using local PostgreSQL
   pg_isready
   ```
3. **Verify database credentials** in your `.env` file
4. **Check logs** - Look for error messages in your editor's output panel

### Issue: "Database connection failed"

**Solutions:**
1. Ensure PostgreSQL is running
2. Verify database credentials in `.env`:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=agent_mcp
   DB_USER=agent_mcp
   DB_PASSWORD=your-password
   ```
3. Test connection:
   ```bash
   psql -h localhost -U agent_mcp -d agent_mcp
   ```

### Issue: Configuration not loading

**Solutions:**
1. Verify config file path is correct
2. Check JSON syntax is valid (use a JSON validator)
3. Ensure the config file has proper permissions
4. Check editor logs for MCP-related errors

### Issue: Config path shows `/root/.config/...` (Linux)

**Problem:** You're running the install command as root.

**Solution:**
```bash
# Don't run as root! Use your regular user account
# If you see /root/ in the path, you're running as root

# Exit root and run as your regular user:
exit  # if you're in a root shell
# Then run the install command again as your regular user

# The correct path should be:
# /home/your-username/.config/Cursor/...
# NOT /root/.config/Cursor/...
```

### Issue: Tools work but no agents/tasks

**Solution:** This is normal! You need to create agents and tasks first. Try:
- "Create a backend agent"
- "List all agents"
- "Create a task for implementing a feature"

---

## Verification Commands

### Check Configuration

```bash
# Verify Cursor configuration
uv run -m agent_mcp.cli mcp-setup verify --client cursor

# Verify VS Code configuration
uv run -m agent_mcp.cli mcp-setup verify --client vscode
```

### Test MCP Server Directly

```bash
# Test that the server can start
uv run -m agent_mcp.cli --transport stdio --project-dir /path/to/your/project

# Should start without errors (will wait for input on stdin)
```

---

## Alternative: SSE Mode (HTTP)

If you need HTTP access or want to share a server between multiple clients:

### Step 1: Start Server Separately

```bash
uv run -m agent_mcp.cli start --port 8080 --transport sse --project-dir /path/to/project
```

### Step 2: Configure Editor to Use URL

```json
{
  "mcpServers": {
    "agent-mcp": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

**When to use SSE mode:**
- Need HTTP API access
- Want to share server between multiple clients
- Need dashboard access
- Want to access from other tools

---

## Next Steps

Once set up, you can:

1. **Create your first agent:**
   - Ask Cursor/VS Code: "Create a backend agent for API development"

2. **Add project context:**
   - "Add this project's architecture to the knowledge graph"

3. **Create and assign tasks:**
   - "Create a task to implement user authentication"

4. **Query project knowledge:**
   - "What do we know about the authentication system?"

For more detailed usage, see:
- [Cursor Integration Guide](./CURSOR_INTEGRATION_GUIDE.md) - Complete workflow examples
- [Getting Started Guide](./getting-started.md) - Your first multi-agent project
- [MCD Guide](./mcd-guide.md) - Creating effective project specifications

---

## Summary

**Quick Setup:**
1. Install Agent-MCP: `uv pip install -e .`
2. Set up database (Docker or local PostgreSQL)
3. Run: `uv run -m agent_mcp.cli mcp-setup install --client cursor`
4. Restart Cursor/VS Code
5. Verify: Look for "🔌 agent-mcp" in chat

**That's it!** Your AI assistant now has access to multi-agent orchestration, persistent memory, task management, and a knowledge graph - all directly from your code editor! 🚀

