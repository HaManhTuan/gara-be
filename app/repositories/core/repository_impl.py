"""
Unified repository implementation with all capabilities.

This module provides a single, comprehensive repository implementation that includes:
- Basic CRUD operations
- Optimistic locking
- Soft delete operations
- Relationship management
- Cascade operations
- Model Relationship Manager integration
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base_model import BaseModel
from app.repositories.core.interfaces import OptimisticLockValidator, QueryBuilder, Repository
from app.utils.i18n import __
from app.utils.model_utils import (
    get_model_dependents,
    get_model_manager,
    get_related_model,
    get_relationship_type,
    validate_nested_data,
)
from app.utils.relationship_types import RelationshipType
from app.utils.tracing import get_trace_logger

# Generic type for database models
ModelType = TypeVar("ModelType", bound=BaseModel)

# Create logger instance for this module
logger = get_trace_logger("repository")


class RepositoryImpl(Repository[ModelType], Generic[ModelType]):
    """
    Unified repository implementation with all capabilities.

    This class provides comprehensive repository functionality including:
    - Basic CRUD operations
    - Optimistic locking
    - Soft delete operations
    - Relationship management with Model Relationship Manager
    - Cascade operations
    """

    def __init__(
        self,
        model: Type[ModelType],
        query_builder: QueryBuilder,
        optimistic_lock_validator: OptimisticLockValidator,
    ):
        """
        Initialize the repository with dependencies.

        Args:
            model: The SQLAlchemy model class
            query_builder: Query builder implementation (injected dependency)
            optimistic_lock_validator: Optimistic lock validator (injected dependency)
        """
        self.model = model
        self.query_builder = query_builder
        self.optimistic_lock_validator = optimistic_lock_validator
        self.model_name = model.__name__
        self.model_relationship_manager = get_model_manager()

    # ===== BASIC CRUD OPERATIONS =====

    async def get_by_id(self, db: AsyncSession, id: str, include_deleted: bool = False) -> Optional[ModelType]:
        """Get a record by id."""
        query = select(self.model).filter(self.model.id == id)

        # Filter out soft-deleted records unless explicitly requested
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_by_id_with_relations(
        self, db: AsyncSession, id: str, *, include_deleted: bool = False, relations: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """
        Get a record by id with relationships loaded.

        Args:
            db: Database session
            id: Record ID
            include_deleted: Whether to include soft-deleted records
            relations: List of relationship names to load (None = load all)

        Returns:
            Model instance with relationships loaded or None if not found
        """
        logger.debug(f"Getting {self.model_name} with id: {id} and relations: {relations}")

        query = select(self.model).filter(self.model.id == id)

        # Filter out soft-deleted records unless explicitly requested
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        # Load relationships if specified
        relationship_options = []
        if relations:
            # Load specific relationships
            for rel_name in relations:
                try:
                    if rel_name in self.model_relationship_manager.get_relationships(self.model_name):
                        relationship_options.append(selectinload(getattr(self.model, rel_name)))
                        logger.debug(f"Loading relationship: {rel_name}")
                    else:
                        logger.warning(f"Unknown relationship: {self.model_name}.{rel_name}")
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error loading relationship {self.model_name}.{rel_name}: {e}")
        else:
            # Load all relationships
            all_relations = self.model_relationship_manager.get_relationships(self.model_name)
            for rel_name in all_relations.keys():
                try:
                    relationship_options.append(selectinload(getattr(self.model, rel_name)))
                    logger.debug(f"Loading relationship: {rel_name}")
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error loading relationship {self.model_name}.{rel_name}: {e}")

        # Apply all relationship options at once
        if relationship_options:
            query = query.options(*relationship_options)

        result = await db.execute(query)
        record = result.scalar_one_or_none()  # type: ignore[no-any-return]

        if record:
            # Debug: Check what relationships were actually loaded
            for rel_name in self.model_relationship_manager.get_relationships(self.model_name).keys():
                try:
                    rel_value = getattr(record, rel_name, None)
                    if rel_value is not None:
                        logger.info(
                            f"Relationship {rel_name} loaded: {len(rel_value) if hasattr(rel_value, '__len__') else 'single'}"
                        )
                    else:
                        logger.warning(f"Relationship {rel_name} is None")
                except Exception as e:
                    logger.error(f"Error checking relationship {rel_name}: {e}")

            logger.info(f"Found {self.model_name} with id: {id} and relationships loaded")
        else:
            logger.warning(f"No {self.model_name} found with id: {id}")

        return record

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
        query = self.query_builder.build_base_query(filter_by, include_deleted)
        query = self.query_builder.apply_sorting(query, order_by)
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()  # type: ignore[no-any-return]

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
        logger.debug(f"Getting all {self.model_name} records with relations: {relations}")

        query = self.query_builder.build_base_query(filter_by, include_deleted)
        query = self.query_builder.apply_sorting(query, order_by)
        query = query.offset(skip).limit(limit)

        # Load relationships if specified
        relationship_options = []
        if relations:
            # Load specific relationships
            for rel_name in relations:
                try:
                    if rel_name in self.model_relationship_manager.get_relationships(self.model_name):
                        relationship_options.append(selectinload(getattr(self.model, rel_name)))
                        logger.debug(f"Loading relationship: {rel_name}")
                    else:
                        logger.warning(f"Unknown relationship: {self.model_name}.{rel_name}")
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error loading relationship {self.model_name}.{rel_name}: {e}")
        else:
            # Load all relationships
            all_relations = self.model_relationship_manager.get_relationships(self.model_name)
            for rel_name in all_relations.keys():
                try:
                    relationship_options.append(selectinload(getattr(self.model, rel_name)))
                    logger.debug(f"Loading relationship: {rel_name}")
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error loading relationship {self.model_name}.{rel_name}: {e}")

        # Apply all relationship options at once
        if relationship_options:
            query = query.options(*relationship_options)

        result = await db.execute(query)
        records = result.scalars().all()  # type: ignore[no-any-return]

        logger.debug(f"Found {len(records)} {self.model_name} records with loaded relationships")
        return records

    async def count(
        self, db: AsyncSession, filter_by: Optional[Dict[str, Any]] = None, include_deleted: bool = False
    ) -> int:
        """Count records with optional filtering."""
        from sqlalchemy import func

        query = self.query_builder.build_base_query(filter_by, include_deleted)
        count_query = select(func.count()).select_from(query.subquery())

        result = await db.execute(count_query)
        return result.scalar_one()  # type: ignore[no-any-return]

    async def create(self, db: AsyncSession, *, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """
        Create a new record.

        Note: This method only handles the main model data. For nested relationships,
        use create_with_relations() method instead.
        """
        obj_data = obj_in
        if not isinstance(obj_in, dict):
            obj_data = jsonable_encoder(obj_in)

        # Validate and separate nested data (but don't process it)
        main_data, nested_data = validate_nested_data(self.model_name, obj_data)

        if nested_data:
            logger.warning(
                f"Nested relationship data detected in create() for {self.model_name}. "
                f"Consider using create_with_relations() instead. "
                f"Nested fields: {list(nested_data.keys())}"
            )

        db_obj = self.model(**main_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.debug(f"Created {getattr(self.model, '__name__', 'Model')} with id: {db_obj.id}")
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], ModelType],
    ) -> ModelType:
        """
        Update a record.

        Note: This method only handles the main model data. For nested relationships,
        use update_with_optimistic_lock_and_relations() method instead.
        """
        obj_data = jsonable_encoder(db_obj)
        update_data = obj_in

        if not isinstance(obj_in, dict):
            update_data = jsonable_encoder(obj_in)

        # Validate and separate nested data (but don't process it)
        main_data, nested_data = validate_nested_data(self.model_name, update_data)

        if nested_data:
            logger.warning(
                f"Nested relationship data detected in update() for {self.model_name}. "
                f"Consider using update_with_optimistic_lock_and_relations() instead. "
                f"Nested fields: {list(nested_data.keys())}"
            )

        for field in obj_data:
            if field in main_data:
                setattr(db_obj, field, main_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        logger.debug(f"Updated {self.model.__name__} with id: {db_obj.id}")
        return db_obj

    async def delete(self, db: AsyncSession, *, id: str) -> ModelType:
        """Delete a record."""
        result = await db.execute(select(self.model).filter(self.model.id == id))
        obj = result.scalar_one_or_none()
        if obj is not None:
            await db.delete(obj)
            await db.commit()
            logger.debug(f"Deleted {self.model.__name__} with id: {id}")
        return obj  # type: ignore[no-any-return]

    # ===== OPTIMISTIC LOCKING OPERATIONS =====

    async def update_with_optimistic_lock(
        self,
        db: AsyncSession,
        *,
        id: str,
        obj_in: Union[Dict[str, Any], ModelType],
        expected_updated_at: Optional[str] = None,
    ) -> ModelType:
        """Update a record with optimistic locking."""
        update_data = obj_in
        if not isinstance(obj_in, dict):
            update_data = jsonable_encoder(obj_in)

        # Remove updated_at from update data as it will be set automatically
        update_data.pop("updated_at", None)

        # Build the update query with optimistic locking
        query = update(self.model).where(self.model.id == id)

        # Add optimistic lock condition if expected_updated_at is provided
        if expected_updated_at:
            expected_timestamp = self.optimistic_lock_validator.parse_timestamp(expected_updated_at)
            query = query.where(self.model.updated_at == expected_timestamp)

        # Add the update data and explicitly set updated_at
        update_data["updated_at"] = datetime.utcnow()
        query = query.values(**update_data)

        # Execute the update
        result = await db.execute(query)

        if result.rowcount == 0:
            # No rows were updated, which means either:
            # 1. Record doesn't exist, or
            # 2. Optimistic lock failed (record was modified)
            current_record = await self.get_by_id(db, id)
            if current_record is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=__("optimistic_lock.not_found"))
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=__("optimistic_lock.conflict"),
                )

        await db.commit()

        # Fetch and return the updated record
        updated_record = await self.get_by_id(db, id)
        logger.debug(f"Updated {self.model.__name__} with id: {id} using optimistic lock")
        return updated_record

    # ===== SOFT DELETE OPERATIONS =====

    async def soft_delete(self, db: AsyncSession, *, id: str) -> ModelType:
        """Soft delete a record (set deleted_at timestamp)."""
        result = await db.execute(select(self.model).filter(self.model.id == id))
        obj = result.scalar_one_or_none()
        if obj is not None:
            obj.deleted_at = datetime.utcnow()
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            logger.debug(f"Soft deleted {self.model.__name__} with id: {id}")
        return obj  # type: ignore[no-any-return]

    async def restore(self, db: AsyncSession, *, id: str) -> ModelType:
        """Restore a soft-deleted record (set deleted_at to None)."""
        result = await db.execute(select(self.model).filter(self.model.id == id))
        obj = result.scalar_one_or_none()
        if obj is not None:
            obj.deleted_at = None
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            logger.debug(f"Restored {self.model.__name__} with id: {id}")
        return obj  # type: ignore[no-any-return]

    # ===== RELATIONSHIP OPERATIONS =====

    async def create_with_relations(self, db: AsyncSession, *, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """
        Create record with nested relationships using Model Relationship Manager.

        Args:
            db: Database session
            obj_in: Input data with potential nested relationships

        Returns:
            Created model instance with relationships
        """
        logger.info(f"Creating {self.model_name} with nested relationships")

        # Convert to dict if needed
        obj_data = obj_in
        if not isinstance(obj_in, dict):
            obj_data = jsonable_encoder(obj_in)

        # Separate main data from nested relationship data
        logger.info(f"Full obj_data keys for {self.model_name}: {list(obj_data.keys())}")
        main_data, nested_data = validate_nested_data(self.model_name, obj_data)

        logger.info(f"Main data for {self.model_name}: {list(main_data.keys())}")
        logger.info(f"Nested data for {self.model_name}: {list(nested_data.keys()) if nested_data else 'None'}")
        if nested_data:
            for key, value in nested_data.items():
                logger.info(f"Nested key '{key}' has {len(value) if isinstance(value, list) else 1} item(s)")

        # Create the main object
        instance = self.model(**main_data)
        db.add(instance)
        await db.flush()  # Get the ID

        # Capture the ID immediately after flush when it's safe
        instance_id = str(instance.id)

        # Handle nested relationships
        if nested_data:
            logger.info(f"Processing nested data: {nested_data}")
            await self._handle_nested_relationships(db, instance, nested_data)
        else:
            logger.warning(f"No nested data to process for {self.model_name}")

        await db.commit()

        # Reload instance with all relationships eagerly loaded
        instance_with_relations = await self.get_by_id_with_relations(db, instance_id)
        if not instance_with_relations:
            logger.warning(f"Failed to reload {self.model_name} with id: {instance_id} after creation")
            return instance

        # Debug: Check if relationships are loaded
        logger.info(f"Created {self.model_name} with id: {instance_id}")
        if hasattr(instance_with_relations, "employees"):
            emp_count = len(instance_with_relations.employees) if instance_with_relations.employees else 0
            logger.info(f"Loaded employees: {emp_count}")
        if hasattr(instance_with_relations, "managers"):
            mgr_count = len(instance_with_relations.managers) if instance_with_relations.managers else 0
            logger.info(f"Loaded managers: {mgr_count}")

        return instance_with_relations

    async def update_with_optimistic_lock_and_relations(
        self, db: AsyncSession, *, id: str, obj_in: Union[Dict[str, Any], ModelType], sync_mode: str = "merge"
    ) -> Optional[ModelType]:
        """
        Update record with nested relationships and optimistic locking.

        Args:
            db: Database session
            id: Record ID to update
            obj_in: Input data with potential nested relationships
            sync_mode: Sync mode for relationships ("merge", "replace", "add")

        Returns:
            Updated model instance or None if not found
        """
        logger.info(f"Updating {self.model_name} with id: {id} and nested relationships")

        # Convert to dict if needed
        obj_data = obj_in
        if not isinstance(obj_in, dict):
            obj_data = jsonable_encoder(obj_in)

        # Get existing record
        existing_record = await self.get_by_id(db, id)
        if not existing_record:
            return None

        # Separate main data from nested relationship data
        main_data, nested_data = validate_nested_data(self.model_name, obj_data)

        # Handle optimistic locking if updated_at is provided
        if "updated_at" in obj_data and obj_data["updated_at"] is not None:
            expected_updated_at = obj_data["updated_at"]
            # Parse the expected timestamp
            try:
                expected_timestamp = self.optimistic_lock_validator.parse_timestamp(expected_updated_at)
                # Check if the current updated_at matches the expected one
                if existing_record.updated_at != expected_timestamp:
                    logger.warning(f"Optimistic lock conflict for {self.model_name} with id: {id}")
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=__("optimistic_lock.conflict"))
            except ValueError as e:
                logger.warning(f"Invalid timestamp format for optimistic lock: {e}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=__("optimistic_lock.invalid_timestamp")
                )

        # Update main object fields (only non-None values)
        for field, value in main_data.items():
            if hasattr(existing_record, field) and value is not None:
                setattr(existing_record, field, value)

        # Handle nested relationships based on sync mode
        # For updates, use "replace" mode to ensure new relationships replace old ones
        if nested_data:
            await self._handle_nested_relationships_update(db, existing_record, nested_data, "replace")

        # Update timestamp for optimistic locking
        existing_record.updated_at = datetime.utcnow()

        db.add(existing_record)
        await db.commit()

        # Reload instance with all relationships eagerly loaded
        updated_with_relations = await self.get_by_id_with_relations(db, id)
        if not updated_with_relations:
            logger.warning(f"Failed to reload {self.model_name} with id: {id} after update")
            return existing_record

        # Debug: Check if relationships are loaded
        logger.info(f"Updated {self.model_name} with id: {id}")
        if hasattr(updated_with_relations, "employees"):
            emp_count = len(updated_with_relations.employees) if updated_with_relations.employees else 0
            logger.info(f"Loaded employees: {emp_count}")
        if hasattr(updated_with_relations, "managers"):
            mgr_count = len(updated_with_relations.managers) if updated_with_relations.managers else 0
            logger.info(f"Loaded managers: {mgr_count}")

        return updated_with_relations

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
        Add or remove relationships dynamically.

        Args:
            db: Database session
            parent_id: ID of the parent record
            relation_name: Name of the relationship
            obj_in: List of objects or IDs to add/remove
            operation: Operation type ("add", "remove", "replace")

        Returns:
            Updated parent model instance or None if not found
        """
        logger.info(f"Managing {relation_name} relationship for {self.model_name} with id: {parent_id}")

        # Get parent record
        parent_record = await self.get_by_id(db, parent_id)
        if not parent_record:
            return None

        # Validate relationship exists
        if relation_name not in self.model_relationship_manager.get_relationships(self.model_name):
            raise ValueError(f"Relationship {relation_name} not found in {self.model_name}")

        rel_type = get_relationship_type(self.model_name, relation_name)
        related_model = get_related_model(self.model_name, relation_name)

        if not rel_type or not related_model:
            raise ValueError(f"Invalid relationship {relation_name}")

        # Handle different relationship types
        if rel_type in [RelationshipType.ONE_TO_MANY, RelationshipType.MANY_TO_MANY]:
            await self._manage_collection_relationship(
                db, parent_record, relation_name, obj_in, related_model, operation
            )
        elif rel_type == RelationshipType.MANY_TO_ONE:
            await self._manage_single_relationship(db, parent_record, relation_name, obj_in, related_model, operation)
        elif rel_type == RelationshipType.ONE_TO_ONE:
            await self._manage_single_relationship(db, parent_record, relation_name, obj_in, related_model, operation)

        await db.commit()
        await db.refresh(parent_record)
        logger.debug(f"Managed {relation_name} relationship for {self.model_name} with id: {parent_id}")
        return parent_record

    # ===== CASCADE OPERATIONS =====

    async def delete_with_cascade(self, db: AsyncSession, *, id: str, hard_delete: bool = False) -> Optional[ModelType]:
        """
        Delete record with cascade options.

        Args:
            db: Database session
            id: Record ID to delete
            hard_delete: Whether to perform hard delete (True) or soft delete (False)

        Returns:
            Deleted model instance or None if not found
        """
        logger.info(f"Deleting {self.model_name} with id: {id}, hard_delete: {hard_delete}")

        # Get the record to delete
        record = await self.get_by_id(db, id)
        if not record:
            return None

        if hard_delete:
            # Hard delete with cascade
            await self._hard_delete_with_cascade(db, record)
        else:
            # Soft delete with cascade
            await self._soft_delete_with_cascade(db, record)

        await db.commit()
        logger.debug(f"Deleted {self.model_name} with id: {id}")
        return record

    # ===== PRIVATE HELPER METHODS =====

    async def _handle_nested_relationships(
        self, db: AsyncSession, instance: ModelType, nested_data: Dict[str, Any]
    ) -> None:
        """Handle nested relationships for a model instance."""
        logger.info(f"Starting to handle {len(nested_data)} nested relationships for {self.model_name}")

        for rel_name, rel_data in nested_data.items():
            rel_type = get_relationship_type(self.model_name, rel_name)
            related_model = get_related_model(self.model_name, rel_name)

            if not rel_type or not related_model:
                logger.warning(f"Unknown relationship: {self.model_name}.{rel_name}")
                continue

            logger.info(
                f"Handling {rel_type.value} relationship: {rel_name} with {len(rel_data) if isinstance(rel_data, list) else 1} items"
            )

            if rel_type == RelationshipType.ONE_TO_MANY:
                await self._handle_one_to_many(db, instance, rel_name, rel_data, related_model)
            elif rel_type == RelationshipType.MANY_TO_ONE:
                await self._handle_many_to_one(db, instance, rel_name, rel_data, related_model)
            elif rel_type == RelationshipType.ONE_TO_ONE:
                await self._handle_one_to_one(db, instance, rel_name, rel_data, related_model)
            elif rel_type == RelationshipType.MANY_TO_MANY:
                await self._handle_many_to_many(db, instance, rel_name, rel_data, related_model)

    async def _handle_nested_relationships_update(
        self, db: AsyncSession, instance: ModelType, nested_data: Dict[str, Any], sync_mode: str
    ) -> None:
        """Handle nested relationships update for a model instance."""
        for rel_name, rel_data in nested_data.items():
            rel_type = get_relationship_type(self.model_name, rel_name)
            related_model = get_related_model(self.model_name, rel_name)

            if not rel_type or not related_model:
                logger.warning(f"Unknown relationship: {self.model_name}.{rel_name}")
                continue

            logger.debug(f"Updating {rel_type.value} relationship: {rel_name} with mode: {sync_mode}")

            if rel_type == RelationshipType.ONE_TO_MANY:
                await self._update_one_to_many(db, instance, rel_name, rel_data, related_model, sync_mode)
            elif rel_type == RelationshipType.MANY_TO_ONE:
                await self._update_many_to_one(db, instance, rel_name, rel_data, related_model, sync_mode)
            elif rel_type == RelationshipType.ONE_TO_ONE:
                await self._update_one_to_one(db, instance, rel_name, rel_data, related_model, sync_mode)
            elif rel_type == RelationshipType.MANY_TO_MANY:
                await self._update_many_to_many(db, instance, rel_name, rel_data, related_model, sync_mode)

    async def _handle_one_to_many(
        self,
        db: AsyncSession,
        parent: ModelType,
        rel_name: str,
        children_data: List[Dict[str, Any]],
        child_model: Type[BaseModel],
    ) -> None:
        """Handle one-to-many relationship creation."""
        logger.info(
            f"Creating {len(children_data)} {getattr(child_model, '__name__', 'Model')} instances for {self.model_name}.{rel_name}"
        )

        for idx, child_data in enumerate(children_data):
            # Separate main data from nested data for the child
            child_main_data, child_nested_data = validate_nested_data(
                getattr(child_model, "__name__", "Model"), child_data
            )

            # Filter out fields that don't exist in the model
            # Only include fields that are actual columns in the model
            model_columns = [column.name for column in child_model.__table__.columns]
            filtered_child_data = {key: value for key, value in child_main_data.items() if key in model_columns}

            # Set foreign key to parent
            parent_id_field = f"{self.model_name.lower()}_id"
            filtered_child_data[parent_id_field] = parent.id

            # Create child instance
            child_instance = child_model(**filtered_child_data)
            db.add(child_instance)
            await db.flush()

            logger.info(
                f"Created {getattr(child_model, '__name__', 'Model')} #{idx+1} with ID: {child_instance.id} linked to {self.model_name} ID: {parent.id}"
            )

            # Handle nested relationships in child
            if child_nested_data:
                await self._handle_child_nested_relationships(db, child_instance, child_nested_data, child_model)

    async def _handle_many_to_one(
        self,
        db: AsyncSession,
        child: ModelType,
        rel_name: str,
        parent_data: Dict[str, Any],
        parent_model: Type[BaseModel],
    ) -> None:
        """Handle many-to-one relationship creation."""
        logger.debug(f"Creating {parent_model.__name__} instance for {self.model_name}")

        # Separate main data from nested data
        parent_main_data, parent_nested_data = validate_nested_data(parent_model.__name__, parent_data)

        # Filter out fields that don't exist in the model
        model_columns = [column.name for column in parent_model.__table__.columns]
        filtered_parent_data = {key: value for key, value in parent_main_data.items() if key in model_columns}

        # Create parent instance
        parent_instance = parent_model(**filtered_parent_data)
        db.add(parent_instance)
        await db.flush()

        # Set foreign key on child
        parent_id_field = f"{parent_model.__name__.lower()}_id"
        setattr(child, parent_id_field, parent_instance.id)

        # Handle nested relationships in parent
        if parent_nested_data:
            await self._handle_child_nested_relationships(db, parent_instance, parent_nested_data, parent_model)

    async def _handle_one_to_one(
        self,
        db: AsyncSession,
        instance: ModelType,
        rel_name: str,
        related_data: Dict[str, Any],
        related_model: Type[BaseModel],
    ) -> None:
        """Handle one-to-one relationship creation."""
        logger.debug(f"Creating {related_model.__name__} instance for {self.model_name}")

        # Separate main data from nested data
        related_main_data, related_nested_data = validate_nested_data(related_model.__name__, related_data)

        # Filter out fields that don't exist in the model
        model_columns = [column.name for column in related_model.__table__.columns]
        filtered_related_data = {key: value for key, value in related_main_data.items() if key in model_columns}

        # Set foreign key
        instance_id_field = f"{self.model_name.lower()}_id"
        filtered_related_data[instance_id_field] = instance.id

        # Create related instance
        related_instance = related_model(**filtered_related_data)
        db.add(related_instance)
        await db.flush()

        # Handle nested relationships
        if related_nested_data:
            await self._handle_child_nested_relationships(db, related_instance, related_nested_data, related_model)

    async def _handle_many_to_many(
        self,
        db: AsyncSession,
        instance: ModelType,
        rel_name: str,
        related_data: List[Dict[str, Any]],
        related_model: Type[BaseModel],
    ) -> None:
        """Handle many-to-many relationship creation."""
        logger.debug(f"Creating {len(related_data)} {related_model.__name__} instances for many-to-many")

        related_instances = []

        for item_data in related_data:
            # Separate main data from nested data
            item_main_data, item_nested_data = validate_nested_data(related_model.__name__, item_data)

            # Filter out fields that don't exist in the model
            model_columns = [column.name for column in related_model.__table__.columns]
            filtered_item_data = {key: value for key, value in item_main_data.items() if key in model_columns}

            # Create related instance
            related_instance = related_model(**filtered_item_data)
            db.add(related_instance)
            await db.flush()

            # Handle nested relationships
            if item_nested_data:
                await self._handle_child_nested_relationships(db, related_instance, item_nested_data, related_model)

            related_instances.append(related_instance)

        # Link many-to-many relationship
        # Get the junction table for this relationship
        junction_table = self._get_junction_table(rel_name)
        if junction_table is not None:
            # Insert records into junction table
            for related_instance in related_instances:
                junction_data = {
                    f"{self.model_name.lower()}_id": instance.id,
                    f"{related_model.__name__.lower()}_id": related_instance.id,
                }
                await db.execute(junction_table.insert().values(**junction_data))
            logger.debug(f"Linked {self.model_name} to {len(related_instances)} {related_model.__name__} instances")
        else:
            logger.warning(f"No junction table found for {self.model_name}.{rel_name}")

    async def _handle_child_nested_relationships(
        self, db: AsyncSession, child_instance: BaseModel, nested_data: Dict[str, Any], child_model: Type[BaseModel]
    ) -> None:
        """Recursively handle nested relationships in child objects."""
        # Create a temporary repository for the child model to handle its relationships
        from app.repositories.factory import repository_factory

        child_repo = repository_factory.create_repository(child_model)
        await child_repo._handle_nested_relationships(db, child_instance, nested_data)

    # Update methods for relationships
    async def _update_one_to_many(
        self,
        db: AsyncSession,
        parent: ModelType,
        rel_name: str,
        children_data: List[Dict[str, Any]],
        child_model: Type[BaseModel],
        sync_mode: str,
    ) -> None:
        """Update one-to-many relationship."""
        if sync_mode == "replace":
            # Delete existing children and create new ones
            await self._delete_existing_children(db, parent, rel_name)
            await self._handle_one_to_many(db, parent, rel_name, children_data, child_model)
        elif sync_mode == "add":
            # Add new children to existing ones
            await self._handle_one_to_many(db, parent, rel_name, children_data, child_model)
        elif sync_mode == "merge":
            # Merge based on IDs if present
            await self._merge_one_to_many(db, parent, rel_name, children_data, child_model)

    async def _update_many_to_one(
        self,
        db: AsyncSession,
        child: ModelType,
        rel_name: str,
        parent_data: Dict[str, Any],
        parent_model: Type[BaseModel],
        sync_mode: str,
    ) -> None:
        """Update many-to-one relationship."""
        await self._handle_many_to_one(db, child, rel_name, parent_data, parent_model)

    async def _update_one_to_one(
        self,
        db: AsyncSession,
        instance: ModelType,
        rel_name: str,
        related_data: Dict[str, Any],
        related_model: Type[BaseModel],
        sync_mode: str,
    ) -> None:
        """Update one-to-one relationship."""
        await self._handle_one_to_one(db, instance, rel_name, related_data, related_model)

    async def _update_many_to_many(
        self,
        db: AsyncSession,
        instance: ModelType,
        rel_name: str,
        related_data: List[Dict[str, Any]],
        related_model: Type[BaseModel],
        sync_mode: str,
    ) -> None:
        """Update many-to-many relationship."""
        if sync_mode == "replace":
            # Clear existing relationships and add new ones
            await self._clear_many_to_many_relationships(db, instance, rel_name)
            await self._handle_many_to_many(db, instance, rel_name, related_data, related_model)
        elif sync_mode == "add":
            # Add new relationships
            await self._handle_many_to_many(db, instance, rel_name, related_data, related_model)
        elif sync_mode == "merge":
            # Merge based on IDs if present
            await self._merge_many_to_many(db, instance, rel_name, related_data, related_model)

    # Relationship management methods
    async def _manage_collection_relationship(
        self,
        db: AsyncSession,
        parent_record: ModelType,
        relation_name: str,
        obj_in: Union[List[Dict], List[str]],
        related_model: Type[BaseModel],
        operation: str,
    ) -> None:
        """Manage collection relationships (one-to-many, many-to-many)."""
        if operation == "add":
            # Add new relationships
            for item in obj_in:
                if isinstance(item, dict):
                    # Create new related object
                    related_instance = related_model(**item)
                    db.add(related_instance)
                    await db.flush()
                    # Link relationship
                    await self._link_relationship(db, parent_record, relation_name, related_instance)
                elif isinstance(item, str):
                    # Link to existing object
                    existing_related = await self._get_related_by_id(db, related_model, item)
                    if existing_related:
                        await self._link_relationship(db, parent_record, relation_name, existing_related)
        elif operation == "remove":
            # Remove relationships
            for item in obj_in:
                if isinstance(item, str):
                    await self._unlink_relationship(db, parent_record, relation_name, item)
        elif operation == "replace":
            # Replace all relationships
            await self._clear_relationship(db, parent_record, relation_name)
            await self._manage_collection_relationship(db, parent_record, relation_name, obj_in, related_model, "add")

    async def _manage_single_relationship(
        self,
        db: AsyncSession,
        instance: ModelType,
        relation_name: str,
        obj_in: Union[List[Dict], List[str]],
        related_model: Type[BaseModel],
        operation: str,
    ) -> None:
        """Manage single relationships (many-to-one, one-to-one)."""
        if not obj_in:
            return

        item = obj_in[0] if isinstance(obj_in, list) else obj_in

        if isinstance(item, dict):
            # Create new related object
            related_instance = related_model(**item)
            db.add(related_instance)
            await db.flush()
            await self._link_relationship(db, instance, relation_name, related_instance)
        elif isinstance(item, str):
            # Link to existing object
            existing_related = await self._get_related_by_id(db, related_model, item)
            if existing_related:
                await self._link_relationship(db, instance, relation_name, existing_related)

    # Cascade delete methods
    async def _hard_delete_with_cascade(self, db: AsyncSession, record: ModelType) -> None:
        """Perform hard delete with cascade."""
        # Get dependent models
        dependents = get_model_dependents(self.model_name)

        # Delete dependent records first
        for dependent_model_name in dependents:
            dependent_model = self.model_relationship_manager.get_model_class(dependent_model_name)
            if dependent_model:
                # Find records that depend on this record
                dependent_records = await self._get_dependent_records(db, dependent_model, record.id)
                for dependent_record in dependent_records:
                    await self._hard_delete_with_cascade(db, dependent_record)

        # Delete the record itself
        await db.delete(record)

    async def _soft_delete_with_cascade(self, db: AsyncSession, record: ModelType) -> None:
        """Perform soft delete with cascade."""
        # Get dependent models
        dependents = get_model_dependents(self.model_name)

        # Soft delete dependent records first
        for dependent_model_name in dependents:
            dependent_model = self.model_relationship_manager.get_model_class(dependent_model_name)
            if dependent_model:
                # Find records that depend on this record
                dependent_records = await self._get_dependent_records(db, dependent_model, record.id)
                for dependent_record in dependent_records:
                    await self._soft_delete_with_cascade(db, dependent_record)

        # Soft delete the record itself
        record.deleted_at = datetime.utcnow()
        db.add(record)

    # Helper methods for relationship operations
    async def _delete_existing_children(self, db: AsyncSession, parent: ModelType, rel_name: str) -> None:
        """Delete existing children in a one-to-many relationship."""
        logger.debug(f"Deleting existing children for {self.model_name}.{rel_name}")

        # Get the related model for this relationship
        related_model = get_related_model(self.model_name, rel_name)
        if related_model:
            # Delete all children that reference this parent
            parent_id_field = f"{self.model_name.lower()}_id"
            await db.execute(select(related_model).filter(getattr(related_model, parent_id_field) == parent.id))
            # For now, we'll use soft delete if the model supports it
            if hasattr(related_model, "deleted_at"):
                await db.execute(
                    related_model.__table__.update()
                    .where(getattr(related_model, parent_id_field) == parent.id)
                    .values(deleted_at=datetime.utcnow())
                )
            else:
                # Hard delete if no soft delete support
                await db.execute(
                    related_model.__table__.delete().where(getattr(related_model, parent_id_field) == parent.id)
                )
            logger.debug(f"Deleted existing children for {self.model_name}.{rel_name}")
        else:
            logger.warning(f"Could not find related model for {self.model_name}.{rel_name}")

    async def _merge_one_to_many(
        self,
        db: AsyncSession,
        parent: ModelType,
        rel_name: str,
        children_data: List[Dict[str, Any]],
        child_model: Type[BaseModel],
    ) -> None:
        """Merge one-to-many relationship data."""
        # This would need to be implemented based on the specific relationship
        logger.debug(f"Merging one-to-many relationship for {self.model_name}.{rel_name}")
        pass

    async def _clear_many_to_many_relationships(self, db: AsyncSession, instance: ModelType, rel_name: str) -> None:
        """Clear many-to-many relationships."""
        logger.debug(f"Clearing many-to-many relationships for {self.model_name}.{rel_name}")

        # Get the junction table for this relationship
        junction_table = self._get_junction_table(rel_name)
        if junction_table is not None:
            # Delete all records from junction table for this instance
            parent_id_field = f"{self.model_name.lower()}_id"
            await db.execute(junction_table.delete().where(getattr(junction_table.c, parent_id_field) == instance.id))
            logger.debug(f"Cleared {self.model_name}.{rel_name} relationships")
        else:
            logger.warning(f"No junction table found for {self.model_name}.{rel_name}")

    async def _merge_many_to_many(
        self,
        db: AsyncSession,
        instance: ModelType,
        rel_name: str,
        related_data: List[Dict[str, Any]],
        related_model: Type[BaseModel],
    ) -> None:
        """Merge many-to-many relationship data."""
        # This would need to be implemented based on the specific relationship
        logger.debug(f"Merging many-to-many relationship for {self.model_name}.{rel_name}")
        pass

    async def _link_relationship(self, db: AsyncSession, parent: ModelType, rel_name: str, related: BaseModel) -> None:
        """Link a relationship between parent and related objects."""
        # This would need to be implemented based on the specific relationship type
        logger.debug(f"Linking {self.model_name}.{rel_name} to {related.__class__.__name__}")
        pass

    async def _unlink_relationship(self, db: AsyncSession, parent: ModelType, rel_name: str, related_id: str) -> None:
        """Unlink a relationship between parent and related objects."""
        # This would need to be implemented based on the specific relationship type
        logger.debug(f"Unlinking {self.model_name}.{rel_name} from {related_id}")
        pass

    async def _clear_relationship(self, db: AsyncSession, parent: ModelType, rel_name: str) -> None:
        """Clear all relationships for a given relationship name."""
        # This would need to be implemented based on the specific relationship type
        logger.debug(f"Clearing {self.model_name}.{rel_name}")
        pass

    async def _get_related_by_id(
        self, db: AsyncSession, related_model: Type[BaseModel], related_id: str
    ) -> Optional[BaseModel]:
        """Get a related object by ID."""
        result = await db.execute(select(related_model).filter(related_model.id == related_id))
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def _get_dependent_records(
        self, db: AsyncSession, dependent_model: Type[BaseModel], parent_id: str
    ) -> List[BaseModel]:
        """Get records that depend on the parent record."""
        # This would need to be implemented based on the specific foreign key relationships
        logger.debug(f"Getting dependent records for {dependent_model.__name__} with parent_id: {parent_id}")
        return []

    def _get_junction_table(self, rel_name: str):
        """Get the junction table for a many-to-many relationship."""
        # Hardcode the junction table for Post.tags relationship for now
        if self.model_name == "Post" and rel_name == "tags":
            from app.models.post_tags import post_tags

            return post_tags

        # TODO: Implement generic junction table detection
        logger.warning(f"No junction table mapping for {self.model_name}.{rel_name}")
        return None
