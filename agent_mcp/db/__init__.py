"""
Database module - PostgreSQL only.
Provides compatibility imports for existing code.
"""
from .connection_factory import (
    get_db_connection,
    get_db_connection_read,
    db_connection,
    return_connection,
    get_pool_stats,
    check_pool_health,
    close_pg_pool,
)

# Compatibility: PostgreSQL always supports vector operations if pgvector is installed
def is_vss_loadable() -> bool:
    """For PostgreSQL, vector support is always available if pgvector extension exists."""
    return True

def check_vss_loadability() -> bool:
    """For PostgreSQL, vector support check is handled at connection time."""
    return True

# For PostgreSQL, we don't need a write queue (PostgreSQL handles concurrency better)
# But we'll provide a compatibility function
async def execute_db_write(operation_func):
    """
    Execute a database write operation.
    For PostgreSQL, this is a simple wrapper since PostgreSQL handles concurrency well.
    """
    return await operation_func()

# Re-export for compatibility
__all__ = [
    'get_db_connection',
    'get_db_connection_read',
    'db_connection',  # Context manager for automatic connection management
    'return_connection',
    'get_pool_stats',
    'check_pool_health',
    'close_pg_pool',
    'is_vss_loadable',
    'check_vss_loadability',
    'execute_db_write',
]
