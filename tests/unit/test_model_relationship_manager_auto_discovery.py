"""
Tests for ModelRelationshipManager auto-discovery functionality.

This module tests the automatic model discovery from app.models.__init__.py
and verifies that the ModelRelationshipManager correctly detects and registers models.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import Column, String

from app.models.base_model import BaseModel
from app.utils.model_relationship_manager import (
    ModelRelationshipManager,
    ModelNode,
    RelationshipEdge,
    model_relationship_manager,
    initialize_model_relationships,
)


class TestModel(BaseModel):
    """Test model for auto-discovery testing."""

    __tablename__ = "test_models"

    name = Column(String(100), nullable=False)
    description = Column(String(500))


class AnotherTestModel(BaseModel):
    """Another test model for auto-discovery testing."""

    __tablename__ = "another_test_models"

    title = Column(String(200), nullable=False)


class TestModelRelationshipManagerAutoDiscovery:
    """Test auto-discovery functionality of ModelRelationshipManager."""

    def test_auto_discovery_discovers_models_from_init(self):
        """Test that auto-discovery finds models from app.models.__init__.py."""
        # Create a fresh manager instance
        manager = ModelRelationshipManager()

        # Mock the models module to return our test models
        with patch('inspect.getmembers') as mock_getmembers:
            mock_getmembers.return_value = [
                ('TestModel', TestModel),
                ('AnotherTestModel', AnotherTestModel),
                ('BaseModel', BaseModel),  # Should be filtered out
                ('SomeOtherClass', str),   # Should be filtered out
            ]

            # Test auto-discovery
            models = manager._discover_models()

            # Should discover TestModel and AnotherTestModel, but not BaseModel or str
            assert len(models) == 2
            assert TestModel in models
            assert AnotherTestModel in models
            assert BaseModel not in models

    def test_auto_discovery_filters_correctly(self):
        """Test that auto-discovery filters models correctly."""
        manager = ModelRelationshipManager()

        # Mock getmembers to return various types of objects
        with patch('inspect.getmembers') as mock_getmembers:
            mock_getmembers.return_value = [
                ('TestModel', TestModel),
                ('BaseModel', BaseModel),  # Should be filtered out (is BaseModel itself)
                ('StringClass', str),       # Should be filtered out (not BaseModel subclass)
                ('IntClass', int),          # Should be filtered out (not BaseModel subclass)
                ('AnotherTestModel', AnotherTestModel),
            ]

            models = manager._discover_models()

            # Should only include TestModel and AnotherTestModel
            assert len(models) == 2
            assert TestModel in models
            assert AnotherTestModel in models
            assert BaseModel not in models
            assert str not in models
            assert int not in models

    def test_auto_discovery_requires_tablename(self):
        """Test that auto-discovery requires __tablename__ attribute."""
        manager = ModelRelationshipManager()

        # Create a mock class that's not a proper model
        class MockClassWithoutTable:
            """A class that's not a BaseModel subclass."""
            pass

        with patch('inspect.getmembers') as mock_getmembers:
            mock_getmembers.return_value = [
                ('TestModel', TestModel),
                ('MockClassWithoutTable', MockClassWithoutTable),  # Should be filtered out
            ]

            models = manager._discover_models()

            # Should only include TestModel
            assert len(models) == 1
            assert TestModel in models
            assert MockClassWithoutTable not in models

    def test_auto_discovery_handles_import_error(self):
        """Test that auto-discovery handles import errors gracefully."""
        manager = ModelRelationshipManager()

        # Mock the import to raise an ImportError
        with patch('inspect.getmembers') as mock_getmembers:
            mock_getmembers.side_effect = ImportError("Cannot import models module")

            with pytest.raises(ImportError):
                manager._discover_models()

    def test_initialize_with_auto_discovery(self):
        """Test that initialize() works with auto-discovery."""
        manager = ModelRelationshipManager()

        # Mock auto-discovery to return our test models
        with patch.object(manager, '_discover_models') as mock_discover:
            mock_discover.return_value = [TestModel, AnotherTestModel]

            # Initialize the manager
            manager.initialize()

            # Verify models were discovered and registered
            assert manager.is_initialized()
            assert len(manager._nodes) == 2
            assert 'TestModel' in manager._nodes
            assert 'AnotherTestModel' in manager._nodes

            # Verify nodes were created correctly
            test_node = manager.get_model_node('TestModel')
            assert test_node is not None
            assert test_node.model_class == TestModel
            assert test_node.table_name == 'test_models'

    def test_global_manager_auto_discovery(self):
        """Test that the global manager uses auto-discovery."""
        # Reset the global manager
        global_manager = model_relationship_manager
        global_manager._initialized = False
        global_manager._nodes.clear()
        global_manager._edges.clear()

        # Mock auto-discovery
        with patch.object(global_manager, '_discover_models') as mock_discover:
            mock_discover.return_value = [TestModel]

            # Initialize using the global function
            initialize_model_relationships()

            # Verify the global manager was initialized
            assert global_manager.is_initialized()
            assert len(global_manager._nodes) == 1
            assert 'TestModel' in global_manager._nodes

    def test_auto_discovery_with_real_models_module(self):
        """Test auto-discovery with the actual models module."""
        manager = ModelRelationshipManager()

        # This test uses the real models module
        models = manager._discover_models()

        # Should discover at least the User model
        assert len(models) >= 1
        model_names = [model.__name__ for model in models]
        assert 'User' in model_names

        # All discovered models should be BaseModel subclasses
        for model in models:
            assert issubclass(model, BaseModel)
            assert model is not BaseModel
            assert hasattr(model, '__tablename__')

    def test_auto_discovery_logs_correctly(self):
        """Test that auto-discovery logs the correct information."""
        manager = ModelRelationshipManager()

        with patch('app.utils.model_relationship_manager.logger') as mock_logger:
            with patch('inspect.getmembers') as mock_getmembers:
                mock_getmembers.return_value = [
                    ('TestModel', TestModel),
                    ('AnotherTestModel', AnotherTestModel),
                ]

                models = manager._discover_models()

                # Verify debug logs for each discovered model
                debug_calls = [call for call in mock_logger.debug.call_args_list if 'Discovered model:' in str(call)]
                assert len(debug_calls) == 2

                # Verify info log with count and names
                info_calls = [call for call in mock_logger.info.call_args_list if 'Discovered' in str(call)]
                assert len(info_calls) == 1
                assert '2 models' in str(info_calls[0])
                assert 'TestModel' in str(info_calls[0])
                assert 'AnotherTestModel' in str(info_calls[0])


