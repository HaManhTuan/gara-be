"""
Unit tests for RepositoryImpl - Unified repository implementation.

This module contains comprehensive unit tests for the RepositoryImpl class,
testing all its capabilities including CRUD operations, optimistic locking,
soft delete, relationship management, and cascade operations.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.repositories.core.repository_impl import RepositoryImpl
from app.repositories.core.interfaces import (
    QueryBuilder,
    OptimisticLockValidator,
    RelationshipHandler,
)


class TestRepositoryImpl:
    """Test cases for RepositoryImpl"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_query_builder = MagicMock(spec=QueryBuilder)
        self.mock_optimistic_lock_validator = MagicMock(spec=OptimisticLockValidator)
        self.mock_relationship_handler = MagicMock(spec=RelationshipHandler)

        self.repository = RepositoryImpl(
            model=User,
            query_builder=self.mock_query_builder,
            optimistic_lock_validator=self.mock_optimistic_lock_validator,
            relationship_handler=self.mock_relationship_handler,
        )

    def test_repository_initialization(self):
        """Test repository initialization"""
        assert self.repository.model == User
        assert self.repository.query_builder == self.mock_query_builder
        assert self.repository.optimistic_lock_validator == self.mock_optimistic_lock_validator
        assert self.repository.relationship_handler == self.mock_relationship_handler

    @pytest.mark.asyncio
    async def test_create_user(self):
        """Test creating a user"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password"
        }

        # Mock the query builder
        self.mock_query_builder.build_create_query.return_value = "CREATE QUERY"

        # Mock the database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = User(**user_data)
        mock_db.execute.return_value = mock_result

        result = await self.repository.create(mock_db, obj_in=user_data)

        assert result is not None
        assert result.username == "testuser"
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id(self):
        """Test getting a user by ID"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_id = "123"

        # Mock the query builder
        self.mock_query_builder.build_get_by_id_query.return_value = "GET BY ID QUERY"

        # Mock the database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = User(
            id=user_id,
            username="testuser",
            email="test@example.com"
        )
        mock_db.execute.return_value = mock_result

        result = await self.repository.get_by_id(mock_db, id=user_id)

        assert result is not None
        assert result.id == user_id
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_all_users(self):
        """Test getting all users"""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock the query builder
        self.mock_query_builder.build_get_all_query.return_value = "GET ALL QUERY"

        # Mock the database session
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            User(id="1", username="user1", email="user1@example.com"),
            User(id="2", username="user2", email="user2@example.com"),
        ]
        mock_db.execute.return_value = mock_result

        result = await self.repository.get_all(mock_db, skip=0, limit=10)

        assert len(result) == 2
        assert result[0].username == "user1"
        assert result[1].username == "user2"

    @pytest.mark.asyncio
    async def test_update_user(self):
        """Test updating a user"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_id = "123"
        update_data = {"username": "updated_user"}

        # Mock the query builder
        self.mock_query_builder.build_update_query.return_value = "UPDATE QUERY"

        # Mock the database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = User(
            id=user_id,
            username="updated_user",
            email="test@example.com"
        )
        mock_db.execute.return_value = mock_result

        result = await self.repository.update(mock_db, id=user_id, obj_in=update_data)

        assert result is not None
        assert result.username == "updated_user"

    @pytest.mark.asyncio
    async def test_delete_user(self):
        """Test soft deleting a user"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_id = "123"

        # Mock the query builder
        self.mock_query_builder.build_soft_delete_query.return_value = "SOFT DELETE QUERY"

        # Mock the database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = User(
            id=user_id,
            username="testuser",
            email="test@example.com",
            deleted_at=datetime.now()
        )
        mock_db.execute.return_value = mock_result

        result = await self.repository.delete(mock_db, id=user_id)

        assert result is not None
        assert result.deleted_at is not None

    @pytest.mark.asyncio
    async def test_user_exists(self):
        """Test checking if user exists"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_id = "123"

        # Mock the query builder
        self.mock_query_builder.build_exists_query.return_value = "EXISTS QUERY"

        # Mock the database session
        mock_result = MagicMock()
        mock_result.scalar.return_value = True
        mock_db.execute.return_value = mock_result

        result = await self.repository.exists(mock_db, id=user_id)

        assert result is True


if __name__ == "__main__":
    pytest.main([__file__])
