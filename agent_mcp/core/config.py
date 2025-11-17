# MCP Agent Maestro - Core configuration module
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# Import unified settings
from .settings import get_settings

# Version and description information - read from pyproject.toml (single source of truth)
def _get_pyproject_data() -> dict:
    """Read project metadata from pyproject.toml to keep it in sync with UV."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # Fallback for Python < 3.11
        except ImportError:
            # If tomli not available, try reading manually
            pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                data = {}
                with open(pyproject_path, "r", encoding="utf-8") as f:
                    in_project_section = False
                    for line in f:
                        line_stripped = line.strip()
                        if line_stripped == "[project]":
                            in_project_section = True
                            continue
                        if line_stripped.startswith("[") and in_project_section:
                            break
                        if in_project_section and "=" in line_stripped:
                            key, value = line_stripped.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == "version":
                                data["version"] = value
                            elif key == "description":
                                data["description"] = value
                return data
            return {"version": "0.2.0", "description": "MCP Agent Maestro"}  # Fallback
    
    pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            project_data = data.get("project", {})
            return {
                "version": project_data.get("version", "0.2.0"),
                "description": project_data.get("description", "MCP Agent Maestro")
            }
    return {"version": "0.2.0", "description": "MCP Agent Maestro"}  # Fallback

_pyproject_data = _get_pyproject_data()
VERSION = _pyproject_data.get("version", "0.2.0")
DESCRIPTION = _pyproject_data.get("description", "MCP Agent Maestro")
GITHUB_REPO = "jreakin/mcp-agent-maestro"
AUTHOR = "John R. Eakin"
GITHUB_URL = "https://github.com/jreakin"

# Get settings instance
_settings = get_settings()


# --- TUI Colors (ANSI Escape Codes) ---
class TUIColors:
    HEADER = "\033[95m"  # Light Magenta
    OKBLUE = "\033[94m"  # Light Blue
    OKCYAN = "\033[96m"  # Light Cyan
    OKGREEN = "\033[92m"  # Light Green
    WARNING = "\033[93m"  # Yellow
    FAIL = "\033[91m"  # Red
    ENDC = "\033[0m"  # Reset to default
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    DIM = "\033[2m"

    # Specific log level colors
    DEBUG = OKCYAN
    INFO = OKGREEN
    WARNING = WARNING
    ERROR = FAIL
    CRITICAL = BOLD + FAIL


class ColorfulFormatter(logging.Formatter):
    """Custom formatter to add colors to log messages for console output."""

    LOG_LEVEL_COLORS = {
        logging.DEBUG: TUIColors.DEBUG,
        logging.INFO: TUIColors.INFO,
        logging.WARNING: TUIColors.WARNING,
        logging.ERROR: TUIColors.ERROR,
        logging.CRITICAL: TUIColors.CRITICAL,
    }

    def format(self, record):
        color = self.LOG_LEVEL_COLORS.get(record.levelno, TUIColors.ENDC)
        record.levelname = (
            f"{color}{record.levelname:<8}{TUIColors.ENDC}"  # Pad levelname
        )
        record.name = f"{TUIColors.OKBLUE}{record.name}{TUIColors.ENDC}"
        return super().format(record)


# --- General Configuration ---
DB_FILE_NAME: str = "mcp_state.db"  # From main.py:39

# --- Logging Configuration ---
LOG_FILE_NAME: str = "mcp_server.log"  # Based on main.py:46
LOG_LEVEL: int = logging.INFO  # From main.py:43
# Default request_id for logs without request context
LOG_FORMAT_FILE: str = "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
LOG_FORMAT_CONSOLE: str = (
    f"%(asctime)s - %(name)s - %(levelname)s - {TUIColors.DIM}[%(request_id)s]{TUIColors.ENDC} - {TUIColors.DIM}%(message)s{TUIColors.ENDC}"  # Dim message text
)

# Use settings for debug mode
CONSOLE_LOGGING_ENABLED = _settings.mcp_debug  # Enable console logging in debug mode


def setup_logging():
    """Configures global logging for the application."""

    root_logger = logging.getLogger()  # Get the root logger
    root_logger.setLevel(LOG_LEVEL)  # Set level on the root logger

    # Clear any existing handlers on the root logger to avoid duplication
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 1. File Handler (only in debug mode)
    debug_mode = _settings.mcp_debug
    if debug_mode:
        from ..utils.structured_logging import StructuredFormatter
        file_formatter = StructuredFormatter(LOG_FORMAT_FILE)
        file_handler = logging.FileHandler(
            _settings.log_file, mode="a", encoding="utf-8"
        )  # Append mode
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # 2. Console Handler (with colors, conditional)
    if CONSOLE_LOGGING_ENABLED:
        from ..utils.structured_logging import StructuredFormatter
        console_formatter = StructuredFormatter(
            LOG_FORMAT_CONSOLE, datefmt="%H:%M:%S"
        )  # Simpler datefmt for console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        # Filter out less important messages for console if desired
        # console_handler.setLevel(logging.INFO)  # Example: only INFO and above for console
        root_logger.addHandler(console_handler)

    # Suppress overly verbose logs from specific libraries for both file and console
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    # Uvicorn access logs are handled by Uvicorn's config (access_log=False in cli.py)
    # but we can also try to manage its error logger if needed.
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)  # General uvicorn logger
    logging.getLogger("mcp.server.lowlevel.server").propagate = (
        False  # Prevent duplication if it logs directly
    )


def enable_console_logging():
    """Enable console logging dynamically (used when debug mode is enabled)."""
    global CONSOLE_LOGGING_ENABLED
    CONSOLE_LOGGING_ENABLED = True
    # Re-setup logging to add file handler when debug mode is enabled
    setup_logging()

    root_logger = logging.getLogger()

    # Check if console handler already exists
    has_console_handler = any(
        isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout
        for handler in root_logger.handlers
    )

    if not has_console_handler:
        console_formatter = ColorfulFormatter(LOG_FORMAT_CONSOLE, datefmt="%H:%M:%S")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        # Set logging level to DEBUG for more verbose output
        console_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)

        # Also set root logger to DEBUG level
        root_logger.setLevel(logging.DEBUG)


# Initialize logging when this module is imported
setup_logging()
logger = logging.getLogger("mcp_agent_maestro")  # Main application logger

# --- Agent Appearance ---
AGENT_COLORS: List[str] = (
    [  # From main.py:160-164 (Note: original had 160-165, but list ends on 164)
        "#FF5733",
        "#33FF57",
        "#3357FF",
        "#FF33A1",
        "#A133FF",
        "#33FFA1",
        "#FFBD33",
        "#33FFBD",
        "#BD33FF",
        "#FF3333",
        "#33FF33",
        "#3333FF",
        "#FF8C00",
        "#00CED1",
        "#9400D3",
        "#FF1493",
        "#7FFF00",
        "#1E90FF",
    ]
)

# --- OpenAI Model Configuration ---
# Use settings for all OpenAI configuration
ADVANCED_EMBEDDINGS: bool = _settings.advanced_embeddings
DISABLE_AUTO_INDEXING: bool = _settings.disable_auto_indexing

# Backward compatibility exports (using settings)
SIMPLE_EMBEDDING_MODEL: str = _settings.embedding_model
SIMPLE_EMBEDDING_DIMENSION: int = _settings.embedding_dimension
ADVANCED_EMBEDDING_MODEL: str = _settings.advanced_embedding_model
ADVANCED_EMBEDDING_DIMENSION: int = _settings.advanced_embedding_dimension

# Dynamic configuration based on mode (using settings properties)
EMBEDDING_MODEL: str = _settings.effective_embedding_model
EMBEDDING_DIMENSION: int = _settings.effective_embedding_dimension

CHAT_MODEL: str = _settings.openai_model
TASK_ANALYSIS_MODEL: str = _settings.task_analysis_model
MAX_EMBEDDING_BATCH_SIZE: int = _settings.max_embedding_batch_size
MAX_CONTEXT_TOKENS: int = _settings.max_context_tokens
TASK_ANALYSIS_MAX_TOKENS: int = _settings.task_analysis_max_tokens

# --- Project Directory Helpers ---
# These rely on an environment variable "MCP_PROJECT_DIR" being set,
# typically by the CLI entry point (previously in main.py:1953, will be in cli.py).


def get_project_dir() -> Path:
    """Gets the resolved absolute path to the project directory."""
    # Check settings first, then fall back to environment variable for backward compatibility
    project_dir_str = _settings.project_dir or os.environ.get("MCP_PROJECT_DIR")
    if not project_dir_str:
        # This case should ideally be handled at startup by the CLI,
        # ensuring MCP_PROJECT_DIR is always set.
        logger.error("CRITICAL: MCP_PROJECT_DIR environment variable is not set.")
        # Fallback to current directory, but this is likely not intended for normal operation.
        return Path(".").resolve()
    return Path(project_dir_str).resolve()


def get_agent_dir() -> Path:
    """Gets the path to the .mcp-maestro directory within the project directory."""
    return get_project_dir() / ".mcp-maestro"


def get_db_path() -> Path:
    """Gets the full path to the SQLite database file."""
    return get_agent_dir() / DB_FILE_NAME


# --- OpenAI API Key (backward compatibility) ---
OPENAI_API_KEY_ENV: Optional[str] = (
    _settings.openai_api_key.get_secret_value() 
    if _settings.openai_api_key is not None 
    else None
)
if not OPENAI_API_KEY_ENV:
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    if embedding_provider != "ollama":
        logger.warning(
            "OPENAI_API_KEY not found in environment variables. "
            "Set it in your .env file or use EMBEDDING_PROVIDER=ollama for local models."
        )

# --- Task Placement Configuration (System 8) ---
ENABLE_TASK_PLACEMENT_RAG: bool = _settings.enable_task_placement_rag
TASK_DUPLICATION_THRESHOLD: float = _settings.task_duplication_threshold
ALLOW_RAG_OVERRIDE: bool = _settings.allow_rag_override
TASK_PLACEMENT_RAG_TIMEOUT: int = _settings.task_placement_rag_timeout

# --- Security Configuration ---
SECURITY_ENABLED: bool = _settings.security_enabled
SECURITY_SCAN_TOOL_SCHEMAS: bool = _settings.security_scan_tool_schemas
SECURITY_SCAN_TOOL_RESPONSES: bool = _settings.security_scan_tool_responses
SECURITY_SANITIZATION_MODE: str = _settings.security_sanitization_mode
SECURITY_ALERT_WEBHOOK: Optional[str] = _settings.security_alert_webhook
SECURITY_USE_ML_DETECTION: bool = _settings.security_use_ml_detection

# Log that configuration is loaded (optional)
logger.info("Core configuration loaded (with colorful logging setup).")
# Example of how other modules will use this logger:
# from agent_mcp.core.config import logger
# logger.info("This is a log message from another module.")
