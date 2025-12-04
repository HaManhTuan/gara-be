"""
Celery tasks for background job processing.

This module contains all Celery tasks that process background jobs.
All tasks use async/await for IO operations and reuse code from FastAPI services.
"""
import asyncio
from typing import Any, Dict, Optional

from celery import Task
from celery.utils.log import get_task_logger

from app.config.database import get_async_db
from app.repositories.concrete.user_repository import UserRepository
from app.utils.logger import get_logger
from app.workers.async_task import run_async
from app.workers.celery_app import celery_app

# Get Celery task logger
celery_logger = get_task_logger(__name__)
# Get application logger
logger = get_logger("tasks")


# Example async helper function (can be reused in FastAPI endpoints)
async def example_task_async(name: str) -> str:
    """
    Async example task that logs a message

    Args:
        name: Name to include in the logged message

    Returns:
        Result message
    """
    logger.info(f"Running async example task for {name}")

    # Simulate async IO operation
    await asyncio.sleep(2)

    result = f"Hello, {name}! Task completed."
    logger.info(f"Task completed with result: {result}")

    return result


# Celery task wrapper
@celery_app.task(name="example_task")  # type: ignore[misc]
def example_task(name: str) -> str:
    """
    Example task that runs async function

    Args:
        name: Name to include in the logged message

    Returns:
        Result message
    """
    return run_async(example_task_async(name))


# Async helper function for data processing
async def process_data_async(data_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Async data processing logic

    Args:
        data_id: ID of the data to process
        options: Optional processing options

    Returns:
        Processing result
    """
    logger.info(f"Processing data {data_id} with options {options}")

    # Simulate async processing
    await asyncio.sleep(3)

    # Return success result
    return {
        "status": "success",
        "data_id": data_id,
        "message": "Data processed successfully",
    }


# Celery task wrapper with retry
@celery_app.task(name="process_data", bind=True, max_retries=3)  # type: ignore[misc]
def process_data(self: Task, data_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Example of data processing task with retry capabilities

    Args:
        self: Task instance (injected by Celery when bind=True)
        data_id: ID of the data to process
        options: Optional processing options

    Returns:
        Processing result
    """
    try:
        return run_async(process_data_async(data_id, options))
    except Exception as exc:
        logger.error(f"Error processing data {data_id}: {str(exc)}")
        # Retry with exponential backoff
        retry_in = 60 * (2**self.request.retries)  # 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=retry_in)


# Example: Database IO task using async repositories
async def get_user_info_async(user_id: str) -> Dict[str, Any]:
    """
    Async function that queries database using repository pattern

    Args:
        user_id: ID of the user to retrieve

    Returns:
        User information
    """
    logger.info(f"Fetching user info for user_id: {user_id}")

    async with get_async_db() as db:
        user_repository = UserRepository()
        user = await user_repository.get_by_id(db, user_id)

        if not user:
            return {"status": "error", "message": "User not found", "user_id": user_id}

        return {
            "status": "success",
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        }


@celery_app.task(name="get_user_info")  # type: ignore[misc]
def get_user_info(user_id: str) -> Dict[str, Any]:
    """
    Task to fetch user information from database

    Args:
        user_id: ID of the user to retrieve

    Returns:
        User information dictionary
    """
    return run_async(get_user_info_async(user_id))


# Example: External API call using httpx
async def call_external_api_async(url: str, method: str = "GET") -> Dict[str, Any]:
    """
    Async function that calls external API

    Args:
        url: URL to call
        method: HTTP method (GET, POST, etc.)

    Returns:
        API response data
    """
    logger.info(f"Calling external API: {method} {url}")

    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, timeout=10.0)
            response.raise_for_status()

            return {
                "status": "success",
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "data": response.json()
                if response.headers.get("content-type", "").startswith("application/json")
                else response.text,
            }
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling {url}: {str(e)}")
        return {"status": "error", "url": url, "error": str(e)}


@celery_app.task(name="call_external_api")  # type: ignore[misc]
def call_external_api(url: str, method: str = "GET") -> Dict[str, Any]:
    """
    Task to call external API

    Args:
        url: URL to call
        method: HTTP method

    Returns:
        API response
    """
    return run_async(call_external_api_async(url, method))
