# Quick Reference: CRUD Operations with Base Service and Repository

This is a quick reference guide for common CRUD operations and patterns.

## Model Template

```python
# app/models/example.py
from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_model import BaseModel

class Example(BaseModel):
    __tablename__ = "examples"

    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign key relationships
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="examples")

    # One-to-many relationships
    items = relationship("Item", back_populates="example", cascade="all, delete-orphan")

    # Many-to-many relationships
    tags = relationship("Tag", secondary="example_tags", back_populates="examples")

    def get_relationships(self):
        """Return list of relationship names for this model."""
        return ["category", "items", "tags"]
```

## Repository Template

```python
# app/repositories/concrete/example_repository.py
from sqlalchemy import select
from app.repositories.core import FullRepositoryImpl
from app.models.example import Example
from app.repositories.factory import repository_factory

class ExampleRepository(FullRepositoryImpl[Example]):
    def __init__(self) -> None:
        full_repo = repository_factory.create_full_repository(Example)
        super().__init__(
            model=Example,
            query_builder=full_repo.query_builder,
            optimistic_lock_validator=full_repo.optimistic_lock_validator,
            relationship_handler=full_repo.relationship_handler,
        )

    # Custom query methods
    async def get_by_name(self, db, name: str):
        """Get example by name."""
        query = select(Example).where(Example.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_examples(self, db):
        """Get all active examples."""
        query = select(Example).where(Example.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()
```

## Service Template

```python
# app/services/example_service.py
from app.services.base_service import BaseService
from app.repositories.concrete.example_repository import ExampleRepository
from app.models.example import Example
from app.utils.tracing import get_trace_logger

logger = get_trace_logger("example-service")

class ExampleService(BaseService[Example, ExampleRepository]):
    def __init__(self) -> None:
        super().__init__(ExampleRepository())

    # Basic CRUD operations (inherited from BaseService)
    # - create(db, obj_in)
    # - get_by_id(db, id)
    # - get_all(db, skip=0, limit=100)
    # - update(db, db_obj_id, obj_in)
    # - delete(db, id, hard_delete=False)

    # Custom business logic methods
    async def create_example_with_relationships(self, db, example_data):
        """Create example with nested relationships."""
        return await self.repository.create_with_relations(
            db,
            obj_in=example_data,
            sync_mode="append"
        )

    async def get_example_by_name(self, db, name: str):
        """Get example by name."""
        return await self.repository.get_by_name(db, name)

    async def activate_example(self, db, example_id: str):
        """Activate an example."""
        example = await self.get_by_id(db, id=example_id)
        if example:
            return await self.update(db, db_obj_id=example_id, obj_in={"is_active": True})
        return None

    async def get_examples_with_relationships(self, db, example_id: str):
        """Get example with all relationships loaded."""
        return await self.repository.get_by_id_with_relations(
            db,
            id=example_id,
            relations=["category", "items", "tags"]
        )
```

## Controller Template

