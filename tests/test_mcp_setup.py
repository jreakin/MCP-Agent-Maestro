"""
Hypothesis tests for MCP setup configuration generation and installation.
Tests config generation, installation, and verification.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import text, integers, one_of, none, dictionaries
from typing import Dict, Any

from agent_mcp.api.mcp_setup import (
    MCPConfigGenerator,
    MCPConfigInstaller,
    MCPConfigVerifier,
    ClientType
)


class TestMCPConfigGenerator:
    """Test MCP config generator with Hypothesis."""
    
    @given(
        host=text(min_size=1, max_size=100),
        port=integers(min_value=1, max_value=65535),
        command=text(min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_generate_config_always_returns_dict(self, host: str, port: int, command: str):
        """Generate config always returns a dictionary."""
        generator = MCPConfigGenerator(host=host, port=port, command=command)
        
        for client in ['cursor', 'claude', 'windsurf', 'vscode']:
            config = generator.generate_config(client)
            assert isinstance(config, dict)
            assert 'mcpServers' in config
            assert 'agent-mcp' in config['mcpServers']
    
    @given(
        client=st.sampled_from(['cursor', 'claude', 'windsurf', 'vscode']),
        host=text(min_size=1, max_size=100),
        port=integers(min_value=1, max_value=65535)
    )
    @settings(max_examples=30)
    def test_generate_config_has_correct_structure(self, client: ClientType, host: str, port: int):
        """Generated config has correct structure."""
        generator = MCPConfigGenerator(host=host, port=port)
        config = generator.generate_config(client)
        
        assert 'mcpServers' in config
        server_config = config['mcpServers']['agent-mcp']
        assert 'command' in server_config
        assert 'args' in server_config
        assert isinstance(server_config['args'], list)
    
    @given(
        client=st.sampled_from(['cursor', 'claude', 'windsurf', 'vscode'])
    )
    @settings(max_examples=20)
    def test_generate_config_includes_command(self, client: ClientType):
        """Generated config includes command."""
        command = "custom-command"
        generator = MCPConfigGenerator(command=command)
        config = generator.generate_config(client)
        
        assert config['mcpServers']['agent-mcp']['command'] == command
    
    @given(
        invalid_client=text(min_size=1, max_size=20).filter(lambda x: x not in ['cursor', 'claude', 'windsurf', 'vscode'])
    )
    @settings(max_examples=10)
    def test_generate_config_rejects_invalid_client(self, invalid_client: str):
        """Generate config rejects invalid client types."""
        generator = MCPConfigGenerator()
        with pytest.raises(ValueError):
            generator.generate_config(invalid_client)  # type: ignore


class TestMCPConfigInstaller:
    """Test MCP config installer with Hypothesis (mocked for unit tests)."""
    
    @given(
        client=st.sampled_from(['cursor', 'claude', 'windsurf', 'vscode']),
        config=dictionaries(text(), st.text(), min_size=1, max_size=10),
        backup=st.booleans()
    )
    @settings(max_examples=20)
    @pytest.mark.skip(reason="Requires file system access - run as integration test")
    def test_install_config_returns_result_dict(self, client: ClientType, config: Dict[str, Any], backup: bool):
        """Install config returns a result dictionary."""
        installer = MCPConfigInstaller()
        result = installer.install(client, config, backup=backup)
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert isinstance(result['success'], bool)
        assert 'path' in result
    
    @given(
        invalid_client=text(min_size=1, max_size=20).filter(lambda x: x not in ['cursor', 'claude', 'windsurf', 'vscode'])
    )
    @settings(max_examples=5)
    def test_install_config_rejects_invalid_client(self, invalid_client: str):
        """Install config rejects invalid client types."""
        installer = MCPConfigInstaller()
        with pytest.raises(ValueError):
            installer._get_config_path(invalid_client)  # type: ignore


class TestMCPConfigVerifier:
    """Test MCP config verifier with Hypothesis."""
    
    @given(
        client=st.sampled_from(['cursor', 'claude', 'windsurf', 'vscode'])
    )
    @settings(max_examples=20)
    @pytest.mark.skip(reason="Requires file system access - run as integration test")
    def test_verify_returns_result_dict(self, client: ClientType):
        """Verify returns a result dictionary."""
        verifier = MCPConfigVerifier()
        result = verifier.verify(client)
        
        assert isinstance(result, dict)
        assert 'exists' in result
        assert 'valid' in result
        assert isinstance(result['exists'], bool)
        assert isinstance(result['valid'], bool)
    
    @given(
        invalid_client=text(min_size=1, max_size=20).filter(lambda x: x not in ['cursor', 'claude', 'windsurf', 'vscode'])
    )
    @settings(max_examples=5)
    def test_verify_rejects_invalid_client(self, invalid_client: str):
        """Verify rejects invalid client types."""
        verifier = MCPConfigVerifier()
        with pytest.raises(ValueError):
            verifier.verify(invalid_client)  # type: ignore
    
    @pytest.mark.skip(reason="Requires file system access - run as integration test")
    def test_verify_all_returns_all_clients(self):
        """Verify all returns results for all clients."""
        verifier = MCPConfigVerifier()
        results = verifier.verify_all()
        
        assert isinstance(results, dict)
        assert set(results.keys()) == {'cursor', 'claude', 'windsurf', 'vscode'}
        for client, result in results.items():
            assert 'exists' in result
            assert 'valid' in result

