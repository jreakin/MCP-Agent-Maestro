"""
MCP Setup Configuration Generator and Installer
Generates and installs MCP client configurations for Cursor, Claude Desktop, Windsurf, VS Code.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Optional, List
from typing_extensions import Literal

ClientType = Literal["cursor", "claude", "windsurf", "vscode"]


class MCPConfigGenerator:
    """Generate MCP client configurations."""
    
    def __init__(self, host: str = "localhost", port: int = 8080, command: Optional[str] = None):
        """
        Initialize config generator.
        
        Args:
            host: MCP server host
            port: MCP server port
            command: Command to run the MCP server (defaults to 'agent-mcp' if not provided)
        """
        self.host = host
        self.port = port
        self.command = command or "agent-mcp"
    
    def generate_cursor_config(self) -> Dict:
        """Generate Cursor MCP configuration."""
        # Build args based on command type
        if self.command == "uv":
            args = [
                "run",
                "-m",
                "agent_mcp.cli",
                "--transport",
                "stdio",
                "--project-dir",
                "${workspaceFolder}"
            ]
        elif self.command in ["python", "python3"]:
            args = [
                "-m",
                "agent_mcp.cli",
                "--transport",
                "stdio",
                "--project-dir",
                "${workspaceFolder}"
            ]
        else:
            # For other commands (like "agent-mcp" binary), use direct args
            args = [
                "--transport",
                "stdio",
                "--project-dir",
                "${workspaceFolder}"
            ]
        
        return {
            "mcpServers": {
                "agent-mcp": {
                    "command": self.command,
                    "args": args,
                    "env": {}
                }
            }
        }
    
    def generate_claude_config(self) -> Dict:
        """Generate Claude Desktop MCP configuration."""
        # Build args based on command type
        if self.command == "uv":
            args = [
                "run",
                "-m",
                "agent_mcp.cli",
                "--transport",
                "stdio",
                "--project-dir",
                "."
            ]
        elif self.command in ["python", "python3"]:
            args = [
                "-m",
                "agent_mcp.cli",
                "--transport",
                "stdio",
                "--project-dir",
                "."
            ]
        else:
            # For other commands (like "agent-mcp" binary), use direct args
            args = [
                "--transport",
                "stdio",
                "--project-dir",
                "."
            ]
        
        return {
            "mcpServers": {
                "agent-mcp": {
                    "command": self.command,
                    "args": args,
                    "env": {}
                }
            }
        }
    
    def generate_windsurf_config(self) -> Dict:
        """Generate Windsurf MCP configuration."""
        # Build args based on command type
        if self.command == "uv":
            args = [
                "run",
                "-m",
                "agent_mcp.cli",
                "--transport",
                "stdio",
                "--project-dir",
                "${workspaceFolder}"
            ]
        elif self.command in ["python", "python3"]:
            args = [
                "-m",
                "agent_mcp.cli",
                "--transport",
                "stdio",
                "--project-dir",
                "${workspaceFolder}"
            ]
        else:
            # For other commands (like "agent-mcp" binary), use direct args
            args = [
                "--transport",
                "stdio",
                "--project-dir",
                "${workspaceFolder}"
            ]
        
        return {
            "mcpServers": {
                "agent-mcp": {
                    "command": self.command,
                    "args": args,
                    "env": {}
                }
            }
        }
    
    def generate_vscode_config(self) -> Dict:
        """Generate VS Code MCP configuration."""
        # Build args based on command type
        if self.command == "uv":
            args = [
                "run",
                "-m",
                "agent_mcp.cli",
                "--transport",
                "stdio",
                "--project-dir",
                "${workspaceFolder}"
            ]
        elif self.command in ["python", "python3"]:
            args = [
                "-m",
                "agent_mcp.cli",
                "--transport",
                "stdio",
                "--project-dir",
                "${workspaceFolder}"
            ]
        else:
            # For other commands (like "agent-mcp" binary), use direct args
            args = [
                "--transport",
                "stdio",
                "--project-dir",
                "${workspaceFolder}"
            ]
        
        return {
            "mcpServers": {
                "agent-mcp": {
                    "command": self.command,
                    "args": args,
                    "env": {}
                }
            }
        }
    
    def generate_config(self, client: ClientType) -> Dict:
        """
        Generate configuration for specified client.
        
        Args:
            client: Client type (cursor, claude, windsurf, vscode)
            
        Returns:
            Configuration dictionary
        """
        generators = {
            "cursor": self.generate_cursor_config,
            "claude": self.generate_claude_config,
            "windsurf": self.generate_windsurf_config,
            "vscode": self.generate_vscode_config,
        }
        
        if client not in generators:
            raise ValueError(f"Unsupported client: {client}")
        
        return generators[client]()


class MCPConfigInstaller:
    """Install MCP configurations to client config files."""
    
    # Config file locations by client
    CONFIG_PATHS = {
        "cursor": {
            "macos": Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "claude_desktop_config.json",
            "linux": Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "claude_desktop_config.json",
            "windows": Path.home() / "AppData" / "Roaming" / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "claude_desktop_config.json",
        },
        "claude": {
            "macos": Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            "linux": Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
            "windows": Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
        },
        "windsurf": {
            "macos": Path.home() / "Library" / "Application Support" / "Windsurf" / "mcp.json",
            "linux": Path.home() / ".config" / "Windsurf" / "mcp.json",
            "windows": Path.home() / "AppData" / "Roaming" / "Windsurf" / "mcp.json",
        },
        "vscode": {
            "macos": Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "claude_desktop_config.json",
            "linux": Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "claude_desktop_config.json",
            "windows": Path.home() / "AppData" / "Roaming" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "claude_desktop_config.json",
        },
    }
    
    def _get_platform(self) -> str:
        """Get current platform."""
        import platform
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        elif system == "windows":
            return "windows"
        else:
            return "linux"  # Default to linux
    
    def _get_config_path(self, client: ClientType) -> Path:
        """Get configuration file path for client on current platform."""
        platform = self._get_platform()
        if client not in self.CONFIG_PATHS:
            raise ValueError(f"Unsupported client: {client}")
        if platform not in self.CONFIG_PATHS[client]:
            raise ValueError(f"Unsupported platform: {platform}")
        return self.CONFIG_PATHS[client][platform]
    
    def _backup_config(self, config_path: Path) -> Optional[Path]:
        """Create backup of existing config file."""
        if not config_path.exists():
            return None
        
        backup_path = config_path.with_suffix(f".json.backup.{int(Path(config_path).stat().st_mtime)}")
        shutil.copy2(config_path, backup_path)
        return backup_path
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load existing configuration file."""
        if not config_path.exists():
            return {}
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_config(self, config_path: Path, config: Dict) -> None:
        """Save configuration to file."""
        # Create parent directories if they don't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    
    def _merge_config(self, existing: Dict, new: Dict) -> Dict:
        """Merge new MCP server config into existing config."""
        merged = existing.copy()
        
        # Ensure mcpServers key exists
        if "mcpServers" not in merged:
            merged["mcpServers"] = {}
        
        # Merge server configs
        merged["mcpServers"].update(new.get("mcpServers", {}))
        
        return merged
    
    def install(self, client: ClientType, config: Dict, backup: bool = True) -> Dict:
        """
        Install configuration to client config file.
        
        Args:
            client: Client type
            config: Configuration dictionary from generator
            backup: Whether to create backup of existing config
            
        Returns:
            Dict with 'success', 'path', 'backup_path' keys
        """
        config_path = self._get_config_path(client)
        
        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = self._backup_config(config_path)
        
        # Load existing config
        existing_config = self._load_config(config_path)
        
        # Merge new config
        merged_config = self._merge_config(existing_config, config)
        
        # Save merged config
        try:
            self._save_config(config_path, merged_config)
            return {
                "success": True,
                "path": str(config_path),
                "backup_path": str(backup_path) if backup_path else None,
                "message": f"Configuration installed to {config_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "path": str(config_path),
                "backup_path": str(backup_path) if backup_path else None,
                "error": str(e),
                "message": f"Failed to install configuration: {e}"
            }


