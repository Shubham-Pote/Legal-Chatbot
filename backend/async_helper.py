"""
Streamlit-compatible wrapper for async Prisma operations
Fixes "Event loop is closed" errors
"""
import asyncio
import functools
from typing import Any, Callable

def run_async(coro):
    """
    Safely run async coroutine in Streamlit
    Creates a new event loop if needed to avoid "Event loop is closed" errors
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)

def async_to_sync(async_func: Callable) -> Callable:
    """
    Decorator to convert async function to sync for Streamlit
    """
    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        return run_async(async_func(*args, **kwargs))
    return wrapper

