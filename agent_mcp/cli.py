#!/usr/bin/env python3
"""
MCP Agent Maestro CLI: Command-line interface for multi-agent collaboration.

Copyright (C) 2025 Luis Alejandro Rincon (rinadelph)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import click
import uvicorn  # For running the Starlette app in SSE mode
import anyio  # For running async functions and task groups
import os
import sys
import json
import psycopg2
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

# Load environment variables before importing other modules
# First, ensure .env file exists (will be created with defaults if missing)
# Import ensure_env_file from a separate utility to avoid circular imports
def ensure_env_file_simple(project_dir=None):
    """Simple version of ensure_env_file that doesn't require logger."""
    from pathlib import Path
    
    if project_dir:
        env_path = Path(project_dir) / ".env"
    else:
        # Search for .env in current directory and up to 3 parent directories
        current = Path.cwd()
        for level in range(4):
            candidate = current / (".." * level) / ".env"
            candidate = candidate.resolve()
            if candidate.exists():
                return candidate
        # If not found, create in current directory
        env_path = Path.cwd() / ".env"
    
    # Create .env file if it doesn't exist
    if not env_path.exists():
        print(f"Creating default .env file at: {env_path}")
        
        default_env_content = """# MCP Agent Maestro Configuration
# This file was automatically generated. Edit as needed.

# API & Server Configuration
AGENT_MCP_API_HOST=localhost
AGENT_MCP_API_PORT=8080
AGENT_MCP_DASHBOARD_PORT=3000

# Database Configuration
# For Docker: use 'postgres' as host, for local: use 'localhost'
AGENT_MCP_DB_HOST=localhost
AGENT_MCP_DB_PORT=5432
AGENT_MCP_DB_NAME=agent_mcp
AGENT_MCP_DB_USER=agent_mcp
AGENT_MCP_DB_PASSWORD=
AGENT_MCP_DB_POOL_MIN=1
AGENT_MCP_DB_POOL_MAX=10

# OpenAI Configuration (optional - leave empty if using Ollama)
# AGENT_MCP_OPENAI_API_KEY=sk-your-api-key-here
AGENT_MCP_OPENAI_MODEL=gpt-4.1-2025-04-14
AGENT_MCP_EMBEDDING_MODEL=text-embedding-3-large
AGENT_MCP_EMBEDDING_DIMENSION=1536

# Embedding Provider (openai or ollama)
# Set to 'ollama' to use local Ollama models instead of OpenAI
EMBEDDING_PROVIDER=openai

# Ollama Configuration (if using EMBEDDING_PROVIDER=ollama)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_EMBEDDING_MODEL=nomic-embed-text
# OLLAMA_CHAT_MODEL=llama3.2

# Security Configuration
AGENT_MCP_SECURITY_ENABLED=true
AGENT_MCP_SECURITY_POISON_DETECTION_ENABLED=true
AGENT_MCP_SECURITY_SCAN_TOOL_SCHEMAS=true
AGENT_MCP_SECURITY_SCAN_TOOL_RESPONSES=true
AGENT_MCP_SECURITY_SANITIZATION_MODE=remove

# RAG Configuration
AGENT_MCP_RAG_ENABLED=true
AGENT_MCP_RAG_MAX_RESULTS=13
AGENT_MCP_DISABLE_AUTO_INDEXING=false

# Logging Configuration
AGENT_MCP_LOG_LEVEL=INFO
AGENT_MCP_MCP_DEBUG=false
AGENT_MCP_LOG_FILE=mcp_server.log

# Agent Management
AGENT_MCP_MAX_WORKERS=5
AGENT_MCP_AGENT_TIMEOUT=3600

# Task Analysis
AGENT_MCP_TASK_ANALYSIS_MODEL=gpt-4.1-2025-04-14
AGENT_MCP_TASK_ANALYSIS_MAX_TOKENS=1000000

# Task Placement
AGENT_MCP_ENABLE_TASK_PLACEMENT_RAG=true
AGENT_MCP_TASK_DUPLICATION_THRESHOLD=0.8
AGENT_MCP_ALLOW_RAG_OVERRIDE=true
AGENT_MCP_TASK_PLACEMENT_RAG_TIMEOUT=5
"""
        
        try:
            env_path.parent.mkdir(parents=True, exist_ok=True)
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(default_env_content)
            print(f"Created default .env file at: {env_path}")
        except Exception as e:
            print(f"Warning: Failed to create .env file at {env_path}: {e}. Continuing with environment variables only.")
    else:
        print(f"Using existing .env file at: {env_path}")
    
    return env_path

