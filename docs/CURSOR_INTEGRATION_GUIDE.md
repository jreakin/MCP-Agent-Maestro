# How Agent-MCP Works with Cursor

## 🎯 Overview

Agent-MCP integrates with Cursor through the **Model Context Protocol (MCP)**, allowing Cursor's AI assistant to use Agent-MCP's tools and resources directly within your code editor.

---

## 🔌 **How the Integration Works**

### **Architecture Flow**

```
┌─────────────────────────────────────────────────────────────┐
│                    Cursor IDE                                │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Cursor AI Assistant (Claude)                      │    │
│  │  - Code completion                                 │    │
│  │  - Chat interface                                  │    │
│  │  - Code generation                                 │    │
│  └──────────────┬─────────────────────────────────────┘    │
│                 │                                            │
│                 │ MCP Protocol (stdio)                       │
│                 │ - Tool calls                               │
│                 │ - Resource access                          │
│                 │ - Real-time communication                  │
│                 ▼                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  MCP Client (built into Cursor)                    │    │
│  │  - Manages MCP connections                         │    │
│  │  - Routes tool calls                               │    │
│  │  - Handles stdio communication                     │    │
│  └──────────────┬─────────────────────────────────────┘    │
└─────────────────┼──────────────────────────────────────────┘
                  │
                  │ stdio (stdin/stdout)
                  │ JSON-RPC messages
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent-MCP Server Process                        │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  MCP Server (stdio transport)                      │    │
│  │  - Receives tool calls from Cursor                 │    │
│  │  - Executes tools                                  │    │
│  │  - Returns results                                 │    │
│  └──────────────┬─────────────────────────────────────┘    │
│                 │                                            │
│                 ▼                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Tool Registry                                     │    │
│  │  - create_agent                                    │    │
│  │  - assign_task                                     │    │
│  │  - query_project_rag                               │    │
│  │  - update_project_context                          │    │
│  │  - ... (20+ tools)                                 │    │
│  └──────────────┬─────────────────────────────────────┘    │
│                 │                                            │
│                 ▼                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Agent-MCP Core                                    │    │
│  │  - Multi-agent orchestration                       │    │
│  │  - Task management                                 │    │
│  │  - RAG system                                      │    │
│  │  - Knowledge graph                                 │    │
│  └──────────────┬─────────────────────────────────────┘    │
│                 │                                            │
│                 ▼                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  PostgreSQL Database                               │    │
│  │  - Agents, tasks, context                          │    │
│  │  - RAG embeddings                                  │    │
│  │  - Project memory                                  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 **Step-by-Step: How It Works**

### **1. Configuration Setup**

#### **Automatic Setup (Recommended)**

```bash
# Generate and install Cursor configuration
uv run -m agent_mcp.cli mcp-setup install --client cursor

# This automatically:
# 1. Generates the correct config for Cursor
# 2. Finds Cursor's config file location
# 3. Backs up existing config
# 4. Installs Agent-MCP configuration
# 5. Shows you the config path
```

#### **Manual Setup**

**Cursor Config File Location:**
- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/claude_desktop_config.json`
- **Linux**: `~/.config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\claude_desktop_config.json`

**Configuration Format:**
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

**Key Points:**
- `command`: How to run Agent-MCP (usually `uv` or `python`)
- `args`: Arguments to pass to Agent-MCP
  - `--transport stdio`: Use stdio for MCP communication
  - `--project-dir ${workspaceFolder}`: Use current workspace as project
- `env`: Environment variables (API keys, etc.)

---

### **2. How Cursor Connects**

#### **Connection Flow:**

1. **Cursor Starts**
   - Cursor reads its MCP configuration file
   - Finds `agent-mcp` server definition
   - Prepares to launch the server

2. **Agent-MCP Server Launches**
   - Cursor executes: `uv run -m agent_mcp.cli --transport stdio --project-dir /path/to/workspace`
   - Agent-MCP starts in stdio mode (not HTTP/SSE)
   - Server initializes:
     - Loads project directory
     - Connects to PostgreSQL
     - Loads agents/tasks from database
     - Registers all available tools

3. **MCP Handshake**
   - Cursor sends initialization request via stdin
   - Agent-MCP responds with:
     - Server capabilities
     - Available tools list
     - Available resources
   - Connection established

4. **Ready to Use**
   - Cursor shows "🔌 agent-mcp" in chat interface
   - Tools are available to Cursor's AI
   - Resources can be accessed

