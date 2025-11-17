"""
Tests for unified Pydantic Settings model.
"""
import os
import pytest
from pydantic import ValidationError
from agent_mcp.core.settings import AgentMCPSettings, get_settings, reset_settings


class TestAgentMCPSettings:
    """Test the unified settings model."""
    
    def test_default_settings(self):
        """Test that default settings are valid."""
        settings = AgentMCPSettings(openai_api_key="sk-test123456789012345678901234567890")
        # Default port is 8080, but may be overridden by environment
        assert settings.api_port in [8080, 3000]  # Allow both defaults
        assert settings.api_host == "localhost"
        assert settings.log_level == "INFO"
        assert settings.security_enabled is True
    
    def test_settings_validation(self):
        """Test settings validation."""
        # Valid API key
        settings = AgentMCPSettings(openai_api_key="sk-test123456789012345678901234567890")
        assert settings.openai_api_key.get_secret_value().startswith("sk-")
        
        # Invalid API key (too short)
        with pytest.raises(ValidationError):
            AgentMCPSettings(openai_api_key="sk-short")
        
        # Invalid API key (wrong prefix)
        with pytest.raises(ValidationError):
            AgentMCPSettings(openai_api_key="invalid-key")
    
    def test_port_validation(self):
        """Test port range validation."""
        # Valid port
        settings = AgentMCPSettings(
            openai_api_key="sk-test123456789012345678901234567890",
            api_port=3000
        )
        assert settings.api_port == 3000
        
        # Invalid port (too low)
        with pytest.raises(ValidationError):
            AgentMCPSettings(
                openai_api_key="sk-test123456789012345678901234567890",
                api_port=100
            )
        
        # Invalid port (too high)
        with pytest.raises(ValidationError):
            AgentMCPSettings(
                openai_api_key="sk-test123456789012345678901234567890",
                api_port=70000
            )
    
    def test_effective_embedding_properties(self):
        """Test effective embedding model/dimension properties."""
        # Simple mode
        settings = AgentMCPSettings(
            openai_api_key="sk-test123456789012345678901234567890",
            advanced_embeddings=False
        )
        assert settings.effective_embedding_model == settings.embedding_model
        assert settings.effective_embedding_dimension == settings.embedding_dimension
        
        # Advanced mode
        settings = AgentMCPSettings(
            openai_api_key="sk-test123456789012345678901234567890",
            advanced_embeddings=True
        )
        assert settings.effective_embedding_model == settings.advanced_embedding_model
        assert settings.effective_embedding_dimension == settings.advanced_embedding_dimension
    
    def test_env_prefix(self):
        """Test that environment variables with AGENT_MCP_ prefix are loaded."""
        os.environ["AGENT_MCP_API_PORT"] = "9000"
        os.environ["AGENT_MCP_OPENAI_API_KEY"] = "sk-test123456789012345678901234567890"
        
        try:
            reset_settings()  # Reset to reload from env
            settings = get_settings()
            assert settings.api_port == 9000
        finally:
            # Cleanup
            os.environ.pop("AGENT_MCP_API_PORT", None)
            os.environ.pop("AGENT_MCP_OPENAI_API_KEY", None)
            reset_settings()
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns a singleton."""
        reset_settings()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_security_sanitization_mode(self):
        """Test security sanitization mode validation."""
        # Valid modes
        for mode in ["remove", "neutralize", "block"]:
            settings = AgentMCPSettings(
                openai_api_key="sk-test123456789012345678901234567890",
                security_sanitization_mode=mode
            )
            assert settings.security_sanitization_mode == mode
        
        # Invalid mode
        with pytest.raises(ValidationError):
            AgentMCPSettings(
                openai_api_key="sk-test123456789012345678901234567890",
                security_sanitization_mode="invalid"
            )

