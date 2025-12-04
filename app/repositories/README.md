# Repositories Module Organization

This module follows a clean, organized structure that separates concerns and follows SOLID principles.

## Structure

```
app/repositories/
├── __init__.py              # Main module exports
├── factory.py               # Repository factory for dependency injection
├── base_repository.py       # Legacy base repository (for backward compatibility)
├── core/                    # Core repository components
│   ├── __init__.py
│   ├── interfaces.py        # Abstract base classes/interfaces
│   ├── base_repository_impl.py    # Base repository implementation
│   ├── full_repository_impl.py    # Full repository with relationships
│   ├── query_builder.py           # Query building utilities
│   ├── optimistic_lock_validator.py # Optimistic locking validation
│   └── relationship_handler.py     # Relationship management utilities
└── concrete/                # Concrete model-specific repositories
    ├── __init__.py
    ├── user_repository.py   # User model repository
    └── post_repository.py   # Post model repository
```

## Core Components (`core/`)

The core folder contains the foundational components of the repository pattern:

- **`interfaces.py`**: Abstract base classes defining contracts for different repository capabilities
- **`base_repository_impl.py`**: Concrete implementation of basic CRUD operations
- **`full_repository_impl.py`**: Extended implementation with relationship management
- **`query_builder.py`**: Utility for building database queries
- **`optimistic_lock_validator.py`**: Handles optimistic locking validation
- **`relationship_handler.py`**: Manages relationship operations

## Concrete Repositories (`concrete/`)

The concrete folder contains model-specific repository implementations:

- **`user_repository.py`**: User-specific database operations
- **`post_repository.py`**: Post-specific database operations with relationships

## Factory Pattern

The `factory.py` file provides a centralized way to create repository instances with proper dependency injection, following the Dependency Inversion Principle.

## Usage

### Creating Repositories

```python
from app.repositories.factory import repository_factory

# Create a base repository
user_repo = repository_factory.create_base_repository(User)

# Create a full repository with relationship capabilities
post_repo = repository_factory.create_full_repository(Post)
```

### Using Concrete Repositories

```python
from app.repositories.concrete import UserRepository, PostRepository

# Use the concrete repositories
user_repo = UserRepository()
post_repo = PostRepository()
```

### Importing Components

```python
# Import from main module
from app.repositories import (
    RepositoryFactory,
    BaseRepositoryImpl,
    UserRepository,
    PostRepository
)

# Import from specific submodules
from app.repositories.core import BaseRepository, OptimisticLockRepository
from app.repositories.concrete import user_repository
```

## Benefits

1. **Separation of Concerns**: Core logic is separated from concrete implementations
2. **SOLID Principles**: Follows Single Responsibility and Dependency Inversion principles
3. **Maintainability**: Easy to modify core components without affecting concrete repositories
4. **Testability**: Each component can be tested independently
5. **Extensibility**: Easy to add new repository types or modify existing ones
6. **Clean Architecture**: Clear boundaries between different layers of abstraction
