"""Dashboard and post history routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.middleware import get_current_user_web
from app.models import APIKey, Post, User, XiaohongshuAuth
from app.services.publish_service import publish_service
from app.services.xiaohongshu_service import XiaohongshuOAuthService

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")
oauth_service = XiaohongshuOAuthService()


@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """Render home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_web)],
    authorized: bool = False,
):
    """Render user dashboard."""
    # Get user's API keys
    api_keys_result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id, APIKey.is_active == True)
        .order_by(APIKey.created_at.desc())
    )
    api_keys = list(api_keys_result.scalars().all())

    # Check Xiaohongshu authorization status
    auth_result = await db.execute(
        select(XiaohongshuAuth).where(XiaohongshuAuth.user_id == current_user.id)
    )
    xiaohongshu_auth = auth_result.scalar_one_or_none()
    is_authorized = xiaohongshu_auth is not None and not xiaohongshu_auth.is_expired()

    # Get post statistics
    total_posts_result = await db.execute(
        select(func.count(Post.id)).where(Post.user_id == current_user.id)
    )
    total_posts = total_posts_result.scalar() or 0

    success_posts_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == current_user.id, Post.status == "success"
        )
    )
    success_posts = success_posts_result.scalar() or 0

    # Get recent posts
    recent_posts = await publish_service.get_user_posts(db, current_user.id, limit=5)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
            "api_keys": api_keys,
            "xiaohongshu_authorized": is_authorized,
            "total_posts": total_posts,
            "success_posts": success_posts,
            "recent_posts": recent_posts,
            "authorized": authorized,
            "csrf_token": request.state.csrf_token,
        },
    )


@router.get("/posts", response_class=HTMLResponse)
async def posts_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_web)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Render posts history page."""
    offset = (page - 1) * per_page
    posts = await publish_service.get_user_posts(
        db, current_user.id, limit=per_page, offset=offset
    )

    # Get total count for pagination
    from sqlalchemy import select, func
    count_result = await db.execute(
        select(func.count(Post.id)).where(Post.user_id == current_user.id)
    )
    total_posts = count_result.scalar() or 0
    total_pages = (total_posts + per_page - 1) // per_page

    return templates.TemplateResponse(
        "posts.html",
        {
            "request": request,
            "user": current_user,
            "posts": posts,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "csrf_token": request.state.csrf_token,
        },
    )
