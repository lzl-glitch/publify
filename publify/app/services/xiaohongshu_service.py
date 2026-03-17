"""Xiaohongshu OAuth service for token management."""
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import XiaohongshuAuth

settings = get_settings()


class XiaohongshuOAuthService:
    """Service for Xiaohongshu OAuth operations."""

    def __init__(self) -> None:
        self.auth_url = settings.xiaohongshu_auth_url
        self.token_url = settings.xiaohongshu_token_url
        self.client_id = settings.xiaohongshu_client_id
        self.client_secret = settings.xiaohongshu_client_secret
        self.redirect_uri = settings.xiaohongshu_redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """Generate the authorization URL for Xiaohongshu OAuth."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "write_public read_public",
            "state": state,
        }
        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> dict | None:
        """Exchange authorization code for access token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": self.redirect_uri,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                # Calculate token expiration (default 30 days)
                expires_in = data.get("expires_in", 2592000)  # 30 days in seconds
                expires_at = datetime.now() + timedelta(seconds=expires_in)

                return {
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token"),
                    "expires_at": expires_at,
                }
        except httpx.HTTPError as e:
            # Log error in production
            return None
        except Exception as e:
            # Log error in production
            return None

    async def refresh_access_token(self, refresh_token: str) -> dict | None:
        """Refresh access token using refresh token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                expires_in = data.get("expires_in", 2592000)
                expires_at = datetime.now() + timedelta(seconds=expires_in)

                return {
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token", refresh_token),
                    "expires_at": expires_at,
                }
        except httpx.HTTPError as e:
            # Log error in production
            return None
        except Exception as e:
            # Log error in production
            return None

    async def get_user_auth(self, db: AsyncSession, user_id: int) -> XiaohongshuAuth | None:
        """Get Xiaohongshu auth record for a user."""
        result = await db.execute(
            select(XiaohongshuAuth).where(XiaohongshuAuth.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def ensure_valid_token(
        self, db: AsyncSession, user_id: int
    ) -> XiaohongshuAuth | None:
        """Ensure the user has a valid access token, refresh if needed."""
        auth = await self.get_user_auth(db, user_id)

        if not auth:
            return None

        # Check if token is expired
        if auth.is_expired():
            # Try to refresh the token
            new_tokens = await self.refresh_access_token(auth.refresh_token)
            if new_tokens:
                auth.access_token = new_tokens["access_token"]
                auth.refresh_token = new_tokens["refresh_token"]
                auth.expires_at = new_tokens["expires_at"]
                await db.commit()
                await db.refresh(auth)
            else:
                # Refresh failed, return None to indicate re-authorization needed
                return None

        return auth

    async def publish_content(
        self,
        access_token: str,
        content_type: str,
        text: str,
        media_urls: list[str] | None = None,
    ) -> dict:
        """Publish content to Xiaohongshu."""
        # Note: This is a placeholder implementation
        # The actual Xiaohongshu API endpoints and request format would go here
        # For MVP, this simulates the API call

        try:
            # Simulate API call
            # In production, this would call the actual Xiaohongshu publishing API
            api_url = "https://open.xiaohongshu.com/api/publish"  # Placeholder URL

            async with httpx.AsyncClient() as client:
                payload = {
                    "text": text,
                    "type": content_type,
                }

                if media_urls:
                    payload["media"] = media_urls

                # This would be the actual API call in production
                # For MVP, we simulate the response
                # response = await client.post(
                #     api_url,
                #     headers={"Authorization": f"Bearer {access_token}"},
                #     json=payload,
                #     timeout=60.0,
                # )
                # response.raise_for_status()
                # return response.json()

                # Simulated success response for MVP
                return {
                    "success": True,
                    "post_id": f"xhs_{secrets.token_hex(16)}",
                    "status": "published",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
