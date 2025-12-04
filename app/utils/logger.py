import contextvars
import os
import sys
from typing import Any, Optional

from loguru import logger

from app.config.settings import settings

# Create a context variable to store request ID
request_id_var = contextvars.ContextVar[Optional[str]]("request_id", default=None)

# Enhanced log format with request ID
text_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[request_id]}</cyan> | "
    "<blue>{extra[context]}</blue> | "
    "<level>{message}</level>"
)

# JSON log format
json_format = (
    "{{"
    '"timestamp": "{time:YYYY-MM-DD HH:mm:ss}", '
    '"level": "{level}", '
    '"request_id": "{extra[request_id]}", '
    '"context": "{extra[context]}", '
    '"message": "{message}"'
    "}}"
)


def configure_logger() -> None:
    """Configure the logger based on current settings"""
    # Remove all existing handlers
    logger.remove()

    # Choose format based on configuration
    log_format = json_format if settings.LOG_FORMAT_JSON else text_format

    # Configure console output
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=not settings.LOG_FORMAT_JSON,  # Disable colorization for JSON format
    )

    # Configure file output if enabled
    if settings.LOG_TO_FILE and settings.LOG_FILE_PATH:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(settings.LOG_FILE_PATH), exist_ok=True)

        # Add file logger
        logger.add(
            settings.LOG_FILE_PATH,
            format=log_format,  # Use the same format as console
            serialize=False,  # Always use custom format, not loguru's serialize
            level=settings.LOG_LEVEL,
            rotation="10 MB",  # Rotate when file reaches 10MB
            retention="30 days",  # Keep logs for 30 days
            compression="zip",  # Compress rotated logs
        )


# Configure logger on module import
configure_logger()


def set_request_id(id_value: Optional[str]) -> None:
    """Set the request ID for the current context"""
    if id_value:
        request_id_var.set(id_value)


def get_request_id() -> Optional[str]:
    """Get the request ID for the current context"""
    return request_id_var.get()


# Create a function to get logger
def get_logger(name: Optional[str] = None) -> Any:
    """Get a logger with an optional name and current request ID"""
    request_id = get_request_id() or "no-request-id"
    return logger.bind(context=name, request_id=request_id)