# Ensure .env file exists in current or parent directories
env_file = ensure_env_file_simple()
print(f"Using .env file at: {env_file}")

# Load environment variables from .env file
load_dotenv(dotenv_path=str(env_file))

# Also try normal load_dotenv as fallback
load_dotenv()

# Check if API key was set (without logging the actual key)
try:
    settings = get_settings()
    api_key = (
        settings.openai_api_key.get_secret_value() 
        if settings.openai_api_key is not None 
        else None
    )
    if api_key:
        print("OPENAI_API_KEY successfully loaded from environment")
    else:
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        if embedding_provider == "ollama":
            print("Using Ollama for embeddings (no OpenAI API key needed)")
        else:
            print("OPENAI_API_KEY not found in environment (optional if using Ollama)")
except Exception:
    # Settings not yet available, skip check
    pass

# Project-specific imports
# Ensure core.config (and thus logging) is initialized early.
from .core.config import (
    logger,
    CONSOLE_LOGGING_ENABLED,
    enable_console_logging,
)  # Logger is initialized in config.py
from .core.settings import get_settings  # For lambda defaults in click options
from .core import globals as g  # For g.server_running and other globals

# Import app creation and lifecycle functions
from .app.main_app import create_app, mcp_app_instance  # mcp_app_instance for stdio
from .app.server_lifecycle import (
    start_background_tasks,
    application_startup,
    application_shutdown,
)  # application_startup is called by create_app's on_startup
from .tui.display import TUIDisplay  # Import TUI display

# Import setup commands
try:
    from .cli_setup import setup, doctor
except ImportError:
    # Setup commands are optional
    setup = None
    doctor = None

# Import database connection utilities
from .db import get_db_connection, return_connection


