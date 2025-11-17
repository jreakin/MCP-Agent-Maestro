# Testing GitHub Actions Workflows Locally

This guide explains how to test GitHub Actions workflows locally using `act`.

## Prerequisites

### Install `act`

**On macOS (using Homebrew):**
```bash
brew install act
```

**On Linux:**
```bash
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

**On Windows (using Chocolatey):**
```bash
choco install act-cli
```

**Or download from releases:**
- Visit: https://github.com/nektos/act/releases

### Install Docker

`act` requires Docker to be running. Install Docker Desktop:
- macOS/Windows: https://www.docker.com/products/docker-desktop
- Linux: Follow Docker installation guide for your distribution

## Testing Individual Workflows

### Test the Unit Tests Workflow

```bash
# List available workflows
act -l

# Run the tests workflow (dry run to see what would execute)
act push --workflows .github/workflows/tests.yml --dryrun

# Run the tests workflow (actual execution)
act push --workflows .github/workflows/tests.yml

# Run on a specific event
act push -W .github/workflows/tests.yml
```

### Test the Deployment Check Workflow

```bash
# Run the deploy-check workflow
act push --workflows .github/workflows/deploy-check.yml

# Or run manually
act workflow_dispatch -W .github/workflows/deploy-check.yml
```

## Using GitHub Secrets Locally

Create a `.secrets` file in the project root to provide secrets locally:

```bash
# Create .secrets file (add to .gitignore!)
cat > .secrets << EOF
OPENAI_API_KEY=your-actual-api-key-here
EOF

# Run with secrets
act push -W .github/workflows/tests.yml --secret-file .secrets
```

Or use environment variables:

```bash
export OPENAI_API_KEY="your-key-here"
act push -W .github/workflows/tests.yml
```

## Common `act` Commands

```bash
# List all workflows and their jobs
act -l

# Run a specific job from a workflow
act push -j test -W .github/workflows/tests.yml

# Run with verbose output
act push -W .github/workflows/tests.yml -v

# Use a specific GitHub Actions runner image
act push -W .github/workflows/tests.yml -P ubuntu-latest=catthehacker/ubuntu:act-latest

# Run with larger timeout (for longer-running tests)
act push -W .github/workflows/tests.yml --timeout 30m
```

## Troubleshooting

### Docker Not Running
```bash
# Start Docker Desktop, or on Linux:
sudo systemctl start docker
```

### PostgreSQL Service Issues
If PostgreSQL service doesn't start correctly in `act`, you may need to:
- Use a different Docker image tag
- Adjust port mappings
- Check Docker logs: `docker ps` and `docker logs <container-id>`

### Permission Issues on Linux
```bash
# Add your user to docker group
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

### Act Version Issues
Make sure you have a recent version:
```bash
act --version
# Should be >= 0.2.40 for GitHub Actions v3 support
```

## Alternative: Manual Workflow Testing

You can also manually run the workflow steps:

```bash
# Set up Python
python3 --version  # Should be 3.10+

# Install uv
pip install uv

# Install dependencies
uv pip install --system -e ".[dev]"

# Set environment variables
export AGENT_MCP_DB_HOST=localhost
export AGENT_MCP_DB_PORT=5432
export AGENT_MCP_DB_NAME=agent_mcp
export AGENT_MCP_DB_USER=agent_mcp
export AGENT_MCP_DB_PASSWORD=agent_mcp_password

# Start PostgreSQL (using Docker)
docker run -d --name test-postgres \
  -e POSTGRES_DB=agent_mcp \
  -e POSTGRES_USER=agent_mcp \
  -e POSTGRES_PASSWORD=agent_mcp_password \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Wait for PostgreSQL
until pg_isready -h localhost -p 5432 -U agent_mcp; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

# Initialize database
python3 -c "from agent_mcp.db.postgres_schema import init_database; init_database()"

# Run tests
uv run pytest tests/ --ignore=tests/benchmarks -v
```

