"""User-related Pydantic schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")


class UserCreate(UserBase):
    """User registration schema."""

    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(BaseModel):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime
    updated_at: datetime
