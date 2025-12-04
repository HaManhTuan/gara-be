"""
Repository module.

This module provides access to all repository components including
the factory, core implementations, and concrete repositories.
"""

# Core components
from .core import OptimisticLockValidator, QueryBuilder, RelationshipHandler, Repository, RepositoryImpl

# Factory
from .factory import RepositoryFactory, repository_factory

__all__ = [
    # Factory
    "RepositoryFactory",
    "repository_factory",
    # Core interfaces
    "Repository",
    "QueryBuilder",
    "OptimisticLockValidator",
    "RelationshipHandler",
    # Unified implementation
    "RepositoryImpl",
    # Default implementations
    # Concrete repositories
]
