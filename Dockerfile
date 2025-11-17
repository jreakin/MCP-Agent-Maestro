# MCP Agent Maestro Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (separate layer for better caching)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    clang \
    llvm \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management (cached layer)
RUN pip install --no-cache-dir uv

# Copy dependency files first (for better layer caching)
# This layer only changes when dependencies change
COPY pyproject.toml ./
COPY uv.lock* ./

# Install Python dependencies (including dev dependencies for testing tools and pydantic-ai)
# This layer is cached unless pyproject.toml or uv.lock changes
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -e ".[dev,pydantic-ai]"

# Copy application code last (changes most frequently)
# Only this layer invalidates when code changes
COPY . .

# Create directory for project data
RUN mkdir -p /app/project-data

# Expose default port
EXPOSE 3000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=3000
ENV AGENT_MCP_API_PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/api/status || exit 1

# Run the application with port from environment variable
CMD ["sh", "-c", "uv run -m agent_mcp.cli --port ${PORT:-3000} --project-dir /app/project-data"]
