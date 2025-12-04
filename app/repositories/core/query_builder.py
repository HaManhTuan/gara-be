"""
Query builder implementation following Single Responsibility Principle.

This module handles query building operations, separating this concern
from the main repository logic.
"""

from typing import Any, Dict, List, Optional, Type

from sqlalchemy import select

from app.models.base_model import BaseModel
from app.repositories.core.interfaces import QueryBuilder


class DefaultQueryBuilder(QueryBuilder):
    """Handles query building operations."""

    def __init__(self, model: Type[BaseModel]):
        self.model = model

    def build_base_query(
        self,
        filter_by: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False,
    ) -> Any:
        """
        Build base query with common filters.

        Args:
            filter_by: Dictionary of filter conditions {column_name: value}
            include_deleted: Whether to include soft-deleted records

        Returns:
            Base query object
        """
        query = select(self.model)

        # Apply filters if provided
        if filter_by:
            for column, value in filter_by.items():
                if hasattr(self.model, column):
                    query = query.filter(getattr(self.model, column) == value)

        # Filter out soft-deleted records unless explicitly requested
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query

    def apply_sorting(self, query: Any, order_by: Optional[List[str]]) -> Any:
        """
        Apply sorting to query.

        Args:
            query: SQLAlchemy query object
            order_by: List of columns to sort by, prefix with - for descending

        Returns:
            Query with sorting applied
        """
        if not order_by:
            return query

        for column in order_by:
            if column.startswith("-"):
                # Descending order
                query = query.order_by(getattr(self.model, column[1:]).desc())
            else:
                # Ascending order
                query = query.order_by(getattr(self.model, column).asc())

        return query
