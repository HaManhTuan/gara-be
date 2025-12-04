from datetime import datetime
from typing import Any, Dict

from sqlalchemy import BigInteger, Column, DateTime, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty

from app.config.database import Base


class BaseModel(Base):
    """Base model for all database models"""

    __abstract__ = True

    @declared_attr  # type: ignore[misc]
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically from class name"""
        return cls.__name__.lower() + "s"  # type: ignore[no-any-return]

    # Common columns for all models
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)

    @property
    def is_active(self) -> bool:
        """Check if the record is active (not deleted)"""
        return self.deleted_at is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create model instance from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__table__.columns.keys()})

    def __repr__(self) -> str:
        """String representation of the model"""
        return f"<{self.__class__.__name__}(id={self.id})>"

    @classmethod
    def get_relationships(cls) -> Dict[str, RelationshipProperty]:
        """
        Discover relationships using SQLAlchemy inspection.

        Returns:
            Dict mapping relationship name to SQLAlchemy RelationshipProperty
        """
        mapper = inspect(cls)
        relationships = {}
        for prop in mapper.relationships:
            relationships[prop.key] = prop
        return relationships
