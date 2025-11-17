# MCP Agent Maestro - Frequently Asked Questions

## General Questions

### What is MCP Agent Maestro?

MCP Agent Maestro is a sophisticated multi-agent orchestration framework that coordinates specialized AI agents to work harmoniously on complex software development tasks. Like a conductor leading an orchestra, Maestro ensures each agent performs its part at the right time.

### How is it different from other AI coding assistants?

Unlike traditional single-agent assistants, MCP Agent Maestro uses multiple specialized agents that work in parallel. Each agent is a virtuoso in their domain (frontend, backend, testing, etc.), and they coordinate through a shared knowledge graph. This enables:
- Parallel execution of tasks
- Specialized expertise per agent
- Persistent knowledge across sessions
- Real-time visualization of agent activity

### What does "Maestro" mean in this context?

"Maestro" refers to a conductor of an orchestra. In MCP Agent Maestro, the conductor orchestrates specialized agents (like musicians) to work together harmoniously. Each agent is a specialist, and the Maestro coordinates them.

## Installation & Setup

### What are the system requirements?

- Python 3.10+ with uv package manager
- Node.js 18.0.0+
- PostgreSQL 14+ with pgvector extension
- Docker & Docker Compose (optional but recommended)
- Minimum 4GB RAM (8GB+ recommended)

### Do I need an OpenAI API key?

You can use either:
- **OpenAI API** (requires API key) - Cloud-based embeddings
- **Ollama** (no API key needed) - Local embeddings

Set `EMBEDDING_PROVIDER=ollama` to use local models.

### How do I set up the database?

The easiest way is using Docker Compose:
```bash
docker-compose up -d postgres
```

The database will be automatically initialized with the required schema and pgvector extension.

### Can I run it without Docker?

Yes, you can run it locally:
1. Install PostgreSQL with pgvector
2. Create database: `createdb agent_mcp`
3. Run: `uv run -m agent_mcp.cli --port 8080`

## Usage

### How do I create my first agent?

After starting the server, create a conductor agent:
```bash
maestro init --role conductor
```

Then create specialized agents through the API or dashboard.

### What is a Main Context Document (MCD)?

An MCD is a comprehensive blueprint for your project. It defines:
- Project phases (movements)
- Required agents (instruments)
- Technical architecture
- Task breakdowns

Think of it as the musical score that guides your AI orchestra.

### How do agents communicate?

Agents communicate through:
1. **Shared Knowledge Graph**: Primary communication medium
2. **Task Events**: Completion events trigger dependent tasks
3. **Direct Messages**: Agents can send messages when needed

Agents don't directly talk to each other - they interact through the shared memory system.

### What happens when an agent finishes a task?

1. Agent documents its work in the knowledge graph
2. Task completion event is triggered
3. Dependent tasks are automatically assigned
4. Agent is terminated (short-lived model)
5. Resources are freed up

## Technical Questions

### Why are agents short-lived?

Short-lived agents provide several benefits:
- **Security**: Agents can't access more context than needed
- **Performance**: No context bloat to slow down responses
- **Determinism**: Limited context means predictable outputs
- **Resource Efficiency**: Agents are cleaned up after tasks

### How does the knowledge graph work?

The knowledge graph uses:
- **Vector Embeddings**: Semantic search using embeddings
- **PostgreSQL + pgvector**: Production-ready storage
- **Automatic Indexing**: Code, docs, and conversations are indexed
- **Semantic Queries**: Agents query by meaning, not keywords

### What is the difference between simple and advanced embedding modes?

- **Simple Mode** (1536 dimensions):
  - Indexes markdown files and context
  - Faster and cheaper
  - Good for most use cases

- **Advanced Mode** (3072 dimensions):
  - Indexes code, tasks, and documentation
  - More accurate but slower and more expensive
  - Better for complex codebases

### How many agents can run simultaneously?

Default limit is 10 agents, but this can be configured:
```bash
AGENT_MCP_MAX_WORKERS=20  # Adjust based on resources
```

The system automatically manages agent lifecycle to prevent resource exhaustion.

### How does conflict resolution work?

