"""
Relationship handler implementation following Single Responsibility Principle.

This module handles relationship direction mapping and method resolution,
separating this concern from the main repository logic.
"""

from typing import Any, Dict, List, Optional, Type

from app.models.base_model import BaseModel
from app.repositories.core.interfaces import RelationshipHandler
from app.utils.model_utils import get_model_manager, get_related_model, get_relationship_type
from app.utils.relationship_types import RelationshipAdapter, RelationshipType
from app.utils.tracing import get_trace_logger

logger = get_trace_logger("relationship-handler")


class DefaultRelationshipHandler(RelationshipHandler):
    """Handles relationship direction mapping and method resolution using the model relationship manager."""

    def get_relationship_handler(self, direction: Any, uselist: bool = True) -> str:
        """
        Get the appropriate handler method name for a relationship direction.

        Args:
            direction: SQLAlchemy relationship direction constant
            uselist: Whether the relationship uses a list (False for one-to-one)

        Returns:
            Handler method name
        """
        relationship_type = RelationshipAdapter.get_application_type(direction, uselist)
        return RelationshipAdapter.get_handler_method(relationship_type)

    def get_relationship_manager(self, direction: Any, uselist: bool = True) -> str:
        """
        Get the appropriate manager method name for a relationship direction.

        Args:
            direction: SQLAlchemy relationship direction constant
            uselist: Whether the relationship uses a list (False for one-to-one)

        Returns:
            Manager method name
        """
        relationship_type = RelationshipAdapter.get_application_type(direction, uselist)
        return RelationshipAdapter.get_manager_method(relationship_type)

    def get_model_relationships(self, model_name: str) -> Dict[str, Any]:
        """
        Get all relationships for a model using the model relationship manager.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary of relationship names to relationship properties
        """
        manager = get_model_manager()
        return manager.get_relationships(model_name)

    def get_relationship_info(self, model_name: str, relationship_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific relationship.

        Args:
            model_name: Name of the model
            relationship_name: Name of the relationship

        Returns:
            Dictionary with relationship information or None if not found
        """
        rel_type = get_relationship_type(model_name, relationship_name)
        related_model = get_related_model(model_name, relationship_name)

        if not rel_type or not related_model:
            return None

        return {
            "type": rel_type,
            "related_model": related_model,
            "related_model_name": related_model.__name__,
            "handler_method": RelationshipAdapter.get_handler_method(rel_type),
            "manager_method": RelationshipAdapter.get_manager_method(rel_type),
        }

    def validate_relationship_path(self, model_name: str, path: str) -> bool:
        """
        Validate a relationship path (e.g., 'posts.comments').

        Args:
            model_name: Starting model name
            path: Dot-separated relationship path

        Returns:
            True if the path is valid
        """
        path_parts = path.split(".")
        current_model = model_name

        for part in path_parts:
            relationships = get_model_manager().get_relationships(current_model)
            if part not in relationships:
                return False

            rel_prop = relationships[part]
            current_model = rel_prop.mapper.class_.__name__

        return True

    def get_relationship_chain(self, model_name: str, path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get a chain of relationship information for a path.

        Args:
            model_name: Starting model name
            path: Dot-separated relationship path

        Returns:
            List of relationship information dictionaries or None if invalid
        """
        if not self.validate_relationship_path(model_name, path):
            return None

        path_parts = path.split(".")
        chain = []
        current_model = model_name

        for part in path_parts:
            rel_info = self.get_relationship_info(current_model, part)
            if not rel_info:
                return None

            chain.append(rel_info)
            current_model = rel_info["related_model_name"]

        return chain

    def get_cascade_delete_relationships(self, model_name: str) -> List[str]:
        """
        Get all relationships that have cascade delete enabled.

        Args:
            model_name: Name of the model

        Returns:
            List of relationship names with cascade delete
        """
        manager = get_model_manager()
        cascade_relationships = []

        for edge in manager.get_outgoing_edges(model_name):
            if edge.cascade_delete:
                cascade_relationships.append(edge.relationship_name)

        return cascade_relationships

    def get_soft_delete_cascade_relationships(self, model_name: str) -> List[str]:
        """
        Get all relationships that have soft delete cascade enabled.

        Args:
            model_name: Name of the model

        Returns:
            List of relationship names with soft delete cascade
        """
        manager = get_model_manager()
        cascade_relationships = []

        for edge in manager.get_outgoing_edges(model_name):
            if edge.cascade_soft_delete:
                cascade_relationships.append(edge.relationship_name)

        return cascade_relationships

    def get_dependent_models(self, model_name: str) -> List[str]:
        """
        Get all models that depend on the given model.

        Args:
            model_name: Name of the model

        Returns:
            List of dependent model names
        """
        manager = get_model_manager()
        return list(manager.get_model_dependents(model_name))

    def get_dependency_models(self, model_name: str) -> List[str]:
        """
        Get all models that the given model depends on.

        Args:
            model_name: Name of the model

        Returns:
            List of dependency model names
        """
        manager = get_model_manager()
        return list(manager.get_model_dependencies(model_name))

    def is_relationship_field(self, model_name: str, field_name: str) -> bool:
        """
        Check if a field is a relationship field.

        Args:
            model_name: Name of the model
            field_name: Name of the field

        Returns:
            True if the field is a relationship field
        """
        relationships = self.get_model_relationships(model_name)
        return field_name in relationships

    def get_relationship_type_for_field(self, model_name: str, field_name: str) -> Optional[RelationshipType]:
        """
        Get the relationship type for a specific field.

        Args:
            model_name: Name of the model
            field_name: Name of the field

        Returns:
            RelationshipType or None if not a relationship field
        """
        if not self.is_relationship_field(model_name, field_name):
            return None

        return get_relationship_type(model_name, field_name)

    def get_related_model_for_field(self, model_name: str, field_name: str) -> Optional[Type[BaseModel]]:
        """
        Get the related model for a specific field.

        Args:
            model_name: Name of the model
            field_name: Name of the field

        Returns:
            Related model class or None if not a relationship field
        """
        if not self.is_relationship_field(model_name, field_name):
            return None

        return get_related_model(model_name, field_name)
