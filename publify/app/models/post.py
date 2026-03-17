"""Post/Publish record database model."""
import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.user import User


class Post(Base):
    """Post/Publish record model for tracking publishing history."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    content_type: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="posts")

    def get_media_urls(self) -> list[str]:
        """Get media URLs as a list."""
        if not self.media_urls:
            return []
        try:
            return json.loads(self.media_urls)
        except json.JSONDecodeError:
            return []

    def set_media_urls(self, urls: list[str]) -> None:
        """Set media URLs from a list."""
        self.media_urls = json.dumps(urls) if urls else None

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, platform='{self.platform}', status='{self.status}')>"