```python
# app/controllers/example_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.database import get_db
from app.schemas.common import ResponseBuilder, SuccessResponse
from app.schemas.examples.request import ExampleCreateRequest, ExampleUpdateRequest
from app.schemas.examples.response import ExampleResponse
from app.services.example_service import ExampleService
from app.utils.auth import get_current_user
from app.utils.tracing import get_trace_logger

logger = get_trace_logger("example-controller")
router = APIRouter()

# CREATE
@router.post("/", response_model=SuccessResponse[ExampleResponse])
async def create_example(
    *,
    db: AsyncSession = Depends(get_db),
    example_data: ExampleCreateRequest,
    current_user = Depends(get_current_user)
) -> SuccessResponse[ExampleResponse]:
    """Create a new example."""
    logger.info(f"Creating example: {example_data.name}")

    example_service = ExampleService()
    example = await example_service.create_example_with_relationships(
        db,
        example_data.model_dump()
    )

    return ResponseBuilder.success(
        message="Example created successfully",
        data=example
    )

# READ ALL
@router.get("/", response_model=SuccessResponse[List[ExampleResponse]])
async def get_examples(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> SuccessResponse[List[ExampleResponse]]:
    """Get all examples with pagination."""
    example_service = ExampleService()
    examples = await example_service.get_all(db, skip=skip, limit=limit)

    return ResponseBuilder.success(
        message="Examples retrieved successfully",
        data=examples
    )

# READ ONE
@router.get("/{example_id}", response_model=SuccessResponse[ExampleResponse])
async def get_example(
    *,
    db: AsyncSession = Depends(get_db),
    example_id: str
) -> SuccessResponse[ExampleResponse]:
    """Get a specific example by ID."""
    example_service = ExampleService()
    example = await example_service.get_examples_with_relationships(db, example_id)

    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Example not found"
        )

    return ResponseBuilder.success(
        message="Example retrieved successfully",
        data=example
    )

# UPDATE
@router.put("/{example_id}", response_model=SuccessResponse[ExampleResponse])
async def update_example(
    *,
    db: AsyncSession = Depends(get_db),
    example_id: str,
    example_data: ExampleUpdateRequest,
    current_user = Depends(get_current_user)
) -> SuccessResponse[ExampleResponse]:
    """Update an example."""
    logger.info(f"Updating example: {example_id}")

    example_service = ExampleService()
    example = await example_service.update(
        db,
        db_obj_id=example_id,
        obj_in=example_data.model_dump(exclude_unset=True)
    )

    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Example not found"
        )

    return ResponseBuilder.success(
        message="Example updated successfully",
        data=example
    )

# DELETE
@router.delete("/{example_id}", response_model=SuccessResponse[None])
async def delete_example(
    *,
    db: AsyncSession = Depends(get_db),
    example_id: str,
    current_user = Depends(get_current_user),
    hard_delete: bool = False
) -> SuccessResponse[None]:
    """Delete an example."""
    logger.info(f"Deleting example: {example_id}")

    example_service = ExampleService()
    example = await example_service.delete(db, id=example_id, hard_delete=hard_delete)

    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Example not found"
        )

    return ResponseBuilder.deleted(message="Example deleted successfully")
```

## Schema Templates

### Request Schema
```python
# app/schemas/examples/request.py
from pydantic import Field
from app.schemas.common.base_schema import BaseSchema
from typing import Optional, List

class ExampleCreateRequest(BaseSchema):
    """Schema for creating an example."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[List[dict]] = None
    items: Optional[List[dict]] = None

class ExampleUpdateRequest(BaseSchema):
    """Schema for updating an example."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    updated_at: Optional[str] = Field(None, description="Required for optimistic locking")
```

### Response Schema
```python
# app/schemas/examples/response.py
from pydantic import Field
from app.schemas.common.base_schema import BaseSchema
from typing import Optional, List
from datetime import datetime

class ExampleResponse(BaseSchema):
    """Schema for example response."""
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    category_id: Optional[str] = None
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None
    tags: Optional[List[dict]] = None
    items: Optional[List[dict]] = None
```

### Converter
```python
# app/schemas/examples/converters.py
from app.models.example import Example
from app.schemas.examples.response import ExampleResponse

def convert_example_model_to_response(example: Example) -> ExampleResponse:
    """Convert Example model to ExampleResponse."""
    return ExampleResponse(
        id=str(example.id),
        name=example.name,
        description=example.description,
        is_active=example.is_active,
        category_id=str(example.category_id) if example.category_id else None,
        created_at=example.created_at.isoformat() if example.created_at else "",
        updated_at=example.updated_at.isoformat() if example.updated_at else "",
        deleted_at=example.deleted_at.isoformat() if example.deleted_at else None,
        tags=[{"id": str(tag.id), "name": tag.name} for tag in example.tags] if hasattr(example, 'tags') and example.tags else None,
        items=[{"id": str(item.id), "name": item.name} for item in example.items] if hasattr(example, 'items') and example.items else None,
    )
```

## Test Template

