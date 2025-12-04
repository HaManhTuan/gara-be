# Relational CRUD Operations

This document explains how to use the relational CRUD operations in the FastAPI MVC application. The system supports creating, updating, and deleting records with nested relationships using a simple, intuitive interface.

## Overview

The relational CRUD system automatically handles:
- **One-to-One (1-1)**: Direct relationships between two models
- **One-to-Many (1-n)**: Parent-child relationships
- **Many-to-Many (n-n)**: Many-to-many relationships with junction tables
- **Multi-level nesting**: Nested relationships within nested relationships
- **Optimistic locking**: Prevents lost updates across all related records
- **Soft deletion**: Cascade soft deletes to related records

## Interface Design

All relational operations use the `obj_in` parameter with nested relationship data:

```python
# Example: Create post with tags and comments
obj_in = {
    "title": "My Post",
    "content": "Post content",
    "tags": [{"name": "python"}, {"name": "fastapi"}],  # 1-n or n-n
    "author": {"id": "user-123"},  # 1-1 or reference
    "comments": [
        {
            "text": "Great post!",
            "replies": [{"text": "Thanks!"}]  # Multi-level nesting
        }
    ]
}

# Repository/Service automatically detects and handles relationships
result = await repository.create_with_relations(db, obj_in=obj_in)
```

## Repository Methods

### BaseRepository Extensions

The `BaseRepository` class has been extended with relationship methods:

#### `create_with_relations(db, obj_in)`
Creates a record with nested relationships.

```python
# Create post with tags and comments
post_data = {
    "title": "My Post",
    "content": "Post content",
    "author_id": "user-123",
    "tags": [
        {"name": "python", "description": "Python programming"},
        {"name": "fastapi", "description": "FastAPI framework"}
    ],
    "comments": [
        {"text": "Great post!"},
        {"text": "Very informative"}
    ]
}

post = await post_repository.create_with_relations(db, obj_in=post_data)
```

#### `update_with_optimistic_lock_and_relations(db, id, obj_in, sync_mode="merge")`
Updates a record with relationship synchronization and optimistic locking.

```python
# Update post and manage tags with optimistic locking
update_data = {
    "title": "Updated Title",
    "tags": [
        {
            "id": "existing-tag-id",
            "name": "updated-python",
            "description": "Updated description",
            "updated_at": "2023-01-01T12:00:00Z"  # Optimistic lock for tag
        },
        {"name": "new-tag", "description": "New tag"}  # Create new tag
    ],
    "updated_at": "2023-01-01T12:00:00Z"  # Optimistic lock for post
}

post = await post_repository.update_with_optimistic_lock_and_relations(
    db, id=post_id, obj_in=update_data, sync_mode="replace"
)
```

**Sync Modes:**
- `"add"`: Add new relationships without removing existing ones
- `"replace"`: Replace all relationships with new ones
- `"merge"`: Update existing relationships and add new ones (default)

#### `delete_with_cascade(db, id, hard_delete=False)`
Deletes a record with cascade options.

```python
# Soft delete with cascade (default)
post = await post_repository.delete_with_cascade(db, id=post_id, hard_delete=False)

# Hard delete with cascade
post = await post_repository.delete_with_cascade(db, id=post_id, hard_delete=True)
```

