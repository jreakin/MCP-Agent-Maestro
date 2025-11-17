#!/usr/bin/env python3
"""
Agent-MCP Setup CLI Commands
Interactive setup wizard for easy configuration
"""
import click
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
import httpx

from ..core.config import logger


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    try:
        subprocess.run(
            [command, "--version"],
            capture_output=True,
            check=True,
            timeout=5
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_service_running(url: str, timeout: float = 2.0) -> bool:
    """Check if a service is running at the given URL."""
    if httpx is None:
        # Fallback to curl if httpx not available
        try:
            result = subprocess.run(
                ["curl", "-s", "-f", "-m", str(timeout), url],
                capture_output=True,
                timeout=timeout + 1
            )
            return result.returncode == 0
        except Exception:
            return False
    
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        return response.status_code < 500
    except Exception:
        return False


def detect_ollama_models() -> tuple[Optional[str], Optional[str]]:
    """Detect available Ollama models."""
    try:
        if httpx:
            response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = [model.get("name", "").split(":")[0] for model in data.get("models", [])]
            else:
                return None, None
        else:
            # Fallback to curl
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return None, None
            import json
            data = json.loads(result.stdout)
            models = [model.get("name", "").split(":")[0] for model in data.get("models", [])]
        
        embedding_model = None
        chat_model = None
        
        # Prefer nomic-embed-text for embeddings
        if "nomic-embed-text" in models:
            embedding_model = "nomic-embed-text"
        elif models:
            embedding_model = models[0]  # Fallback to first model
        
        # Prefer llama3.2 for chat
        if "llama3.2" in models:
            chat_model = "llama3.2"
        elif "llama3" in models:
            chat_model = "llama3"
        elif "llama" in str(models):
            chat_model = next((m for m in models if "llama" in m.lower()), models[0] if models else None)
        elif models:
            chat_model = models[0]  # Fallback to first model
        
        return embedding_model, chat_model
    except Exception as e:
        if logger:
            logger.debug(f"Could not detect Ollama models: {e}")
    
    return None, None


@click.command()
@click.option(
    "--provider",
    type=click.Choice(["openai", "ollama", "auto"]),
    default="auto",
    help="AI provider to use (auto detects available providers)"
)
@click.option(
    "--openai-key",
    help="OpenAI API key (if not provided, will prompt)"
)
@click.option(
    "--db-password",
    default="agent_mcp_password",
    help="Database password"
)
@click.option(
    "--port",
    default=8080,
    type=int,
    help="Agent-MCP port"
)
@click.option(
    "--db-port",
    default=5433,
    type=int,
    help="PostgreSQL port on host"
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Non-interactive mode (uses defaults or fails)"
)
@click.option(
    "--output",
    default=".env",
    help="Output file for environment variables"
)
def setup(
    provider: str,
    openai_key: Optional[str],
    db_password: str,
    port: int,
    db_port: int,
    non_interactive: bool,
    output: str
):
    """Interactive setup wizard for Agent-MCP."""
    
    click.echo("\n" + "="*60)
    click.echo(click.style("Agent-MCP Setup Wizard", fg="cyan", bold=True))
    click.echo("="*60 + "\n")
    
    env_file = Path(output)
    env_vars = {}
    
    # Load existing .env if it exists
    if env_file.exists() and not non_interactive:
        click.echo(click.style("⚠ ", fg="yellow") + f"Found existing {output}")
        overwrite = click.confirm("Overwrite existing configuration?", default=False)
        if not overwrite:
            click.echo("Setup cancelled.")
            return
        # Load existing values as defaults
        from dotenv import dotenv_values
        existing = dotenv_values(env_file)
        env_vars.update(existing)
    
    # Step 1: Choose AI Provider
    if provider == "auto":
        click.echo(click.style("Step 1: ", fg="blue") + "Detecting AI Provider...\n")
        
        # Check Ollama
        ollama_available = False
        ollama_running = False
        
        if check_command_exists("ollama"):
            ollama_available = True
            ollama_running = check_service_running("http://localhost:11434/api/tags")
            
            if ollama_available:
                if ollama_running:
                    click.echo(click.style("✓ ", fg="green") + "Ollama is installed and running")
                    embedding_model, chat_model = detect_ollama_models()
                    if embedding_model:
                        click.echo(f"  Detected models: {embedding_model}, {chat_model or 'none'}")
                else:
                    click.echo(click.style("⚠ ", fg="yellow") + "Ollama is installed but not running")
        
        # Check OpenAI key
        openai_configured = bool(openai_key or os.getenv("OPENAI_API_KEY") or env_vars.get("OPENAI_API_KEY"))
        
        if ollama_running and not non_interactive:
            provider = click.prompt(
                "\nChoose AI provider",
                type=click.Choice(["ollama", "openai"], case_sensitive=False),
                default="ollama"
            ).lower()
        elif openai_configured:
            provider = "openai"
            click.echo(click.style("✓ ", fg="green") + "Using OpenAI (API key found)")
        elif ollama_available:
            provider = "ollama"
            click.echo(click.style("✓ ", fg="green") + "Using Ollama (detected)")
        else:
            if non_interactive:
                click.echo(click.style("✗ ", fg="red") + "No AI provider available")
                sys.exit(1)
            provider = click.prompt(
                "\nNo AI provider detected. Choose one",
                type=click.Choice(["ollama", "openai"], case_sensitive=False)
            ).lower()
    
    # Configure provider
    if provider == "ollama":
        click.echo(f"\n{click.style('✓', fg='green')} Configuring Ollama...")
        
        # Check if Ollama is running
        if not check_service_running("http://localhost:11434/api/tags"):
            click.echo(click.style("✗ ", fg="red") + "Ollama is not running")
            click.echo("  Please start Ollama: ollama serve")
            if not non_interactive:
                wait = click.confirm("  Wait and check again?", default=False)
                if wait:
                    import time
                    click.echo("  Waiting 5 seconds...")
                    time.sleep(5)
                    if not check_service_running("http://localhost:11434/api/tags"):
                        click.echo(click.style("✗ ", fg="red") + "Ollama still not running")
                        sys.exit(1)
                else:
                    sys.exit(1)
            else:
                sys.exit(1)
        
        embedding_model, chat_model = detect_ollama_models()
        
        if not embedding_model:
            embedding_model = click.prompt("Embedding model name", default="nomic-embed-text")
            chat_model = click.prompt("Chat model name", default="llama3.2")
        else:
            click.echo(f"  Using embedding model: {embedding_model}")
            click.echo(f"  Using chat model: {chat_model or 'llama3.2'}")
            chat_model = chat_model or "llama3.2"
        
        # Determine base URL based on OS
        import platform
        if platform.system() == "Linux":
            ollama_base_url = "http://host.docker.internal:11434"
        else:
            ollama_base_url = "http://host.docker.internal:11434"
        
        env_vars.update({
            "EMBEDDING_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": ollama_base_url,
            "OLLAMA_EMBEDDING_MODEL": embedding_model,
            "OLLAMA_CHAT_MODEL": chat_model,
        })
        
    else:  # OpenAI
        click.echo(f"\n{click.style('✓', fg='green')} Configuring OpenAI...")
        
        api_key = openai_key or os.getenv("OPENAI_API_KEY") or env_vars.get("OPENAI_API_KEY")
        
        if not api_key:
            if non_interactive:
                click.echo(click.style("✗ ", fg="red") + "OpenAI API key required")
                sys.exit(1)
            api_key = click.prompt(
                "Enter OpenAI API key",
                hide_input=True,
                confirmation_prompt=True
            )
        
        env_vars["OPENAI_API_KEY"] = api_key
        click.echo("  API key configured")
    
    # Step 2: Database Configuration
    click.echo(f"\n{click.style('Step 2: ', fg='blue')}Database Configuration...")
    
    if not non_interactive:
        db_password = click.prompt("Database password", default=db_password, hide_input=True)
        port = click.prompt("Agent-MCP port", default=port, type=int)
        db_port = click.prompt("PostgreSQL port (host)", default=db_port, type=int)
    
    env_vars.update({
        "DB_PASSWORD": db_password,
        "PORT": str(port),
        "DB_PORT": str(db_port),
    })
    
    # Step 3: Write .env file
    click.echo(f"\n{click.style('Step 3: ', fg='blue')}Writing configuration...")
    
    env_content = f"""# Agent-MCP Configuration
# Generated by setup wizard on {click.format_datetime(click.get_current_context().meta)}

"""
    
    if provider == "ollama":
        env_content += f"""# Ollama Configuration
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL={env_vars['OLLAMA_BASE_URL']}
OLLAMA_EMBEDDING_MODEL={env_vars['OLLAMA_EMBEDDING_MODEL']}
OLLAMA_CHAT_MODEL={env_vars['OLLAMA_CHAT_MODEL']}

"""
    else:
        env_content += f"""# OpenAI Configuration
OPENAI_API_KEY={env_vars['OPENAI_API_KEY']}

"""
    
    env_content += f"""# Database Configuration
DB_PASSWORD={db_password}
PORT={port}
DB_PORT={db_port}

# Optional: Project Directory
# MCP_PROJECT_DIR=/path/to/your/project
"""
    
    env_file.write_text(env_content)
    click.echo(click.style("✓ ", fg="green") + f"Configuration saved to {output}")
    
    # Step 4: Start Services (optional)
    if not non_interactive:
        start_services = click.confirm("\nStart services with Docker Compose?", default=True)
    else:
        start_services = False
    
    if start_services:
        click.echo(f"\n{click.style('Step 4: ', fg='blue')}Starting services...")
        
        # Check Docker Compose
        docker_compose_cmd = None
        for cmd in ["docker-compose", "docker compose"]:
            try:
                subprocess.run(
                    cmd.split() + ["--version"],
                    capture_output=True,
                    check=True,
                    timeout=5
                )
                docker_compose_cmd = cmd.split()
                break
            except Exception:
                continue
        
        if not docker_compose_cmd:
            click.echo(click.style("✗ ", fg="red") + "Docker Compose not found")
            sys.exit(1)
        
        # Start services
        try:
            result = subprocess.run(
                docker_compose_cmd + ["up", "-d"],
                check=True,
                capture_output=True,
                text=True
            )
            click.echo(click.style("✓ ", fg="green") + "Services started")
            
            import time
            click.echo("  Waiting for services to be ready...")
            time.sleep(5)
            
            # Check services
            if check_service_running(f"http://localhost:{port}/api/status"):
                click.echo(click.style("✓ ", fg="green") + f"Agent-MCP is running on http://localhost:{port}")
            else:
                click.echo(click.style("⚠ ", fg="yellow") + "Agent-MCP may still be starting")
            
        except subprocess.CalledProcessError as e:
            click.echo(click.style("✗ ", fg="red") + f"Failed to start services: {e.stderr}")
            sys.exit(1)
    
    # Summary
    click.echo("\n" + "="*60)
    click.echo(click.style("Setup Complete! 🎉", fg="green", bold=True))
    click.echo("="*60 + "\n")
    
    click.echo(f"Configuration saved to: {output}")
    click.echo(f"\nAccess points:")
    click.echo(f"  • API: http://localhost:{port}")
    click.echo(f"  • API Status: http://localhost:{port}/api/status")
    click.echo(f"  • PostgreSQL: localhost:{db_port}")
    
    click.echo(f"\nUseful commands:")
    click.echo(f"  • Start services: docker-compose up -d")
    click.echo(f"  • View logs: docker-compose logs -f agent-mcp")
    click.echo(f"  • Stop services: docker-compose down")
    
    if provider == "ollama":
        click.echo(f"\nNote: Make sure Ollama is running: ollama serve")
    
    click.echo(f"\nNext steps:")
    click.echo(f"  1. Configure MCP client: http://localhost:{port}/mcp")
    click.echo(f"  2. Start dashboard: cd agent_mcp/dashboard && npm install && npm run dev")
    click.echo(f"  3. Read docs: docs/setup/QUICK_START.md")
    click.echo()


@click.command()
@click.option("--check-docker", is_flag=True, help="Check Docker installation")
@click.option("--check-ollama", is_flag=True, help="Check Ollama installation and status")
@click.option("--check-openai", is_flag=True, help="Check OpenAI API key")
@click.option("--check-services", is_flag=True, help="Check if services are running")
def doctor(
    check_docker: bool,
    check_ollama: bool,
    check_openai: bool,
    check_services: bool
):
    """Diagnose Agent-MCP setup and configuration issues."""
    
    click.echo("\n" + "="*60)
    click.echo(click.style("Agent-MCP Doctor", fg="cyan", bold=True))
    click.echo("="*60 + "\n")
    
    all_checks = not any([check_docker, check_ollama, check_openai, check_services])
    
    issues = []
    
    # Check Docker
    if all_checks or check_docker:
        click.echo(click.style("Docker:", fg="blue", bold=True))
        if check_command_exists("docker"):
            try:
                result = subprocess.run(
                    ["docker", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                click.echo(f"  {click.style('✓', fg='green')} Installed: {result.stdout.strip()}")
            except Exception as e:
                click.echo(f"  {click.style('✗', fg='red')} Error: {e}")
                issues.append("Docker version check failed")
            
            # Check if Docker daemon is running
            try:
                subprocess.run(
                    ["docker", "info"],
                    capture_output=True,
                    check=True,
                    timeout=5
                )
                click.echo(f"  {click.style('✓', fg='green')} Daemon is running")
            except Exception:
                click.echo(f"  {click.style('✗', fg='red')} Daemon is not running")
                issues.append("Docker daemon not running")
        else:
            click.echo(f"  {click.style('✗', fg='red')} Not installed")
            issues.append("Docker not installed")
        
        # Check Docker Compose
        docker_compose_cmd = None
        for cmd in ["docker-compose", "docker compose"]:
            try:
                subprocess.run(
                    cmd.split() + ["--version"],
                    capture_output=True,
                    check=True,
                    timeout=5
                )
                docker_compose_cmd = cmd
                break
            except Exception:
                continue
        
        if docker_compose_cmd:
            click.echo(f"  {click.style('✓', fg='green')} Docker Compose available: {docker_compose_cmd}")
        else:
            click.echo(f"  {click.style('✗', fg='red')} Docker Compose not found")
            issues.append("Docker Compose not installed")
        
        click.echo()
    
    # Check Ollama
    if all_checks or check_ollama:
        click.echo(click.style("Ollama:", fg="blue", bold=True))
        if check_command_exists("ollama"):
            click.echo(f"  {click.style('✓', fg='green')} Installed")
            
            if check_service_running("http://localhost:11434/api/tags"):
                click.echo(f"  {click.style('✓', fg='green')} Service is running")
                embedding_model, chat_model = detect_ollama_models()
                if embedding_model:
                    click.echo(f"  {click.style('✓', fg='green')} Models detected:")
                    click.echo(f"    • Embedding: {embedding_model}")
                    click.echo(f"    • Chat: {chat_model or 'none'}")
                else:
                    click.echo(f"  {click.style('⚠', fg='yellow')} No models detected")
                    click.echo(f"    Run: ollama pull nomic-embed-text")
            else:
                click.echo(f"  {click.style('✗', fg='red')} Service is not running")
                click.echo(f"    Start with: ollama serve")
                issues.append("Ollama not running")
        else:
            click.echo(f"  {click.style('✗', fg='red')} Not installed")
            click.echo(f"    Install: curl -fsSL https://ollama.ai/install.sh | sh")
            issues.append("Ollama not installed")
        click.echo()
    
    # Check OpenAI
    if all_checks or check_openai:
        click.echo(click.style("OpenAI:", fg="blue", bold=True))
        api_key = os.getenv("OPENAI_API_KEY")
        env_file = Path(".env")
        if env_file.exists():
            try:
                from dotenv import dotenv_values
                env_vars = dotenv_values(env_file)
                api_key = api_key or env_vars.get("OPENAI_API_KEY")
            except ImportError:
                # Fallback if python-dotenv not available
                pass
        
        if api_key:
            # Mask the key for display
            masked_key = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 11 else "***"
            click.echo(f"  {click.style('✓', fg='green')} API key found: {masked_key}")
        else:
            click.echo(f"  {click.style('✗', fg='red')} API key not found")
            click.echo(f"    Set OPENAI_API_KEY in .env or environment")
            issues.append("OpenAI API key not found")
        click.echo()
    
    # Check Services
    if all_checks or check_services:
        click.echo(click.style("Services:", fg="blue", bold=True))
        
        # Check Agent-MCP Backend
        port = int(os.getenv("PORT", "8080"))
        if check_service_running(f"http://localhost:{port}/api/status"):
            click.echo(f"  {click.style('✓', fg='green')} Agent-MCP backend is running on port {port}")
        else:
            click.echo(f"  {click.style('✗', fg='red')} Agent-MCP backend is not running")
            click.echo(f"    Start with: docker-compose up -d")
            issues.append("Agent-MCP backend not running")
        
        # Check Dashboard
        if check_service_running("http://localhost:3000"):
            click.echo(f"  {click.style('✓', fg='green')} Dashboard is running on port 3000")
        else:
            click.echo(f"  {click.style('⚠', fg='yellow')} Dashboard is not running (optional)")
            click.echo(f"    Start with: docker-compose up -d")
        
        # Check PostgreSQL
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=agent-mcp-postgres", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "healthy" in result.stdout or "Up" in result.stdout:
                click.echo(f"  {click.style('✓', fg='green')} PostgreSQL is running")
            else:
                click.echo(f"  {click.style('✗', fg='red')} PostgreSQL is not running")
                issues.append("PostgreSQL not running")
        except Exception:
            click.echo(f"  {click.style('⚠', fg='yellow')} Could not check PostgreSQL status")
        
        click.echo()
    
    # Summary
    if issues:
        click.echo("="*60)
        click.echo(click.style(f"Found {len(issues)} issue(s):", fg="yellow", bold=True))
        for issue in issues:
            click.echo(f"  • {issue}")
        click.echo("\nRun 'agent-mcp setup' to configure Agent-MCP")
        click.echo()
        return 1
    else:
        click.echo("="*60)
        click.echo(click.style("All checks passed! ✓", fg="green", bold=True))
        click.echo()
        return 0


