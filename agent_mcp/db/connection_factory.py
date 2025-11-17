"""
Database connection factory - PostgreSQL only.
"""
from ..core.config import logger
from .postgres_connection import (
    get_postgres_connection,
    db_connection,
    return_connection,
    get_pool_stats,
    check_pool_health,
    close_pg_pool,
)

def get_db_connection():
    """
    Returns a PostgreSQL database connection.
    PostgreSQL is now the only supported database.
    
    Note: For automatic connection management, use db_connection() context manager instead.
    """
    return get_postgres_connection()

def get_db_connection_read():
    """Get a read-only database connection."""
    return get_db_connection()

# Export context manager and utilities
__all__ = [
    'get_db_connection',
    'get_db_connection_read',
    'db_connection',  # Context manager for automatic connection management
    'return_connection',
    'get_pool_stats',
    'check_pool_health',
    'close_pg_pool',
]
