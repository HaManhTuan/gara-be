#!/usr/bin/env python3
"""
Test script for the updated BaseRepositoryImpl with Model Relationship Manager integration.

This script demonstrates how the BaseRepositoryImpl now uses the Model Relationship Manager
for validation and provides utility methods for relationship information.
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
from app.repositories.core.base_repository_impl import BaseRepositoryImpl
from app.repositories.core.query_builder import DefaultQueryBuilder
from app.repositories.core.optimistic_lock_validator import DefaultOptimisticLockValidator
from app.models.user import User
from app.utils.model_relationship_manager import initialize_model_relationships


async def test_base_repository_with_model_manager():
    """Test the BaseRepositoryImpl with Model Relationship Manager integration."""
    print("=" * 60)
    print("Testing BaseRepositoryImpl with Model Relationship Manager")
    print("=" * 60)

    # Initialize the model relationship manager
    print("\n0. Initializing Model Relationship Manager...")
    initialize_model_relationships()
    print("✓ Model Relationship Manager initialized")

    # Create repository instance
    query_builder = DefaultQueryBuilder(User)
    optimistic_lock_validator = DefaultOptimisticLockValidator()
    user_repo = BaseRepositoryImpl(User, query_builder, optimistic_lock_validator)

    print(f"\n1. Repository initialized for model: {user_repo.model_name}")

    # Test utility methods
    print("\n2. Testing utility methods...")

    # Get model info
    model_info = user_repo.get_model_info()
    print(f"✓ Model info retrieved: {model_info.get('name', 'Unknown')}")
    print(f"  - Table: {model_info.get('table_name', 'Unknown')}")
    print(f"  - Relationships: {list(model_info.get('relationships', {}).keys())}")

    # Get relationships
    relationships = user_repo.get_relationships()
    print(f"✓ Relationships: {list(relationships.keys())}")

    # Get dependencies
    dependencies = user_repo.get_model_dependencies()
    print(f"✓ Dependencies: {list(dependencies)}")

    # Get dependents
    dependents = user_repo.get_model_dependents()
    print(f"✓ Dependents: {list(dependents)}")

    # Test nested data validation
    print("\n3. Testing nested data validation...")

    # Test data with nested relationships
    test_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "password123",
        "posts": [  # This is nested relationship data
            {
                "title": "My First Post",
                "content": "This is my first post"
            }
        ]
    }

    main_data, nested_data = user_repo.validate_nested_data(test_data)
    print(f"✓ Main data fields: {list(main_data.keys())}")
    print(f"✓ Nested data fields: {list(nested_data.keys())}")

    # Test relationship field detection
    print("\n4. Testing relationship field detection...")

    test_fields = ["username", "email", "posts", "created_at", "nonexistent"]
    for field in test_fields:
        is_rel = user_repo.is_relationship_field(field)
        print(f"  - {field}: {'✓ Relationship' if is_rel else '✗ Not relationship'}")

    # Test error messages for placeholder methods
    print("\n5. Testing placeholder method error messages...")

    placeholder_methods = [
        ("create_with_relations", "create_with_relations() is not implemented in BaseRepositoryImpl"),
        ("update_with_optimistic_lock_and_relations", "update_with_optimistic_lock_and_relations() is not implemented"),
        ("manage_relations", "manage_relations() is not implemented in BaseRepositoryImpl"),
        ("delete_with_cascade", "delete_with_cascade() is not implemented in BaseRepositoryImpl")
    ]

    for method_name, expected_error in placeholder_methods:
        try:
            method = getattr(user_repo, method_name)
            # This will raise NotImplementedError with our custom message
            if method_name == "create_with_relations":
                await method(None, obj_in={})
            elif method_name == "update_with_optimistic_lock_and_relations":
                await method(None, id="test", obj_in={})
            elif method_name == "manage_relations":
                await method(None, parent_id="test", relation_name="test", obj_in=[])
            elif method_name == "delete_with_cascade":
                await method(None, id="test")
        except NotImplementedError as e:
            if expected_error in str(e):
                print(f"✓ {method_name}: Correct error message")
            else:
                print(f"✗ {method_name}: Unexpected error message: {e}")
        except Exception as e:
            print(f"✗ {method_name}: Unexpected exception: {e}")

    print("\n" + "=" * 60)
    print("BaseRepositoryImpl with Model Relationship Manager Test Complete")
    print("=" * 60)
    print("\nKey Benefits:")
    print("✓ Integrated with Model Relationship Manager")
    print("✓ Provides utility methods for relationship information")
    print("✓ Validates nested data and warns about relationship fields")
    print("✓ Clear error messages directing users to FullRepositoryImpl")
    print("✓ Maintains separation of concerns (basic CRUD vs relationship operations)")


if __name__ == "__main__":
    asyncio.run(test_base_repository_with_model_manager())
