"""
Configuration management API routes.
Handles reading and updating .env file values through the dashboard.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from ..decorators import api_route
from ...core.config import get_project_dir, logger


@api_route
async def get_config_api_route(request: Request, token: str) -> JSONResponse:
    """Get current configuration values from .env file."""
    try:
        project_dir = get_project_dir()
        env_file = project_dir / ".env"
        
        config_values: Dict[str, Any] = {}
        
        if env_file.exists():
            # Read .env file
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    # Parse KEY=VALUE
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        # Mask sensitive values
                        if "API_KEY" in key or "PASSWORD" in key or "SECRET" in key:
                            if value:
                                config_values[key] = "***" + value[-4:] if len(value) > 4 else "***"
                            else:
                                config_values[key] = ""
                        else:
                            config_values[key] = value
        
        # Also check environment variables (for Docker/container setups)
        important_keys = [
            "AGENT_MCP_OPENAI_API_KEY",
            "OPENAI_API_KEY",
            "EMBEDDING_PROVIDER",
            "OLLAMA_BASE_URL",
            "OLLAMA_EMBEDDING_MODEL",
            "OLLAMA_CHAT_MODEL",
            "AGENT_MCP_DB_HOST",
            "AGENT_MCP_DB_PORT",
            "AGENT_MCP_DB_NAME",
            "AGENT_MCP_DB_USER",
            "AGENT_MCP_DB_PASSWORD",
            "AGENT_MCP_API_PORT",
            "AGENT_MCP_LOG_LEVEL",
        ]
        
        for key in important_keys:
            env_value = os.environ.get(key)
            if env_value and key not in config_values:
                # Mask sensitive values
                if "API_KEY" in key or "PASSWORD" in key or "SECRET" in key:
                    config_values[key] = "***" + env_value[-4:] if len(env_value) > 4 else "***"
                else:
                    config_values[key] = env_value
        
        return JSONResponse({
            "success": True,
            "config": config_values,
            "env_file_path": str(env_file)
        })
    
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        return JSONResponse({"error": f"Failed to get configuration: {str(e)}"}, status_code=500)


@api_route
async def update_config_api_route(request: Request, token: str) -> JSONResponse:
    """Update configuration values in .env file."""
    try:
        data = await request.json()
        updates = data.get("updates", {})
        
        if not updates:
            return JSONResponse({"error": "No updates provided"}, status_code=400)
        
        project_dir = get_project_dir()
        env_file = project_dir / ".env"
        
        # Read existing .env file
        lines: list[str] = []
        existing_keys: set[str] = set()
        
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Track existing keys
                for line in lines:
                    line_stripped = line.strip()
                    if line_stripped and not line_stripped.startswith("#") and "=" in line_stripped:
                        key = line_stripped.split("=", 1)[0].strip()
                        existing_keys.add(key)
        
        # Update or add new values
        updated_keys: list[str] = []
        for key, value in updates.items():
            # Skip if value is masked (starts with ***)
            if isinstance(value, str) and value.startswith("***"):
                continue
            
            key_found = False
            # Update existing lines
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith("#") and "=" in line_stripped:
                    line_key = line_stripped.split("=", 1)[0].strip()
                    if line_key == key:
                        # Update the line
                        lines[i] = f"{key}={value}\n"
                        key_found = True
                        updated_keys.append(key)
                        break
            
            # Add new key if not found
            if not key_found:
                # Find a good place to insert (after last non-comment line or at end)
                insert_pos = len(lines)
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].strip() and not lines[i].strip().startswith("#"):
                        insert_pos = i + 1
                        break
                lines.insert(insert_pos, f"{key}={value}\n")
                updated_keys.append(key)
        
        # Write back to file
        try:
            # Ensure directory exists
            env_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
            
            logger.info(f"Updated configuration: {', '.join(updated_keys)}")
            
            return JSONResponse({
                "success": True,
                "updated_keys": updated_keys,
                "message": f"Successfully updated {len(updated_keys)} configuration value(s)"
            })
        
        except PermissionError:
            return JSONResponse({
                "error": "Permission denied: Cannot write to .env file. Check file permissions."
            }, status_code=403)
        except Exception as e:
            return JSONResponse({
                "error": f"Failed to write .env file: {str(e)}"
            }, status_code=500)
    
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        return JSONResponse({"error": f"Failed to update configuration: {str(e)}"}, status_code=500)


# Route definitions
routes = [
    Route('/api/config', endpoint=get_config_api_route, name="get_config_api", methods=['GET', 'OPTIONS']),
    Route('/api/config', endpoint=update_config_api_route, name="update_config_api", methods=['PUT', 'OPTIONS']),
]

