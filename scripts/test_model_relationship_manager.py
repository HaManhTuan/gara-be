#!/usr/bin/env python3
"""
Test script for the Model Relationship Manager.

This script tests the model relationship manager functionality
and demonstrates how to use it for managing model relationships.
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Set the environment to test
os.environ["APP_ENV"] = "test"

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import after setting environment
from app.utils.model_relationship_manager import initialize_model_relationships, get_model_relationship_manager
from app.utils.model_utils import (
    get_model_class,
    get_model_relationships,
    get_relationship_type,
    get_related_model,
    find_model_path,
    get_model_dependencies,
    get_model_dependents,
    get_graph_summary,
    detect_relationship_cycles,
    get_model_info
)


async def test_model_relationship_manager():
    """Test the model relationship manager functionality."""
    print("=" * 60)
    print("Testing Model Relationship Manager")
    print("=" * 60)

    # Initialize the manager
    print("\n1. Initializing Model Relationship Manager...")
    initialize_model_relationships()

    manager = get_model_relationship_manager()
    print(f"✓ Manager initialized: {manager.is_initialized()}")

    # Get graph summary
    print("\n2. Getting Graph Summary...")
    summary = get_graph_summary()
    print(f"✓ Total models: {summary['total_models']}")
    print(f"✓ Total relationships: {summary['total_relationships']}")
    print(f"✓ Cycles detected: {summary['cycles_detected']}")

    if summary['cycles']:
        print("⚠️  Cycles found:")
        for cycle in summary['cycles']:
            print(f"   {' -> '.join(cycle)}")

    # Test model discovery
    print("\n3. Testing Model Discovery...")
    models = list(summary['models'].keys())
    print(f"✓ Discovered models: {models}")

    for model_name in models:
        model_info = get_model_info(model_name)
        if model_info:
            print(f"   {model_name}:")
            print(f"     - Table: {model_info['table_name']}")
            print(f"     - Relationships: {list(model_info['relationships'].keys())}")
            print(f"     - Dependencies: {model_info['dependencies']}")
            print(f"     - Dependents: {model_info['dependents']}")

    # Test relationship queries
    print("\n4. Testing Relationship Queries...")

    # Test User model relationships
    user_relationships = get_model_relationships("User")
    print(f"✓ User relationships: {list(user_relationships.keys())}")

    # Test Post model relationships
    post_relationships = get_model_relationships("Post")
    print(f"✓ Post relationships: {list(post_relationships.keys())}")

    # Test relationship types
    print("\n5. Testing Relationship Types...")
    for model_name in ["User", "Post", "Tag", "Comment"]:
        relationships = get_model_relationships(model_name)
        print(f"   {model_name}:")
        for rel_name in relationships.keys():
            rel_type = get_relationship_type(model_name, rel_name)
            related_model = get_related_model(model_name, rel_name)
            if rel_type and related_model:
                print(f"     - {rel_name}: {rel_type.value} -> {related_model.__name__}")

    # Test path finding
    print("\n6. Testing Path Finding...")
    test_paths = [
        ("User", "Post"),
        ("User", "Comment"),
        ("Post", "Tag"),
        ("Comment", "User"),
        ("Tag", "Comment")
    ]

    for source, target in test_paths:
        path = find_model_path(source, target)
        if path:
            path_str = f"{source} -> " + " -> ".join([edge.target_model for edge in path])
            print(f"✓ Path from {source} to {target}: {path_str}")
        else:
            print(f"✗ No path found from {source} to {target}")

    # Test dependencies
    print("\n7. Testing Dependencies...")
    for model_name in ["User", "Post", "Tag", "Comment"]:
        dependencies = get_model_dependencies(model_name)
        dependents = get_model_dependents(model_name)
        print(f"   {model_name}:")
        print(f"     - Depends on: {list(dependencies)}")
        print(f"     - Dependents: {list(dependents)}")

    # Test model class retrieval
    print("\n8. Testing Model Class Retrieval...")
    for model_name in models:
        model_class = get_model_class(model_name)
        if model_class:
            print(f"✓ {model_name}: {model_class.__name__} (table: {model_class.__tablename__})")
        else:
            print(f"✗ Failed to get model class for {model_name}")

    # Test cycle detection
    print("\n9. Testing Cycle Detection...")
    cycles = detect_relationship_cycles()
    if cycles:
        print("⚠️  Cycles detected:")
        for cycle in cycles:
            print(f"   {' -> '.join(cycle)}")
    else:
        print("✓ No cycles detected")

    print("\n" + "=" * 60)
    print("Model Relationship Manager Test Complete")
    print("=" * 60)


async def test_nested_data_validation():
    """Test nested data validation functionality."""
    print("\n" + "=" * 60)
    print("Testing Nested Data Validation")
    print("=" * 60)

    from app.utils.model_utils import validate_nested_data

    # Test data for different models
    test_cases = [
        {
            "model": "User",
            "data": {
                "username": "test_user",
                "email": "test@example.com",
                "password": "password123",
                "posts": [
                    {
                        "title": "My First Post",
                        "content": "This is my first post",
                        "tags": [
                            {"name": "python", "description": "Python programming"},
                            {"name": "fastapi", "description": "FastAPI framework"}
                        ]
                    }
                ]
            }
        },
        {
            "model": "Post",
            "data": {
                "title": "Test Post",
                "content": "Test content",
                "author_id": "user123",
                "tags": [
                    {"name": "test", "description": "Test tag"}
                ],
                "comments": [
                    {
                        "text": "Great post!",
                        "post_id": "post123"
                    }
                ]
            }
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['model']} nested data validation:")

        try:
            main_data, nested_data = validate_nested_data(test_case['model'], test_case['data'])

            print(f"   Main data fields: {list(main_data.keys())}")
            print(f"   Nested data fields: {list(nested_data.keys())}")

            for field, value in nested_data.items():
                if isinstance(value, list):
                    print(f"   - {field}: {len(value)} items")
                else:
                    print(f"   - {field}: single object")

        except Exception as e:
            print(f"   ✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_model_relationship_manager())
    asyncio.run(test_nested_data_validation())