**Cascade Behavior:**
- **1-n relationships**: Cascade deletes/soft deletes all children
- **n-n relationships**: Clears junction table entries (doesn't delete related records)
- **1-1 relationships**: Cascade deletes/soft deletes the related object
- **n-1 relationships**: Doesn't cascade delete the parent
- **Recursive**: Handles nested relationships at multiple levels

## Service Methods

### BaseService Extensions

The `BaseService` class provides business logic wrappers:

#### `create_with_nested(db, obj_in)`
Creates records with validation and logging.

```python
post_service = PostService()

post = await post_service.create_with_nested(db, obj_in=post_data)
```

#### `update_with_nested(db, id, obj_in, sync_mode="merge")`
Updates records with business rules and optimistic locking.

```python
post = await post_service.update_with_nested(
    db,
    id=post_id,
    obj_in=update_data,
    sync_mode="replace"  # or "add", "merge"
)
```

#### `delete_cascade(db, id, hard_delete=False)`
Deletes records with permission checks.

```python
post = await post_service.delete_cascade(db, id=post_id, hard_delete=False)
```

## Relationship Types

### One-to-Many (1-n)

When creating a parent with children:

```python
post_data = {
    "title": "My Post",
    "content": "Post content",
    "author_id": "user-123",
    "comments": [  # Children
        {"text": "First comment"},
        {"text": "Second comment"}
    ]
}
```

### Many-to-One (n-1)

When creating a child referencing a parent:

```python
# Case 1: Reference existing parent
comment_data = {
    "text": "My comment",
    "post": {"id": "existing-post-123"}  # Just link to existing
}

# Case 2: Create new parent inline
comment_data = {
    "text": "My comment",
    "post": {  # Create new parent first
        "title": "New Post",
        "content": "Content",
        "author_id": "user-123"
    }
}
```

### Many-to-Many (n-n)

When creating records with many-to-many relationships:

```python
post_data = {
    "title": "My Post",
    "content": "Post content",
    "author_id": "user-123",
    "tags": [  # Many-to-many
        {"name": "python"},
        {"name": "fastapi"}
    ]
}
```

### Multi-level Nesting

Support for nested relationships within nested relationships:

```python
post_data = {
    "title": "My Post",
    "content": "Post content",
    "author_id": "user-123",
    "comments": [
        {
            "text": "Main comment",
            "replies": [  # Nested within comment
                {"text": "Reply 1"},
                {"text": "Reply 2"}
            ]
        }
    ]
}
```

## Optimistic Locking

The system supports optimistic locking across all related records:

```python
# Collect all updated_at timestamps
expected_timestamps = {
    "post-123": "2023-01-01T12:00:00Z",
    "comment-456": "2023-01-01T11:30:00Z",
    "tag-789": "2023-01-01T10:00:00Z"
}

# Validate all locks before update
await validate_all_optimistic_locks(db, expected_timestamps)

# Update with relationships
update_data = {
    "title": "Updated Title",
    "comments": [
        {
            "id": "comment-456",
            "text": "Updated comment",
            "updated_at": "2023-01-01T11:30:00Z"
        }
    ],
    "updated_at": "2023-01-01T12:00:00Z"
}

post = await post_repository.update_with_optimistic_lock_and_relations(db, id=post_id, obj_in=update_data)
```

### Optimistic Locking Features

1. **Automatic Validation**: All `updated_at` timestamps are automatically validated
2. **Cross-Record Locking**: Validates locks for main record and all related records
3. **Conflict Detection**: Raises `HTTPException(409)` if any record was modified
4. **Timestamp Tolerance**: Allows 1-second tolerance for clock differences
5. **Error Handling**: Provides clear error messages for lock conflicts

### Sync Modes

The `update_with_optimistic_lock_and_relations` method supports three sync modes:

#### Add Mode (`sync_mode="add"`)
Adds new relationships without removing existing ones:

```python
update_data = {
    "title": "Updated Post",
    "tags": [{"name": "additional-tag"}],  # Adds to existing tags
    "updated_at": current_timestamp
}

post = await repository.update_with_optimistic_lock_and_relations(
    db, id=post_id, obj_in=update_data, sync_mode="add"
)
```

#### Replace Mode (`sync_mode="replace"`)
Replaces all relationships with new ones:

```python
update_data = {
    "title": "Updated Post",
    "tags": [{"name": "new-tag-1"}, {"name": "new-tag-2"}],  # Replaces all tags
    "updated_at": current_timestamp
}

post = await repository.update_with_optimistic_lock_and_relations(
    db, id=post_id, obj_in=update_data, sync_mode="replace"
)
```

#### Merge Mode (`sync_mode="merge"`) - Default
Updates existing relationships and adds new ones:

```python
update_data = {
    "title": "Updated Post",
    "tags": [
        {
            "id": "existing-tag-id",
            "name": "updated-tag",
            "updated_at": tag_timestamp
        },
        {"name": "new-tag"}  # Adds new tag
    ],
    "updated_at": current_timestamp
}

post = await repository.update_with_optimistic_lock_and_relations(
    db, id=post_id, obj_in=update_data, sync_mode="merge"
)
```

## Controller Usage

### FastAPI Endpoints

The controller layer provides REST endpoints for relational operations:

```python
@router.post("/", response_model=PostResponse)
async def create_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_in: PostCreate,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new post with nested relationships"""
    post_service = PostService()

    # Convert Pydantic model to dict
    post_data = post_in.dict()
    post_data["author_id"] = current_user.id

    # Create with relationships
    post = await post_service.create_with_nested(db, obj_in=post_data)

    return {
        "message": "Post created successfully",
        "data": post.to_dict()
    }
```

### Request Examples

#### Create Post with Tags and Comments

```json
POST /api/v1/posts/
{
    "title": "My First Post",
    "content": "This is my first post",
    "tags": [
        {"name": "python", "description": "Python programming"},
        {"name": "fastapi", "description": "FastAPI framework"}
    ],
    "comments": [
        {"text": "Great post!"},
        {"text": "Very informative"}
    ]
}
```

#### Update Post with Optimistic Locking

```json
PUT /api/v1/posts/123
{
    "title": "Updated Title",
    "tags": [
        {"name": "python"},
        {"name": "django"}
    ],
    "updated_at": "2023-01-01T12:00:00Z"
}
```

## Naming Conventions

The system uses consistent naming conventions for automatic discovery:

### Database to Code Mapping
- **Table**: `posts` (lowercase plural)
- **Model**: `Post` (PascalCase singular) in `app/models/post.py`
- **Repository**: `PostRepository` in `app/repositories/post_repository.py`
- **Service**: `PostService` in `app/services/post_service.py`
- **Schema**: `PostCreate`, `PostUpdate`, `PostResponse` in `app/schemas/post_schema.py`
- **Controller**: `PostController` in `app/controllers/post_controller.py`

### Relationship Naming
- **One-to-Many**: Parent has plural name, e.g., `user.posts` (collection)
- **Many-to-One**: Child has singular name, e.g., `post.author` (single object)
- **Many-to-Many**: Both sides have plural names, e.g., `post.tags`, `tag.posts`
- **Junction Table**: Combines both table names alphabetically, e.g., `post_tags`

### Legacy Database Support

For databases with non-standard table names, models can override `__tablename__`:

```python
# Example: Legacy database table is 'tbl_posts' instead of 'posts'
class Post(BaseModel):
    __tablename__ = "tbl_posts"  # Override default convention

    title = Column(String)
    content = Column(String)
```

Application code still follows standard conventions:
- Model file: `app/models/post.py`
- Repository: `app/repositories/post_repository.py` (PostRepository)
- Service: `app/services/post_service.py` (PostService)
- Schemas: `app/schemas/post_schema.py` (PostCreate, PostUpdate)

## Error Handling

The system provides comprehensive error handling:

### Optimistic Lock Conflicts
```python
# HTTP 409 Conflict
{
    "detail": "Record was modified by another process. Please refresh and try again."
}
```

### Validation Errors
```python
# HTTP 422 Unprocessable Entity
{
    "detail": [
        {
            "loc": ["body", "title"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

### Not Found Errors
```python
# HTTP 404 Not Found
{
    "detail": "Record not found"
}
```

## Best Practices

1. **Always use transactions**: All relational operations are wrapped in transactions
2. **Validate input data**: Use Pydantic schemas for validation
3. **Handle optimistic locking**: Always include `updated_at` for updates
4. **Use soft deletes**: Prefer soft deletes over hard deletes for data integrity
5. **Log operations**: All operations are logged for debugging and auditing
6. **Test thoroughly**: Use the provided test suite to verify functionality

## Testing

The system includes comprehensive tests covering:
- All relationship types (1-1, 1-n, n-n)
- Multi-level nesting
- Optimistic locking
- Soft deletion with cascade
- Error scenarios

Run tests with:
```bash
poetry run pytest tests/test_relational_crud.py -v
```

## Migration

The system includes Alembic migrations for all new models and relationships:

```bash
# Generate migration
poetry run alembic revision --autogenerate -m "Add relational models"

# Apply migration
poetry run alembic upgrade head
```

## Performance Considerations

1. **Eager loading**: Use `selectinload` or `joinedload` for relationships
2. **Batch operations**: Create multiple related records in single transaction
3. **Index optimization**: Ensure foreign keys are indexed
4. **Query optimization**: Use specific relationship loading strategies

## Troubleshooting

### Common Issues

1. **Missing relationships**: Ensure all models are imported in `alembic/env.py`
2. **Circular imports**: Use string references in relationship definitions
3. **Transaction issues**: Ensure all operations are within database transactions
4. **Optimistic lock failures**: Check `updated_at` timestamps are current

### Debug Mode

Enable debug logging to see relationship processing:

```python
import logging
logging.getLogger("repository").setLevel(logging.DEBUG)
logging.getLogger("service").setLevel(logging.DEBUG)
```
