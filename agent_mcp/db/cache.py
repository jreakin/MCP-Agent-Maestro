"""
Simple in-memory cache for database query results.
Provides TTL-based caching for frequently accessed data.
"""
import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
import hashlib
import json

from ..core.config import logger


class QueryCache:
    """Simple TTL-based cache for database query results."""
    
    def __init__(self, default_ttl: int = 60):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
    
    def invalidate(self, pattern: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            pattern: If provided, only invalidate keys starting with pattern
        """
        if pattern:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of cached entries."""
        return len(self._cache)


# Global cache instance
_cache = QueryCache(default_ttl=60)


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    # Create a stable representation of arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.sha256(key_str.encode()).hexdigest()[:16]


def cached_query(ttl: int = 60, key_prefix: str = ""):
    """
    Decorator to cache database query results.
    
    Usage:
        @cached_query(ttl=120, key_prefix="tasks")
        def get_all_tasks():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Check cache
            cached_result = _cache.get(cache_key_str)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            _cache.set(cache_key_str, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Check cache
            cached_result = _cache.get(cache_key_str)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            _cache.set(cache_key_str, result, ttl)
            return result
        
        # Return appropriate wrapper
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern."""
    _cache.invalidate(pattern)


def clear_cache():
    """Clear all cache entries."""
    _cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return {
        "size": _cache.size(),
        "default_ttl": _cache.default_ttl
    }