class MCPConfigVerifier:
    """Verify existing MCP configurations."""
    
    def __init__(self):
        self.installer = MCPConfigInstaller()
    
    def verify(self, client: str) -> Dict:
        """
        Verify configuration for client.
        
        Args:
            client: Client type
            
        Returns:
            Dict with 'exists', 'valid', 'config', 'errors' keys
        """
        # Validate client type
        if client not in ["cursor", "claude", "windsurf", "vscode"]:
            raise ValueError(f"Unsupported client: {client}")
        
        try:
            config_path = self.installer._get_config_path(client)
            home = Path.home()
            is_root = str(home) == "/root"
            
            # Build errors list
            errors = []
            if is_root:
                errors.append("⚠️ Server is running as root. Config path shown is for root user. Run server as regular user for correct paths.")
            
            if not config_path.exists():
                if not is_root:
                    errors.append("Configuration file does not exist")
                return {
                    "exists": False,
                    "valid": False,
                    "path": str(config_path),
                    "config": None,
                    "errors": errors,
                }
            
            # Load and validate config
            config = self.installer._load_config(config_path)
            
            # Check if agent-mcp server is configured
            # Note: errors list already initialized above
            if "mcpServers" not in config:
                errors.append("No mcpServers section found")
            elif "agent-mcp" not in config.get("mcpServers", {}):
                errors.append("agent-mcp server not found in configuration")
            
            return {
                "exists": True,
                "valid": len(errors) == 0,
                "path": str(config_path),
                "config": config.get("mcpServers", {}).get("agent-mcp") if errors == [] else None,
                "errors": errors,
            }
        except Exception as e:
            return {
                "exists": False,
                "valid": False,
                "path": None,
                "config": None,
                "errors": [str(e)],
            }
    
    def verify_all(self) -> Dict[ClientType, Dict]:
        """Verify configurations for all supported clients."""
        return {
            client: self.verify(client)
            for client in ["cursor", "claude", "windsurf", "vscode"]
        }

