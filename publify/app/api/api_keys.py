"""API Key management routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware import get_current_user_web
from app.models import User
from app.services.auth_service import APIKeyManager

router = APIRouter(prefix="/api-keys", tags=["api-keys"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def api_keys_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_web)],
):
    """Render API keys management page."""
    api_keys = await APIKeyManager.list_user_api_keys(db, current_user.id)
    return templates.TemplateResponse(
        "api_keys.html",
        {
            "request": request,
            "user": current_user,
            "api_keys": api_keys,
            "csrf_token": request.state.csrf_token,
        },
    )


@router.post("", response_class=HTMLResponse)
async def create_api_key(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_web)],
    name: Annotated[str, Form(...)],
):
    """Create a new API key."""
    api_key = await APIKeyManager.create_api_key(db, current_user.id, name)

    # Show the key only once
    return templates.TemplateResponse(
        "api_key_created.html",
        {
            "request": request,
            "api_key": api_key,
            "csrf_token": request.state.csrf_token,
        },
    )


@router.post("/{api_key_id}/revoke")
async def revoke_api_key(
    api_key_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_web)],
):
    """Revoke an API key."""
    await APIKeyManager.revoke_api_key(db, api_key_id, current_user.id)
    return RedirectResponse(
        url="/api-keys", status_code=status.HTTP_303_SEE_OTHER
    )
