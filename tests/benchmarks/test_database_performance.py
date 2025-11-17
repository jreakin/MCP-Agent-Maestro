"""
Benchmark tests for database connection pool efficiency.
"""
import pytest
import time
from agent_mcp.db import get_db_connection, return_connection, check_pool_health, get_pool_stats
from agent_mcp.core.settings import get_settings


@pytest.mark.benchmark
def test_connection_acquire_time(benchmark):
    """Benchmark database connection acquisition time."""
    
    def acquire_connection():
        """Acquire and return a database connection."""
        conn = get_db_connection()
        return_connection(conn)
        return True
    
    result = benchmark(acquire_connection)
    assert result is True


@pytest.mark.benchmark
def test_pool_health_check_performance(benchmark):
    """Benchmark pool health check performance."""
    
    def check_health():
        """Check database pool health."""
        return check_pool_health()
    
    result = benchmark(check_health)
    assert isinstance(result, bool)


@pytest.mark.benchmark
def test_pool_stats_retrieval(benchmark):
    """Benchmark pool statistics retrieval."""
    
    def get_stats():
        """Get database pool statistics."""
        return get_pool_stats()
    
    result = benchmark(get_stats)
    assert isinstance(result, dict)


@pytest.mark.benchmark
def test_concurrent_connection_usage(benchmark):
    """Benchmark concurrent connection usage."""
    import concurrent.futures
    
    def use_connection():
        """Use a database connection."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        finally:
            return_connection(conn)
    
    def concurrent_usage():
        """Use multiple connections concurrently."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(use_connection) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        return results
    
    result = benchmark(concurrent_usage)
    assert len(result) == 5

