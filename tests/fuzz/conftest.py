"""
Pytest configuration and fixtures for fuzzing tests.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ.setdefault("MCP_DEBUG", "true")
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("FUZZING", "true")

# Fuzzing corpus directory (mounted as volume in docker-compose)
CORPUS_DIR = Path(project_root) / ".corpus"
CORPUS_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def corpus_dir():
    """Provide corpus directory for fuzzing."""
    return CORPUS_DIR

