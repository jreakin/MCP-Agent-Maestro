"""
Utilities for async/await optimization and non-blocking operations.
"""
import asyncio
import functools
from typing import Callable, Any, Coroutine
from concurrent.futures import ThreadPoolExecutor
import threading

from ..core.config import logger

# Thread pool for CPU-bound or blocking operations
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="agent-mcp-async")


def run_in_executor(func: Callable) -> Callable:
    """
    Decorator to run a blocking function in a thread pool executor.
    
    Usage:
        @run_in_executor
        def blocking_operation():
            # This will run in a thread pool
            ...
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))
    
    return async_wrapper


async def run_blocking(func: Callable, *args, **kwargs) -> Any:
    """
    Run a blocking function in a thread pool executor.
    
    Usage:
        result = await run_blocking(some_blocking_function, arg1, arg2)
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


def async_to_sync(async_func: Callable) -> Callable:
    """
    Convert an async function to a sync function (for compatibility).
    Creates a new event loop if needed.
    
    Usage:
        sync_func = async_to_sync(async_function)
        result = sync_func()  # Blocks until async function completes
    """
    @functools.wraps(async_func)
    def sync_wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If loop is already running, we need to use a different approach
            # This is a fallback - ideally we should avoid this pattern
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(async_func(*args, **kwargs))
                )
                return future.result()
        else:
            return loop.run_until_complete(async_func(*args, **kwargs))
    
    return sync_wrapper


async def gather_with_limit(coroutines: list[Coroutine], limit: int = 10) -> list[Any]:
    """
    Run coroutines with a concurrency limit.
    
    Usage:
        results = await gather_with_limit([coro1(), coro2(), ...], limit=5)
    """
    semaphore = asyncio.Semaphore(limit)
    
    async def bounded_coro(coro: Coroutine):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*[bounded_coro(coro) for coro in coroutines])


def is_blocking_operation(func: Callable) -> bool:
    """
    Check if a function is likely a blocking operation.
    This is a heuristic check based on common patterns.
    """
    import inspect
    
    # Check if function is async
    if inspect.iscoroutinefunction(func):
        return False
    
    # Check for common blocking operations in source
    try:
        source = inspect.getsource(func)
        blocking_patterns = [
            'time.sleep',
            'open(',
            '.read(',
            '.write(',
            'requests.',
            'urllib.',
            'socket.',
            'subprocess.',
        ]
        
        for pattern in blocking_patterns:
            if pattern in source:
                return True
    except (OSError, TypeError):
        # Can't inspect source, assume it might be blocking
        pass
    
    return False

