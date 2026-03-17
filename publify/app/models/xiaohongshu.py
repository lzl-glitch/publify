"""Xiaohongshu OAuth authentication database model."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.user import User


class XiaohongshuAuth(Base):
    """Xiaohongshu OAuth token storage model."""

    __tablename__ = "xiaohongshu_auth"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="xiaohongshu_auth")

    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    def __repr__(self) -> str:
        return f"<XiaohongshuAuth(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
