"""
Model Relationship Manager

This module provides a comprehensive system for managing model relationships
as a graph structure. It discovers all models, builds relationship graphs,
and provides utilities for navigating and managing nested object operations.

The manager is initialized at application startup and provides:
- Model discovery and registration
- Relationship graph building
- Path finding between models
- Cycle detection
- Relationship traversal utilities
- Support for nested CRUD operations
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from sqlalchemy.orm import RelationshipProperty

from app.models.base_model import BaseModel
from app.utils.relationship_types import RelationshipAdapter, RelationshipType
from app.utils.tracing import get_trace_logger

logger = get_trace_logger("model-relationship-manager")


@dataclass
class ModelNode:
    """Represents a model in the relationship graph"""

    model_class: Type[BaseModel]
    table_name: str
    relationships: Dict[str, RelationshipProperty] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Extract relationships after initialization"""
        if not self.relationships:
            self.relationships = self.model_class.get_relationships()

    @property
    def model_name(self) -> str:
        """Get the model class name"""
        return self.model_class.__name__

    def get_relationship_type(self, rel_name: str) -> Optional[RelationshipType]:
        """Get the relationship type for a specific relationship"""
        if rel_name not in self.relationships:
            return None

        rel_prop = self.relationships[rel_name]
        return RelationshipAdapter.get_application_type(rel_prop.direction, rel_prop.uselist)

    def get_related_model(self, rel_name: str) -> Optional[Type[BaseModel]]:
        """Get the related model class for a specific relationship"""
        if rel_name not in self.relationships:
            return None

        rel_prop = self.relationships[rel_name]
        related_class = rel_prop.mapper.class_
        # Type check to ensure it's a BaseModel subclass
        if isinstance(related_class, type) and issubclass(related_class, BaseModel):
            return related_class
        return None


@dataclass
class RelationshipEdge:
    """Represents a relationship between two models"""

    source_model: str  # Source model name
    target_model: str  # Target model name
    relationship_name: str  # Name of the relationship attribute
    relationship_type: RelationshipType
    back_populates: Optional[str] = None
    foreign_key: Optional[str] = None
    junction_table: Optional[str] = None
    cascade_delete: bool = False
    cascade_soft_delete: bool = True

    @property
    def is_bidirectional(self) -> bool:
        """Check if this relationship is bidirectional"""
        return self.back_populates is not None

    def get_reverse_edge(self) -> Optional["RelationshipEdge"]:
        """Get the reverse edge if this relationship is bidirectional"""
        if not self.is_bidirectional:
            return None

        return RelationshipEdge(
            source_model=self.target_model,
            target_model=self.source_model,
            relationship_name=self.back_populates,
            relationship_type=self._get_reverse_type(),
            back_populates=self.relationship_name,
            foreign_key=self.foreign_key,
            junction_table=self.junction_table,
            cascade_delete=self.cascade_delete,
            cascade_soft_delete=self.cascade_soft_delete,
        )

    def _get_reverse_type(self) -> RelationshipType:
        """Get the reverse relationship type"""
        reverse_map = {
            RelationshipType.ONE_TO_ONE: RelationshipType.ONE_TO_ONE,
            RelationshipType.ONE_TO_MANY: RelationshipType.MANY_TO_ONE,
            RelationshipType.MANY_TO_ONE: RelationshipType.ONE_TO_MANY,
            RelationshipType.MANY_TO_MANY: RelationshipType.MANY_TO_MANY,
        }
        return reverse_map[self.relationship_type]


