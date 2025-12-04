"""
Repository factory following SOLID principles.

This module provides a factory for creating repository instances with
proper dependency injection, following the Dependency Inversion Principle.
"""

from typing import Optional, Type

from app.models.base_model import BaseModel
from app.repositories.core import (
    DefaultOptimisticLockValidator,
    DefaultQueryBuilder,
    OptimisticLockValidator,
    QueryBuilder,
)
from app.repositories.core.repository_impl import RepositoryImpl
from app.utils.tracing import get_trace_logger

# Create logger instance for this module
logger = get_trace_logger("repository-factory")


class RepositoryFactory:
    """Factory for creating repository instances with dependency injection."""

    def __init__(
        self,
        query_builder_class: Type[QueryBuilder] = DefaultQueryBuilder,
        optimistic_lock_validator_class: Type[OptimisticLockValidator] = DefaultOptimisticLockValidator,
    ):
        """
        Initialize the factory with component classes.

        Args:
            query_builder_class: Query builder implementation class
            optimistic_lock_validator_class: Optimistic lock validator implementation class
        """
        self.query_builder_class = query_builder_class
        self.optimistic_lock_validator_class = optimistic_lock_validator_class

    def create_repository(
        self,
        model: Type[BaseModel],
        query_builder: Optional[QueryBuilder] = None,
        optimistic_lock_validator: Optional[OptimisticLockValidator] = None,
    ) -> RepositoryImpl:
        """
        Create a unified repository instance with all capabilities.

        Args:
            model: The SQLAlchemy model class
            query_builder: Optional query builder instance
            optimistic_lock_validator: Optional optimistic lock validator instance

        Returns:
            Unified repository instance with all capabilities
        """
        return RepositoryImpl(
            model=model,
            query_builder=query_builder or self.query_builder_class(model),
            optimistic_lock_validator=optimistic_lock_validator or self.optimistic_lock_validator_class(),
        )


# Global factory instance
repository_factory = RepositoryFactory()
