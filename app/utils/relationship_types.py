"""
Application-level relationship types and mapping to SQLAlchemy constants.

This module defines our own relationship types that are more comprehensive
than SQLAlchemy's built-in constants, and provides mapping to the framework.
"""

from enum import Enum
from typing import Any, Dict

from sqlalchemy.orm import MANYTOMANY, MANYTOONE, ONETOMANY


class RelationshipType(Enum):
    """Application-level relationship types."""

    # One-to-One relationships
    ONE_TO_ONE = "one_to_one"

    # One-to-Many relationships
    ONE_TO_MANY = "one_to_many"

    # Many-to-One relationships
    MANY_TO_ONE = "many_to_one"

    # Many-to-Many relationships
    MANY_TO_MANY = "many_to_many"


class RelationshipAdapter:
    """Adapter to map application relationship types to SQLAlchemy constants."""

    # Mapping from our enum to SQLAlchemy constants
    APPLICATION_TO_SQLALCHEMY: Dict[RelationshipType, Any] = {
        RelationshipType.ONE_TO_ONE: MANYTOONE,  # One-to-one is MANYTOONE with uselist=False
        RelationshipType.ONE_TO_MANY: ONETOMANY,
        RelationshipType.MANY_TO_ONE: MANYTOONE,
        RelationshipType.MANY_TO_MANY: MANYTOMANY,
    }

    # Reverse mapping for convenience
    SQLALCHEMY_TO_APPLICATION: Dict[Any, RelationshipType] = {
        ONETOMANY: RelationshipType.ONE_TO_MANY,
        MANYTOONE: RelationshipType.MANY_TO_ONE,  # Note: Could be ONE_TO_ONE if uselist=False
        MANYTOMANY: RelationshipType.MANY_TO_MANY,
    }

    @classmethod
    def get_sqlalchemy_direction(cls, relationship_type: RelationshipType) -> Any:
        """
        Get SQLAlchemy direction constant from application relationship type.

        Args:
            relationship_type: Application relationship type

        Returns:
            SQLAlchemy direction constant
        """
        return cls.APPLICATION_TO_SQLALCHEMY[relationship_type]

    @classmethod
    def get_application_type(cls, sqlalchemy_direction: Any, uselist: bool = True) -> RelationshipType:
        """
        Get application relationship type from SQLAlchemy direction and uselist flag.

        Args:
            sqlalchemy_direction: SQLAlchemy direction constant
            uselist: Whether the relationship uses a list (False for one-to-one)

        Returns:
            Application relationship type
        """
        if sqlalchemy_direction == MANYTOONE and not uselist:
            return RelationshipType.ONE_TO_ONE
        return cls.SQLALCHEMY_TO_APPLICATION[sqlalchemy_direction]

    @classmethod
    def is_one_to_one(cls, sqlalchemy_direction: Any, uselist: bool) -> bool:
        """
        Check if a relationship is one-to-one based on SQLAlchemy properties.

        Args:
            sqlalchemy_direction: SQLAlchemy direction constant
            uselist: Whether the relationship uses a list

        Returns:
            True if the relationship is one-to-one
        """
        return sqlalchemy_direction == MANYTOONE and not uselist

    @classmethod
    def get_handler_method(cls, relationship_type: RelationshipType) -> str:
        """
        Get the handler method name for a relationship type.

        Args:
            relationship_type: Application relationship type

        Returns:
            Handler method name
        """
        handlers = {
            RelationshipType.ONE_TO_ONE: "_handle_one_to_one",
            RelationshipType.ONE_TO_MANY: "_handle_one_to_many",
            RelationshipType.MANY_TO_ONE: "_handle_many_to_one",
            RelationshipType.MANY_TO_MANY: "_handle_many_to_many",
        }
        return handlers[relationship_type]

    @classmethod
    def get_manager_method(cls, relationship_type: RelationshipType) -> str:
        """
        Get the manager method name for a relationship type.

        Args:
            relationship_type: Application relationship type

        Returns:
            Manager method name
        """
        managers = {
            RelationshipType.ONE_TO_ONE: "_manage_one_to_one_relations",
            RelationshipType.ONE_TO_MANY: "_manage_one_to_many_relations",
            RelationshipType.MANY_TO_ONE: "_manage_many_to_one_relations",
            RelationshipType.MANY_TO_MANY: "_manage_many_to_many_relations",
        }
        return managers[relationship_type]
