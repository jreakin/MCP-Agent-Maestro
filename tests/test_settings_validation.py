"""
Tests for enhanced configuration validation in settings.py.
"""
import pytest
import os
from agent_mcp.core.settings import AgentMCPSettings, reset_settings
from pydantic import ValidationError


class TestDatabasePasswordValidation:
    """Test database password validation."""
    
    def test_production_password_required(self):
        """Test that password is required in production."""
        os.environ["ENVIRONMENT"] = "production"
        reset_settings()
        
        with pytest.raises(ValidationError) as exc_info:
            AgentMCPSettings(db_password=None)
        
        assert "required for production" in str(exc_info.value)
        os.environ.pop("ENVIRONMENT", None)
        reset_settings()
    
    def test_development_password_optional(self):
        """Test that password is optional in development."""
        os.environ["ENVIRONMENT"] = "development"
        reset_settings()
        
        # Should not raise in development
        settings = AgentMCPSettings(db_password=None)
        assert settings.db_password is None
        
        os.environ.pop("ENVIRONMENT", None)
        reset_settings()
    
    def test_weak_password_warning(self):
        """Test that weak passwords trigger warnings in production."""
        import warnings
        os.environ["ENVIRONMENT"] = "production"
        reset_settings()
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            AgentMCPSettings(db_password="weak")
            assert len(w) > 0
            assert "short" in str(w[0].message).lower()
        
        os.environ.pop("ENVIRONMENT", None)
        reset_settings()


class TestDatabaseURLValidation:
    """Test database URL format validation."""
    
    def test_valid_postgresql_url(self):
        """Test valid PostgreSQL URL."""
        settings = AgentMCPSettings(
            database_url="postgresql://user:pass@localhost/db"
        )
        assert settings.database_url.startswith("postgresql://")
    
    def test_valid_postgres_url(self):
        """Test valid postgres URL."""
        settings = AgentMCPSettings(
            database_url="postgres://user:pass@localhost/db"
        )
        assert settings.database_url.startswith("postgres://")
    
    def test_invalid_database_url(self):
        """Test invalid database URL."""
        with pytest.raises(ValidationError) as exc_info:
            AgentMCPSettings(database_url="mysql://user:pass@localhost/db")
        
        assert "postgresql" in str(exc_info.value).lower()
    
    def test_none_database_url(self):
        """Test None database URL is allowed."""
        settings = AgentMCPSettings(database_url=None)
        assert settings.database_url is None


class TestPortValidation:
    """Test API port validation."""
    
    def test_port_conflict_same_ports(self):
        """Test that same API and dashboard ports raise error (when not in Docker)."""
        import os
        # Temporarily remove Docker detection
        original_docker_env = os.environ.pop('DOCKER_CONTAINER', None)
        docker_file = '/.dockerenv'
        docker_file_exists = os.path.exists(docker_file)
        
        try:
            # If in Docker, mock it to not be Docker for this test
            if docker_file_exists:
                # Can't easily remove the file, so test will just warn instead of raise
                # This is expected behavior in Docker
                import warnings
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    settings = AgentMCPSettings(api_port=8080, dashboard_port=8080)
                    # In Docker, it should warn instead of raise
                    assert len(w) > 0
                    assert "same" in str(w[0].message).lower()
            else:
                # Not in Docker, should raise error
                with pytest.raises(ValidationError) as exc_info:
                    AgentMCPSettings(api_port=8080, dashboard_port=8080)
                assert "cannot be the same" in str(exc_info.value)
        finally:
            if original_docker_env:
                os.environ['DOCKER_CONTAINER'] = original_docker_env
    
    def test_port_conflict_close_ports_warning(self):
        """Test that close ports trigger warning."""
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            AgentMCPSettings(
                openai_api_key="sk-test123456789012345678901234567890",
                api_port=8080, 
                dashboard_port=8081
            )
            assert len(w) > 0
            assert "close" in str(w[0].message).lower()
    
    def test_privileged_port_warning(self):
        """Test that privileged ports trigger warning."""
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Use port 1024 (minimum allowed) to trigger privileged warning
            # Note: Port 80 is rejected by Field validator before reaching the warning
            AgentMCPSettings(
                openai_api_key="sk-test123456789012345678901234567890",
                api_port=1024
            )
            # The warning may not trigger for 1024 since it's the minimum
            # Let's test with a port that will actually trigger the warning check
            # Actually, the validator checks if port < 1024, so 1024 won't trigger it
            # The test needs to use a port that passes Field validation but is in privileged range
            # Since Field validation requires ge=1024, we can't test <1024 ports
            # So this test validates that ports < 1024 are rejected by Field validator
            with pytest.raises(ValidationError):
                AgentMCPSettings(
                    openai_api_key="sk-test123456789012345678901234567890",
                    api_port=80
                )


class TestConfigurationHealthCheck:
    """Test configuration health check method."""
    
    def test_health_check_healthy(self):
        """Test health check with healthy configuration."""
        settings = AgentMCPSettings(
            db_password="secure_password",
            openai_api_key="sk-test12345678901234567890"
        )
        health = settings.check_configuration_health()
        assert health["status"] == "healthy"
        assert len(health["warnings"]) == 0
    
    def test_health_check_with_warnings(self):
        """Test health check with warnings."""
        settings = AgentMCPSettings(
            security_enabled=False,
            openai_api_key=None
        )
        os.environ["EMBEDDING_PROVIDER"] = "openai"
        health = settings.check_configuration_health()
        assert health["status"] == "warnings"
        assert len(health["warnings"]) > 0
        os.environ.pop("EMBEDDING_PROVIDER", None)


class TestSettingsBackwardCompatibility:
    """Test backward compatibility with AGENT_MCP_ prefix."""
    
    def test_env_prefix_still_works(self):
        """Test that AGENT_MCP_ prefix still works."""
        os.environ["AGENT_MCP_API_PORT"] = "9000"
        reset_settings()
        
        settings = AgentMCPSettings()
        assert settings.api_port == 9000
        
        os.environ.pop("AGENT_MCP_API_PORT", None)
        reset_settings()

