"""
PostgreSQL database connection module with connection pooling and context managers.
"""
import os
import time
from typing import Optional, Generator
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from psycopg2 import OperationalError, InterfaceError

from ..core.config import logger
from ..core.settings import get_settings

# Connection pool for PostgreSQL
_pg_pool: Optional[ThreadedConnectionPool] = None

# Store pool references for connections (since psycopg2 connections don't allow arbitrary attributes)
_connection_pools: dict = {}

# Connection retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
CONNECTION_TIMEOUT = 30  # seconds

def _get_pg_pool() -> ThreadedConnectionPool:
    """Get or create PostgreSQL connection pool with configurable settings."""
    global _pg_pool
    
    if _pg_pool is None:
        settings = get_settings()
        
        # Use database_url if provided, otherwise use individual settings
        if settings.database_url:
            # Parse connection string (format: postgresql://user:password@host:port/dbname)
            import urllib.parse
            parsed = urllib.parse.urlparse(settings.database_url)
            db_host = parsed.hostname or settings.db_host
            db_port = parsed.port or settings.db_port
            db_name = parsed.path.lstrip('/') or settings.db_name
            db_user = parsed.username or settings.db_user
            db_password = parsed.password or settings.db_password or ""
        else:
            # Use individual settings (prioritize env vars for Docker compatibility)
            # Environment variables take precedence over settings defaults
            db_host = os.environ.get("DB_HOST") or settings.db_host
            db_port = int(os.environ.get("DB_PORT") or str(settings.db_port))
            db_name = os.environ.get("DB_NAME") or settings.db_name
            db_user = os.environ.get("DB_USER") or settings.db_user
            db_password = os.environ.get("DB_PASSWORD") or settings.db_password or ""
        
        # Configurable pool size
        minconn = settings.db_pool_min or int(os.environ.get("DB_POOL_MIN", "1"))
        maxconn = settings.db_pool_max or int(os.environ.get("DB_POOL_MAX", "10"))
        
        try:
            _pg_pool = ThreadedConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password,
                connect_timeout=CONNECTION_TIMEOUT,
            )
            logger.info(
                f"PostgreSQL connection pool created: {db_user}@{db_host}:{db_port}/{db_name} "
                f"(min={minconn}, max={maxconn})"
            )
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise RuntimeError(f"Failed to connect to PostgreSQL: {e}") from e
    
    return _pg_pool

def _check_connection_health(conn) -> bool:
    """Check if a connection is healthy."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except (OperationalError, InterfaceError):
        return False
    except Exception:
        return False

def _get_connection_with_retry() -> psycopg2.extensions.connection:
    """Get a connection from the pool with retry logic."""
    pool = _get_pg_pool()
    
    for attempt in range(MAX_RETRIES):
        try:
            conn = pool.getconn()
            
            # Check connection health
            if not _check_connection_health(conn):
                # Connection is dead, close it and try again
                try:
                    conn.close()
                except Exception:
                    pass
                pool.putconn(conn, close=True)
                
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    raise RuntimeError("Failed to get healthy connection after retries")
            
            # Enable pgvector extension if available (only once per connection)
            try:
                with conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    conn.commit()
                    logger.debug("pgvector extension enabled")
            except Exception as e:
                logger.warning(f"Could not enable pgvector extension: {e}")
                conn.rollback()
            
            # Set connection to return dict-like rows (similar to sqlite3.Row)
            conn.cursor_factory = RealDictCursor
            
            # Store pool reference in external dict
            _connection_pools[id(conn)] = pool
            
            return conn
            
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Failed to get connection (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to get connection after {MAX_RETRIES} attempts: {e}")
                raise
    
    raise RuntimeError("Failed to get connection after retries")

def get_postgres_connection():
    """
    Get a PostgreSQL connection from the pool.
    Returns a connection that acts like sqlite3.Connection for compatibility.
    
    Note: Caller is responsible for closing the connection or returning it to the pool.
    For automatic management, use db_connection() context manager instead.
    """
    return _get_connection_with_retry()

@contextmanager
def db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Context manager for database connections.
    Automatically returns connection to pool on exit.
    
    Usage:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks")
            results = cursor.fetchall()
    """
    conn = None
    try:
        conn = _get_connection_with_retry()
        yield conn
    except Exception as e:
        if conn:
            # On error, mark connection as bad
            conn_id = id(conn)
            if conn_id in _connection_pools:
                pool = _connection_pools.pop(conn_id)
                try:
                    conn.rollback()
                except Exception:
                    pass
                pool.putconn(conn, close=True)
        raise
    finally:
        if conn:
            return_connection(conn)

def return_connection(conn):
    """Return a connection to the pool."""
    conn_id = id(conn)
    if conn_id in _connection_pools:
        pool = _connection_pools.pop(conn_id)
        try:
            # Check if connection is still healthy before returning
            if _check_connection_health(conn):
                pool.putconn(conn)
            else:
                # Connection is dead, close it
                try:
                    conn.close()
                except Exception:
                    pass
                pool.putconn(conn, close=True)
                logger.warning("Returned dead connection to pool, it was closed")
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")
            try:
                conn.close()
            except Exception:
                pass
    else:
        # Connection not from our pool, just close it
        try:
            conn.close()
        except Exception:
            pass

def get_pool_stats() -> dict:
    """Get connection pool statistics."""
    pool = _get_pg_pool()
    return {
        "minconn": pool.minconn,
        "maxconn": pool.maxconn,
        "closed": pool.closed,
    }

def check_pool_health() -> bool:
    """Check if the connection pool is healthy."""
    try:
        pool = _get_pg_pool()
        if pool.closed:
            return False
        
        # Try to get and return a connection
        conn = pool.getconn()
        try:
            if _check_connection_health(conn):
                pool.putconn(conn)
                return True
            else:
                pool.putconn(conn, close=True)
                return False
        except Exception:
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
            return False
    except Exception as e:
        logger.error(f"Pool health check failed: {e}")
        return False

def close_pg_pool():
    """Close the PostgreSQL connection pool."""
    global _pg_pool
    if _pg_pool:
        _pg_pool.closeall()
        _pg_pool = None
        _connection_pools.clear()
        logger.info("PostgreSQL connection pool closed")
