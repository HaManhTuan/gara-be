# Architecture Guide

This document provides a comprehensive overview of the FastAPI MVC application architecture, design patterns, and system components.

## Architecture Overview

This project follows the Model-View-Controller (MVC) architecture with an additional service layer, providing a clean separation of concerns and maintainable code structure.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Controllers   │────│    Services     │────│  Repositories   │
│   (FastAPI)     │    │ (Business Logic)│    │ (Data Access)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Schemas      │    │     Models      │    │    Database     │
│  (Pydantic)     │    │  (SQLAlchemy)   │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Application Layers

### 1. Controller Layer (`app/controllers/`)

**Purpose:** Handles HTTP requests and responses, validates input, and delegates business logic to services.

**Responsibilities:**
- HTTP request/response handling
- Input validation using Pydantic models
- Authentication and authorization
- Error handling and status codes
- Delegating business logic to services

**Example:**
```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.user_service import UserService
from app.schemas.users import UserCreateRequest, UserResponse, convert_user_create_request_to_internal

router = APIRouter()

@router.post("/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    user_service: UserService = Depends()
):
    # Convert request schema to internal schema
    internal_data = convert_user_create_request_to_internal(user_data)
    return await user_service.create_user(internal_data)
```

### 2. Service Layer (`app/services/`)

**Purpose:** Contains business logic, orchestrates operations using repositories, and handles data transformations.

**Responsibilities:**
- Business logic implementation
- Data validation and transformation
- Orchestrating multiple repository operations
- Handling complex business rules
- Transaction management

**Example:**
```python
from app.repositories.concrete.user_repository import UserRepository
from app.schemas.users import UserCreate, UserResponse

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        # Business logic
        if await self.user_repo.exists_by_email(user_data.email):
            raise ValueError("Email already exists")

        # Create user using internal schema
        user = await self.user_repo.create(user_data)
        return UserResponse.from_orm(user)
```

### 3. Repository Layer (`app/repositories/`)

**Purpose:** Handles data access operations, interacts with the database via SQLAlchemy, and provides CRUD operations with organized structure.

**Architecture:** SOLID principles with organized folder structure:
```
app/repositories/
├── core/                       # Core interfaces and base implementations
│   ├── __init__.py
│   ├── interfaces.py           # Abstract base classes
│   ├── base_repository_impl.py # Base repository implementation
│   ├── full_repository_impl.py # Full repository with relationships
│   ├── query_builder.py        # Query building utilities
│   ├── optimistic_lock_validator.py # Optimistic locking
│   └── relationship_handler.py # Relationship management
├── concrete/                   # Model-specific implementations
│   ├── __init__.py
│   ├── user_repository.py      # User-specific repository
│   └── post_repository.py      # Post-specific repository
├── factory.py                  # Repository factory
└── __init__.py                 # Main exports
```

**Responsibilities:**
- Database operations (CRUD)
- Query optimization
- Data mapping between models and schemas
- Database-specific logic
- Connection management
- Optimistic locking
- Relationship handling
- Soft deletion support

**Example:**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.users import UserCreate
from app.repositories.core import BaseRepositoryImpl
from app.repositories.factory import repository_factory

class UserRepository(BaseRepositoryImpl[User]):
    """Repository for User model extending from base repository"""

    def __init__(self) -> None:
        # Create base repository using factory
        base_repo = repository_factory.create_base_repository(User)
        super().__init__(
            model=User,
            query_builder=base_repo.query_builder,
            optimistic_lock_validator=base_repo.optimistic_lock_validator,
        )

    # User-specific methods
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()
```

### 4. Model Layer (`app/models/`)

**Purpose:** Defines SQLAlchemy ORM models representing database structure.

**Responsibilities:**
- Database table definitions
- Relationships between entities
- Data validation at model level
- Database constraints

**Example:**
```python
from sqlalchemy import Column, String, Boolean
from app.models.base_model import BaseModel

