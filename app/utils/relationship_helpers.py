from typing import Any, Dict, List, Optional, Tuple, Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import RelationshipProperty

from app.models.base_model import BaseModel


def extract_nested_data(obj_in: Dict[str, Any], model: Type[BaseModel]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Separate main object data from nested relationship data.

    Args:
        obj_in: Input data dictionary
        model: Model class to check relationships against

    Returns:
        Tuple of (main_data, relations_data)

    Example:
        obj_in = {"title": "Post", "tags": [{"name": "python"}]}
        main_data = {"title": "Post"}
        relations_data = {"tags": [{"name": "python"}]}
    """
    relationships = model.get_relationships()
    main_data = {}
    relations_data = {}

    for key, value in obj_in.items():
        if key in relationships and isinstance(value, (dict, list)):
            relations_data[key] = value
        else:
            main_data[key] = value

    return main_data, relations_data


def collect_updated_at_timestamps(obj_in: Dict[str, Any], model: Type[BaseModel]) -> Dict[str, str]:
    """
    Collect all updated_at timestamps from nested objects for optimistic locking.

    Args:
        obj_in: Input data dictionary
        model: Model class

    Returns:
        Dict mapping record ids to their expected updated_at timestamps
    """
    timestamps = {}

    # Check main object
    if "updated_at" in obj_in and "id" in obj_in:
        timestamps[obj_in["id"]] = obj_in["updated_at"]

    # Check nested relationships
    relationships = model.get_relationships()
    for rel_name, rel_prop in relationships.items():
        if rel_name in obj_in:
            rel_data = obj_in[rel_name]

            if isinstance(rel_data, dict):
                # Single object (1-1, many-to-one)
                if "updated_at" in rel_data and "id" in rel_data:
                    timestamps[rel_data["id"]] = rel_data["updated_at"]
            elif isinstance(rel_data, list):
                # Collection (1-n, n-n)
                for item in rel_data:
                    if isinstance(item, dict) and "updated_at" in item and "id" in item:
                        timestamps[item["id"]] = item["updated_at"]

    return timestamps


async def validate_all_optimistic_locks(db: AsyncSession, expected_timestamps: Dict[str, str]) -> None:
    """
    Validate all optimistic locks before performing updates.
    Raises HTTPException 409 if any record was modified.

    Args:
        db: Database session
        expected_timestamps: Dict mapping record ids to expected updated_at timestamps
    """
    for record_id, expected_timestamp in expected_timestamps.items():
        # This would need to be implemented based on the specific model
        # For now, we'll raise an exception indicating this needs implementation
        raise NotImplementedError("Optimistic lock validation needs to be implemented per model")


def build_nested_response(db_obj: BaseModel, include_relations: List[str], depth: int) -> Dict[str, Any]:
    """
    Serialize model instance with nested relationships.

    Args:
        db_obj: Model instance
        include_relations: List of relationship names to include
        depth: How many levels deep to serialize

    Returns:
        Dictionary representation with nested data
    """
    result = db_obj.to_dict()

    if depth > 0 and include_relations:
        relationships = db_obj.__class__.get_relationships()
        for rel_name in include_relations:
            if rel_name in relationships and hasattr(db_obj, rel_name):
                rel_value = getattr(db_obj, rel_name)
                if rel_value is not None:
                    if isinstance(rel_value, list):
                        result[rel_name] = [
                            build_nested_response(item, include_relations, depth - 1) for item in rel_value
                        ]
                    else:
                        result[rel_name] = build_nested_response(rel_value, include_relations, depth - 1)

    return result


def get_relationship_config(model: Type[BaseModel], relation_name: str) -> Optional[RelationshipProperty]:
    """
    Get relationship configuration for a specific relationship.

    Args:
        model: Model class
        relation_name: Name of the relationship

    Returns:
        RelationshipProperty or None if not found
    """
    relationships = model.get_relationships()
    return relationships.get(relation_name)


def resolve_relationship_path(model: Type[BaseModel], path: str) -> Optional[RelationshipProperty]:
    """
    Resolve nested relationship path (e.g., 'posts.comments').

    Args:
        model: Starting model class
        path: Dot-separated relationship path

    Returns:
        Final RelationshipProperty or None if path is invalid
    """
    current_model = model
    path_parts = path.split(".")

    for part in path_parts:
        relationships = current_model.get_relationships()
        if part not in relationships:
            return None

        rel_prop = relationships[part]
        current_model = rel_prop.mapper.class_

    return relationships[path_parts[-1]]


def is_nested_data(key: str, value: Any, model: Type[BaseModel]) -> bool:
    """
    Check if a key-value pair represents nested relationship data.

    Args:
        key: Dictionary key
        value: Dictionary value
        model: Model class to check relationships against

    Returns:
        True if this represents nested relationship data
    """
    relationships = model.get_relationships()
    if key not in relationships:
        return False

    return isinstance(value, (dict, list))