---

### **3. How Tools Are Called**

#### **When You Use Cursor's AI:**

**Example: You ask Cursor:**
> "Create a backend agent to work on the API endpoints"

**What Happens:**

1. **Cursor's AI decides to use a tool**
   ```json
   {
     "method": "tools/call",
     "params": {
       "name": "create_agent",
       "arguments": {
         "agent_id": "backend-agent-001",
         "capabilities": ["backend", "api", "database"],
         "working_directory": "/path/to/project"
       }
     }
   }
   ```

2. **Agent-MCP receives the call**
   - Tool registry routes to `create_agent_tool_impl()`
   - Security scanner checks input for threats
   - Input sanitized if needed

3. **Tool executes**
   ```python
   # Agent-MCP creates the agent
   - Generates agent token
   - Creates agent record in PostgreSQL
   - Sets up working directory
   - Registers agent in memory (g.active_agents)
   - Returns agent details
   ```

4. **Result sent back to Cursor**
   ```json
   {
     "result": [
       {
         "type": "text",
         "text": "✅ Created backend agent 'backend-agent-001'\nToken: abc123...\nStatus: active\nWorking directory: /path/to/project"
       }
     ]
   }
   ```

5. **Cursor's AI responds to you**
   > "I've created a backend agent for you. The agent is now active and ready to work on API endpoints. You can assign tasks to it using the assign_task tool."

---

### **4. Available Tools in Cursor**

Once connected, Cursor's AI can use these tools:

#### **Agent Management**
- `create_agent` - Create specialized agents (backend, frontend, testing, etc.)
- `list_agents` - View all active agents
- `terminate_agent` - Shut down agents
- `get_agent_tokens` - Get agent authentication tokens

#### **Task Management**
- `assign_task` - Assign tasks to agents
- `view_tasks` - View all tasks
- `update_task_status` - Update task status
- `create_task` - Create new tasks
- `bulk_update_tasks` - Update multiple tasks

#### **Knowledge & Context**
- `ask_project_rag` - Query the knowledge graph
- `update_project_context` - Add project information
- `view_project_context` - View stored context
- `query_project_context` - Search context

#### **Communication**
- `send_agent_message` - Send messages between agents
- `broadcast_message` - Broadcast to all agents
- `get_agent_messages` - Retrieve messages

#### **File Management**
- `claim_file` - Claim file for editing
- `release_file` - Release file
- `get_file_metadata` - Get file information

---

### **5. Real-World Usage Examples**

#### **Example 1: Creating a Multi-Agent Team**

**You in Cursor:**
> "Set up a team of agents: one for backend API work, one for frontend React components, and one for testing"

**Cursor's AI uses tools:**
```python
# Tool call 1
create_agent(
    agent_id="backend-dev",
    capabilities=["backend", "api", "database"],
    working_directory="${workspaceFolder}"
)

# Tool call 2
create_agent(
    agent_id="frontend-dev",
    capabilities=["frontend", "react", "ui"],
    working_directory="${workspaceFolder}"
)

# Tool call 3
create_agent(
    agent_id="qa-tester",
    capabilities=["testing", "qa", "validation"],
    working_directory="${workspaceFolder}"
)
```

**Result:**
- Three agents created
- Each has its own token
- Each can work independently
- All share the same project context

---

#### **Example 2: Querying Project Knowledge**

**You in Cursor:**
> "What do we know about the authentication system?"

**Cursor's AI uses tool:**
```python
ask_project_rag(
    query="authentication system architecture and implementation",
    max_results=5
)
```

**Agent-MCP:**
1. Embeds your query
2. Searches RAG embeddings in PostgreSQL
3. Finds relevant context from:
   - Project documentation
   - Code comments
   - Previous conversations
   - Architectural decisions
4. Returns top 5 results

**Cursor's AI responds:**
> "Based on the project knowledge graph, here's what I found about authentication:
> - Uses JWT tokens
> - Implemented in `/auth/` directory
> - Supports OAuth2
> - ..."

---

#### **Example 3: Task Assignment**

**You in Cursor:**
> "Have the backend agent implement the user profile API endpoint"

**Cursor's AI uses tools:**
```python
# First, create the task
create_task(
    title="Implement user profile API endpoint",
    description="Create GET /api/users/:id endpoint with authentication",
    priority="high",
    assigned_to="backend-dev"
)

# Then assign it
assign_task(
    task_id="task_123",
    agent_id="backend-dev"
)
```

