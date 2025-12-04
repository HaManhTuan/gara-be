from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base_model import BaseModel
from app.repositories.core.interfaces import Repository
from app.utils.tracing import get_trace_logger

# Generic types
ModelType = TypeVar("ModelType", bound=BaseModel)
RepositoryType = TypeVar("RepositoryType", bound=Repository)

# Module-level logger
logger = get_trace_logger("service")


class BaseService(Generic[ModelType, RepositoryType]):
    """
    Base service class with business logic

    This class serves as a service layer between controllers and repositories,
    containing business logic and validation
    """

    def __init__(self, repository: RepositoryType) -> None:
        """
        Initialize the service with a repository

        Args:
            repository: The repository instance to use for data access
        """
        self.repository = repository
        self.model_name = repository.model.__name__

    async def get_by_id(self, db: AsyncSession, id: str) -> Optional[ModelType]:
        """
        Get a record by id

        Args:
            db: Database session
            id: Record ID

        Returns:
            Record object or None if not found
        """
        logger.debug(f"Getting {self.model_name} with id: {id}")
        return await self.repository.get_by_id_with_relations(db, id=id)

    async def get_all(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filter_by: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
    ) -> List[ModelType]:
        """
        Get all records with optional filtering, sorting, and pagination

        Args:
            db: Database session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            filter_by: Dictionary of filter conditions {column_name: value}
            order_by: List of columns to sort by, prefix with - for descending
              Returns:
            List of record objects
        """
        logger.debug(f"Getting list of {self.model_name}")
        return await self.repository.get_all_with_relations(
            db, skip=skip, limit=limit, filter_by=filter_by, order_by=order_by
        )

    async def count(self, db: AsyncSession, filter_by: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering

        Args:
            db: Database session
            filter_by: Dictionary of filter conditions {column_name: value}

        Returns:
            Count of records
        """
        return await self.repository.count(db, filter_by=filter_by)

    async def create(self, db: AsyncSession, *, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """
        Create a new record with nested relationships support.

        This method automatically handles both simple model data and nested
        relationship data. The Model Relationship Manager will process the data
        appropriately.

        Args:
            db: Database session
            obj_in: Input data, can be a dict or model instance
            (with or without nested relationships)

        Returns:
            Created record object
        """
        logger.info(f"Creating new {self.model_name}")

        # Convert to dict if needed
        if not isinstance(obj_in, dict):
            obj_in = obj_in.dict() if hasattr(obj_in, "dict") else obj_in

        # Always use create_with_relations to handle both simple and nested
        # data
        return await self.repository.create_with_relations(db, obj_in=obj_in)  # type: ignore[no-any-return]

    async def update(
        self,
        db: AsyncSession,
        *,
        id: str,
        obj_in: Union[Dict[str, Any], ModelType],
    ) -> Optional[ModelType]:
        """
        Update a record with nested relationships support.

        This method automatically handles both simple model data and nested
        relationship data. The Model Relationship Manager will process the data
        appropriately.

        Args:
            db: Database session
            id: Record ID
            obj_in: New data, can be a dict or model instance (with or without
            nested relationships)

        Returns:
            Updated record object or None if not found
        """

        db_obj = await self.repository.get_by_id(db, id=id)
        if db_obj:
            logger.info(f"Updating {self.model_name} with id: {id}")

            # Convert to dict if needed
            if not isinstance(obj_in, dict):
                obj_in = obj_in.dict() if hasattr(obj_in, "dict") else obj_in

            # Always use update_with_optimistic_lock_and_relations to handle both
            # simple and nested data
            return await self.repository.update_with_optimistic_lock_and_relations(
                db, id=id, obj_in=obj_in, sync_mode="merge"
            )
        logger.warning(f"{self.model_name} with id {id} not found for update")
        return None

    async def delete(self, db: AsyncSession, *, id: str, hard_delete: bool = False) -> Optional[ModelType]:
        """
        Delete a record with cascade support.

        This method automatically handles cascade deletion based on model
        relationships. By default, it performs soft delete with cascade. Set
        hard_delete=True for hard delete.

        Args:
            db: Database session
            id: Record ID
            hard_delete: Whether to perform hard delete (default: False for soft
            delete)

        Returns:
            Deleted record object or None if not found
        """

        logger.info(f"Deleting {self.model_name} with id: {id} (hard_delete: {hard_delete})")

        # Always use delete_with_cascade to handle both simple and cascade
        # deletion
        return await self.repository.delete_with_cascade(db, id=id, hard_delete=hard_delete)

    async def manage_relations(
        self,
        db: AsyncSession,
        *,
        parent_id: str,
        relation_name: str,
        obj_in: Union[List[Dict], List[str]],
        operation: str = "add",
    ) -> Optional[ModelType]:
        """
        Add or remove relationships.

        Args:
            db: Database session
            parent_id: Parent record ID
            relation_name: Name of the relationship
            obj_in: List of objects to add or list of ids to remove
            operation: "add" or "remove"

        Returns:
            Parent record or None if not found
        """
        logger.info(f"Managing {operation} operation for {relation_name} on {self.model_name} {parent_id}")

        # Delegate to repository layer for database operations
        result = await self.repository.manage_relations(
            db=db,
            parent_id=parent_id,
            relation_name=relation_name,
            obj_in=obj_in,
            operation=operation,
        )

        if result:
            logger.info(f"Successfully completed {operation} operation for {relation_name}")
        else:
            logger.warning(f"Failed to complete {operation} operation for {relation_name}")

        return result
