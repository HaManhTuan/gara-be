# Development Guide: Adding New Features with Base Service and Repository

This guide provides step-by-step instructions for developers to add new features using our base service and repository pattern. It covers creating complete CRUD operations with relationship handling.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Pattern](#architecture-pattern)
3. [Step-by-Step Guide](#step-by-step-guide)
   - [Step 1: Add New Model](#step-1-add-new-model)
   - [Step 2: Create Schemas](#step-2-create-schemas)
   - [Step 3: Create New Repository](#step-3-create-new-repository)
   - [Step 4: Create New Service](#step-4-create-new-service)
   - [Step 5: Create New Controller](#step-5-create-new-controller)
   - [Step 6: Create CRUD Tests](#step-6-create-crud-tests)
4. [Relationship Handling](#relationship-handling)
5. [Best Practices](#best-practices)
6. [Common Patterns](#common-patterns)
7. [Troubleshooting](#troubleshooting)

## Overview

Our application follows a layered architecture pattern with:
- **Models**: SQLAlchemy ORM models with relationships
- **Schemas**: Pydantic models for validation and data transformation (3-layer structure)
- **Repositories**: Data access layer using `RepositoryImpl` or `FullRepositoryImpl`
- **Services**: Business logic layer using `BaseService`
- **Controllers**: API endpoints using FastAPI

## Architecture Pattern

```
Request → Controller → Service → Repository → Database
                ↓
Response ← Request/Response Schema ← Internal Schema ← Service ← Repository ← Database
```

## Step-by-Step Guide

### Step 1: Add New Model

Create a new SQLAlchemy model in `app/models/`:

```python
# app/models/category.py
from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.base_model import BaseModel

class Category(BaseModel):
    __tablename__ = "categories"

    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    posts = relationship("Post", back_populates="category")

    def get_relationships(self):
        """Return list of relationship names for this model."""
        return ["posts"]
```

**Key Points:**
- Inherit from `BaseModel` (provides `id`, `created_at`, `updated_at`, `deleted_at`)
- Define relationships using `relationship()`
- Implement `get_relationships()` method for relationship discovery
- Use appropriate SQLAlchemy column types

### Step 2: Create Schemas

Create a schema directory structure with 3 files for each domain:

```
app/schemas/{domain}/
├── __init__.py           # Export all schemas
├── request.py            # Request/Response schemas for API
├── schema.py             # Internal schemas for application logic
└── converters.py         # Conversion functions between schemas
```

#### 2.1 Request/Response Schemas (`request.py`)

Create schemas for API request and response validation:

```python
# app/schemas/categories/request.py
from pydantic import Field
from app.schemas.common.base_schema import BaseSchema
from typing import Optional

class CategoryCreateRequest(BaseSchema):
    """Schema for creating a category."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: bool = Field(True, description="Whether category is active")
    sort_order: int = Field(0, ge=0, description="Display order")

class CategoryUpdateRequest(BaseSchema):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: Optional[bool] = Field(None, description="Whether category is active")
    sort_order: Optional[int] = Field(None, ge=0, description="Display order")

class CategoryResponse(BaseSchema):
    """Schema for category response."""
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    sort_order: int
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None
```

**Key Points:**
- Use `Field()` for validation rules and descriptions
- Request schemas validate input data
- Response schemas format output data
- Use `Optional` for fields that can be null
- Include timestamps in response schemas

#### 2.2 Internal Schemas (`schema.py`)

Create schemas for internal application logic:

```python
# app/schemas/categories/schema.py
from pydantic import Field
from app.schemas.common.base_schema import BaseSchema
from typing import Optional

class CategoryCreate(BaseSchema):
    """Internal schema for creating a category."""
    name: str
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class CategoryUpdate(BaseSchema):
    """Internal schema for updating a category."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class CategoryInternal(BaseSchema):
    """Internal schema for category data."""
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    sort_order: int
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None
```

**Key Points:**
- Internal schemas are simpler, focused on business logic
- No API-specific validation rules
- Used for service layer operations
- Can include computed fields or business-specific data

#### 2.3 Converter Functions (`converters.py`)

Create functions to convert between different schema types:

```python
# app/schemas/categories/converters.py
from app.models.category import Category
from app.schemas.categories.request import CategoryCreateRequest, CategoryUpdateRequest, CategoryResponse
from app.schemas.categories.schema import CategoryCreate, CategoryUpdate

def convert_category_create_request_to_internal(request: CategoryCreateRequest) -> CategoryCreate:
    """Convert CategoryCreateRequest to internal CategoryCreate."""
    return CategoryCreate(
        name=request.name,
        description=request.description,
        is_active=request.is_active,
        sort_order=request.sort_order
    )

def convert_category_update_request_to_internal(request: CategoryUpdateRequest) -> CategoryUpdate:
    """Convert CategoryUpdateRequest to internal CategoryUpdate."""
    return CategoryUpdate(
        name=request.name,
        description=request.description,
        is_active=request.is_active,
        sort_order=request.sort_order
    )

def convert_category_model_to_response(category: Category) -> CategoryResponse:
    """Convert Category model to CategoryResponse."""
    return CategoryResponse(
        id=str(category.id),
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        sort_order=category.sort_order,
        created_at=category.created_at.isoformat() if category.created_at else "",
        updated_at=category.updated_at.isoformat() if category.updated_at else "",
        deleted_at=category.deleted_at.isoformat() if category.deleted_at else None
    )

def convert_category_internal_to_model(internal: CategoryInternal) -> dict:
    """Convert CategoryInternal to model data dict."""
    return {
        "name": internal.name,
        "description": internal.description,
        "is_active": internal.is_active,
        "sort_order": internal.sort_order
    }
```

**Key Points:**
- Converters handle data transformation between layers
- Handle type conversions (UUID to string, datetime to ISO format)
- Provide clear separation between API and internal data
- Handle optional fields appropriately

#### 2.4 Schema Exports (`__init__.py`)

Export all schemas and converters for easy importing:

```python
# app/schemas/categories/__init__.py
from .request import CategoryCreateRequest, CategoryUpdateRequest, CategoryResponse
from .schema import CategoryCreate, CategoryUpdate, CategoryInternal
from .converters import (
    convert_category_create_request_to_internal,
    convert_category_update_request_to_internal,
    convert_category_model_to_response,
    convert_category_internal_to_model
)

__all__ = [
    # Request/Response schemas
    "CategoryCreateRequest",
    "CategoryUpdateRequest",
    "CategoryResponse",
    # Internal schemas
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryInternal",
    # Converters
    "convert_category_create_request_to_internal",
    "convert_category_update_request_to_internal",
    "convert_category_model_to_response",
    "convert_category_internal_to_model"
]
```

**Key Points:**
- Export all schemas and converters
- Use clear naming conventions
- Group exports by type (request, internal, converters)
- Enable clean imports in controllers and services

### Step 3: Create New Repository

Create a repository in `app/repositories/concrete/`:

```python
# app/repositories/concrete/category_repository.py
from sqlalchemy import select
from app.repositories.core import RepositoryImpl
from app.models.category import Category
from app.repositories.factory import repository_factory

class CategoryRepository(RepositoryImpl[Category]):
    def __init__(self) -> None:
        repo = repository_factory.create_repository(Category)
        super().__init__(
            model=Category,
            query_builder=repo.query_builder,
            optimistic_lock_validator=repo.optimistic_lock_validator,
        )

    # Add custom methods if needed
    async def get_by_name(self, db, name: str):
        """Get category by name."""
        query = select(Category).where(Category.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()
```

**Key Points:**
- Inherit from `RepositoryImpl[ModelType]` for simple CRUD or `FullRepositoryImpl[ModelType]` for relationships
- Use `repository_factory.create_repository()` or `create_full_repository()` for initialization
- Add custom query methods as needed
- The base repository provides all CRUD operations automatically

### Step 4: Create New Service

Create a service in `app/services/`:

```python
# app/services/category_service.py
from app.services.base_service import BaseService
from app.repositories.concrete.category_repository import CategoryRepository
from app.models.category import Category
from app.utils.tracing import get_trace_logger

logger = get_trace_logger("category-service")

class CategoryService(BaseService[Category, CategoryRepository]):
    def __init__(self) -> None:
        super().__init__(CategoryRepository())

    # Use base methods directly - no wrapping needed
    # Available base methods:
    # - create(db, obj_in)
    # - get_by_id(db, id)
    # - get_all(db, skip=0, limit=100)
    # - update(db, id, obj_in)
    # - delete(db, id, hard_delete=False)
    # - exists(db, id)

    # Custom business logic methods only when base methods don't suffice
    async def get_category_by_name(self, db, name: str):
        """Get category by name - custom business logic."""
        logger.info(f"Getting category by name: {name}")
        return await self.repository.get_by_name(db, name)

    async def activate_category(self, db, category_id: str):
        """Activate a category - custom business logic."""
        logger.info(f"Activating category: {category_id}")
        return await self.update(db, id=category_id, obj_in={"is_active": True})

    async def deactivate_category(self, db, category_id: str):
        """Deactivate a category - custom business logic."""
        logger.info(f"Deactivating category: {category_id}")
        return await self.update(db, id=category_id, obj_in={"is_active": False})

# Ready-to-use service instance
category_service = CategoryService()
```

**Key Points:**
- Inherit from `BaseService[ModelType, RepositoryType]`
- Use `self.repository` to access repository methods
- Use `self.create()`, `self.get_by_id()`, `self.update()`, `self.delete()` for basic operations
- Add custom business logic methods as needed

### Step 5: Create New Controller

Create a controller in `app/controllers/`:

```python
# app/controllers/category_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.config.database import get_db
from app.schemas.common import ResponseBuilder, SuccessResponse
from app.schemas.categories import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
    CategoryResponse,
    convert_category_create_request_to_internal,
    convert_category_update_request_to_internal,
    convert_category_model_to_response
)
from app.services.category_service import category_service
from app.utils.auth import get_current_user
from app.utils.tracing import get_trace_logger

logger = get_trace_logger("category-controller")
router = APIRouter()

@router.post("/", response_model=SuccessResponse[CategoryResponse])
async def create_category(
    *,
    db: AsyncSession = Depends(get_db),
    category_data: CategoryCreateRequest,
    current_user = Depends(get_current_user)
) -> SuccessResponse[CategoryResponse]:
    """Create a new category."""
    logger.info(f"Creating category: {category_data.name}")

    # Convert request schema to internal format
    internal_category_data = convert_category_create_request_to_internal(category_data)

    # Use base service method directly
    category = await category_service.create(db, obj_in=internal_category_data.model_dump())

    # Convert model to response schema
    category_response = convert_category_model_to_response(category)

    return ResponseBuilder.success(
        message="Category created successfully",
        data=category_response
    )

@router.get("/", response_model=SuccessResponse[List[CategoryResponse]])
async def get_categories(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> SuccessResponse[List[CategoryResponse]]:
    """Get all categories with pagination."""
    # Use base service method directly
    categories = await category_service.get_all(db, skip=skip, limit=limit)

    # Convert models to response schemas
    categories_response = [convert_category_model_to_response(category) for category in categories]

    return ResponseBuilder.success(
        message="Categories retrieved successfully",
        data=categories_response
    )

@router.get("/{category_id}", response_model=SuccessResponse[CategoryResponse])
async def get_category(
    *,
    db: AsyncSession = Depends(get_db),
    category_id: str
) -> SuccessResponse[CategoryResponse]:
    """Get a specific category by ID."""
    category_service = CategoryService()
    category = await category_service.get_by_id(db, id=category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return ResponseBuilder.success(
        message="Category retrieved successfully",
        data=category
    )

@router.put("/{category_id}", response_model=SuccessResponse[CategoryResponse])
async def update_category(
    *,
    db: AsyncSession = Depends(get_db),
    category_id: str,
    category_data: CategoryUpdateRequest,
    current_user = Depends(get_current_user)
) -> SuccessResponse[CategoryResponse]:
    """Update a category."""
    logger.info(f"Updating category: {category_id}")

    category_service = CategoryService()
    category = await category_service.update(
        db,
        db_obj_id=category_id,
        obj_in=category_data.model_dump(exclude_unset=True)
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return ResponseBuilder.success(
        message="Category updated successfully",
        data=category
    )

@router.delete("/{category_id}", response_model=SuccessResponse[None])
async def delete_category(
    *,
    db: AsyncSession = Depends(get_db),
    category_id: str,
    current_user = Depends(get_current_user),
    hard_delete: bool = False
) -> SuccessResponse[None]:
    """Delete a category."""
    logger.info(f"Deleting category: {category_id}")

    category_service = CategoryService()
    category = await category_service.delete(db, id=category_id, hard_delete=hard_delete)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return ResponseBuilder.deleted(message="Category deleted successfully")
```

**Key Points:**
- Use `APIRouter` for route definition
- Use `Depends(get_db)` for database session
- Use `Depends(get_current_user)` for authentication
- Use `ResponseBuilder` for consistent response format
- Handle errors with appropriate HTTP status codes

### Step 6: Create CRUD Tests

Create comprehensive tests following TDD approach:

```python
# tests/api/test_category_crud_tdd.py
import pytest
import uuid
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.user import User
from app.services.category_service import CategoryService
from tests.api.conftest import PostTestFixtures

class TestCategoryCRUDTDD(PostTestFixtures):
    """TDD Test class for Category CRUD operations."""

    # CREATE Tests
    def test_create_category_success(self, client: TestClient, test_user: User):
        """Test creating a category successfully."""
        category_data = {
            "name": f"Test Category {str(uuid.uuid4())[:8]}",
            "description": "Test category description"
        }

        response = client.post(
            "/api/v1/categories/",
            json=category_data,
            headers={"Authorization": f"Bearer {self._create_test_token(test_user)}"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == category_data["name"]

    def test_create_category_unauthorized(self, client: TestClient):
        """Test creating a category without authentication."""
        category_data = {"name": "Test Category", "description": "Test"}

        response = client.post("/api/v1/categories/", json=category_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # READ Tests
    def test_get_categories_success(self, client: TestClient):
        """Test getting all categories."""
        response = client.get("/api/v1/categories/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_category_by_id_success(self, client: TestClient, test_category: Category):
        """Test getting a category by ID."""
        response = client.get(f"/api/v1/categories/{test_category.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["id"] == test_category.id

    def test_get_category_not_found(self, client: TestClient):
        """Test getting a non-existent category."""
        response = client.get("/api/v1/categories/nonexistent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # UPDATE Tests
    def test_update_category_success(self, client: TestClient, test_user: User, test_category: Category):
        """Test updating a category."""
        update_data = {
            "name": "Updated Category Name",
            "description": "Updated description"
        }

        response = client.put(
            f"/api/v1/categories/{test_category.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self._create_test_token(test_user)}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["name"] == update_data["name"]

    # DELETE Tests
    def test_delete_category_success(self, client: TestClient, test_user: User, test_category: Category):
        """Test deleting a category."""
        response = client.delete(
            f"/api/v1/categories/{test_category.id}",
            headers={"Authorization": f"Bearer {self._create_test_token(test_user)}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None

    # Service Layer Tests
    async def test_service_layer_integration(self, db: AsyncSession, test_user: User):
        """Test service layer integration."""
        category_service = CategoryService()

        category_data = {
            "name": f"Service Test Category {str(uuid.uuid4())[:8]}",
            "description": "Service test"
        }

        category = await category_service.create_category(db, category_data)
        assert category is not None
        assert category.name == category_data["name"]
```

**Key Points:**
- Inherit from `PostTestFixtures` for shared test data
- Test all CRUD operations (Create, Read, Update, Delete)
- Test authentication and authorization
- Test error cases (not found, validation errors)
- Test service layer integration
- Use unique test data to avoid conflicts

## Relationship Handling

### One-to-Many Relationships

```python
# Model with one-to-many relationship
class Author(BaseModel):
    __tablename__ = "authors"

    name = Column(String(100), nullable=False)
    posts = relationship("Post", back_populates="author")  # One-to-many

class Post(BaseModel):
    __tablename__ = "posts"

    title = Column(String(200), nullable=False)
    author_id = Column(String, ForeignKey("authors.id"), nullable=False)
    author = relationship("Author", back_populates="posts")  # Many-to-one
```

### Many-to-Many Relationships

```python
# Junction table
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", String, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", String, ForeignKey("tags.id"), primary_key=True),
)

# Models with many-to-many relationship
class Post(BaseModel):
    __tablename__ = "posts"

    title = Column(String(200), nullable=False)
    tags = relationship("Tag", secondary="post_tags", back_populates="posts")

class Tag(BaseModel):
    __tablename__ = "tags"

    name = Column(String(50), unique=True, nullable=False)
    posts = relationship("Post", secondary="post_tags", back_populates="tags")
```

### Creating with Relationships

```python
# Service method for creating with relationships
async def create_post_with_tags(self, db, post_data):
    """Create post with nested tags."""
    return await self.repository.create_with_relations(
        db,
        obj_in=post_data,  # Includes nested tags data
        sync_mode="append"  # Add to existing relationships
    )
```

## Schema Best Practices

### 1. Schema Structure
- **Always use 3-file structure**: `request.py`, `schema.py`, `converters.py`
- **Separate concerns**: API schemas vs internal schemas vs conversion logic
- **Use converters**: Never pass raw request data to services
- **Export everything**: Use `__init__.py` for clean imports

### 2. Request/Response Schemas
- **Validation rules**: Use `Field()` with appropriate constraints
- **Descriptions**: Always provide field descriptions for API documentation
- **Optional fields**: Use `Optional` for nullable fields in update requests
- **Response format**: Include all necessary fields for client consumption

### 3. Internal Schemas
- **Business logic focused**: No API-specific validation rules
- **Simpler structure**: Focus on data transformation
- **Computed fields**: Can include business-specific calculated fields
- **Type safety**: Maintain strong typing for service layer

### 4. Converter Functions
- **Type conversion**: Handle UUID to string, datetime to ISO format
- **Safe access**: Use try-catch for relationship access to avoid lazy loading issues
- **Null handling**: Properly handle optional fields and None values
- **Performance**: Avoid unnecessary conversions

### 5. Schema Naming Conventions
- **Request schemas**: `{Entity}{Action}Request` (e.g., `CategoryCreateRequest`)
- **Response schemas**: `{Entity}Response` (e.g., `CategoryResponse`)
- **Internal schemas**: `{Entity}{Action}` (e.g., `CategoryCreate`)
- **Converters**: `convert_{from}_to_{to}` (e.g., `convert_category_model_to_response`)

## Best Practices

### 1. Model Design
- Always inherit from `BaseModel`
- Use appropriate column types and constraints
- Implement `get_relationships()` method
- Use descriptive relationship names

### 2. Repository Pattern
- Inherit from `FullRepositoryImpl[ModelType]`
- Use factory pattern for initialization
- Add custom query methods only when needed
- Leverage base repository methods

### 3. Service Layer
- Inherit from `BaseService[ModelType, RepositoryType]`
- Keep business logic in services, not controllers
- Use dependency injection for repositories
- Handle business exceptions appropriately

### 4. Controller Design
- Use FastAPI `APIRouter`
- Apply authentication middleware where needed
- Use consistent response format with `ResponseBuilder`
- Handle errors with appropriate HTTP status codes

### 5. Testing
- Follow TDD approach
- Test all CRUD operations
- Test authentication and authorization
- Test error cases and edge cases
- Use shared fixtures to avoid duplication

## Common Patterns

### 1. Soft Delete Pattern
```python
# Service method for soft delete
async def soft_delete_category(self, db, category_id: str):
    """Soft delete a category."""
    return await self.delete(db, id=category_id, hard_delete=False)
```

### 2. Optimistic Locking
```python
# Update with optimistic locking
async def update_with_lock(self, db, category_id: str, data: dict):
    """Update with optimistic locking."""
    return await self.repository.update_with_optimistic_lock_and_relations(
        db, id=category_id, obj_data=data
    )
```

### 3. Pagination
```python
# Get with pagination
async def get_categories_paginated(self, db, skip: int = 0, limit: int = 100):
    """Get categories with pagination."""
    return await self.get_all(db, skip=skip, limit=limit)
```

### 4. Search Functionality
```python
# Repository method for search
async def search_categories(self, db, search_term: str):
    """Search categories by name."""
    query = select(Category).where(Category.name.ilike(f"%{search_term}%"))
    result = await db.execute(query)
    return result.scalars().all()
```

## Troubleshooting

### Common Issues

1. **Missing Relationship Method**
   - Ensure `get_relationships()` is implemented in your model
   - Return list of relationship attribute names

2. **Repository Initialization Error**
   - Use `repository_factory.create_repository(Model)` or `create_full_repository(Model)` for initialization
   - Pass all required components to parent constructor

3. **Service Method Not Found**
   - Use `self.repository` to access repository methods
   - Use `self.create()`, `self.get_by_id()`, etc. for base operations

4. **Schema Conversion Errors**
   - Use converters instead of passing raw request data to services
   - Handle lazy loading issues with try-catch blocks in converters
   - Ensure proper type conversions (UUID to string, datetime to ISO)

5. **Test Fixture Conflicts**
   - Use unique test data (UUIDs, timestamps)
   - Clean up test data after each test

6. **Relationship Loading Issues**
   - Use `selectinload()` for eager loading
   - Handle lazy loading in converters with try-catch blocks
   - Use direct SQL for many-to-many relationships in tests

### Debug Tips

1. **Enable Logging**
   ```python
   from app.utils.tracing import get_trace_logger
   logger = get_trace_logger("your-component")
   logger.info("Debug message")
   ```

2. **Check Database State**
   ```python
   # In tests, check what's in the database
   categories = await db.execute(select(Category))
   print(categories.scalars().all())
   ```

3. **Validate Relationships**
   ```python
   # Check if relationships are properly loaded
   post = await post_service.get_by_id(db, post_id)
   print(f"Post tags: {post.tags}")  # Should not trigger lazy load
   ```

## Conclusion

This guide provides a comprehensive approach to adding new features using our base service and repository pattern with a 3-layer schema structure. By following these steps and best practices, developers can create robust, maintainable, and well-tested CRUD operations with relationship handling.

Remember to:
- Follow the established patterns
- Use the 3-file schema structure (request.py, schema.py, converters.py)
- Write comprehensive tests
- Handle relationships properly
- Use consistent error handling
- Document your code appropriately

For more specific examples, refer to the existing Post, User, Tag, Comment, Category, and Product implementations in the codebase.
