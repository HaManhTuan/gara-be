# Model Relationship Manager

The Model Relationship Manager is a comprehensive system for managing model relationships as a graph structure. It discovers all models, builds relationship graphs, and provides utilities for navigating and managing nested object operations.

## Overview

The Model Relationship Manager provides:

- **Model Discovery**: Automatically discovers all models that inherit from `BaseModel`
- **Relationship Graph Building**: Creates a graph where models are nodes and relationships are edges
- **Path Finding**: Find paths between models through relationships
- **Cycle Detection**: Detect circular dependencies in the relationship graph
- **Dependency Analysis**: Understand which models depend on others
- **Nested Data Validation**: Separate main data from nested relationship data
- **Repository Integration**: Enhanced repository operations with relationship awareness

## Architecture

### Core Components

1. **ModelNode**: Represents a model in the relationship graph
2. **RelationshipEdge**: Represents a relationship between two models
3. **ModelRelationshipManager**: Main class that manages the graph
4. **ModelRelationshipExample**: Example implementation for repositories/services

### Graph Structure

```
Models (Nodes)          Relationships (Edges)
┌─────────┐             ┌─────────────────────┐
│  User   │────────────▶│  posts (one-to-many)│
└─────────┘             └─────────────────────┘
    │                           │
    │                           ▼
    │                      ┌─────────┐
    │                      │  Post   │
    │                      └─────────┘
    │                           │
    │                           │
    │                           ▼
    │                      ┌─────────┐
    │                      │ Comment │
    │                      └─────────┘
    │                           │
    │                           │
    │                           ▼
    │                      ┌─────────┐
    │                      │   Tag   │
    │                      └─────────┘
    │                           │
    │                           │
    │                           ▼
    └───────────────────────────┘
```

## Usage

### Basic Usage

```python
from app.utils.model_relationship_manager import initialize_model_relationships, get_model_relationship_manager
from app.utils.model_utils import get_model_class, get_relationship_type, get_related_model

# Initialize the manager (done automatically at app startup)
initialize_model_relationships()

# Get the manager instance
manager = get_model_relationship_manager()

# Get model information
user_class = get_model_class("User")
rel_type = get_relationship_type("User", "posts")
related_model = get_related_model("User", "posts")
```

### Repository Integration

```python
from app.utils.model_utils import validate_nested_data, get_model_manager
from app.models.user import User

class UserRepository:
    def __init__(self):
        self.model_class = User
        self.model_name = "User"
        self.manager = get_model_manager()

    async def create_with_relationships(self, db: AsyncSession, data: Dict[str, Any]) -> User:
        # Separate main data from nested relationship data
        main_data, nested_data = validate_nested_data(self.model_name, data)

        # Create main object
        user = User(**main_data)
        db.add(user)
        await db.flush()

        # Handle nested relationships
        if nested_data:
            await self._handle_nested_relationships(db, user, nested_data)

        await db.commit()
        return user

    async def _handle_nested_relationships(self, db: AsyncSession, user: User, nested_data: Dict[str, Any]):
        for rel_name, rel_data in nested_data.items():
            rel_type = get_relationship_type(self.model_name, rel_name)
            related_model = get_related_model(self.model_name, rel_name)

            if rel_type == RelationshipType.ONE_TO_MANY:
                await self._handle_one_to_many(db, user, rel_name, rel_data, related_model)
            # ... handle other relationship types
```

### Service Integration

```python
from app.utils.model_utils import get_model_dependencies, get_model_dependents, find_model_path

class UserService:
    def __init__(self):
        self.model_name = "User"

    def get_dependency_info(self) -> Dict[str, List[str]]:
        """Get information about model dependencies."""
        return {
            "dependencies": list(get_model_dependencies(self.model_name)),
            "dependents": list(get_model_dependents(self.model_name))
        }

    def find_path_to_model(self, target_model: str) -> Optional[List[str]]:
        """Find a path from User to another model."""
        path_edges = find_model_path(self.model_name, target_model)
        if not path_edges:
            return None

        path = [self.model_name]
        for edge in path_edges:
            path.append(edge.target_model)
        return path
```

## API Reference

### ModelRelationshipManager

#### Methods

- `initialize(models: Optional[List[Type[BaseModel]]] = None)`: Initialize the manager
- `get_model_node(model_name: str) -> Optional[ModelNode]`: Get a model node
- `get_model_class(model_name: str) -> Optional[Type[BaseModel]]`: Get a model class
- `get_relationships(model_name: str) -> Dict[str, RelationshipProperty]`: Get model relationships
- `find_path(source_model: str, target_model: str, max_depth: int = 5) -> Optional[List[RelationshipEdge]]`: Find path between models
- `detect_cycles() -> List[List[str]]`: Detect cycles in the graph
- `get_model_dependencies(model_name: str) -> Set[str]`: Get model dependencies
- `get_model_dependents(model_name: str) -> Set[str]`: Get model dependents
- `validate_nested_data(model_name: str, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]`: Validate nested data
- `get_graph_summary() -> Dict[str, Any]`: Get graph summary

### ModelNode

#### Properties

- `model_class: Type[BaseModel]`: The model class
- `table_name: str`: Database table name
- `relationships: Dict[str, RelationshipProperty]`: Model relationships
- `model_name: str`: Model class name

#### Methods

- `get_relationship_type(rel_name: str) -> Optional[RelationshipType]`: Get relationship type
- `get_related_model(rel_name: str) -> Optional[Type[BaseModel]]`: Get related model

### RelationshipEdge

#### Properties