class TestModelRelationshipManagerIntegration:
    """Integration tests for ModelRelationshipManager auto-discovery."""

    def test_full_initialization_workflow(self):
        """Test the complete initialization workflow with auto-discovery."""
        # Create a fresh manager
        manager = ModelRelationshipManager()

        # Mock auto-discovery to return test models
        with patch.object(manager, '_discover_models') as mock_discover:
            mock_discover.return_value = [TestModel, AnotherTestModel]

            # Initialize the manager
            manager.initialize()

            # Verify complete initialization
            assert manager.is_initialized()
            assert len(manager._nodes) == 2
            assert len(manager._edges) == 0  # No relationships between test models

            # Verify graph structure
            summary = manager.get_graph_summary()
            assert summary['total_models'] == 2
            assert summary['total_relationships'] == 0
            assert 'TestModel' in summary['models']
            assert 'AnotherTestModel' in summary['models']

    def test_auto_discovery_with_relationships(self):
        """Test auto-discovery with models that have relationships."""
        # Create models with relationships
        class ParentModel(BaseModel):
            __tablename__ = "parent_models"
            name = Column(String(100))

        class ChildModel(BaseModel):
            __tablename__ = "child_models"
            name = Column(String(100))
            parent_id = Column(String(36))  # Foreign key

        # Mock relationship properties
        mock_rel_prop = MagicMock()
        mock_rel_prop.direction = "ONETOMANY"
        mock_rel_prop.uselist = True
        mock_rel_prop.mapper.class_ = ChildModel
        mock_rel_prop.back_populates = None

        # Mock the get_relationships method to return our mock relationship
        with patch.object(ParentModel, 'get_relationships', return_value={'children': mock_rel_prop}):
            manager = ModelRelationshipManager()

            with patch.object(manager, '_discover_models') as mock_discover:
                mock_discover.return_value = [ParentModel, ChildModel]

                manager.initialize()

                # Verify models were discovered
                assert manager.is_initialized()
                assert len(manager._nodes) == 2

                # Verify relationships were processed
                parent_node = manager.get_model_node('ParentModel')
                assert parent_node is not None
                assert 'children' in parent_node.relationships


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