class User(BaseModel):
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
```

### 5. Schema Layer (`app/schemas/`)

**Purpose:** Defines Pydantic models for request/response validation and serialization with clear separation of concerns.

**Architecture:** Three-layer schema pattern for clean data flow:
- **Request Schemas** (Data In): What we receive from API clients
- **Internal Schemas** (Data Using): What we use internally in the application
- **Response Schemas** (Data Out): What we send back to API clients

**Folder Structure:**
```
app/schemas/
├── common/
│   ├── __init__.py
│   └── base_schema.py          # BaseSchema class
├── users/
│   ├── __init__.py
│   ├── schema.py              # Internal schemas (UserBase, UserCreate, UserUpdate, UserInDB)
│   ├── request.py             # Request/Response schemas (UserRegistrationRequest, UserResponse, etc.)
│   └── converters.py           # User schema converters
├── posts/
│   ├── __init__.py
│   ├── schema.py              # Internal schemas (PostCreate, PostUpdate, TagCreate, etc.)
│   ├── request.py             # Request/Response schemas (PostCreateRequest, PostResponse, etc.)
│   └── converters.py           # Post schema converters
└── __init__.py                # Main exports
```

**Naming Conventions:**
- **`schema.py`** - Contains internal schemas used within the application
- **`request.py`** - Contains request and response schemas for API
- **`converters.py`** - Contains conversion functions between request and internal schemas
- **`__init__.py`** - Exports all schemas and converters for easy importing

**Responsibilities:**
- Input validation with API-specific constraints
- Response serialization with client-safe data
- Data transformation between layers
- Schema conversion utilities
- API documentation generation

**Example - Request Schema (API Input):**
```python
class UserRegistrationRequest(BaseSchema):
    """Schema for user registration request from API"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
```

**Example - Internal Schema (Application Logic):**
```python
class UserCreate(UserBase):
    """Schema for user creation used internally in the application"""
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    is_superuser: bool = False
```

**Example - Response Schema (API Output):**
```python
class UserResponse(BaseSchema):
    """Schema for user response to API clients"""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    # Note: No password field for security
```

**Example - Schema Converter:**
```python
def convert_user_registration_to_internal(request: UserRegistrationRequest) -> UserCreate:
    """Convert user registration request to internal user creation schema"""
    return UserCreate(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=None,
        is_superuser=False,
    )
```

**Data Flow:**
```
API Request → Request Schema → Converter → Internal Schema → Service/Repository
                                                                    ↓
API Response ← Response Schema ← Converter ← Internal Schema ← Database
```

## Schema Architecture Patterns

### Three-Layer Schema Pattern

The application implements a sophisticated three-layer schema architecture that provides clear separation of concerns and maintains data integrity across different application layers.

#### Layer 1: Request Schemas (Data In)
- **Purpose**: Define the structure of data received from API clients
- **Location**: `app/schemas/{entity}/request.py`
- **Characteristics**:
  - API-specific validation rules
  - Client-facing field names
  - Input constraints and requirements
  - No internal application logic

#### Layer 2: Internal Schemas (Data Using)
- **Purpose**: Define the structure of data used internally within the application
- **Location**: `app/schemas/{entity}/schema.py`
- **Characteristics**:
  - Application-specific structure
  - Internal field requirements
  - Business logic constraints
  - Optimized for service/repository operations

#### Layer 3: Response Schemas (Data Out)
- **Purpose**: Define the structure of data sent back to API clients
- **Location**: `app/schemas/{entity}/request.py` (alongside request schemas)
- **Characteristics**:
  - Client-safe data (no sensitive fields)
  - Formatted timestamps and relationships
  - Optimized for API responses
  - Security-focused design

### Schema Conversion Pattern

**Purpose**: Convert between different schema layers while maintaining data integrity.

**Implementation**:
- **Location**: `app/schemas/{entity}/converters.py`
- **Functions**: `convert_{source}_to_{target}()` naming convention
- **Features**:
  - Type-safe conversions
  - Data validation during conversion
  - Nested object handling
  - Error handling for invalid conversions

**Example Flow**:
```python
# API Request → Internal Schema
request_data = UserRegistrationRequest(...)
internal_data = convert_user_registration_to_internal(request_data)

# Internal Schema → Database Model
user = await user_repository.create(internal_data)

# Database Model → Response Schema
response_data = UserResponse.from_orm(user)
```

### Benefits of Schema Architecture

1. **Security**: Response schemas exclude sensitive data
2. **Flexibility**: Can change internal structure without affecting API
3. **Maintainability**: Clear boundaries between layers
4. **Type Safety**: Full type checking across all layers
5. **API Evolution**: Can evolve API independently from internal logic
6. **Testing**: Easy to test each layer independently

## Configuration Architecture

### Settings Management

The application uses a settings-based configuration pattern:

- Environment variables are loaded through Pydantic Settings
- Default values are provided in `app/config/settings.py`
- Override defaults in `.env` file
- Type validation and conversion

### Database Configuration

**Dual Engine Architecture:**
- **Async Engine**: For application runtime operations
- **Sync Engine**: For migrations and scripts
- Automatic URL conversion between protocols

**Connection Management:**
- Context managers for session management
- Automatic cleanup and error handling
- Support for both sync and async operations

## API Structure

### RESTful Design

The API follows RESTful design principles with versioning:

```
/api/v1/
├── health/          # Health check endpoints
├── users/           # User management
├── auth/            # Authentication endpoints
└── ...              # Other resource endpoints
```

### API Documentation

- **Swagger UI**: `/docs` - Interactive API documentation
- **ReDoc**: `/redoc` - Alternative documentation format
- **OpenAPI Schema**: `/openapi.json` - Machine-readable schema

## Background Processing

### Celery Workers

**Purpose:** Handle background tasks and long-running operations.

**Features:**
- Asynchronous task processing
- Task queuing with Redis
- Retry mechanisms
- Task monitoring

### Scheduled Jobs

**Purpose:** Handle periodic tasks and scheduled operations.

**Features:**
- APScheduler integration
- Cron-like scheduling
- Job persistence
- Error handling and logging

## Middleware Architecture

### Custom Middleware

1. **Context Middleware**: Manages request context and tracing
2. **Logging Middleware**: Handles request/response logging
3. **Authentication Middleware**: JWT token validation

### Middleware Stack

```
Request → Context Middleware → Logging Middleware → Auth Middleware → Route Handler
```

## Security Architecture

### Authentication

- **JWT-based authentication**
- **Token expiration handling**
- **Secure password hashing**
- **Role-based access control**

### Security Features

- **CORS configuration**
- **Input validation**
- **SQL injection prevention**
- **XSS protection**

## Logging Architecture

### Logging System

- **Structured logging** with Loguru
- **Multiple log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **File and console output**
- **Request/response logging**
- **Error tracking and reporting**

### Log Configuration

```python
# Logging levels and formats
LOG_LEVEL = "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
LOG_FILE_PATH = "logs/app.log"
```

## Testing Architecture

### Test Structure

- **API Testing**: Comprehensive endpoint testing
- **Unit Testing**: Individual component testing
- **Integration Testing**: Cross-component testing
- **AAA Pattern**: Arrange-Act-Assert for clarity

### Test Configuration

- **Test Database**: SQLite in-memory for speed
- **Test Fixtures**: Reusable test data and setup
- **Coverage Reporting**: Code coverage analysis
- **Parallel Testing**: Concurrent test execution

## Deployment Architecture

### Docker Support

- **Multi-container setup** with Docker Compose
- **PostgreSQL database** container
- **Redis cache** container
- **Application container** with FastAPI
- **Worker container** for background tasks

### Production Considerations

- **Environment-specific configurations**
- **Database connection pooling**
- **Load balancing support**
- **Health checks and monitoring**
- **Log aggregation and monitoring**

## Development Guidelines

### Code Organization

1. **Separation of Concerns**: Each layer has specific responsibilities
2. **Dependency Injection**: Services and repositories are injected
3. **Interface Segregation**: Clear interfaces between layers
4. **Single Responsibility**: Each class has one reason to change

### Best Practices

1. **Type Hints**: Use type annotations throughout
2. **Error Handling**: Comprehensive error handling at each layer
3. **Logging**: Log important operations and errors
4. **Testing**: Write tests for all business logic
5. **Documentation**: Document complex business rules

### Design Patterns Used

- **Repository Pattern**: Data access abstraction with organized structure
- **Service Layer Pattern**: Business logic encapsulation
- **Dependency Injection**: Loose coupling between components
- **Factory Pattern**: Object creation abstraction for repositories
- **Observer Pattern**: Event handling and notifications
- **Schema Separation Pattern**: Three-layer schema architecture (Request → Internal → Response)
- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Optimistic Locking Pattern**: Concurrency control using version fields
- **Soft Delete Pattern**: Logical deletion using timestamps
- **Relationship Management Pattern**: Handling complex entity relationships

## Scalability Considerations

### Horizontal Scaling

- **Stateless application design**
- **Database connection pooling**
- **Redis for session storage**
- **Load balancer compatibility**

### Performance Optimization

- **Async/await patterns**
- **Database query optimization**
- **Caching strategies**
- **Connection pooling**
- **Background task processing**

This architecture provides a solid foundation for building scalable, maintainable web applications with clear separation of concerns and robust error handling.
