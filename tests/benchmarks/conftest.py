"""
Pytest configuration for benchmark tests.
"""
import pytest


def pytest_configure(config):
    """Register benchmark marker."""
    config.addinivalue_line(
        "markers", "benchmark: mark test as a benchmark test"
    )

