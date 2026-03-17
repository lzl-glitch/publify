"""Authentication middleware and dependencies."""
import secrets
from typing import Annotated

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import APIKey, User
from app.services.auth_service import APIKeyManager, session_manager


async def get_current_user_web(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current authenticated user from session (for web UI)."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/auth/login"},
        )

    user_id = await session_manager.get_user_id(session_id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/auth/login"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/auth/login"},
        )

    # Attach CSRF token to request state
    if not hasattr(request.state, "csrf_token"):
        request.state.csrf_token = secrets.token_hex(32)

    return user


async def get_current_user_api(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current authenticated user from API key (for REST API)."""
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    api_key_str = authorization.replace("Bearer ", "")

    # Validate API key format
    if not api_key_str.startswith(("pk_live_", "pk_test_")) or len(api_key_str) < 40:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key format",
        )

    api_key = await APIKeyManager.get_api_key(db, api_key_str)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or inactive API key",
        )

    # Update last used timestamp
    await APIKeyManager.update_last_used(db, api_key)

    # Get user
    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found",
        )

    # Store user in request state for use in endpoints
    request.state.current_user = user
    return user


# Type aliases for dependencies
CurrentUserWeb = Annotated[User, Depends(get_current_user_web)]
CurrentUserAPI = Annotated[User, Depends(get_current_user_api)]
