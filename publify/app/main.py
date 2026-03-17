"""FastAPI application entry point for Publify."""
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import auth, api_keys, dashboard, publish as publish_api, xiaohongshu
from app.config import get_settings
from app.database import init_db
from app.middleware import get_current_user_web

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> Awaitable[None]:
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Publishing API for Chinese social media platforms",
    lifespan=lifespan,
)

# CORS middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# CSRF middleware for web routes
@app.middleware("http")
async def csrf_middleware(request: Request, call_next: Callable) -> JSONResponse:
    """Add CSRF token to all requests."""
    import secrets

    if not hasattr(request.state, "csrf_token"):
        request.state.csrf_token = secrets.token_hex(32)
    response = await call_next(request)
    return response


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    if exc.status_code == status.HTTP_303_SEE_OTHER:
        # Return redirect response
        from fastapi.responses import RedirectResponse

        return RedirectResponse(
            url=exc.headers.get("Location", "/"),
            status_code=exc.status_code,
        )

    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": exc.detail,
                },
            },
        )

    if exc.status_code == status.HTTP_403_FORBIDDEN:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": exc.detail,
                },
            },
        )

    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": exc.detail,
                },
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": exc.errors(),
            },
        },
    )


# Include routers
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(api_keys.router)
app.include_router(xiaohongshu.router)
app.include_router(publish_api.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Redirect root to dashboard or login
@app.get("/", response_class=HTMLResponse)
async def root_redirect(request: Request):
    """Redirect to appropriate page based on auth status."""
    from fastapi.responses import RedirectResponse

    session_id = request.cookies.get("session_id")
    if session_id:
        from app.services.auth_service import session_manager

        user_id = await session_manager.get_user_id(session_id)
        if user_id:
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
