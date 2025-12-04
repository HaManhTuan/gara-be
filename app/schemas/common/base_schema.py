from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel

# Generic type for data models
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema for all Pydantic models"""

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }
