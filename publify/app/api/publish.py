"""REST API routes for content publishing."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware import CurrentUserAPI
from app.schemas.publish import ErrorResponse, PostResponse, PublishRequest
from app.services.publish_service import ContentValidationError, publish_service

router = APIRouter(prefix="/api/v1", tags=["publish-api"])


@router.post("/publish")
async def publish_content(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUserAPI, Depends()],
    data: PublishRequest,
):
    """Publish content to a social media platform."""
    try:
        post = await publish_service.publish(
            db=db,
            user_id=current_user.id,
            platform=data.platform,
            content_type=data.content_type,
            text=data.text,
            media_urls=data.media_urls,
        )

        return {
            "success": post.status == "success",
            "data": {
                "post_id": post.id,
                "platform": post.platform,
                "status": post.status,
                "created_at": post.created_at.isoformat(),
            },
        }

    except ContentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if e.code != "AUTH_REQUIRED" else status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
        )


@router.get("/posts")
async def list_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUserAPI, Depends()],
    limit: int = 20,
    offset: int = 0,
):
    """List user's publish history."""
    posts = await publish_service.get_user_posts(
        db, current_user.id, limit=min(limit, 100), offset=offset
    )

    return {
        "success": True,
        "data": [
            {
                "id": post.id,
                "platform": post.platform,
                "content_type": post.content_type,
                "content": post.content,
                "media_urls": post.get_media_urls(),
                "status": post.status,
                "error_message": post.error_message,
                "created_at": post.created_at.isoformat(),
            }
            for post in posts
        ],
    }


@router.get("/posts/{post_id}")
async def get_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUserAPI, Depends()],
):
    """Get a specific post by ID."""
    post = await publish_service.get_post_by_id(db, post_id, current_user.id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Post not found"},
        )

    return {
        "success": True,
        "data": {
            "id": post.id,
            "platform": post.platform,
            "content_type": post.content_type,
            "content": post.content,
            "media_urls": post.get_media_urls(),
            "status": post.status,
            "error_message": post.error_message,
            "created_at": post.created_at.isoformat(),
        },
    }


@router.get("/auth/status")
async def get_auth_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUserAPI, Depends()],
):
    """Get user's authorization status for platforms."""
    from app.models import XiaohongshuAuth
    from sqlalchemy import select

    result = await db.execute(
        select(XiaohongshuAuth).where(XiaohongshuAuth.user_id == current_user.id)
    )
    xiaohongshu_auth = result.scalar_one_or_none()

    return {
        "success": True,
        "data": {
            "xiaohongshu": {
                "authorized": xiaohongshu_auth is not None
                and not xiaohongshu_auth.is_expired(),
            }
        },
    }
