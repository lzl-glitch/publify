"""Xiaohongshu OAuth integration routes."""
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.config import get_settings
from app.database import get_db
from app.middleware import get_current_user_web
from app.models import User, XiaohongshuAuth
from app.services.xiaohongshu_service import XiaohongshuOAuthService

router = APIRouter(prefix="/xiaohongshu", tags=["xiaohongshu"])
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()

oauth_service = XiaohongshuOAuthService()


@router.get("/auth")
async def start_oauth(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user_web)],
):
    """Start Xiaohongshu OAuth flow."""
    # Generate state parameter for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state in session for verification
    session_id = request.cookies.get("session_id")
    if session_id:
        from app.services.auth_service import session_manager

        redis = session_manager.get_redis()
        redis.setex(f"oauth_state:{session_id}", 600, state)  # 10 minute TTL

    # Redirect to Xiaohongshu authorization URL
    auth_url = oauth_service.get_authorization_url(state)
    return RedirectResponse(url=auth_url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_web)],
    code: Annotated[str, Query(...)],
    state: Annotated[str, Query(...)],
):
    """Handle Xiaohongshu OAuth callback."""
    errors = []

    try:
        # Verify state parameter
        session_id = request.cookies.get("session_id")
        if session_id:
            from app.services.auth_service import session_manager

            redis = session_manager.get_redis()
            stored_state = redis.get(f"oauth_state:{session_id}")
            redis.delete(f"oauth_state:{session_id}")

            if not stored_state or stored_state != state:
                errors.append("Invalid state parameter. Please try again.")
            else:
                # Exchange code for tokens
                tokens = await oauth_service.exchange_code_for_token(code)

                if tokens:
                    # Delete existing auth records for this user
                    await db.execute(
                        delete(XiaohongshuAuth).where(
                            XiaohongshuAuth.user_id == current_user.id
                        )
                    )

                    # Store new tokens
                    auth_record = XiaohongshuAuth(
                        user_id=current_user.id,
                        access_token=tokens["access_token"],
                        refresh_token=tokens["refresh_token"],
                        expires_at=tokens["expires_at"],
                    )
                    db.add(auth_record)
                    await db.commit()

                    return RedirectResponse(
                        url="/dashboard?authorized=1",
                        status_code=status.HTTP_303_SEE_OTHER,
                    )
                else:
                    errors.append("Failed to exchange authorization code for tokens.")
        else:
            errors.append("No session found. Please login again.")

    except Exception as e:
        errors.append(f"OAuth error: {str(e)}")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
            "errors": errors,
            "csrf_token": request.state.csrf_token,
        },
    )
