# 🎭 MCP Agent Maestro

![Agent MCP Maestro Logo](assets/images/agent-mcp-maestro-banner.png)


---

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/jreakin/mcp-agent-maestro/workflows/Tests/badge.svg)](https://github.com/jreakin/mcp-agent-maestro/actions/workflows/tests.yml)
[![Lint](https://github.com/jreakin/mcp-agent-maestro/workflows/Code%20Quality/badge.svg)](https://github.com/jreakin/mcp-agent-maestro/actions/workflows/lint.yml)
[![Security](https://github.com/jreakin/mcp-agent-maestro/workflows/Security/badge.svg)](https://github.com/jreakin/mcp-agent-maestro/actions/workflows/security.yml)
[![Deploy Check](https://github.com/jreakin/mcp-agent-maestro/workflows/Deploy%20and%20Health%20Check/badge.svg)](https://github.com/jreakin/mcp-agent-maestro/actions/workflows/deploy-check.yml)
[![Coverage](https://codecov.io/gh/jreakin/mcp-agent-maestro/branch/main/graph/badge.svg)](https://codecov.io/gh/jreakin/mcp-agent-maestro)

**Total Tests:** 138 (127 passed, 11 skipped)

### 🛠️ Built With

**Core Python Stack:**
- **Pydantic** `>=2.0` - Data validation and settings management
- **PydanticAI** `>=0.0.12` (optional) - Structured agent orchestration
- **Starlette** - Modern async web framework
- **Uvicorn** - ASGI server for high-performance async applications
- **Click** - Command-line interface framework
- **AnyIO** - Async I/O library

**AI & LLM Integration:**
- **OpenAI** - GPT models and embeddings
- **MCP SDK** `>=1.8.1` - Model Context Protocol implementation

**Database & Storage:**
- **PostgreSQL** with **pgvector** `>=0.3.0` - Vector search and persistent storage
- **psycopg2-binary** `>=2.9.0` - PostgreSQL adapter

**Data Serialization:**
- **TOON Format** `>=0.1.0` - Token-Oriented Object Notation for efficient serialization

**Frontend Dashboard:**
- **Next.js** `15.3.4` - React framework
- **React** `^19.0.0` - UI library
- **Radix UI** - Accessible component primitives
- **Tailwind CSS** `^4` - Utility-first CSS framework
- **Recharts** - Data visualization

**Development Tools:**
- **pytest** `>=8.3.2` - Testing framework
- **ruff** `>=0.5.5` - Fast Python linter and formatter
- **mypy** - Static type checking
- **mutmut** - Mutation testing
- **hypothesis** `>=6.100` - Property-based testing

> **Orchestrating AI Agents Like a Symphony** 🎵

**MCP Agent Maestro** is a sophisticated multi-agent orchestration framework that coordinates specialized AI agents to work harmoniously on complex software development tasks. Like a conductor leading an orchestra, Maestro ensures each agent performs its part at the right time, creating a seamless development experience.

> 📦 **Fork Information**: This is a fork of [Agent-MCP](https://github.com/rinadelph/Agent-MCP) created by John R. Eakin ([github.com/jreakin](https://github.com/jreakin)). For the original project, visit the [Agent-MCP repository](https://github.com/rinadelph/Agent-MCP).


## 🎼 The Maestro Philosophy

Traditional AI coding assistants are solo performers—they try to do everything themselves and often struggle with complex, multi-faceted projects. **MCP Agent Maestro** takes a different approach:

### The Orchestra Metaphor

```
🎻 Frontend Agent    →  Crafting beautiful UIs
🎺 Backend Agent     →  Building robust APIs
🥁 Testing Agent     →  Ensuring quality
🎹 Database Agent    →  Designing data models
🎸 Security Agent    →  Protecting the system

    👨‍🎤 Maestro        →  Conducting the symphony
```

Each agent is a virtuoso in their domain, and the Maestro coordinates them through:

- **Shared Memory** - A living knowledge graph that all agents contribute to and learn from
- **Task Choreography** - Breaking complex work into harmonized, parallelizable tasks
- **Real-time Coordination** - Preventing conflicts and ensuring smooth collaboration
- **Visual Monitoring** - A beautiful dashboard to watch your AI orchestra perform

## ✨ Key Features

<div align="center">
  <img src="assets/images/dashboard-overview.png" alt="Multi-Agent Collaboration Network" width="800">
</div>

**Real-time visualization** shows your AI team at work - purple nodes represent context entries, blue nodes are agents, and connections show active collaborations. It's like having a mission control center for your development team.

### 🎯 Specialized Agent Roles

Create agents with specific expertise:
- **Frontend Virtuosos** - React, Vue, Svelte specialists
- **Backend Maestros** - API, database, and infrastructure experts
- **Testing Conductors** - Unit, integration, and E2E testing
- **Security Guardians** - Vulnerability scanning and secure coding
- **DevOps Harmonizers** - CI/CD, deployment, and monitoring

### 🧠 Persistent Knowledge Graph

Every decision, pattern, and architectural choice is stored in a searchable knowledge graph using advanced RAG (Retrieval-Augmented Generation):

- **Vector embeddings** for semantic search
- **PostgreSQL + pgvector** for production-ready storage
- **Automatic indexing** of code, docs, and conversations
- **Context continuity** across sessions

### 📊 Real-Time Dashboard

<div align="center">
  <img src="assets/images/maestro-dashboard.png" alt="Maestro Dashboard" width="800">
</div>

Watch your AI orchestra perform in real-time:
- **Agent Status** - See what each agent is working on
- **Task Flow** - Visualize task dependencies and progress
- **Knowledge Graph** - Explore the shared memory
- **Performance Metrics** - Monitor agent efficiency

### 🔒 Enterprise-Grade Security

Built-in security features:
- **Prompt injection detection**
- **Tool call sanitization**
- **Access control and authentication**
- **Audit logging**

## 🚀 Quick Start

### One-Command Installation

```bash
# Clone MCP Agent Maestro
git clone https://github.com/jreakin/mcp-agent-maestro.git
cd mcp-agent-maestro

# Run the interactive setup wizard
./scripts/setup.sh
```

The setup wizard will:
- ✅ Check prerequisites (Docker, Node.js, Python)
- ✅ Configure your AI provider (OpenAI or Ollama)
- ✅ Set up the database
- ✅ Launch the dashboard
- ✅ Create your first conductor agent

### Access Your Orchestra

Once setup completes:
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

## 🎭 The Maestro Workflow

### 1. Initialize the Conductor

Your first agent is the **Conductor** - responsible for orchestrating all other agents:

```bash
maestro init --role conductor
```

### 2. Define Your Symphony (MCD)

Create a **Main Context Document** that serves as the musical score for your project:

```markdown
# Project Symphony: My Application

## Movements (Phases)

1. Foundation - Database schema and API structure
2. Performance - Core business logic
3. Presentation - UI components
4. Finale - Testing and deployment

## Instruments (Agents Needed)

- Backend Agent (Django/FastAPI)
- Frontend Agent (React)
- Database Agent (PostgreSQL)
- Testing Agent (Pytest)
```

### 3. Summon Your Orchestra

The Conductor creates specialized agents:

```python
# Backend virtuoso
await maestro.summon_agent(
    role="backend",
    specialization="FastAPI + SQLModel",
    focus="User authentication APIs"
)

# Frontend virtuoso
await maestro.summon_agent(
    role="frontend",
    specialization="React + TypeScript",
    focus="Login and registration flows"
)
```

### 4. Conduct the Performance

Assign tasks and watch the magic happen:

```python
# Parallel execution
await maestro.conduct([
    Task("Create user model", agent="backend"),
    Task("Design login form", agent="frontend"),
    Task("Write auth tests", agent="testing")
])
```

## 🎵 Advanced Features

### Multi-Agent Patterns

**Parallel Composition**
```python
# Multiple agents work simultaneously
backend_task = await backend_agent.implement_api()
frontend_task = await frontend_agent.build_ui()
results = await asyncio.gather(backend_task, frontend_task)
```

**Sequential Harmony**
```python
# Agents build on each other's work
schema = await database_agent.design_schema()
models = await backend_agent.generate_models(schema)
views = await frontend_agent.create_views(models)
```

**Collaborative Improvisation**
```python
# Agents communicate and adapt
await security_agent.review(backend_agent.latest_code)
await backend_agent.apply_fixes(security_agent.recommendations)
```

### Test Run (See It in Action!) 🧪

Want to quickly see the dashboard with sample data?

```bash
# Start everything with test data
./scripts/test-run.sh --seed
```

This starts all services and populates the dashboard with sample agents, tasks, and context. Perfect for exploring the UI!

See [Test Run Guide](./TEST_RUN_GUIDE.md) for details.

### Alternative: Python CLI Setup

```bash
# Install MCP Agent Maestro
uv pip install -e .

# Run interactive setup
uv run -m agent_mcp.cli setup

# Check your setup
uv run -m agent_mcp.cli doctor
```

### Docker Compose (Manual Setup)

For manual setup without the wizard:

```bash
# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
echo "DB_PASSWORD=your_secure_password" >> .env

# Start all services (Backend + Dashboard + PostgreSQL)
docker-compose up -d

# Access:
# - Dashboard UI: http://localhost:3000
# - Backend API: http://localhost:8080
# - API Docs: http://localhost:8080/docs
```

**All services start automatically** - no need to run the dashboard separately!

See [Quick Start Guide](./docs/setup/QUICK_START.md) for detailed manual instructions.

### Python Implementation (Local Development)

For local development without Docker:

```bash
# Clone and setup
git clone https://github.com/jreakin/mcp-agent-maestro.git
cd mcp-agent-maestro

# Check version requirements
python --version  # Should be >=3.10
node --version    # Should be >=18.0.0
npm --version     # Should be >=9.0.0

# If using nvm for Node.js version management
nvm use  # Uses the version specified in .nvmrc

# Configure environment
cp .env.example .env  # Add your OpenAI API key
uv venv
uv install

# Start the server
uv run -m agent_mcp.cli --port 8080 --project-dir path-to-directory

# Launch dashboard (recommended for full experience)
cd agent_mcp/dashboard && npm install && npm run dev
```

**Note**: Local development requires a PostgreSQL database. See [DOCKER_SETUP.md](./DOCKER_SETUP.md) for database setup options.

### Node.js/TypeScript Implementation (Alternative)

```bash
# Clone and setup
git clone https://github.com/jreakin/mcp-agent-maestro.git
cd mcp-agent-maestro/agent-mcp-node

# Install dependencies
npm install

# Configure environment
cp .env.example .env  # Add your OpenAI API key

# Start the server
npm run server

# Or use the built version
npm run build
npm start

# Or install globally
npm install -g agent-mcp-node
agent-mcp --port 8080 --project-dir path-to-directory
```

## MCP Integration Guide

### What is MCP?

The **Model Context Protocol (MCP)** is an open standard that enables AI assistants to securely connect to external data sources and tools. Agent-MCP leverages MCP to provide seamless integration with various development tools and services.

### Running Agent-MCP as an MCP Server

Agent-MCP can function as an MCP server, exposing its multi-agent capabilities to MCP-compatible clients like Claude Desktop, Cline, and other AI coding assistants.

#### Quick MCP Setup

```bash
# 1. Install Agent-MCP
uv venv
uv install

# 2. Start the MCP server
uv run -m agent_mcp.cli --port 8080

# 3. Configure your MCP client to connect to:
# HTTP: http://localhost:8000/mcp
# WebSocket: ws://localhost:8000/mcp/ws
```

#### MCP Server Configuration

Create an MCP configuration file (`mcp_config.json`):

```json
{
  "server": {
    "name": "agent-mcp",
    "version": "1.0.0"
  },
  "tools": [
    {
      "name": "create_agent",
      "description": "Create a new specialized AI agent"
    },
    {
      "name": "assign_task", 
      "description": "Assign tasks to specific agents"
    },
    {
      "name": "query_project_context",
      "description": "Query the shared knowledge graph"
    },
    {
      "name": "manage_agent_communication",
      "description": "Handle inter-agent messaging"
    }
  ],
  "resources": [
    {
      "name": "agent_status",
      "description": "Real-time agent status and activity"
    },
    {
      "name": "project_memory",
      "description": "Persistent project knowledge graph"
    }
  ]
}
```

#### Using Agent-MCP with Claude Desktop

1. **Add to Claude Desktop Config**:
   
   Open `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent:
   
   ```json
   {
     "mcpServers": {
       "agent-mcp": {
         "command": "uv",
         "args": ["run", "-m", "agent_mcp.cli", "--port", "8080"],
         "env": {
           "OPENAI_API_KEY": "your-openai-api-key"
         }
       }
     }
   }
   ```

2. **Restart Claude Desktop** to load the MCP server

3. **Verify Connection**: Claude should show "🔌 agent-mcp" in the conversation

#### MCP Tools Available

Once connected, you can use these MCP tools directly in Claude:

**Agent Management**
- `create_agent` - Spawn specialized agents (backend, frontend, testing, etc.)
- `list_agents` - View all active agents and their status
- `terminate_agent` - Safely shut down agents

**Task Orchestration**  
- `assign_task` - Delegate work to specific agents
- `view_tasks` - Monitor task progress and dependencies
- `update_task_status` - Track completion and blockers

**Knowledge Management**
- `ask_project_rag` - Query the persistent knowledge graph
- `update_project_context` - Add architectural decisions and patterns
- `view_project_context` - Access stored project information

**Communication**
- `send_agent_message` - Direct messaging between agents
- `broadcast_message` - Send updates to all agents
- `request_assistance` - Escalate complex issues

#### Advanced MCP Configuration

**Custom Transport Options**:
```bash
# HTTP with custom port
uv run -m agent_mcp.cli --port 8080

# WebSocket with authentication
uv run -m agent_mcp.cli --port 8080 --auth-token your-secret-token

# Unix socket (Linux/macOS)
uv run -m agent_mcp.cli --port 8080
```

**Environment Variables**:
```bash
export AGENT_MCP_HOST=0.0.0.0          # Server host
export AGENT_MCP_PORT=8000              # Server port  
export AGENT_MCP_LOG_LEVEL=INFO         # Logging level
export AGENT_MCP_PROJECT_DIR=/your/project  # Default project directory
export AGENT_MCP_MAX_AGENTS=10          # Maximum concurrent agents
```

### MCP Client Examples

#### Python Client
```python
import asyncio
from mcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        # Create a backend agent
        result = await client.call_tool("create_agent", {
            "role": "backend",
            "specialization": "API development"
        })
        
        # Assign a task
        await client.call_tool("assign_task", {
            "agent_id": result["agent_id"],
            "task": "Implement user authentication endpoints"
        })
        
        # Query project context
        context = await client.call_tool("ask_project_rag", {
            "query": "What's our current database schema?"
        })
        print(context)

asyncio.run(main())
```

#### JavaScript Client
```javascript
import { MCPClient } from '@modelcontextprotocol/client';

const client = new MCPClient('http://localhost:8000/mcp');

async function createAgent() {
  await client.connect();
  
  const agent = await client.callTool('create_agent', {
    role: 'frontend',
    specialization: 'React components'
  });
  
  console.log('Created agent:', agent.agent_id);
  
  await client.disconnect();
}

createAgent().catch(console.error);
```

### Troubleshooting MCP Connection

**Connection Issues**:
```bash
# Check if MCP server is running
curl http://localhost:8000/mcp/health

# Verify WebSocket connection
wscat -c ws://localhost:8000/mcp/ws

# Check server logs
uv run -m agent_mcp.cli --port 8080 --log-level DEBUG
```

**Common Issues**:
- **Port conflicts**: Change port with `--port` flag
- **Permission errors**: Ensure OpenAI API key is set
- **Client timeout**: Increase timeout in client configuration
- **Agent limit reached**: Check active agent count with `list_agents`

### Integration Examples

**VS Code with MCP**:
Use the MCP extension to integrate Agent-MCP directly into your editor workflow.

**Terminal Usage**:
```bash
# Quick task assignment via curl
curl -X POST http://localhost:8000/mcp/tools/assign_task \
  -H "Content-Type: application/json" \
  -d '{"task": "Add error handling to API endpoints", "agent_role": "backend"}'
```

**CI/CD Integration**:
```yaml
# GitHub Actions example
- name: Run Agent-MCP Code Review
  run: |
    uv run -m agent_mcp.cli --port 8080 --daemon
    curl -X POST localhost:8000/mcp/tools/assign_task \
      -d '{"task": "Review PR for security issues", "agent_role": "security"}'
```

## How It Works: Breaking Complexity into Simple Steps

```mermaid
graph LR
    A[Step 1] --> B[Step 2] --> C[Step 3] --> D[Step 4] --> E[Done!]
    style A fill:#4ecdc4,color:#fff
    style E fill:#ff6b6b,color:#fff
```

Every task can be broken down into linear steps. This is the core insight that makes Agent-MCP powerful.

### The Problem with Complex Tasks

```mermaid
graph TD
    A["Build User Authentication"] -->|Single Agent Tries Everything| B{???}
    B --> C[Database?]
    B --> D[API?]
    B --> E[Frontend?]
    B --> F[Security?]
    B --> G[Tests?]
    C -.->|Confused| H[Incomplete Implementation]
    D -.->|Overwhelmed| H
    E -.->|Context Lost| H
    F -.->|Assumptions| H
    G -.->|Forgotten| H
    style A fill:#ff6b6b,color:#fff
    style H fill:#666,color:#fff
```

### The Agent-MCP Solution

```mermaid
graph TD
    A["Build User Authentication"] -->|Break Down| B[Linear Tasks]
    B --> C["Agent 1: Database"]
    B --> D["Agent 2: API"]
    B --> E["Agent 3: Frontend"]
    
    C --> C1[Create users table]
    C1 --> C2[Add indexes]
    C2 --> C3[Create sessions table]
    
    D --> D1[POST /register]
    D1 --> D2[POST /login]
    D2 --> D3[POST /logout]
    
    E --> E1[Login Form]
    E1 --> E2[Register Form]
    E2 --> E3[Auth Context]
    
    C3 --> F[Working System]
    D3 --> F
    E3 --> F
    
    style A fill:#4ecdc4,color:#fff
    style F fill:#4ecdc4,color:#fff
```

Each agent focuses on their linear chain. No confusion. No context pollution. Just clear, deterministic progress.

## The 5-Step Workflow

### 1. Initialize Admin Agent
```
You are the admin agent.
Admin Token: "your_admin_token_from_server"

Your role is to:
- Coordinate all development work
- Create and manage worker agents
- Maintain project context
- Assign tasks based on agent specializations
```

### 2. Load Your Project Blueprint (MCD)
```
Add this MCD (Main Context Document) to project context:

[paste your MCD here - see docs/mcd-guide.md for structure]

Store every detail in the knowledge graph. This becomes the single source of truth for all agents.
```

The MCD (Main Context Document) is your project's comprehensive blueprint - think of it as writing the book of your application before building it. It includes:
- Technical architecture and design decisions
- Database schemas and API specifications
- UI component hierarchies and workflows
- Task breakdowns with clear dependencies

See our [MCD Guide](./docs/mcd-guide.md) for detailed examples and templates.

### 3. Deploy Your Agent Team
```
Create specialized agents for parallel development:

- backend-worker: API endpoints, database operations, business logic
- frontend-worker: UI components, state management, user interactions
- integration-worker: API connections, data flow, system integration
- test-worker: Unit tests, integration tests, validation
- devops-worker: Deployment, CI/CD, infrastructure
```

Each agent specializes in their domain, leading to higher quality implementations and faster development.

### 4. Initialize and Deploy Workers
```
# In new window for each worker:
You are [worker-name] agent.
Your Admin Token: "worker_token_from_admin"

Query the project knowledge graph to understand:
1. Overall system architecture
2. Your specific responsibilities
3. Integration points with other components
4. Coding standards and patterns to follow
5. Current implementation status

Begin implementation following the established patterns.

AUTO --worker --memory
```

**Important: Setting Agent Modes**

Agent modes (like `--worker`, `--memory`, `--playwright`) are not just flags - they activate specific behavioral patterns. In Claude Code, you can make these persistent by:

1. Copy the mode instructions to your clipboard
2. Type `#` to open Claude's memory feature
3. Paste the instructions for persistent behavior

Example for Claude Code memory:
```
# When I use "AUTO --worker --memory", follow these patterns:
- Always check file status before editing
- Query project RAG for context before implementing
- Document all changes in task notes
- Work on one file at a time, completing it before moving on
- Update task status after each completion
```

This ensures consistent behavior across your entire session without repeating instructions.

### 5. Monitor and Coordinate

The dashboard provides real-time visibility into your AI development team:

**Network Visualization** - Watch agents collaborate and share information  
**Task Progress** - Track completion across all parallel work streams  
**Memory Health** - Ensure context remains fresh and accessible  
**Activity Timeline** - See exactly what each agent is doing

Access at `http://localhost:3847` after launching the dashboard.

## Advanced Features

### Specialized Agent Modes

Agent modes fundamentally change how agents behave. They're not just configuration - they're behavioral contracts that ensure agents follow specific patterns optimized for their role.

**Standard Worker Mode**
```
AUTO --worker --memory
```
Optimized for implementation tasks:
- Granular file status checking before any edits
- Sequential task completion (one at a time)
- Automatic documentation of changes
- Integration with project RAG for context
- Task status updates after each completion

**Frontend Specialist Mode**
```
AUTO --worker --playwright
```
Enhanced with visual validation capabilities:
- All standard worker features
- Browser automation for component testing
- Screenshot capabilities for visual regression
- DOM interaction for end-to-end testing
- Component-by-component implementation with visual verification

**Research Mode**
```
AUTO --memory
```
Read-only access for analysis and planning:
- No file modifications allowed
- Deep context exploration via RAG
- Pattern identification across codebase
- Documentation generation
- Architecture analysis and recommendations

**Memory Management Mode**
```
AUTO --memory --manager
```
For context curation and optimization:
- Memory health monitoring
- Stale context identification
- Knowledge graph optimization
- Context summarization for new agents
- Cross-agent knowledge transfer

Each mode enforces specific behaviors that prevent common mistakes and ensure consistent, high-quality output.

### Project Memory Management

The system maintains several types of memory:

**Project Context** - Architectural decisions, design patterns, conventions  
**Task Memory** - Current status, blockers, implementation notes  
**Agent Memory** - Individual agent learnings and specializations  
**Integration Points** - How different components connect

All memory is:
- Searchable via semantic queries
- Version controlled for rollback
- Tagged for easy categorization
- Automatically garbage collected when stale

### Conflict Resolution

File-level locking prevents agents from overwriting each other's work:

1. Agent requests file access
2. System checks if file is locked
3. If locked, agent works on other tasks or waits
4. After completion, lock is released
5. Other agents can now modify the file

This happens automatically - no manual coordination needed.

## Short-Lived vs. Long-Lived Agents: The Critical Difference

### Traditional Long-Lived Agents
Most AI coding assistants maintain conversations across entire projects:
- **Accumulated context grows unbounded** - mixing unrelated code, decisions, and conversations
- **Confused priorities** - yesterday's bug fix mingles with today's feature request
- **Hallucination risks increase** - agents invent connections between unrelated parts
- **Performance degrades over time** - every response processes irrelevant history
- **Security vulnerability** - one carefully crafted prompt could expose your entire project

### MCP Agent Maestro's Ephemeral Agents
Each agent is purpose-built for a single task:
- **Minimal, focused context** - only what's needed for the specific task
- **Crystal clear objectives** - one task, one goal, no ambiguity
- **Deterministic behavior** - limited context means predictable outputs
- **Consistently fast responses** - no context bloat to slow things down
- **Secure by design** - agents literally cannot access what they don't need

### A Practical Example

**Traditional Approach**: "Update the user authentication system"
```
Agent: I'll update your auth system. I see from our previous conversation about 
database migrations, UI components, API endpoints, deployment scripts, and that 
bug in the payment system... wait, which auth approach did we decide on? Let me 
try to piece this together from our 50+ message history...

[Agent produces confused implementation mixing multiple patterns]
```

**MCP Agent Maestro Approach**: Same request, broken into focused tasks
```
Agent 1 (Database): Create auth tables with exactly these fields...
Agent 2 (API): Implement /auth endpoints following REST patterns...
Agent 3 (Frontend): Build login forms using existing component library...
Agent 4 (Tests): Write auth tests covering these specific scenarios...
Agent 5 (Integration): Connect components following documented interfaces...

[Each agent completes their specific task without confusion]
```

## The Theory Behind Linear Decomposition

### The Philosophy: Short-Lived Agents, Granular Tasks

Most AI development approaches suffer from a fundamental flaw: they try to maintain massive context windows with a single, long-running agent. This leads to:

- **Context pollution** - Irrelevant information drowns out what matters
- **Hallucination risks** - Agents invent connections between unrelated parts
- **Security vulnerabilities** - Agents with full context can be manipulated
- **Performance degradation** - Large contexts slow down reasoning
- **Unpredictable behavior** - Too much context creates chaos

### Our Solution: Ephemeral Agents with Shared Memory

MCP Agent Maestro implements a radically different approach:

**Short-Lived, Focused Agents**  
Each agent lives only as long as their specific task. They:
- Start with minimal context (just what they need)
- Execute granular, linear tasks with clear boundaries
- Document their work in shared memory
- Terminate upon completion

**Shared Knowledge Graph (RAG)**  
Instead of cramming everything into context windows:
- Persistent memory stores all project knowledge
- Agents query only what's relevant to their task
- Knowledge accumulates without overwhelming any single agent
- Clear separation between working memory and reference material

**Result**: Agents that are fast, focused, and safe. They can't be manipulated to reveal full project details because they never have access to it all at once.

### Why This Matters for Safety

Traditional long-context agents are like giving someone your entire codebase, documentation, and secrets in one conversation. Our approach is like having specialized contractors who only see the blueprint for their specific room.

- **Reduced attack surface** - Agents can't leak what they don't know
- **Deterministic behavior** - Limited context means predictable outputs
- **Audit trails** - Every agent action is logged and traceable
- **Rollback capability** - Mistakes are isolated to specific tasks

### The Cleanup Protocol: Keeping Your System Lean

MCP Agent Maestro enforces strict lifecycle management:

**Maximum 10 Active Agents**
- Hard limit prevents resource exhaustion
- Forces thoughtful task allocation
- Maintains system performance

**Automatic Cleanup Rules**
- Agent finishes task → Immediately terminated
- Agent idle 60+ seconds → Killed and task reassigned
- Need more than 10 agents → Least productive agents removed

**Why This Matters**
- **No zombie processes** eating resources
- **Fresh context** for every task
- **Predictable resource usage**
- **Clean system state** always

This isn't just housekeeping - it's fundamental to the security and performance benefits of the short-lived agent model.

### The Fundamental Principle

**Any task that cannot be expressed as `Step 1 → Step 2 → Step N` is not atomic enough.**

This principle drives everything in MCP Agent Maestro:

1. **Complex goals** must decompose into **linear sequences**
2. **Linear sequences** can execute **in parallel** when independent
3. **Each step** must have **clear prerequisites** and **deterministic outputs**
4. **Integration points** are **explicit** and **well-defined**

### Why Linear Decomposition Works

**Traditional Approach**: "Build a user authentication system"
- Vague requirements lead to varied implementations
- Agents make different assumptions
- Integration becomes a nightmare

**MCP Agent Maestro Approach**: 
```
Chain 1: Database Layer
  1.1: Create users table with id, email, password_hash
  1.2: Add unique index on email
  1.3: Create sessions table with user_id, token, expiry
  1.4: Write migration scripts
  
Chain 2: API Layer  
  2.1: Implement POST /auth/register endpoint
  2.2: Implement POST /auth/login endpoint
  2.3: Implement POST /auth/logout endpoint
  2.4: Add JWT token generation
  
Chain 3: Frontend Layer
  3.1: Create AuthContext provider
  3.2: Build LoginForm component
  3.3: Build RegisterForm component
  3.4: Implement protected routes
```

Each step is atomic, testable, and has zero ambiguity. Multiple agents can work these chains in parallel without conflict.

## Why Developers Choose Agent-MCP

**The Power of Parallel Development**  
Instead of waiting for one agent to finish the backend before starting the frontend, deploy specialized agents to work simultaneously. Your development speed is limited only by how well you decompose tasks.

**No More Lost Context**  
Every decision, implementation detail, and architectural choice is stored in the shared knowledge graph. New agents instantly understand the project state without reading through lengthy conversation histories.

**Predictable, Reliable Outputs**  
Focused agents with limited context produce consistent results. The same task produces the same quality output every time, making development predictable and testable.

**Built-in Conflict Prevention**  
File-level locking and task assignment prevent agents from stepping on each other's work. No more merge conflicts from simultaneous edits.

**Complete Development Transparency**  
Watch your AI team work in real-time through the dashboard. Every action is logged, every decision traceable. It's like having a live view into your development pipeline.

**For Different Team Sizes**

**Solo Developers**: Transform one AI assistant into a coordinated team. Work on multiple features simultaneously without losing track.

**Small Teams**: Augment human developers with AI specialists that maintain perfect context across sessions.

**Large Projects**: Handle complex systems where no single agent could hold all the context. The shared memory scales infinitely.

**Learning & Teaching**: Perfect for understanding software architecture. Watch how tasks decompose and integrate in real-time.

## System Requirements

- **Python**: 3.10+ with pip or uv
- **Node.js**: 18.0.0+ (recommended: 22.16.0)
- **npm**: 9.0.0+ (recommended: 10.9.2)
- **OpenAI API key** (for embeddings and RAG)
- **RAM**: 4GB minimum
- **AI coding assistant**: Claude Code or Cursor

For consistent development environment:
```bash
# Using nvm (Node Version Manager)
nvm use  # Automatically uses Node v22.16.0 from .nvmrc

# Or manually check versions
node --version  # Should be >=18.0.0
npm --version   # Should be >=9.0.0
python --version  # Should be >=3.10
```

## Troubleshooting

**"Admin token not found"**  
Check the server startup logs - token is displayed when MCP server starts.

**"Worker can't access tasks"**  
Ensure you're using the worker token (not admin token) when initializing workers.

**"Agents overwriting each other"**  
Verify all workers are initialized with the `--worker` flag for proper coordination.

**"Dashboard connection failed"**  
1. Ensure MCP server is running first
2. Check Node.js version (18+ required)
3. Reinstall dashboard dependencies

**"Memory queries returning stale data"**  
Run memory garbage collection through the dashboard or restart with `--refresh-memory`.

## Documentation

- [Setup Guide](./docs/setup/README.md) - **Start here!** Complete installation and setup instructions
- [Getting Started Guide](./docs/getting-started.md) - Complete walkthrough with examples
- [Configuration Guide](./docs/setup/CONFIGURATION.md) - Configuration reference
- [Troubleshooting Guide](./docs/setup/TROUBLESHOOTING.md) - Common issues and solutions
- [MCD Creation Guide](./docs/mcd-guide.md) - Write effective project blueprints
- [Theoretical Foundation](./docs/chapter-1-cognitive-empathy.md) - Understanding AI cognition
- [Architecture Overview](./docs/architecture.md) - System design and components
- [API Reference](./docs/api-reference.md) - Complete technical documentation

## Community and Support

**Get Help**
- [Discord Community](https://discord.gg/7Jm7nrhjGn) - Active developer discussions (original Agent-MCP community)
- [GitHub Issues](https://github.com/jreakin/mcp-agent-maestro/issues) - Bug reports and features for this fork
- [Original Project Issues](https://github.com/rinadelph/Agent-MCP/issues) - Issues for the original Agent-MCP project

**Contributing**
We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for:
- Code style and standards
- Testing requirements
- Pull request process
- Development setup

## License

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

**What this means:**
- ✅ You can use, modify, and distribute this software
- ✅ You can use it for commercial purposes
- ⚠️ **Important**: If you run a modified version on a server that users interact with over a network, you **must** provide the source code to those users
- ⚠️ Any derivative works must also be licensed under AGPL-3.0
- ⚠️ You must include copyright notices and license information

See the [LICENSE](LICENSE) file for complete terms and conditions.

**Why AGPL?** We chose AGPL to ensure that improvements to Agent-MCP benefit the entire community, even when used in server/SaaS deployments. This prevents proprietary forks that don't contribute back to the ecosystem.

---

Built by developers who believe AI collaboration should be as sophisticated as human collaboration.