**Agent-MCP:**
1. Creates task in database
2. Assigns to backend agent
3. Agent can now see the task
4. Updates task status as work progresses

---

### **6. Transport Modes**

#### **stdio Mode (Used with Cursor)**

```json
{
  "command": "uv",
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
```

**How it works:**
- Cursor launches Agent-MCP as a subprocess
- Communication via stdin/stdout
- JSON-RPC protocol
- One server instance per Cursor workspace
- Automatic lifecycle (starts/stops with Cursor)

**Advantages:**
- ✅ Simple setup
- ✅ Automatic lifecycle
- ✅ No port conflicts
- ✅ Secure (no network exposure)
- ✅ Works offline

**Limitations:**
- ❌ One instance per workspace
- ❌ Can't share between multiple Cursor windows
- ❌ No HTTP API access

---

#### **SSE Mode (Alternative - for HTTP access)**

```json
{
  "mcpServers": {
    "agent-mcp": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

**When to use:**
- Need HTTP API access
- Want to share server between multiple clients
- Need dashboard access
- Want to access from other tools

**Setup:**
```bash
# Start server separately
uv run -m agent_mcp.cli start --port 8080 --transport sse

# Then configure Cursor to use SSE URL
```

---

### **7. Project Directory Context**

#### **How `${workspaceFolder}` Works**

When you configure:
```json
"--project-dir", "${workspaceFolder}"
```

**Cursor replaces `${workspaceFolder}` with:**
- The current workspace root directory
- Example: `/Users/johneakin/PyCharmProjects/Agent-MCP-fork`

**Agent-MCP uses this for:**
- Database location (PostgreSQL connection)
- RAG indexing (scans files in this directory)
- Agent working directories
- Project context storage

**Important:**
- Each Cursor workspace = separate Agent-MCP instance
- Each workspace = separate project context
- Agents/tasks are scoped to the workspace
- RAG knowledge is workspace-specific

---

### **8. Environment Variables**

#### **Passing Environment Variables**

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

**Common Variables:**
- `OPENAI_API_KEY` - Required for embeddings/RAG
- `DB_*` - PostgreSQL connection (if not using defaults)
- `MCP_DEBUG` - Enable debug logging
- `AGENT_MCP_*` - Various Agent-MCP settings

**Security Note:**
- ⚠️ Config file is plain text
- Consider using Cursor's environment variable expansion
- Or use `.env` file (Agent-MCP loads it automatically)

---

### **9. Verification & Troubleshooting**

#### **Check Configuration**

```bash
# Verify Cursor configuration
uv run -m agent_mcp.cli mcp-setup verify --client cursor

# Output:
# ✅ cursor: Configuration valid at /path/to/config.json
# Configuration:
# {
#   "command": "uv",
#   "args": [...]
# }
```

#### **Test Connection**

1. **Restart Cursor** after installing config
2. **Open chat** in Cursor
3. **Look for** "🔌 agent-mcp" indicator
4. **Try a tool**: "List all agents"

#### **Common Issues**

**Issue: "agent-mcp not found"**
```bash
# Check if command is in PATH
which uv
which python

# Or use full path in config
"command": "/usr/local/bin/uv"
```

**Issue: "Connection failed"**
- Check PostgreSQL is running
- Verify database credentials
- Check logs: `tail -f mcp_server.log`

**Issue: "Tools not showing"**
- Restart Cursor
- Check MCP server logs
- Verify config file syntax (valid JSON)

---

### **10. Advanced Usage**

#### **Multiple Workspaces**

Each Cursor workspace can have its own Agent-MCP instance:

```
Workspace 1 (/project-a)
  └─ Agent-MCP Instance 1
     └─ Agents, tasks, context for project-a

Workspace 2 (/project-b)
  └─ Agent-MCP Instance 2
     └─ Agents, tasks, context for project-b
```

**Benefits:**
- ✅ Complete isolation between projects
- ✅ Separate agent teams per project
- ✅ Independent RAG knowledge bases

---

#### **Shared Server (SSE Mode)**

If you want to share one server across workspaces:

```bash
# Start shared server
uv run -m agent_mcp.cli start --port 8080 --transport sse --project-dir /shared/project

