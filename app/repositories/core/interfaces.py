"""
Repository abstract base classes following SOLID principles.

This module defines abstract base classes for different repository responsibilities,
allowing for better separation of concerns and dependency inversion.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base_model import BaseModel

# Generic type for database models
ModelType = TypeVar("ModelType", bound=BaseModel)


class Repository(ABC, Generic[ModelType]):
    """Combined repository interface with all capabilities."""

    def __init__(self, model: Type[ModelType], **kwargs: Any) -> None:
        """Initialize repository with model."""
        self.model = model

    # Basic CRUD operations
    @abstractmethod
    async def get_by_id(self, db: AsyncSession, id: str, include_deleted: bool = False) -> Optional[ModelType]:
        """Get a record by id."""
        pass

    @abstractmethod
    async def get_by_id_with_relations(
        self, db: AsyncSession, id: str, *, include_deleted: bool = False, relations: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """Get a record by id with relationships eagerly loaded."""
        pass

    @abstractmethod
    async def get_all(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filter_by: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        include_deleted: bool = False,
    ) -> List[ModelType]:
        """Get all records with optional filtering, sorting, and pagination."""
        pass

    @abstractmethod
    async def get_all_with_relations(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filter_by: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        include_deleted: bool = False,
        relations: Optional[List[str]] = None,
    ) -> List[ModelType]:
        """
        Get all records with relationships loaded.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filter_by: Optional filtering criteria
            order_by: Optional sorting criteria
            include_deleted: Whether to include soft-deleted records
            relations: List of relationship names to load (None = load all)

        Returns:
            List of model instances with relationships loaded
        """
        pass

    @abstractmethod
    async def count(
        self, db: AsyncSession, filter_by: Optional[Dict[str, Any]] = None, include_deleted: bool = False
    ) -> int:
        """Count records with optional filtering."""
        pass

    @abstractmethod
    async def create(self, db: AsyncSession, *, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """Create a new record."""
        pass

    @abstractmethod
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], ModelType],
    ) -> ModelType:
        """Update a record."""
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, *, id: str) -> ModelType:
        """Delete a record."""
        pass

    # Optimistic locking operations
    @abstractmethod
    async def update_with_optimistic_lock(
        self,
        db: AsyncSession,
        *,
        id: str,
        obj_in: Union[Dict[str, Any], ModelType],
        expected_updated_at: Optional[str] = None,
    ) -> ModelType:
        """Update a record with optimistic locking."""
        pass

    # Relationship operations
    @abstractmethod
    async def create_with_relations(self, db: AsyncSession, *, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """Create record with nested relationships."""
        pass

    @abstractmethod
    async def update_with_optimistic_lock_and_relations(
        self, db: AsyncSession, *, id: str, obj_in: Union[Dict[str, Any], ModelType], sync_mode: str = "merge"
    ) -> Optional[ModelType]:
        """Update record with nested relationships and optimistic locking."""
        pass

    @abstractmethod
    async def manage_relations(
        self,
        db: AsyncSession,
        *,
        parent_id: str,
        relation_name: str,
        obj_in: Union[List[Dict], List[str]],
        operation: str = "add",
    ) -> Optional[ModelType]:
        """Add or remove relationships."""
        pass

    # Cascade operations
    @abstractmethod
    async def delete_with_cascade(self, db: AsyncSession, *, id: str, hard_delete: bool = False) -> Optional[ModelType]:
        """Delete record with cascade options."""
        pass

    @abstractmethod
    async def soft_delete(self, db: AsyncSession, *, id: str) -> ModelType:
        """Soft delete a record."""
        pass

    @abstractmethod
    async def restore(self, db: AsyncSession, *, id: str) -> ModelType:
        """Restore a soft-deleted record."""
        pass


class QueryBuilder(ABC):
    """Abstract base class for query building operations."""

    def __init__(self, model: Type[BaseModel]):
        """Initialize query builder with model."""
        self.model = model

    @abstractmethod
    def build_base_query(
        self,
        filter_by: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False,
    ) -> Any:
        """Build base query with common filters."""
        pass

    @abstractmethod
    def apply_sorting(self, query: Any, order_by: Optional[List[str]]) -> Any:
        """Apply sorting to query."""
        pass


class OptimisticLockValidator(ABC):
    """Abstract base class for optimistic lock validation."""

    @abstractmethod
    def parse_timestamp(self, timestamp_str: str) -> Any:
        """Parse timestamp string with timezone handling."""
        pass

    @abstractmethod
    def validate_optimistic_lock(
        self, expected_timestamp: str, actual_timestamp: Any, record_id: str, model_name: str
    ) -> None:
        """Validate optimistic lock by comparing timestamps."""
        pass


class RelationshipHandler(ABC):
    """Abstract base class for relationship handling operations."""

    @abstractmethod
    def get_relationship_handler(self, direction: Any, uselist: bool = True) -> str:
        """Get the appropriate handler method name for a relationship direction."""
        pass

    @abstractmethod
    def get_relationship_manager(self, direction: Any, uselist: bool = True) -> str:
        """Get the appropriate manager method name for a relationship direction."""
        pass

    @abstractmethod
    def is_relationship_field(self, model_name: str, field_name: str) -> bool:
        """Check if a field is a relationship field."""
        pass