def get_admin_token_from_db(project_dir: str) -> Optional[str]:
    """Get the admin token from the PostgreSQL database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the admin token from project_context table
        cursor.execute(
            "SELECT value FROM project_context WHERE context_key = %s",
            ("config_admin_token",),
        )
        row = cursor.fetchone()

        if row and row["value"]:
            try:
                admin_token = json.loads(row["value"])
                if isinstance(admin_token, str) and admin_token:
                    return admin_token
            except json.JSONDecodeError:
                pass

        return None
    except psycopg2.Error as e:
        logger.error(f"Database error reading admin token: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error reading admin token from database: {e}")
        return None
    finally:
        if conn:
            return_connection(conn)


# Import MCP setup utilities
from .api.mcp_setup import MCPConfigGenerator, MCPConfigInstaller, MCPConfigVerifier, ClientType


# --- MCP Setup Command Group ---
@click.group(name="mcp-setup", help="MCP client configuration management")
def mcp_setup_group():
    """MCP Setup command group."""
    pass


@mcp_setup_group.command(name="show-config", help="Show MCP configuration for a client")
@click.option(
    "--client",
    type=click.Choice(["cursor", "claude", "windsurf", "vscode", "all"], case_sensitive=False),
    default="all",
    help="Client to show configuration for"
)
@click.option(
    "--host",
    type=str,
    default="localhost",
    help="MCP server host"
)
@click.option(
    "--port",
    type=int,
    default=8080,
    help="MCP server port"
)
@click.option(
    "--command",
    type=str,
    default="agent-mcp",
    help="Command to run MCP server"
)
@click.option(
    "--output-format",
    type=click.Choice(["json", "shell", "both"], case_sensitive=False),
    default="json",
    help="Output format"
)
@click.option(
    "--save-to-file",
    type=click.Path(file_okay=True, dir_okay=False, writable=True),
    default=None,
    help="Save configuration to file"
)
def show_config(client: str, host: str, port: int, command: str, output_format: str, save_to_file: Optional[str]):
    """Show MCP configuration for specified client(s)."""
    generator = MCPConfigGenerator(host=host, port=port, command=command)
    
    clients = ["cursor", "claude", "windsurf", "vscode"] if client == "all" else [client.lower()]
    
    configs = {}
    for clt in clients:
        try:
            config = generator.generate_config(clt)  # type: ignore
            configs[clt] = config
        except Exception as e:
            click.echo(f"Error generating config for {clt}: {e}", err=True)
            configs[clt] = None
    
    # Output
    if output_format in ["json", "both"]:
        output_json = json.dumps(configs if client == "all" else configs.get(client.lower(), {}), indent=2)
        click.echo(output_json)
        
        if save_to_file:
            with open(save_to_file, "w") as f:
                f.write(output_json)
            click.echo(f"Configuration saved to {save_to_file}", err=True)
    
    if output_format in ["shell", "both"]:
        click.echo("\n# Shell environment variables:", err=True)
        click.echo(f"export MCP_HOST={host}", err=True)
        click.echo(f"export MCP_PORT={port}", err=True)
        click.echo(f"export MCP_COMMAND={command}", err=True)


@mcp_setup_group.command(name="install", help="Install MCP configuration to a client")
@click.option(
    "--client",
    type=click.Choice(["cursor", "claude", "windsurf", "vscode"], case_sensitive=False),
    required=True,
    help="Client to install configuration for"
)
@click.option(
    "--host",
    type=str,
    default="localhost",
    help="MCP server host"
)
@click.option(
    "--port",
    type=int,
    default=8080,
    help="MCP server port"
)
@click.option(
    "--command",
    type=str,
    default="agent-mcp",
    help="Command to run MCP server"
)
@click.option(
    "--no-backup",
    is_flag=True,
    default=False,
    help="Don't create backup of existing configuration"
)
def install_config(client: str, host: str, port: int, command: str, no_backup: bool):
    """Install MCP configuration to specified client."""
    generator = MCPConfigGenerator(host=host, port=port, command=command)
    installer = MCPConfigInstaller()
    
    try:
        # Generate config
        config = generator.generate_config(client)  # type: ignore
        
        # Install config
        result = installer.install(client, config, backup=not no_backup)  # type: ignore
        
        if result["success"]:
            click.echo(f"✅ Configuration installed to {result['path']}")
            if result.get("backup_path"):
                click.echo(f"📦 Backup created at {result['backup_path']}")
        else:
            click.echo(f"❌ Failed to install configuration: {result.get('error', 'Unknown error')}", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@mcp_setup_group.command(name="verify", help="Verify MCP client configurations")
@click.option(
    "--client",
    type=click.Choice(["cursor", "claude", "windsurf", "vscode", "all"], case_sensitive=False),
    default="all",
    help="Client to verify configuration for"
)
def verify_config(client: str):
    """Verify MCP configurations for specified client(s)."""
    verifier = MCPConfigVerifier()
    
    if client == "all":
        results = verifier.verify_all()
        
        click.echo("MCP Configuration Verification:\n")
        for clt, result in results.items():
            if result["exists"]:
                if result["valid"]:
                    click.echo(f"✅ {clt}: Configuration valid at {result['path']}")
                else:
                    click.echo(f"⚠️  {clt}: Configuration exists but has errors:")
                    for error in result["errors"]:
                        click.echo(f"   - {error}")
            else:
                click.echo(f"❌ {clt}: Configuration not found")
                if result["errors"]:
                    for error in result["errors"]:
                        click.echo(f"   - {error}")
    else:
        result = verifier.verify(client)  # type: ignore
        
        if result["exists"]:
            if result["valid"]:
                click.echo(f"✅ Configuration valid at {result['path']}")
                click.echo(f"\nConfiguration:\n{json.dumps(result['config'], indent=2)}")
            else:
                click.echo(f"⚠️  Configuration exists but has errors:")
                for error in result["errors"]:
                    click.echo(f"   - {error}")
        else:
            click.echo(f"❌ Configuration not found")
            if result["errors"]:
                for error in result["errors"]:
                    click.echo(f"   - {error}")


# --- Click Command Definition ---
# This replicates the @click.command and options from the original main.py (lines 1936-1950)
@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
def main_group(ctx: click.Context):
    """MCP Agent Maestro CLI - Multi-agent collaboration framework.
    
    Orchestrating AI Agents Like a Symphony.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)


# Register setup commands if available
if setup:
    main_group.add_command(setup, name="setup")
if doctor:
    main_group.add_command(doctor, name="doctor")

# Add mcp-setup group to main group
main_group.add_command(mcp_setup_group)