```python
# tests/api/test_example_crud_tdd.py
import pytest
import uuid
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.example import Example
from app.models.user import User
from app.services.example_service import ExampleService
from tests.api.conftest import PostTestFixtures

class TestExampleCRUDTDD(PostTestFixtures):
    """TDD Test class for Example CRUD operations."""

    @pytest.fixture
    async def test_example(self, db: AsyncSession, test_user: User) -> Example:
        """Create a test example."""
        unique_id = str(uuid.uuid4())[:8]
        example = Example(
            name=f"test_example_{unique_id}",
            description="Test example description",
            is_active=True
        )
        db.add(example)
        await db.commit()
        await db.refresh(example)
        return example

    # CREATE Tests
    def test_create_example_success(self, client: TestClient, test_user: User):
        """Test creating an example successfully."""
        example_data = {
            "name": f"Test Example {str(uuid.uuid4())[:8]}",
            "description": "Test example description"
        }

        response = client.post(
            "/api/v1/examples/",
            json=example_data,
            headers={"Authorization": f"Bearer {self._create_test_token(test_user)}"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == example_data["name"]

    def test_create_example_unauthorized(self, client: TestClient):
        """Test creating an example without authentication."""
        example_data = {"name": "Test Example", "description": "Test"}

        response = client.post("/api/v1/examples/", json=example_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # READ Tests
    def test_get_examples_success(self, client: TestClient):
        """Test getting all examples."""
        response = client.get("/api/v1/examples/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_example_by_id_success(self, client: TestClient, test_example: Example):
        """Test getting an example by ID."""
        response = client.get(f"/api/v1/examples/{test_example.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["id"] == test_example.id

    def test_get_example_not_found(self, client: TestClient):
        """Test getting a non-existent example."""
        response = client.get("/api/v1/examples/nonexistent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # UPDATE Tests
    def test_update_example_success(self, client: TestClient, test_user: User, test_example: Example):
        """Test updating an example."""
        update_data = {
            "name": "Updated Example Name",
            "description": "Updated description"
        }

        response = client.put(
            f"/api/v1/examples/{test_example.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self._create_test_token(test_user)}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["name"] == update_data["name"]

    # DELETE Tests
    def test_delete_example_success(self, client: TestClient, test_user: User, test_example: Example):
        """Test deleting an example."""
        response = client.delete(
            f"/api/v1/examples/{test_example.id}",
            headers={"Authorization": f"Bearer {self._create_test_token(test_user)}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None

    # Service Layer Tests
    async def test_service_layer_integration(self, db: AsyncSession, test_user: User):
        """Test service layer integration."""
        example_service = ExampleService()

        example_data = {
            "name": f"Service Test Example {str(uuid.uuid4())[:8]}",
            "description": "Service test"
        }

        example = await example_service.create(db, obj_in=example_data)
        assert example is not None
        assert example.name == example_data["name"]
```

## Common Patterns

### 1. Search with Pagination
```python
# Repository
async def search_examples(self, db, search_term: str, skip: int = 0, limit: int = 100):
    """Search examples with pagination."""
    query = select(Example).where(
        Example.name.ilike(f"%{search_term}%")
    ).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

# Controller
@router.get("/search", response_model=SuccessResponse[List[ExampleResponse]])
async def search_examples(
    *,
    db: AsyncSession = Depends(get_db),
    q: str,
    skip: int = 0,
    limit: int = 100
):
    """Search examples."""
    example_service = ExampleService()
    examples = await example_service.repository.search_examples(db, q, skip, limit)
    return ResponseBuilder.success(message="Search completed", data=examples)
```

### 2. Bulk Operations
```python
# Service
async def bulk_create_examples(self, db, examples_data: List[dict]):
    """Create multiple examples."""
    examples = []
    for data in examples_data:
        example = Example(**data)
        db.add(example)
        examples.append(example)
    await db.commit()
    return examples

async def bulk_update_examples(self, db, updates: List[dict]):
    """Update multiple examples."""
    for update in updates:
        await self.update(db, db_obj_id=update["id"], obj_in=update["data"])
```

### 3. Soft Delete with Cascade
```python
# Service
async def soft_delete_with_cascade(self, db, example_id: str):
    """Soft delete example and related items."""
    example = await self.get_by_id(db, id=example_id)
    if example:
        # Soft delete related items
        for item in example.items:
            item.deleted_at = datetime.utcnow()

        # Soft delete the example
        return await self.delete(db, id=example_id, hard_delete=False)
    return None
```

This quick reference provides templates and patterns for common CRUD operations. Use these as starting points and customize them for your specific needs.
