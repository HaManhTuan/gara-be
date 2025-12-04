"""
Services package.

This module provides access to all service implementations for each model,
providing business logic and orchestration between repositories and controllers.
"""

from app.services.user_service import UserService, user_service

__all__ = [
    "UserService",
    "user_service",
]
