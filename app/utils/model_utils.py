"""
Model Relationship Utilities

This module provides convenient access to the model relationship manager
and common operations for working with model relationships.
"""

from typing import Any, Dict, List, Optional, Type

from app.models.base_model import BaseModel
from app.utils.model_relationship_manager import (
    ModelRelationshipManager,
    RelationshipEdge,
    get_model_relationship_manager,
)
from app.utils.relationship_types import RelationshipType


def get_model_manager() -> ModelRelationshipManager:
    """
    Get the global model relationship manager instance.

    Returns:
        The global ModelRelationshipManager instance
    """
    return get_model_relationship_manager()


def get_model_class(model_name: str) -> Optional[Type[BaseModel]]:
    """
    Get a model class by name.

    Args:
        model_name: Name of the model

    Returns:
        Model class or None if not found
    """
    manager = get_model_manager()
    return manager.get_model_class(model_name)


def get_model_relationships(model_name: str) -> Dict[str, Any]:
    """
    Get all relationships for a model.

    Args:
        model_name: Name of the model

    Returns:
        Dictionary of relationship names to RelationshipProperty
    """
    manager = get_model_manager()
    return manager.get_relationships(model_name)


def get_relationship_type(model_name: str, relationship_name: str) -> Optional[RelationshipType]:
    """
    Get the relationship type for a specific relationship.

    Args:
        model_name: Name of the model
        relationship_name: Name of the relationship

    Returns:
        RelationshipType or None if not found
    """
    manager = get_model_manager()
    node = manager.get_model_node(model_name)
    if not node:
        return None

    return node.get_relationship_type(relationship_name)


def get_related_model(model_name: str, relationship_name: str) -> Optional[Type[BaseModel]]:
    """
    Get the related model class for a specific relationship.

    Args:
        model_name: Name of the model
        relationship_name: Name of the relationship

    Returns:
        Related model class or None if not found
    """
    manager = get_model_manager()
    node = manager.get_model_node(model_name)
    if not node:
        return None

    return node.get_related_model(relationship_name)


def find_model_path(source_model: str, target_model: str, max_depth: int = 5) -> Optional[List[RelationshipEdge]]:
    """
    Find a path between two models.

    Args:
        source_model: Starting model name
        target_model: Target model name
        max_depth: Maximum search depth

    Returns:
        List of edges forming the path, or None if no path found
    """
    manager = get_model_manager()
    return manager.find_path(source_model, target_model, max_depth)


def get_model_dependencies(model_name: str) -> set[str]:
    """
    Get all models that the given model depends on.

    Args:
        model_name: Name of the model

    Returns:
        Set of model names that this model depends on
    """
    manager = get_model_manager()
    return manager.get_model_dependencies(model_name)


def get_model_dependents(model_name: str) -> set[str]:
    """
    Get all models that depend on the given model.

    Args:
        model_name: Name of the model

    Returns:
        Set of model names that depend on this model
    """
    manager = get_model_manager()
    return manager.get_model_dependents(model_name)


def validate_nested_data(model_name: str, data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Validate and separate nested relationship data from main data.

    Args:
        model_name: Name of the model
        data: Input data dictionary

    Returns:
        Tuple of (main_data, nested_data)
    """
    manager = get_model_manager()
    return manager.validate_nested_data(model_name, data)


def is_relationship_field(model_name: str, field_name: str) -> bool:
    """
    Check if a field is a relationship field.

    Args:
        model_name: Name of the model
        field_name: Name of the field

    Returns:
        True if the field is a relationship field
    """
    manager = get_model_manager()
    relationships = manager.get_relationships(model_name)
    return field_name in relationships


def get_relationship_edges(model_name: str, direction: str = "outgoing") -> List[RelationshipEdge]:
    """
    Get relationship edges for a model.

    Args:
        model_name: Name of the model
        direction: "outgoing" or "incoming"

    Returns:
        List of RelationshipEdge objects
    """
    manager = get_model_manager()

    if direction == "outgoing":
        return manager.get_outgoing_edges(model_name)
    elif direction == "incoming":
        return manager.get_incoming_edges(model_name)
    else:
        raise ValueError("Direction must be 'outgoing' or 'incoming'")


def get_graph_summary() -> Dict[str, Any]:
    """
    Get a summary of the relationship graph.

    Returns:
        Dictionary containing graph statistics and structure
    """
    manager = get_model_manager()
    return manager.get_graph_summary()


def detect_relationship_cycles() -> List[List[str]]:
    """
    Detect cycles in the relationship graph.

    Returns:
        List of cycles, where each cycle is a list of model names
    """
    manager = get_model_manager()
    return manager.detect_cycles()


def get_model_info(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a model.

    Args:
        model_name: Name of the model

    Returns:
        Dictionary with model information or None if not found
    """
    manager = get_model_manager()
    node = manager.get_model_node(model_name)

    if not node:
        return None

    return {
        "name": node.model_name,
        "table_name": node.table_name,
        "relationships": {
            name: {
                "type": node.get_relationship_type(name).value if node.get_relationship_type(name) else None,
                "target_model": node.get_related_model(name).__name__ if node.get_related_model(name) else None,
            }
            for name in node.relationships.keys()
        },
        "outgoing_edges": len(manager.get_outgoing_edges(model_name)),
        "incoming_edges": len(manager.get_incoming_edges(model_name)),
        "dependencies": list(manager.get_model_dependencies(model_name)),
        "dependents": list(manager.get_model_dependents(model_name)),
    }
