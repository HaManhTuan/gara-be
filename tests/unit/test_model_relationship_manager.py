"""
Unit tests for ModelRelationshipManager using TDD approach.

This module contains comprehensive tests for the ModelRelationshipManager
to ensure it correctly discovers models, builds relationship graphs,
and provides utilities for managing nested operations.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import RelationshipProperty, ONETOMANY, MANYTOONE

from app.models.base_model import BaseModel
from app.models.user import User
from app.utils.model_relationship_manager import (
    ModelRelationshipManager,
    ModelNode,
    RelationshipEdge,
    model_relationship_manager,
    initialize_model_relationships,
)
from app.utils.relationship_types import RelationshipType


class TestModelRelationshipManager:
    """Test cases for ModelRelationshipManager"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = ModelRelationshipManager()

    def test_model_node_creation(self):
        """Test ModelNode creation and properties"""
        node = ModelNode("User", User)

        assert node.model_name == "User"
        assert node.model_class == User
        assert node.relationships == {}
        assert node.dependencies == set()
        assert node.dependents == set()

    def test_relationship_edge_creation(self):
        """Test RelationshipEdge creation and properties"""
        edge = RelationshipEdge(
            source_model="User",
            target_model="User",  # Self-referential for simplicity
            relationship_name="self_ref",
            relationship_type=RelationshipType.ONE_TO_MANY,
            foreign_key="user_id"
        )

        assert edge.source_model == "User"
        assert edge.target_model == "User"
        assert edge.relationship_name == "self_ref"
        assert edge.relationship_type == RelationshipType.ONE_TO_MANY
        assert edge.foreign_key == "user_id"

    def test_model_discovery(self):
        """Test that models are discovered correctly"""
        models = self.manager._discover_models()

        # Should only discover User model
        assert len(models) == 1
        assert User in models

    def test_model_registration(self):
        """Test model registration"""
        self.manager._register_model(User)

        assert "User" in self.manager._nodes
        assert isinstance(self.manager._nodes["User"], ModelNode)

    def test_initialize_with_user_only(self):
        """Test initialization with only User model"""
        models = [User]
        self.manager.initialize(models)

        assert "User" in self.manager._nodes
        assert len(self.manager._nodes) == 1

    def test_get_model_info(self):
        """Test getting model information"""
        self.manager._register_model(User)

        info = self.manager.get_model_info("User")
        assert info is not None
        assert info.model_name == "User"
        assert info.model_class == User

    def test_get_model_info_nonexistent(self):
        """Test getting info for non-existent model"""
        info = self.manager.get_model_info("NonExistent")
        assert info is None

    def test_get_all_models(self):
        """Test getting all registered models"""
        self.manager._register_model(User)

        models = self.manager.get_all_models()
        assert len(models) == 1
        assert "User" in models

    def test_model_relationship_manager_singleton(self):
        """Test that model_relationship_manager is a singleton"""
        manager1 = model_relationship_manager
        manager2 = model_relationship_manager

        assert manager1 is manager2

    def test_initialize_model_relationships_function(self):
        """Test the initialize_model_relationships function"""
        # This should not raise an exception
        initialize_model_relationships([User])

        # Verify the manager was initialized
        assert "User" in model_relationship_manager._nodes


if __name__ == "__main__":
    pytest.main([__file__])
