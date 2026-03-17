"""Authentication-related Pydantic schemas."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class RegisterRequest(BaseModel):
    """Registration request schema."""

    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)


class APIKeyCreate(BaseModel):
    """API Key creation schema."""

    name: str = Field(..., min_length=1, max_length=100)


class APIKeyResponse(BaseModel):
    """API Key response schema."""

    id: int
    name: str
    key: str
    last_used: str | None
    created_at: str
    is_active: bool

    model_config = {"from_attributes": True}


class AuthStatusResponse(BaseModel):
    """Authorization status response schema."""

    authorized: bool
    platform: str | None = None
