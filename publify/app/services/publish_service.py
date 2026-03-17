"""Publish service for content validation and publishing to platforms."""
import re
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post
from app.services.xiaohongshu_service import XiaohongshuOAuthService


class ContentValidationError(Exception):
    """Raised when content validation fails."""

    def __init__(self, message: str, code: str = "INVALID_CONTENT"):
        self.message = message
        self.code = code
        super().__init__(message)


class PublishService:
    """Service for publishing content to social platforms."""

    def __init__(self) -> None:
        self.xiaohongshu_service = XiaohongshuOAuthService()

    def validate_text(self, text: str) -> None:
        """Validate text content."""
        if not text or not text.strip():
            raise ContentValidationError("Text content cannot be empty")

        text = text.strip()

        if len(text) > 1000:
            raise ContentValidationError("Text content exceeds 1000 character limit")

        if len(text) < 1:
            raise ContentValidationError("Text content must be at least 1 character")

        # Remove HTML tags (basic sanitization)
        text = re.sub(r"<[^>]+>", "", text)

    def validate_media_urls(
        self, content_type: str, media_urls: list[str] | None
    ) -> None:
        """Validate media URLs based on content type."""
        if content_type == "text":
            if media_urls:
                raise ContentValidationError("Text content should not include media URLs")
            return

        if content_type == "image":
            if not media_urls or len(media_urls) == 0:
                raise ContentValidationError("Image content must include at least one image URL")
            if len(media_urls) > 9:
                raise ContentValidationError("Maximum 9 images allowed per post")

            # Validate each URL is a valid HTTP(S) URL
            for url in media_urls:
                if not url.startswith(("http://", "https://")):
                    raise ContentValidationError(f"Invalid media URL: {url}")

        elif content_type == "video":
            if not media_urls or len(media_urls) != 1:
                raise ContentValidationError("Video content must include exactly one video URL")

            if not media_urls[0].startswith(("http://", "https://")):
                raise ContentValidationError(f"Invalid media URL: {media_urls[0]}")

    def validate_content(
        self,
        platform: str,
        content_type: str,
        text: str,
        media_urls: list[str] | None = None,
    ) -> None:
        """Validate content before publishing."""
        # Validate platform
        if platform not in ("xiaohongshu",):
            raise ContentValidationError(
                f"Unsupported platform: {platform}", "PLATFORM_ERROR"
            )

        # Validate content type
        if content_type not in ("text", "image", "video"):
            raise ContentValidationError(
                f"Invalid content type: {content_type}", "INVALID_CONTENT"
            )

        # Validate text
        self.validate_text(text)

        # Validate media URLs
        self.validate_media_urls(content_type, media_urls)

    async def create_post_record(
        self,
        db: AsyncSession,
        user_id: int,
        platform: str,
        content_type: str,
        text: str,
        media_urls: list[str] | None = None,
    ) -> Post:
        """Create a post record in the database."""
        post = Post(
            user_id=user_id,
            platform=platform,
            content_type=content_type,
            content=text,
            status="pending",
        )

        if media_urls:
            post.set_media_urls(media_urls)

        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    async def publish_to_xiaohongshu(
        self,
        db: AsyncSession,
        user_id: int,
        content_type: str,
        text: str,
        media_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        """Publish content to Xiaohongshu."""
        # Check if user has valid authorization
        auth = await self.xiaohongshu_service.ensure_valid_token(db, user_id)
        if not auth:
            raise ContentValidationError(
                "Xiaohongshu authorization required. Please authorize your account.",
                "AUTH_REQUIRED",
            )

        # Call Xiaohongshu API
        result = await self.xiaohongshu_service.publish_content(
            access_token=auth.access_token,
            content_type=content_type,
            text=text,
            media_urls=media_urls,
        )

        return result

    async def publish(
        self,
        db: AsyncSession,
        user_id: int,
        platform: str,
        content_type: str,
        text: str,
        media_urls: list[str] | None = None,
    ) -> Post:
        """Main publish method that validates and publishes content."""
        # Validate content
        self.validate_content(platform, content_type, text, media_urls)

        # Create post record
        post = await self.create_post_record(
            db, user_id, platform, content_type, text, media_urls
        )

        try:
            # Publish to platform
            if platform == "xiaohongshu":
                result = await self.publish_to_xiaohongshu(
                    db, user_id, content_type, text, media_urls
                )

                if result.get("success"):
                    post.status = "success"
                else:
                    post.status = "failed"
                    post.error_message = result.get("error", "Unknown error")
            else:
                post.status = "failed"
                post.error_message = f"Unsupported platform: {platform}"

            await db.commit()
            await db.refresh(post)

        except ContentValidationError as e:
            post.status = "failed"
            post.error_message = e.message
            await db.commit()
            await db.refresh(post)
            raise

        except Exception as e:
            post.status = "failed"
            post.error_message = f"Unexpected error: {str(e)}"
            await db.commit()
            await db.refresh(post)
            raise ContentValidationError(
                f"Publishing failed: {str(e)}", "PLATFORM_ERROR"
            )

        return post

    async def get_user_posts(
        self, db: AsyncSession, user_id: int, limit: int = 20, offset: int = 0
    ) -> list[Post]:
        """Get posts for a user with pagination."""
        result = await db.execute(
            select(Post)
            .where(Post.user_id == user_id)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_post_by_id(self, db: AsyncSession, post_id: int, user_id: int) -> Post | None:
        """Get a specific post by ID for a user."""
        result = await db.execute(
            select(Post).where(Post.id == post_id, Post.user_id == user_id)
        )
        return result.scalar_one_or_none()


# Global instance
publish_service = PublishService()
