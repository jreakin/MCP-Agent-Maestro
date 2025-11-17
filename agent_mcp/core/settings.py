# Agent-MCP Unified Settings Configuration
"""
Unified configuration using Pydantic Settings.
Replaces scattered os.environ.get() calls with type-safe, validated settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, field_validator
from typing import Literal, Optional
from pathlib import Path


class AgentMCPSettings(BaseSettings):
    """Unified configuration using Pydantic Settings."""
    
    # API & Server
    api_host: str = Field(default="localhost", description="API server host")
    api_port: int = Field(default=8080, ge=1024, le=65535, description="API server port")
    dashboard_port: int = Field(default=3000, ge=1024, le=65535, description="Dashboard port")
    
    # Database
    database_url: Optional[str] = Field(default=None, description="PostgreSQL connection string")
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    db_name: str = Field(default="agent_mcp", description="Database name")
    db_user: str = Field(default="agent_mcp", description="Database user")
    db_password: Optional[str] = Field(default=None, description="Database password")
    db_pool_min: int = Field(default=1, ge=1, le=50, description="Database connection pool minimum")
    db_pool_max: int = Field(default=10, ge=1, le=50, description="Database connection pool maximum")
    db_max_overflow: int = Field(default=20, ge=0, description="Database max overflow connections")
    
    # OpenAI
    openai_api_key: Optional[SecretStr] = Field(default=None, description="OpenAI API key (optional when using Ollama)")
    openai_model: str = Field(default="gpt-4.1-2025-04-14", description="Default OpenAI chat model")
    embedding_model: str = Field(default="text-embedding-3-large", description="Embedding model")
    embedding_dimension: int = Field(default=1536, description="Embedding dimension")
    max_context_tokens: int = Field(default=1000000, ge=1000, le=2000000, description="Max context tokens")
    max_embedding_batch_size: int = Field(default=100, ge=1, le=1000, description="Max embedding batch size")
    
    # Advanced Embedding Mode
    advanced_embeddings: bool = Field(default=False, description="Use advanced embedding mode")
    advanced_embedding_model: str = Field(default="text-embedding-3-large", description="Advanced embedding model")
    advanced_embedding_dimension: int = Field(default=3072, description="Advanced embedding dimension")
    
    # Task Analysis
    task_analysis_model: str = Field(default="gpt-4.1-2025-04-14", description="Task analysis model")
    task_analysis_max_tokens: int = Field(default=1000000, ge=1000, le=2000000, description="Task analysis max tokens")
    
    # Task Placement (System 8)
    enable_task_placement_rag: bool = Field(default=True, description="Enable task placement RAG")
    task_duplication_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Task duplication threshold")
    allow_rag_override: bool = Field(default=True, description="Allow RAG override")
    task_placement_rag_timeout: int = Field(default=5, ge=1, le=60, description="Task placement RAG timeout (seconds)")
    
    # Security
    security_enabled: bool = Field(default=True, description="Enable security features")
    security_poison_detection_enabled: bool = Field(default=True, description="Enable poison detection")
    security_scan_tool_schemas: bool = Field(default=True, description="Scan tool schemas for threats")
    security_scan_tool_responses: bool = Field(default=True, description="Scan tool responses for threats")
    security_sanitization_mode: Literal["remove", "neutralize", "block"] = Field(
        default="remove", description="Security sanitization mode"
    )
    security_alert_webhook: Optional[str] = Field(default=None, description="Security alert webhook URL")
    security_use_ml_detection: bool = Field(default=False, description="Use ML-based detection")
    
    # RAG
    rag_enabled: bool = Field(default=True, description="Enable RAG system")
    rag_max_results: int = Field(default=13, ge=1, le=50, description="Max RAG results")
    disable_auto_indexing: bool = Field(default=False, description="Disable automatic indexing")
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    mcp_debug: bool = Field(default=False, description="Enable debug mode")
    log_file: str = Field(default="mcp_server.log", description="Log file name")
    
    # Agent Management
    max_workers: int = Field(default=5, ge=1, le=20, description="Maximum number of worker agents")
    agent_timeout: int = Field(default=3600, ge=60, description="Agent timeout in seconds")
    
    # Project Directory (set at runtime, not from env)
    project_dir: Optional[str] = Field(default=None, description="Project directory path")
    
    model_config = SettingsConfigDict(
        env_prefix="AGENT_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[SecretStr]) -> Optional[SecretStr]:
        """Validate OpenAI API key format."""
        if v is None:
            return v
        key_str = v.get_secret_value()
        if not key_str.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        if len(key_str) < 20:
            raise ValueError("API key appears invalid (too short)")
        return v
    
    @property
    def effective_embedding_model(self) -> str:
        """Get the effective embedding model based on mode."""
        if self.advanced_embeddings:
            return self.advanced_embedding_model
        return self.embedding_model
    
    @property
    def effective_embedding_dimension(self) -> int:
        """Get the effective embedding dimension based on mode."""
        if self.advanced_embeddings:
            return self.advanced_embedding_dimension
        return self.embedding_dimension


# Global settings instance
_settings: Optional[AgentMCPSettings] = None


def get_settings() -> AgentMCPSettings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = AgentMCPSettings()
    return _settings


def reset_settings():
    """Reset global settings instance (useful for testing)."""
    global _settings
    _settings = None

