# npm Package Verification Guide

This document describes how to verify the Agent-MCP npm package installation and MCP setup feature.

## Package Structure

The npm package (`@rinadelph/agent-mcp`) includes:
- `bin/agent-mcp` - CLI binary wrapper
- `scripts/postinstall.js` - Post-install setup script
- Python package files
- Configuration files

## Installation Verification

### 1. Install Package

```bash
# Global installation
npm install -g @rinadelph/agent-mcp

# Or local installation
npm install @rinadelph/agent-mcp
```

### 2. Verify Installation

```bash
# Check if binary is available
which agent-mcp
# or
agent-mcp --version

# Check Python environment
agent-mcp --help
```

### 3. Verify Python Dependencies

```bash
# The postinstall script should have set up the Python environment
# Verify it exists
ls -la .venv/

# Test Python CLI directly
uv run python -m agent_mcp.cli --help
```

## MCP Setup Feature Verification

### 1. Show Configuration

```bash
# Show config for Cursor
agent-mcp mcp-setup show-config --client cursor

# Show config for Claude Desktop
agent-mcp mcp-setup show-config --client claude

# Show config for all clients
agent-mcp mcp-setup show-config --all
```

### 2. Install Configuration

```bash
# Install to Cursor
agent-mcp mcp-setup install --client cursor

# Install to Claude Desktop
agent-mcp mcp-setup install --client claude

# Install with custom options
agent-mcp mcp-setup install --client cursor --host localhost --port 8080
```

### 3. Verify Configuration

```bash
# Verify all configurations
agent-mcp mcp-setup verify

# Verify specific client
agent-mcp mcp-setup verify --client cursor
```

## Expected Behavior

### Post-Install Script

1. ✅ Checks for Python 3.10+
2. ✅ Checks for `uv` package manager
3. ✅ Creates virtual environment if needed
4. ✅ Installs Python dependencies
5. ✅ Provides setup instructions

### MCP Setup Commands

1. ✅ `show-config` generates valid JSON configuration
2. ✅ `install` writes to correct config file locations
3. ✅ `verify` checks existing configurations
4. ✅ Handles all supported clients (Cursor, Claude, Windsurf, VS Code)

## Troubleshooting

### Issue: Binary not found after install

**Solution**: Ensure npm bin directory is in PATH
```bash
npm config get prefix
# Add to PATH: export PATH="$(npm config get prefix)/bin:$PATH"
```

### Issue: Python not found

**Solution**: Install Python 3.10+ and ensure it's in PATH
```bash
python3 --version  # Should show 3.10+
```

### Issue: uv not found

**Solution**: Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Issue: MCP config not installing

**Solution**: Check file permissions and config file locations
```bash
# Check config file exists
ls -la ~/.cursor/mcp.json  # Cursor
ls -la ~/Library/Application\ Support/Claude/claude_desktop_config.json  # Claude (macOS)
```

## Testing Checklist

- [ ] Package installs without errors
- [ ] Post-install script runs successfully
- [ ] Binary is accessible via `agent-mcp` command
- [ ] `agent-mcp --help` shows help text
- [ ] `agent-mcp mcp-setup show-config --client cursor` generates valid JSON
- [ ] `agent-mcp mcp-setup install --client cursor` installs config
- [ ] `agent-mcp mcp-setup verify` verifies configurations
- [ ] Server starts with `agent-mcp server --project-dir .`

## CI/CD Verification

The package should be tested in CI/CD:
1. Install package in clean environment
2. Run postinstall script
3. Verify all commands work
4. Test MCP setup feature
5. Verify server starts