# Configure all Cursor workspaces to use:
{
  "mcpServers": {
    "agent-mcp": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

**Benefits:**
- ✅ Shared agent team
- ✅ Shared knowledge base
- ✅ Centralized management

---

#### **Custom Command Paths**

If `uv` or `python` aren't in PATH:

```json
{
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
```

Or use Python directly:
```json
{
  "command": "python3",
  "args": [
    "-m",
    "agent_mcp.cli",
    "--transport",
    "stdio",
    "--project-dir",
    "${workspaceFolder}"
  ]
}
```

---

## 🎯 **Complete Workflow Example**

### **Setting Up Agent-MCP with Cursor**

```bash
# 1. Install Agent-MCP
cd /path/to/your/project
git clone https://github.com/your-fork/Agent-MCP.git
cd Agent-MCP
uv pip install -e .

# 2. Set up PostgreSQL (if not using Docker)
# ... PostgreSQL setup ...

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Install Cursor configuration
uv run -m agent_mcp.cli mcp-setup install --client cursor

# Output:
# ✅ Configuration installed to /path/to/cursor/config.json
# 📦 Backup created at /path/to/cursor/config.json.backup.1234567890

# 5. Restart Cursor

# 6. Verify connection
# In Cursor chat, you should see "🔌 agent-mcp"
# Try: "List all agents" or "What tools are available?"
```

---

### **Using Agent-MCP in Cursor**

**Example Conversation:**

**You:**
> "I need to build a user authentication system. Set up a team of agents to help."

**Cursor's AI (using Agent-MCP tools):**
1. Creates backend agent for API work
2. Creates frontend agent for UI components
3. Creates testing agent for validation
4. Creates tasks for each component
5. Assigns tasks to appropriate agents

**You:**
> "What do we know about authentication patterns in this project?"

**Cursor's AI (using RAG tool):**
- Queries project knowledge graph
- Finds relevant documentation
- Summarizes authentication patterns
- References specific files

**You:**
> "Have the backend agent implement the login endpoint"

**Cursor's AI (using task tools):**
- Creates task for login endpoint
- Assigns to backend agent
- Provides context from RAG
- Monitors progress

---

## 🔍 **How It's Different from Regular Cursor**

### **Without Agent-MCP:**
- Single AI assistant
- No persistent memory between sessions
- No multi-agent coordination
- No task management
- No shared knowledge graph

### **With Agent-MCP:**
- ✅ Multiple specialized agents
- ✅ Persistent memory (PostgreSQL)
- ✅ Coordinated multi-agent workflows
- ✅ Task management and tracking
- ✅ Shared knowledge graph (RAG)
- ✅ Real-time agent communication
- ✅ Project context persistence

---

## 📊 **Technical Details**

### **MCP Protocol Communication**

**Message Format (JSON-RPC):**
```json
// Request from Cursor
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_agent",
    "arguments": {...}
  }
}

// Response from Agent-MCP
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Agent created successfully"
      }
    ]
  }
}
```

### **Tool Execution Flow**

```
Cursor → MCP Client → stdio → Agent-MCP Server
                                    ↓
                            Tool Registry
                                    ↓
                            Security Scanner
                                    ↓
                            Tool Implementation
                                    ↓
                            Database/Operations
                                    ↓
                            Response Formatter
                                    ↓
Agent-MCP Server → stdio → MCP Client → Cursor
```

---

## 🎓 **Key Concepts**

### **1. stdio Transport**
- Communication via standard input/output
- No network required
- One process per workspace
- Automatic lifecycle management

### **2. Tool Registry**
- All tools registered at startup
- Security scanning on input/output
- Automatic routing to implementations
- Consistent error handling

### **3. Project Context**
- Each workspace = separate context
- Shared knowledge graph per project
- Agents scoped to workspace
- RAG indexing per project

### **4. Multi-Agent Coordination**
- Agents can work in parallel
- Shared task queue
- Inter-agent communication
- Coordinated workflows

---

## ✅ **Summary**

**How Agent-MCP works with Cursor:**

1. **Configuration**: Cursor config file tells Cursor how to launch Agent-MCP
2. **Connection**: Cursor launches Agent-MCP as subprocess via stdio
3. **Tools**: Agent-MCP exposes 20+ tools that Cursor's AI can use
4. **Execution**: When you ask Cursor to do something, it calls Agent-MCP tools
5. **Results**: Agent-MCP executes operations and returns results to Cursor
6. **Context**: Everything is stored in PostgreSQL, persisting between sessions

**The result:** Cursor's AI becomes a **multi-agent orchestration system** with persistent memory, task management, and coordinated workflows - all accessible directly from your code editor! 🚀
