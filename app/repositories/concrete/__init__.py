"""
Concrete repository implementations.

This module contains specific repository implementations for each model,
providing model-specific database operations and business logic.
"""

from .user_repository import UserRepository, user_repository

__all__ = [
    "UserRepository",
    "user_repository",
]
