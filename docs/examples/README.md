# Example Files

This directory contains example configuration files and integration patterns.

## Files

- **`INTEGRATION_EXAMPLE.yml`**: Example Docker Compose configuration showing how to integrate MCP Agent Maestro into an existing project's docker-compose.yml.

- **`mcp.json`**: Example MCP client configuration file for connecting to MCP Agent Maestro from Claude Code, Cursor, or other MCP-compatible clients.

## Usage

### Integration Example

To integrate MCP Agent Maestro into your project:

1. Copy the relevant services from `INTEGRATION_EXAMPLE.yml` into your project's `docker-compose.yml`
2. Update network names, container names, and environment variables as needed
3. See `../INTEGRATION_GUIDE.md` for detailed instructions

### MCP Client Configuration

To connect an MCP client to MCP Agent Maestro:

1. Copy `mcp.json` to your client's configuration directory:
   - **Cursor**: `~/.config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/claude_desktop_config.json`
   - **Claude Code**: `~/.config/Claude/claude_desktop_config.json`
   - **Windsurf**: Platform-specific (see MCP setup documentation)

2. Update the URL to match your MCP Agent Maestro server address
3. See `../MCP_SETUP_CURSOR_VSCODE.md` for detailed setup instructions