class ModelRelationshipManager:
    """
    Manages model relationships as a graph structure.

    This class discovers all models, builds relationship graphs,
    and provides utilities for navigating and managing nested operations.
    """

    def __init__(self) -> None:
        """Initialize the relationship manager"""
        self._nodes: Dict[str, ModelNode] = {}
        self._edges: List[RelationshipEdge] = []
        self._adjacency_list: Dict[str, List[RelationshipEdge]] = defaultdict(list)
        self._reverse_adjacency_list: Dict[str, List[RelationshipEdge]] = defaultdict(list)
        self._initialized = False

        logger.info("ModelRelationshipManager initialized")

    def initialize(self, models: Optional[List[Type[BaseModel]]] = None) -> None:
        """
        Initialize the relationship manager with models.

        Args:
            models: List of model classes to register. If None, auto-discover models.
        """
        if self._initialized:
            logger.warning("ModelRelationshipManager already initialized")
            return

        if models is None:
            models = self._discover_models()

        logger.info(f"Initializing ModelRelationshipManager with {len(models)} models")

        # Register all models as nodes
        for model in models:
            self._register_model(model)

        # Build relationship edges
        self._build_relationship_edges()

        # Build adjacency lists
        self._build_adjacency_lists()

        self._initialized = True
        logger.info(f"ModelRelationshipManager initialized with {len(self._nodes)} nodes and {len(self._edges)} edges")

    def _discover_models(self) -> List[Type[BaseModel]]:
        """
        Auto-discover all models that inherit from BaseModel from app.models.__init__.py.

        Returns:
            List of discovered model classes

        Raises:
            ImportError: If models module cannot be imported
        """
        import inspect

        import app.models as models_module

        models = []

        # Get all members from the models module
        for name, obj in inspect.getmembers(models_module):
            # Check if it's a class and subclass of BaseModel (but not BaseModel itself)
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseModel)
                and obj is not BaseModel
                and hasattr(obj, "__tablename__")  # Ensure it's a concrete model
            ):
                models.append(obj)
                logger.debug(f"Discovered model: {obj.__name__}")

        logger.info(f"Discovered {len(models)} models: {[m.__name__ for m in models]}")
        return models

    def _register_model(self, model_class: Type[BaseModel]) -> None:
        """
        Register a model as a node in the graph.

        Args:
            model_class: The model class to register
        """
        model_name = model_class.__name__

        if model_name in self._nodes:
            logger.warning(f"Model {model_name} already registered")
            return

        node = ModelNode(model_class=model_class, table_name=model_class.__tablename__)

        self._nodes[model_name] = node
        logger.debug(f"Registered model: {model_name}")

    def _build_relationship_edges(self) -> None:
        """Build relationship edges from model relationships"""
        for model_name, node in self._nodes.items():
            for rel_name, rel_prop in node.relationships.items():
                try:
                    # Get relationship type
                    rel_type = RelationshipAdapter.get_application_type(rel_prop.direction, rel_prop.uselist)

                    # Get target model
                    target_model = rel_prop.mapper.class_
                    target_model_name = target_model.__name__

                    # Skip if target model is not registered
                    if target_model_name not in self._nodes:
                        logger.warning(
                            f"Target model {target_model_name} not registered for relationship {model_name}.{rel_name}"
                        )
                        continue

                    # Extract relationship metadata
                    back_populates = getattr(rel_prop, "back_populates", None)
                    foreign_key = None
                    junction_table = None

                    # Extract foreign key information
                    if hasattr(rel_prop, "local_columns") and rel_prop.local_columns:
                        foreign_key = str(list(rel_prop.local_columns)[0])
                    elif hasattr(rel_prop, "foreign_keys") and rel_prop.foreign_keys:
                        foreign_key = str(list(rel_prop.foreign_keys)[0])

                    # Extract junction table for many-to-many
                    if rel_type == RelationshipType.MANY_TO_MANY and hasattr(rel_prop, "secondary"):
                        junction_table = str(rel_prop.secondary)

                    # Create edge
                    edge = RelationshipEdge(
                        source_model=model_name,
                        target_model=target_model_name,
                        relationship_name=rel_name,
                        relationship_type=rel_type,
                        back_populates=back_populates,
                        foreign_key=foreign_key,
                        junction_table=junction_table,
                        cascade_delete=getattr(rel_prop, "cascade", False) and "delete" in str(rel_prop.cascade),
                        cascade_soft_delete=True,  # Default to True for soft deletes
                    )

                    self._edges.append(edge)
                    logger.debug(f"Created edge: {model_name}.{rel_name} -> {target_model_name} ({rel_type.value})")

                except Exception as e:
                    logger.error(f"Failed to process relationship {model_name}.{rel_name}: {e}")

    def _build_adjacency_lists(self) -> None:
        """Build adjacency lists for efficient graph traversal"""
        for edge in self._edges:
            self._adjacency_list[edge.source_model].append(edge)
            self._reverse_adjacency_list[edge.target_model].append(edge)

    def get_model_node(self, model_name: str) -> Optional[ModelNode]:
        """
        Get a model node by name.

        Args:
            model_name: Name of the model

        Returns:
            ModelNode or None if not found
        """
        return self._nodes.get(model_name)

    def get_model_class(self, model_name: str) -> Optional[Type[BaseModel]]:
        """
        Get a model class by name.

        Args:
            model_name: Name of the model

        Returns:
            Model class or None if not found
        """
        node = self.get_model_node(model_name)
        return node.model_class if node else None

    def get_relationships(self, model_name: str) -> Dict[str, RelationshipProperty]:
        """
        Get all relationships for a model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary of relationship names to RelationshipProperty
        """
        node = self.get_model_node(model_name)
        return node.relationships if node else {}

    def get_outgoing_edges(self, model_name: str) -> List[RelationshipEdge]:
        """
        Get all outgoing edges from a model.

        Args:
            model_name: Name of the model

        Returns:
            List of outgoing RelationshipEdge objects
        """
        return self._adjacency_list.get(model_name, [])

    def get_incoming_edges(self, model_name: str) -> List[RelationshipEdge]:
        """
        Get all incoming edges to a model.

        Args:
            model_name: Name of the model

        Returns:
            List of incoming RelationshipEdge objects
        """
        return self._reverse_adjacency_list.get(model_name, [])

    def find_path(self, source_model: str, target_model: str, max_depth: int = 5) -> Optional[List[RelationshipEdge]]:
        """
        Find a path between two models using BFS.

        Args:
            source_model: Starting model name
            target_model: Target model name
            max_depth: Maximum search depth

        Returns:
            List of edges forming the path, or None if no path found
        """
        if source_model not in self._nodes or target_model not in self._nodes:
            return None

        if source_model == target_model:
            return []

        # BFS to find shortest path
        queue: deque[Tuple[str, List[RelationshipEdge]]] = deque([(source_model, [])])
        visited = {source_model}

        while queue and len(queue[0][1]) < max_depth:
            current_model, path = queue.popleft()

            for edge in self.get_outgoing_edges(current_model):
                next_model = edge.target_model

                if next_model == target_model:
                    return path + [edge]

                if next_model not in visited:
                    visited.add(next_model)
                    queue.append((next_model, path + [edge]))

        return None

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect cycles in the relationship graph using DFS.

        Returns:
            List of cycles, where each cycle is a list of model names
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for edge in self.get_outgoing_edges(node):
                dfs(edge.target_model, path + [node])

            rec_stack.remove(node)

        for model_name in self._nodes:
            if model_name not in visited:
                dfs(model_name, [])

        return cycles

    def get_model_dependencies(self, model_name: str) -> Set[str]:
        """
        Get all models that the given model depends on (models it references).

        Args:
            model_name: Name of the model

        Returns:
            Set of model names that this model depends on
        """
        dependencies = set()
        visited = set()

        def collect_dependencies(node: str) -> None:
            if node in visited:
                return

            visited.add(node)

            for edge in self.get_outgoing_edges(node):
                dependencies.add(edge.target_model)
                collect_dependencies(edge.target_model)

        collect_dependencies(model_name)
        return dependencies

    def get_model_dependents(self, model_name: str) -> Set[str]:
        """
        Get all models that depend on the given model (models that reference it).

        Args:
            model_name: Name of the model

        Returns:
            Set of model names that depend on this model
        """
        dependents = set()
        visited = set()

        def collect_dependents(node: str) -> None:
            if node in visited:
                return

            visited.add(node)

            for edge in self.get_incoming_edges(node):
                dependents.add(edge.source_model)
                collect_dependents(edge.source_model)

        collect_dependents(model_name)
        return dependents

    def get_relationship_path(
        self, source_model: str, target_model: str, path: List[str]
    ) -> Optional[List[RelationshipEdge]]:
        """
        Get relationship edges for a specific path.

        Args:
            source_model: Starting model name
            target_model: Target model name
            path: List of model names forming the path

        Returns:
            List of RelationshipEdge objects for the path, or None if invalid
        """
        if not path or path[0] != source_model or path[-1] != target_model:
            return None

        edges = []
        for i in range(len(path) - 1):
            current_model = path[i]
            next_model = path[i + 1]

            # Find edge between current and next model
            edge_found = False
            for edge in self.get_outgoing_edges(current_model):
                if edge.target_model == next_model:
                    edges.append(edge)
                    edge_found = True
                    break

            if not edge_found:
                return None

        return edges

    def validate_nested_data(self, model_name: str, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Validate and separate nested relationship data from main data.

        Args:
            model_name: Name of the model
            data: Input data dictionary

        Returns:
            Tuple of (main_data, nested_data)
        """
        node = self.get_model_node(model_name)
        if not node:
            raise ValueError(f"Model {model_name} not found")

        main_data = {}
        nested_data = {}

        for key, value in data.items():
            if key in node.relationships:
                # Always filter out relationship fields, regardless of their value
                # This prevents SQLAlchemy from trying to set relationship fields to None
                if isinstance(value, (dict, list)):
                    nested_data[key] = value
                # If it's None or other non-collection value, just skip it
            else:
                main_data[key] = value

        return main_data, nested_data

    def get_graph_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the relationship graph.

        Returns:
            Dictionary containing graph statistics and structure
        """
        cycles = self.detect_cycles()

        return {
            "total_models": len(self._nodes),
            "total_relationships": len(self._edges),
            "cycles_detected": len(cycles),
            "cycles": cycles,
            "models": {
                name: {
                    "table_name": node.table_name,
                    "relationships": list(node.relationships.keys()),
                    "outgoing_edges": len(self.get_outgoing_edges(name)),
                    "incoming_edges": len(self.get_incoming_edges(name)),
                }
                for name, node in self._nodes.items()
            },
            "relationships": [
                {
                    "source": edge.source_model,
                    "target": edge.target_model,
                    "name": edge.relationship_name,
                    "type": edge.relationship_type.value,
                    "bidirectional": edge.is_bidirectional,
                }
                for edge in self._edges
            ],
        }

    def is_initialized(self) -> bool:
        """Check if the manager is initialized"""
        return self._initialized


# Global instance
model_relationship_manager = ModelRelationshipManager()


def get_model_relationship_manager() -> ModelRelationshipManager:
    """
    Get the global model relationship manager instance.

    Returns:
        The global ModelRelationshipManager instance
    """
    return model_relationship_manager


def initialize_model_relationships(models: Optional[List[Type[BaseModel]]] = None) -> None:
    """
    Initialize the global model relationship manager.

    Args:
        models: List of model classes to register. If None, auto-discover models.
    """
    model_relationship_manager.initialize(models)
