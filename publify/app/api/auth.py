"""Authentication routes for web UI (registration, login, logout)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import UserManager, session_manager

router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render registration page."""
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "csrf_token": request.state.csrf_token},
    )


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    username: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
    confirm_password: Annotated[str, Form(...)],
):
    """Handle user registration."""
    errors = []

    try:
        # Validate input
        RegisterRequest(
            username=username, password=password, confirm_password=confirm_password
        )

        if password != confirm_password:
            errors.append("Passwords do not match")
        else:
            # Check if user already exists
            existing_user = await UserManager.get_user_by_username(db, username)
            if existing_user:
                errors.append("Username already exists")
            else:
                # Create user
                await UserManager.create_user(db, username, password)
                return RedirectResponse(
                    url="/auth/login?registered=1", status_code=status.HTTP_303_SEE_OTHER
                )
    except ValidationError as e:
        for error in e.errors():
            field = error["loc"][0] if error["loc"] else "form"
            errors.append(f"{field}: {error["msg"]}")

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "errors": errors,
            "username": username,
            "csrf_token": request.state.csrf_token,
        },
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, registered: bool = False):
    """Render login page."""
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "csrf_token": request.state.csrf_token,
            "registered": registered,
        },
    )


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    username: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
):
    """Handle user login."""
    errors = []

    try:
        # Validate input
        LoginRequest(username=username, password=password)

        # Authenticate
        user = await UserManager.authenticate_user(db, username, password)
        if user:
            # Create session
            session_id = await session_manager.create_session(user.id)
            response = RedirectResponse(
                url="/dashboard", status_code=status.HTTP_303_SEE_OTHER
            )
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=not settings.is_development,
                samesite="strict",
                max_age=settings.session_expire_days * 86400,
            )
            return response
        else:
            errors.append("Invalid username or password")
    except ValidationError as e:
        for error in e.errors():
            errors.append(error["msg"])

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "errors": errors,
            "username": username,
            "csrf_token": request.state.csrf_token,
        },
    )


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Handle user logout."""
    session_id = request.cookies.get("session_id")
    if session_id:
        await session_manager.delete_session(session_id)

    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_id")
    return response