@main_group.command(name="start", help="Start the MCP server")
@click.option(
    "--port",
    type=int,
<<<<<<< HEAD
    default=os.environ.get("PORT", 3000),  # Read from env var PORT if set, else 3000
=======
    default=lambda: get_settings().api_port,  # Read from settings
>>>>>>> feature/port-3000-default
    show_default=True,
    help="Port to listen on for SSE and HTTP dashboard.",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"], case_sensitive=False),
    default="sse",
    show_default=True,
    help="Transport type for MCP communication (stdio or sse).",
)
@click.option(
    "--project-dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True, writable=True),
    default=".",
    show_default=True,
    help="Project directory. The .mcp-maestro folder will be created/used here. Defaults to current directory.",
)
@click.option(
    "--admin-token",  # Renamed from admin_token_param for clarity
    "admin_token_cli",  # Variable name for the parameter
    type=str,
    default=None,
    help="Admin token for authentication. If not provided, one will be loaded from DB or generated.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=lambda: get_settings().mcp_debug,  # Default from settings
    help="Enable debug mode for the server (more verbose logging, Starlette debug pages).",
)
@click.option(
    "--no-tui",
    is_flag=True,
    default=False,
    help="Disable the terminal UI display (logs will still go to file).",
)
@click.option(
    "--advanced",
    is_flag=True,
    default=False,
    help="Enable advanced embeddings mode with larger dimension (3072) and more sophisticated code analysis.",
)
@click.option(
    "--git",
    is_flag=True,
    default=False,
    help="Enable experimental Git worktree support for parallel agent development (advanced users only).",
)
@click.option(
    "--no-index",
    is_flag=True,
    default=False,
    help="Disable automatic markdown file indexing. Allows selective manual indexing of specific content into the RAG system.",
)
def start_server(
    port: int,
    transport: str,
    project_dir: str,
    admin_token_cli: Optional[str],
    debug: bool,
    no_tui: bool,
    advanced: bool,
    git: bool,
    no_index: bool,
):
    """
    Main Command-Line Interface for starting the MCP Agent Maestro Server.

    The server supports two embedding modes:
    - Simple mode (default): Uses text-embedding-3-large (1536 dimensions) - indexes markdown files and context
    - Advanced mode (--advanced): Uses text-embedding-3-large (3072 dimensions) - includes code analysis, task indexing

    Indexing options:
    - Default: Automatic indexing of all markdown files in project directory
    - --no-index: Disable automatic markdown indexing for selective manual control

    Note: Switching between modes will require re-indexing all content.
    """
    # Set advanced embeddings mode before other imports that might use it
    if advanced:
        from .core import config

        config.ADVANCED_EMBEDDINGS = True
        # Update the dynamic configs
        config.EMBEDDING_MODEL = config.ADVANCED_EMBEDDING_MODEL
        config.EMBEDDING_DIMENSION = config.ADVANCED_EMBEDDING_DIMENSION
        logger.info(
            "Advanced embeddings mode enabled (3072 dimensions, text-embedding-3-large, code & task indexing)"
        )
    else:
        from .core.config import SIMPLE_EMBEDDING_DIMENSION, SIMPLE_EMBEDDING_MODEL

        logger.info(
            f"Using simple embeddings mode ({SIMPLE_EMBEDDING_DIMENSION} dimensions, {SIMPLE_EMBEDDING_MODEL}, markdown & context only)"
        )

    # Initialize Git worktree support if enabled
    if git:
        try:
            from .features.worktree_integration import enable_worktree_support

            worktree_enabled = enable_worktree_support()
            if worktree_enabled:
                logger.info(
                    "🌿 Git worktree support enabled for parallel agent development"
                )
            else:
                logger.warning(
                    "❌ Git worktree support could not be enabled - check requirements"
                )
                logger.warning("   Continuing without worktree support...")
        except ImportError:
            logger.error(
                "❌ Git worktree features not available - missing dependencies"
            )
            logger.warning("   Continuing without worktree support...")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Git worktree support: {e}")
            logger.warning("   Continuing without worktree support...")
    else:
        logger.info("Git worktree support disabled (use --git to enable)")

    # Set auto-indexing configuration
    if no_index:
        from .core import config

        config.DISABLE_AUTO_INDEXING = True
        logger.info(
            "Automatic markdown indexing disabled. Use manual indexing via RAG tools for selective content."
        )
    else:
        from .core import config

        config.DISABLE_AUTO_INDEXING = False
        logger.info("Automatic markdown indexing enabled.")

    if debug:
        os.environ["MCP_DEBUG"] = (
            "true"  # Ensure env var is set for Starlette debug mode
        )
        enable_console_logging()  # Enable console logging for debug mode
        logger.info(
            "Debug mode enabled via CLI flag or MCP_DEBUG environment variable."
        )
        logger.info("Console logging enabled for debug mode.")
        # Logging level might need to be adjusted here if not already handled by config.py
        # For now, config.py sets the base level. Uvicorn also has its own log level.
    else:
        os.environ["MCP_DEBUG"] = "false"

    # Determine if the TUI should be active
    # TUI is active if console logging is disabled AND --no-tui is NOT passed AND not in debug mode
    from .core.config import (
        CONSOLE_LOGGING_ENABLED as current_console_logging,
    )  # Get updated value

    tui_active = not current_console_logging and not no_tui and not debug

    if tui_active:
        logger.info(
            "TUI display mode is active. Standard console logging is suppressed."
        )
    elif current_console_logging or debug:
        logger.info("Standard console logging is enabled (TUI display mode is off).")
        print("MCP Server starting with standard console logging...")
    else:  # Console logging is off, and TUI is also off
        logger.info(
            "Console logging and TUI display are both disabled. Check log file for server messages."
        )

    # Log the embedding mode being used
    embedding_mode_info = "advanced" if advanced else "simple"
    if advanced:
        embedding_model_info = (
            config.EMBEDDING_MODEL if "config" in locals() else "text-embedding-3-large"
        )
        embedding_dim_info = (
            config.EMBEDDING_DIMENSION if "config" in locals() else 3072
        )
    else:
        from .core.config import SIMPLE_EMBEDDING_DIMENSION, SIMPLE_EMBEDDING_MODEL

        embedding_model_info = SIMPLE_EMBEDDING_MODEL
        embedding_dim_info = SIMPLE_EMBEDDING_DIMENSION

    logger.info(
        f"Attempting to start MCP Server: Port={port}, Transport={transport}, ProjectDir='{project_dir}'"
    )
    logger.info(
        f"Embedding Mode: {embedding_mode_info} (Model: {embedding_model_info}, Dimensions: {embedding_dim_info})"
    )

    # --- TUI Display Loop (if not disabled) ---
    async def tui_display_loop(
        cli_port: int,
        cli_transport: str,
        cli_project_dir: str,
        *,
        task_status=anyio.TASK_STATUS_IGNORED,
    ):
        task_status.started()
        logger.info("TUI display loop started.")
        tui = TUIDisplay()
        initial_display = True

        # Import required modules
        from .core import globals as globals_module
        from .db.actions.agent_db import get_all_active_agents_from_db
        from .db.actions.task_db import (
            get_all_tasks_from_db,
            get_task_by_id,
            get_tasks_by_agent_id,
        )
        from datetime import datetime
        from .tui.colors import TUITheme

        # Simple tracking of server status for display
        async def get_server_status():
            try:
                return {
                    "running": globals_module.server_running,
                    "status": "Running" if globals_module.server_running else "Stopped",
                    "port": cli_port,
                }
            except Exception as e:
                logger.error(f"Error getting server status: {e}")
                return {
                    "running": globals_module.server_running,
                    "status": "Error",
                    "port": cli_port,
                }

        try:
            # Wait a moment for server initialization to complete
            await anyio.sleep(2)

            # Setup alternate screen and hide cursor for smoother display
            tui.enable_alternate_screen()
            tui.hide_cursor()

            first_draw = True

            while globals_module.server_running:
                server_status = await get_server_status()

                # Clear screen only on first draw
                if first_draw:
                    tui.clear_screen()
                    first_draw = False

                # Move to top and redraw
                tui.move_cursor(1, 1)
                current_row = tui.draw_header(clear_first=False)

                # Position cursor for status bar
                tui.move_cursor(current_row, 1)
                tui.draw_status_bar(server_status)
                current_row += 2

                # Display simplified server info
                tui.move_cursor(current_row, 1)
                tui.clear_line()
                print(TUITheme.header(" MCP Server Running"))
                current_row += 2

                tui.move_cursor(current_row, 1)
                tui.clear_line()
                print(f"Project Directory: {TUITheme.info(cli_project_dir)}")
                current_row += 1

                tui.move_cursor(current_row, 1)
                tui.clear_line()
                print(f"Transport: {TUITheme.info(cli_transport)}")
                current_row += 1

                tui.move_cursor(current_row, 1)
                tui.clear_line()
                print(f"MCP Port: {TUITheme.info(str(cli_port))}")
                current_row += 1

                # Display admin token
                admin_token = get_admin_token_from_db(cli_project_dir)
                if admin_token:
                    tui.move_cursor(current_row, 1)
                    tui.clear_line()
                    print(f"Admin Token: {TUITheme.info(admin_token)}")
                    current_row += 1

                current_row += 2

                # Display dashboard instructions
                tui.move_cursor(current_row, 1)
                tui.clear_line()
                print(TUITheme.header(" Next Steps"))
                current_row += 2

                tui.move_cursor(current_row, 1)
                tui.clear_line()
                print("1. Open a new terminal window")
                current_row += 1

                tui.move_cursor(current_row, 1)
                tui.clear_line()
                dashboard_path = (
                    f"{cli_project_dir}/agent_mcp/dashboard"
                    if cli_project_dir != "."
                    else "agent_mcp/dashboard"
                )
                print(f"2. Navigate to: {TUITheme.info(dashboard_path)}")
                current_row += 1

                tui.move_cursor(current_row, 1)
                tui.clear_line()
                print(f"3. Run: {TUITheme.bold('npm run dev')}")
                current_row += 1

                tui.move_cursor(current_row, 1)
                tui.clear_line()
                print(f"4. Open: {TUITheme.info('http://localhost:3847')}")
                current_row += 3

                tui.move_cursor(current_row, 1)
                tui.clear_line()
                print(
                    TUITheme.warning(
                        "Keep this MCP server running while using the dashboard"
                    )
                )
                current_row += 2

                tui.move_cursor(current_row, 1)
                tui.clear_line()
                print(TUITheme.info("Press Ctrl+C to stop the MCP server"))
                current_row += 1

                # Clear remaining lines to prevent artifacts
                for row in range(current_row, tui.terminal_height):
                    tui.move_cursor(row, 1)
                    tui.clear_line()

                if initial_display:
                    initial_display = False

                await anyio.sleep(5)  # Refresh less frequently since display is simpler
        except anyio.get_cancelled_exc_class():
            logger.info("TUI display loop cancelled.")
        finally:
            # Cleanup the terminal
            tui.show_cursor()
            tui.disable_alternate_screen()
            tui.clear_screen()
            print("MCP Server TUI has exited.")
            logger.info("TUI display loop finished.")

    # The application_startup logic (including setting MCP_PROJECT_DIR env var,
    # DB init, admin token handling, state loading, OpenAI init, VSS check, signal handlers)
    # is now part of the Starlette app's on_startup event, triggered by create_app.

    if transport == "sse":
        # Create the Starlette application instance.
        # `application_startup` will be called by Starlette during its startup phase.
        starlette_app = create_app(
            project_dir=project_dir, admin_token_cli=admin_token_cli
        )

        # Uvicorn configuration
        # log_config=None prevents Uvicorn from overriding our logging setup from config.py
        # (Original main.py:2630)
        uvicorn_config = uvicorn.Config(
            starlette_app,
            host="0.0.0.0",  # Listen on all available interfaces
            port=port,
            log_config=None,  # Use our custom logging setup
            access_log=False,  # Disable access logs
            lifespan="on",  # Ensure Starlette's on_startup/on_shutdown are used
        )
        server = uvicorn.Server(uvicorn_config)

        # Run Uvicorn server with background tasks managed by an AnyIO task group
        # This replaces the original run_server_with_background_tasks (main.py:2624)
        async def run_sse_server_with_bg_tasks():
            nonlocal server  # Allow modification if server needs to be accessed (e.g. server.should_exit)
            try:
                async with anyio.create_task_group() as tg:
                    # Start background tasks (e.g., RAG indexer)
                    # `application_startup` (called by Starlette) prepares everything.
                    # `start_background_tasks` actually launches them in the task group.
                    await start_background_tasks(tg)

                    # Start TUI display loop if enabled
                    if tui_active:
                        await tg.start(tui_display_loop, port, transport, project_dir)

                    # Start the Uvicorn server
                    logger.info(
                        f"Starting Uvicorn server for SSE transport on http://0.0.0.0:{port}"
                    )
                    logger.info(f"Dashboard available at http://localhost:{port}")
                    logger.info(
                        f"Admin token will be displayed by server startup sequence if generated/loaded."
                    )
                    logger.info("Press Ctrl+C to shut down the server gracefully.")

                    # Show standard startup messages only if TUI is not active
                    if not tui_active:
                        # Show AGENT MCP banner
                        from .tui.colors import get_responsive_agent_mcp_banner

                        print()
                        print(get_responsive_agent_mcp_banner())
                        print()
                        print(f"🚀 MCP Server running on port {port}")
                        print(f"📁 Project: {project_dir}")

                        # Display admin token from database
                        admin_token = get_admin_token_from_db(project_dir)
                        if admin_token:
                            print(f"🔑 Admin Token: {admin_token}")

                        print()
                        print("Next steps:")
                        dashboard_path = (
                            f"{project_dir}/agent_mcp/dashboard"
                            if project_dir != "."
                            else "agent_mcp/dashboard"
                        )
                        print(f"1. Open new terminal → cd {dashboard_path}")
                        print("2. Run: npm run dev")
                        print("3. Open: http://localhost:3847")
                        print()
                        print("Keep this server running. Press Ctrl+C to quit.")

                    await server.serve()

                    # This part is reached after server.serve() finishes (e.g., on shutdown signal)
                    logger.info(
                        "Uvicorn server has stopped. Waiting for background tasks to finalize..."
                    )
            except Exception as e:  # Catch errors during server run or task group setup
                logger.critical(
                    f"Fatal error during SSE server execution: {e}", exc_info=True
                )
                # Ensure g.server_running is false so other parts know to stop
                g.server_running = False
                # Consider re-raising or exiting if this is a critical unrecoverable error
            finally:
                logger.info("SSE server and background task group scope exited.")
                # application_shutdown is called by Starlette's on_shutdown event.

        try:
            anyio.run(run_sse_server_with_bg_tasks)
        except (
            KeyboardInterrupt
        ):  # Should be handled by signal handlers and graceful shutdown
            logger.info(
                "Keyboard interrupt received by AnyIO runner. Server should be shutting down."
            )
        except SystemExit as e:  # Catch SystemExit from application_startup
            logger.error(f"SystemExit caught: {e}. Server will not start.")
            if tui_active:
                tui = TUIDisplay()
                tui.clear_screen()
            sys.exit(e.code if isinstance(e.code, int) else 1)

    elif transport == "stdio":
        # Handle stdio transport (Original main.py:2639-2656 - arun function)
        # For stdio, we don't use Uvicorn or Starlette's HTTP capabilities.
        # We directly run the MCPLowLevelServer with stdio streams.

        async def run_stdio_server_with_bg_tasks():
            try:
                # Perform application startup manually for stdio mode as Starlette lifecycle isn't used.
                await application_startup(
                    project_dir_path_str=project_dir, admin_token_param=admin_token_cli
                )

                async with anyio.create_task_group() as tg:
                    await start_background_tasks(tg)  # Start RAG indexer etc.

                    # Start TUI display loop if enabled
                    if tui_active:
                        await tg.start(
                            tui_display_loop, 0, transport, project_dir
                        )  # Port is 0 for stdio

                    logger.info("Starting MCP server with stdio transport.")
                    logger.info("Press Ctrl+C to shut down.")

                    # Show standard startup messages only if TUI is not active
                    if not tui_active:
                        # Show AGENT MCP banner
                        from .tui.colors import get_responsive_agent_mcp_banner

                        print()
                        print(get_responsive_agent_mcp_banner())
                        print()
                        print("🚀 MCP Server running (stdio transport)")
                        print("Server is ready for AI assistant connections.")

                        # Display admin token from database
                        admin_token = get_admin_token_from_db(project_dir)
                        if admin_token:
                            print(f"🔑 Admin Token: {admin_token}")

                        print("Use Ctrl+C to quit.")

                    # Import stdio_server from mcp library
                    try:
                        from mcp.server.stdio import stdio_server
                    except ImportError:
                        logger.error(
                            "Failed to import mcp.server.stdio. Stdio transport is unavailable."
                        )
                        return

                    try:
                        async with stdio_server() as streams:
                            # mcp_app_instance is created in main_app.py and imported
                            await mcp_app_instance.run(
                                streams[0],  # input_stream
                                streams[1],  # output_stream
                                mcp_app_instance.create_initialization_options(),
                            )
                    except (
                        Exception
                    ) as e_mcp_run:  # Catch errors from mcp_app_instance.run
                        logger.error(
                            f"Error during MCP stdio server run: {e_mcp_run}",
                            exc_info=True,
                        )
                    finally:
                        logger.info("MCP stdio server run finished.")
                        # Ensure g.server_running is false to stop background tasks
                        g.server_running = False

            except Exception as e:  # Catch errors during stdio setup or task group
                logger.critical(
                    f"Fatal error during stdio server execution: {e}", exc_info=True
                )
                g.server_running = False
            finally:
                logger.info("Stdio server and background task group scope exited.")
                # Manually call application_shutdown for stdio mode
                await application_shutdown()

        try:
            anyio.run(run_stdio_server_with_bg_tasks)
        except KeyboardInterrupt:
            logger.info(
                "Keyboard interrupt received by AnyIO runner for stdio. Server should be shutting down."
            )
        except SystemExit as e:  # Catch SystemExit from application_startup
            logger.error(f"SystemExit caught: {e}. Server will not start.")
            if tui_active:
                tui = TUIDisplay()
                tui.clear_screen()
            sys.exit(e.code if isinstance(e.code, int) else 1)

    else:  # Should not happen due to click.Choice
        logger.error(f"Invalid transport type specified: {transport}")
        click.echo(
            f"Error: Invalid transport type '{transport}'. Choose 'stdio' or 'sse'.",
            err=True,
        )
        sys.exit(1)

    logger.info("MCP Server has shut down.")

    # Clear console one last time if TUI was active
    if tui_active:
        tui = TUIDisplay()
        tui.clear_screen()

    sys.exit(0)  # Explicitly exit after cleanup if not already exited by SystemExit


