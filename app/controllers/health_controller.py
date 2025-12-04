from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.common import ResponseBuilder, SuccessResponse
from app.utils.i18n import __
from app.utils.tracing import get_trace_logger

router = APIRouter()
logger = get_trace_logger("health-controller")


@router.get("/health", response_model=SuccessResponse[Dict[str, Any]])  # type: ignore[misc]
def health_check() -> SuccessResponse[Dict[str, Any]]:
    """
    Health check endpoint for the API

    Returns a simple response to indicate the API is running.
    """
    logger.debug("Health check called")
    return ResponseBuilder.success(message=__("health.service_running"), data={"status": "ok"})


@router.get("/health/db", response_model=SuccessResponse[Dict[str, Any]])  # type: ignore[misc]
async def db_health_check(db: AsyncSession = Depends(get_db)) -> SuccessResponse[Dict[str, Any]]:
    """
    Database health check endpoint

    Tests the database connection by executing a simple query.
    """
    logger.debug("Database health check called")

    # Execute a simple query to check DB connection
    await db.execute(text("SELECT 1"))

    logger.info("Database health check successful")
    return ResponseBuilder.success(message=__("health.database_healthy"), data={"status": "ok"})
