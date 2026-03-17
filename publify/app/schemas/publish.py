"""Publishing-related Pydantic schemas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PublishRequest(BaseModel):
    """Content publish request schema."""

    platform: Literal["xiaohongshu"] = Field(..., description="Target platform")
    content_type: Literal["text", "image", "video"] = Field(
        ..., description="Content type"
    )
    text: str = Field(..., min_length=1, max_length=1000, description="Text content")
    media_urls: list[str] | None = Field(
        default=None, max_length=9, description="Media URLs (max 9 for images)"
    )

    @field_validator("media_urls")
    @classmethod
    def validate_media_urls(cls, v: list[str] | None, info) -> list[str] | None:
        """Validate media URLs based on content type."""
        if info.data.get("content_type") == "text":
            if v:
                raise ValueError("Text content should not have media URLs")
            return None
        if info.data.get("content_type") in ("image", "video") and not v:
            raise ValueError("Image and video content must include media URLs")
        if info.data.get("content_type") == "video" and len(v) != 1:
            raise ValueError("Video content must have exactly one media URL")
        return v


class PublishResponse(BaseModel):
    """Publish response schema."""

    post_id: int
    platform: str
    status: str
    created_at: datetime


class PostResponse(BaseModel):
    """Post record response schema."""

    id: int
    platform: str
    content_type: str
    content: str
    media_urls: list[str]
    status: str
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Error response schema."""

    success: bool = False
    error: dict


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: str
    message: str
    details: dict = {}