File-level locking prevents agents from overwriting each other:
1. Agent requests file access
2. System checks if file is locked
3. If locked, agent works on other tasks or waits
4. Lock is released after completion
5. Other agents can now modify the file

## Troubleshooting

### Health check shows "unhealthy"

Check the `/health` endpoint for detailed status:
- Database connection issues
- Missing API keys
- Resource exhaustion
- Service startup problems

### Agents aren't being created

Possible causes:
- Agent limit reached (`max_workers`)
- Database connection issues
- Missing OpenAI API key (if using OpenAI)
- Resource constraints (CPU/RAM)

### RAG queries return no results

1. Verify RAG system is enabled: `AGENT_MCP_RAG_ENABLED=true`
2. Check if content has been indexed
3. Verify pgvector extension is installed
4. Check embedding service is available

### Dashboard won't load

1. Verify backend is running: `curl http://localhost:8080/health`
2. Check dashboard port: Default is 3000
3. Verify Node.js version: Requires 18.0.0+
4. Check browser console for errors

### Database connection errors

1. Verify database is running: `docker ps`
2. Check connection settings in `.env`
3. Verify database credentials
4. Check network connectivity

## Performance

### How can I improve performance?

1. **Use Advanced Embeddings**: Better accuracy but higher cost
2. **Increase Agent Limits**: More parallel execution
3. **Optimize Database**: Connection pooling, indexing
4. **Use Ollama**: Local embeddings reduce latency
5. **Scale Horizontally**: Multiple conductor instances

### What are typical task completion times?

Times vary based on:
- Task complexity
- Agent specialization
- Knowledge graph size
- System resources

Simple tasks: 30-60 seconds
Complex tasks: 2-5 minutes
Very complex tasks: 5-10 minutes

### How do I monitor performance?

Use the `/metrics` endpoint for Prometheus-compatible metrics:
- Agent creation/termination rates
- Task completion times
- Database pool stats
- Memory usage

## Security

### Is my code secure?

Yes, MCP Agent Maestro includes:
- Prompt injection detection
- Tool call sanitization
- Access control and authentication
- Audit logging
- Minimal context per agent (reduces attack surface)

### Where is my code stored?

Your code remains on your machine. The system stores:
- Project context and decisions (in knowledge graph)
- Task assignments and status
- Agent configurations

Code files are not stored in the database - only metadata and context.

### Can agents access my entire codebase?

No. Agents receive minimal, focused context relevant to their specific task. This is by design for security and performance.

## Integration

### Can I use this with Claude Desktop?

Yes! MCP Agent Maestro is a first-class MCP server. Configure it in Claude Desktop:

```json
{
  "mcpServers": {
    "maestro": {
      "command": "uv",
      "args": ["run", "-m", "agent_mcp.cli", "--port", "8080"]
    }
  }
}
```

### Can I use this with Cursor?

Yes, Cursor supports MCP clients. Configure MCP Agent Maestro as an MCP server in Cursor's settings.

### Can I use this in CI/CD?

Yes! The API can be integrated into CI/CD pipelines:

```yaml
- name: Run Code Review
  run: |
    curl -X POST http://localhost:8080/api/tasks \
      -d '{"task": "Review PR for security issues", "agent_role": "security"}'
```

## Licensing

### What license is MCP Agent Maestro under?

GNU Affero General Public License v3.0 (AGPL-3.0)

This means:
- Free to use for personal and commercial projects
- Can modify and distribute
- Must keep source code open
- Must share modifications
- Network use triggers copyleft (SaaS clause)

### Can I use this commercially?

Yes, as long as you comply with AGPL-3.0. If you provide network access to a modified version, you must share the source code.

## Support

### Where can I get help?

- **Discord**: [Join our community](https://discord.gg/maestro-mcp)
- **GitHub Issues**: [Report bugs or request features](https://github.com/jreakin/mcp-agent-maestro/issues)
- **Documentation**: [Read the docs](https://maestro-mcp.readthedocs.io)

### How do I report bugs?

Open an issue on GitHub with:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information
- Relevant logs

### Can I contribute?

Yes! We welcome contributions. See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Development workflow
- Code style guidelines
- Testing requirements
- Pull request process

