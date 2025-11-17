# Configuration Files

This directory contains tool-specific configuration files that have been moved from the root directory for better organization.

## Files

- **`mutmut_config.py`**: Mutation testing configuration for mutmut.
  - Note: Mutmut also reads configuration from `pyproject.toml` `[tool.mutmut]` section, which is the preferred location.
  - This file is kept for reference or if you need Python-based configuration logic.

## Standard Config Files (in root)

The following configuration files remain in the root directory as they are standard locations expected by tools:

- `pytest.ini` - Pytest configuration
- `pyproject.toml` - Python project metadata and tool configurations (preferred for most tools)
- `package.json` - Node.js project metadata
- `docker-compose.yml` - Docker Compose configuration