- `source_model: str`: Source model name
- `target_model: str`: Target model name
- `relationship_name: str`: Relationship attribute name
- `relationship_type: RelationshipType`: Type of relationship
- `back_populates: Optional[str]`: Bidirectional relationship name
- `foreign_key: Optional[str]`: Foreign key column name
- `junction_table: Optional[str]`: Junction table for many-to-many
- `cascade_delete: bool`: Hard delete cascade
- `cascade_soft_delete: bool`: Soft delete cascade

#### Methods

- `is_bidirectional() -> bool`: Check if relationship is bidirectional
- `get_reverse_edge() -> Optional[RelationshipEdge]`: Get reverse edge

## Utility Functions

### Model Utils (`app/utils/model_utils.py`)

- `get_model_manager() -> ModelRelationshipManager`: Get global manager instance
- `get_model_class(model_name: str) -> Optional[Type[BaseModel]]`: Get model class
- `get_model_relationships(model_name: str) -> Dict[str, Any]`: Get model relationships
- `get_relationship_type(model_name: str, relationship_name: str) -> Optional[RelationshipType]`: Get relationship type
- `get_related_model(model_name: str, relationship_name: str) -> Optional[Type[BaseModel]]`: Get related model
- `find_model_path(source_model: str, target_model: str, max_depth: int = 5) -> Optional[List[RelationshipEdge]]`: Find path
- `get_model_dependencies(model_name: str) -> set[str]`: Get dependencies
- `get_model_dependents(model_name: str) -> set[str]`: Get dependents
- `validate_nested_data(model_name: str, data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]`: Validate nested data
- `is_relationship_field(model_name: str, field_name: str) -> bool`: Check if field is relationship
- `get_relationship_edges(model_name: str, direction: str = "outgoing") -> List[RelationshipEdge]`: Get edges
- `get_graph_summary() -> Dict[str, Any]`: Get graph summary
- `detect_relationship_cycles() -> List[List[str]]`: Detect cycles
- `get_model_info(model_name: str) -> Optional[Dict[str, Any]]`: Get model info

## Examples

### Creating Nested Objects

```python
# Create a user with posts, tags, and comments
user_data = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "password123",
    "posts": [
        {
            "title": "My First Post",
            "content": "This is my first post",
            "tags": [
                {"name": "python", "description": "Python programming"},
                {"name": "tutorial", "description": "Tutorial content"}
            ],
            "comments": [
                {
                    "text": "Great post!",
                    "replies": [
                        {"text": "Thanks!"}
                    ]
                }
            ]
        }
    ]
}

# Validate and separate data
main_data, nested_data = validate_nested_data("User", user_data)
# main_data: {"username": "john_doe", "email": "john@example.com", "password": "password123"}
# nested_data: {"posts": [...]}
```

### Path Finding

```python
# Find path from User to Comment
path = find_model_path("User", "Comment")
# Returns: [RelationshipEdge(User -> Post), RelationshipEdge(Post -> Comment)]

# Convert to model names
path_names = ["User"]
for edge in path:
    path_names.append(edge.target_model)
# Result: ["User", "Post", "Comment"]
```

### Dependency Analysis

```python
# Get what models User depends on
dependencies = get_model_dependencies("User")
# Returns: {"Post", "Comment", "Tag"}

# Get what models depend on User
dependents = get_model_dependents("User")
# Returns: {"Post", "Comment"}
```

### Cycle Detection

```python
# Detect cycles in the relationship graph
cycles = detect_relationship_cycles()
# Returns: [["User", "Post", "User"], ["Post", "Tag", "Post"]]
```

## Integration with Existing Code

### Repository Pattern

The model relationship manager integrates seamlessly with the existing repository pattern:

```python
class UserRepository(FullRepositoryImpl[User]):
    def __init__(self):
        super().__init__(...)
        self.model_name = "User"

    async def create_with_relations(self, db: AsyncSession, obj_in: Dict[str, Any]) -> User:
        # Use the manager to validate and separate data
        main_data, nested_data = validate_nested_data(self.model_name, obj_in)

        # Create main object
        user = User(**main_data)
        db.add(user)
        await db.flush()

        # Handle nested relationships using the manager
        if nested_data:
            await self._handle_nested_relationships(db, user, nested_data)

        return user
```

### Service Pattern

Services can use the manager for business logic:

```python
class UserService(BaseService[User, UserRepository]):
    def __init__(self):
        super().__init__(UserRepository())
        self.model_name = "User"

    def get_relationship_info(self) -> Dict[str, Any]:
        """Get information about user relationships."""
        return get_model_info(self.model_name)

    def can_delete_user(self, user_id: str) -> bool:
        """Check if user can be deleted based on dependencies."""
        dependents = get_model_dependents(self.model_name)
        # Business logic to check if deletion is safe
        return len(dependents) == 0
```

## Performance Considerations

- The manager is initialized once at application startup
- Graph operations are O(V + E) where V is vertices (models) and E is edges (relationships)
- Path finding uses BFS with configurable max depth
- Cycle detection uses DFS
- All operations are in-memory after initialization

## Error Handling

The manager provides comprehensive error handling:

- Invalid model names return `None` or empty collections
- Invalid relationship paths are detected and reported
- Import errors during model discovery are logged
- Relationship processing errors are logged with context

## Testing

Run the test script to verify functionality:

```bash
poetry run python scripts/test_model_relationship_manager.py
```

This will test:
- Model discovery
- Relationship detection
- Path finding
- Cycle detection
- Dependency analysis
- Nested data validation

## Future Enhancements

Potential future enhancements:

1. **Caching**: Cache frequently accessed relationship information
2. **Lazy Loading**: Load relationships on-demand
3. **Validation Rules**: Define validation rules for relationships
4. **Migration Support**: Generate migration scripts based on relationship changes
5. **Visualization**: Generate graph visualization for documentation
6. **Performance Metrics**: Track relationship operation performance
7. **Dynamic Updates**: Support for runtime model/relationship changes