# Add MCP setup group to main group
main_group.add_command(mcp_setup_group)

# Backwards compatibility: allow direct invocation
@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--port",
    type=int,
    default=lambda: get_settings().api_port,
    show_default=True,
    help="Port to listen on for SSE and HTTP dashboard.",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"], case_sensitive=False),
    default="sse",
    show_default=True,
    help="Transport type for MCP communication (stdio or sse).",
)
@click.option(
    "--project-dir",
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True, writable=True),
    default=".",
    show_default=True,
    help="Project directory. The .mcp-maestro folder will be created/used here. Defaults to current directory.",
)
@click.option(
    "--admin-token",
    "admin_token_cli",
    type=str,
    default=None,
    help="Admin token for authentication. If not provided, one will be loaded from DB or generated.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=lambda: get_settings().mcp_debug,
    help="Enable debug mode for the server (more verbose logging, Starlette debug pages).",
)
@click.option(
    "--no-tui",
    is_flag=True,
    default=False,
    help="Disable the terminal UI display (logs will still go to file).",
)
@click.option(
    "--advanced",
    is_flag=True,
    default=False,
    help="Enable advanced embeddings mode with larger dimension (3072) and more sophisticated code analysis.",
)
@click.option(
    "--git",
    is_flag=True,
    default=False,
    help="Enable experimental Git worktree support for parallel agent development (advanced users only).",
)
@click.option(
    "--no-index",
    is_flag=True,
    default=False,
    help="Disable automatic markdown file indexing. Allows selective manual indexing of specific content into the RAG system.",
)
def main_cli(
    port: int,
    transport: str,
    project_dir: str,
    admin_token_cli: Optional[str],
    debug: bool,
    no_tui: bool,
    advanced: bool,
    git: bool,
    no_index: bool,
):
    """Main CLI entry point (backwards compatibility)."""
    start_server(
        port=port,
        transport=transport,
        project_dir=project_dir,
        admin_token_cli=admin_token_cli,
        debug=debug,
        no_tui=no_tui,
        advanced=advanced,
        git=git,
        no_index=no_index,
    )


# This allows running `python -m agent_mcp.cli --port ...` or `python -m agent_mcp.cli mcp-setup show-config`
if __name__ == "__main__":
    # Check if command is mcp-setup or start, use group; otherwise use main_cli for backwards compatibility
    if len(sys.argv) > 1 and sys.argv[1] in ["mcp-setup", "start"]:
        main_group()
    else:
        # Backwards compatibility: if no command specified, assume they want to start the server
        # Insert "start" as the first argument if no command is given
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            # If first arg doesn't start with -, it might be a command we don't recognize, use main_cli
            main_cli()
        else:
            # No command given, insert "start" and use group
            sys.argv.insert(1, "start")
            main_group()
