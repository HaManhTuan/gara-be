"""
Core repository components.

This module contains the base implementations, interfaces, and utility classes
that form the foundation of the repository pattern implementation.
"""

from .interfaces import OptimisticLockValidator, QueryBuilder, RelationshipHandler, Repository
from .optimistic_lock_validator import DefaultOptimisticLockValidator
from .query_builder import DefaultQueryBuilder
from .relationship_handler import DefaultRelationshipHandler
from .repository_impl import RepositoryImpl

__all__ = [
    # Main Interface
    "Repository",
    # Component Interfaces
    "QueryBuilder",
    "OptimisticLockValidator",
    "RelationshipHandler",
    # Unified Implementation
    "RepositoryImpl",
    # Default Implementations
    "DefaultQueryBuilder",
    "DefaultOptimisticLockValidator",
    "DefaultRelationshipHandler",
]
