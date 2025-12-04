"""
Async task utilities for Celery workers.

This module provides utilities to run async functions in Celery tasks,
bridging the gap between gevent's greenlet-based concurrency and Python's asyncio.
"""
import asyncio
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar

from app.utils.logger import get_logger

logger = get_logger("async_task")

T = TypeVar("T")


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Get or create an event loop for the current greenlet.

    In gevent context, each greenlet should have its own event loop.
    This function ensures thread-safe event loop management.

    Returns:
        An event loop suitable for running async code
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        # Check if the loop is closed or can't be used
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No event loop exists for this greenlet, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async coroutine in a Celery task context.

    This function reuses or creates an event loop for the current greenlet
    and runs the async coroutine to completion. It handles the event loop
    lifecycle and ensures proper cleanup.

    Args:
        coro: The async coroutine to run

    Returns:
        The result of the coroutine

    Example:
        @celery_app.task
        def my_task(user_id: str) -> dict:
            return run_async(get_user_data_async(user_id))

        async def get_user_data_async(user_id: str) -> dict:
            async with get_db_session() as db:
                user = await user_repository.get_by_id(db, user_id)
                return {"user": user.username}
    """
    try:
        # Get or create event loop for this greenlet
        loop = get_or_create_event_loop()

        # Run the coroutine to completion
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error running async task: {str(e)}")
        raise


def async_task_decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Any]:
    """
    Decorator to convert an async function into a Celery task.

    This decorator wraps an async function to make it callable from Celery,
    automatically handling the event loop management.

    Args:
        func: The async function to wrap

    Returns:
        A wrapped function suitable for use as a Celery task

    Example:
        @celery_app.task
        @async_task_decorator
        async def my_async_task(name: str) -> str:
            await asyncio.sleep(1)
            return f"Hello, {name}!"
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.debug(f"Running async task: {func.__name__}")
        return run_async(func(*args, **kwargs))

    return wrapper


# Cleanup function that can be called when gevent greenlet exits
def cleanup_event_loop() -> None:
    """
    Clean up the event loop for the current greenlet.

    This should be called when a greenlet is shutting down to ensure
    proper resource cleanup.
    """
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            # Cancel all remaining tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            # Run until all tasks are done
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            # Close the loop
            loop.close()
    except (RuntimeError, AttributeError):
        # No event loop to clean up
        pass
