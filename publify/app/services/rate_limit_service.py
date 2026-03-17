"""Rate limiting service using Redis with sliding window."""
import time
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from redis import Redis

from app.config import get_settings

settings = get_settings()


class RateLimiter:
    """Redis-based rate limiter with sliding window."""

    def __init__(self) -> None:
        self.redis_url = settings.redis_url
        self._redis: Redis | None = None

    def get_redis(self) -> Redis:
        """Get Redis connection (lazy initialization)."""
        if self._redis is None:
            self._redis = Redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    def _get_key(self, endpoint: str, identifier: str) -> str:
        """Generate rate limit key."""
        return f"ratelimit:{endpoint}:{identifier}"

    def _get_window(self) -> tuple[int, int]:
        """Get current window start time and window size."""
        return int(time.time()), 60  # 60 second windows

    async def is_allowed(
        self,
        endpoint: str,
        identifier: str,
        limit: int,
        window: int = 60,
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.

        Returns:
            tuple: (allowed, info_dict with remaining, reset_at)
        """
        redis = self.get_redis()
        key = self._get_key(endpoint, identifier)
        now = int(time.time())
        window_start = now - (now % window)

        # Clean up old entries
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)
        results = pipe.execute()

        current_count = results[1]
        pipe.execute()  # Execute the zadd and expire

        remaining = max(0, limit - current_count - 1)
        reset_at = window_start + window

        return current_count < limit, {
            "limit": limit,
            "remaining": remaining,
            "reset_at": reset_at,
        }


class RateLimitConfig:
    """Rate limit configuration for different endpoint types."""

    # Rate limits: (max_requests, window_seconds)
    AUTH_ENDPOINT = (10, 60)  # 10 requests per minute per IP
    API_KEY_CREATE = (5, 3600)  # 5 requests per hour per user
    PUBLISH_API = (60, 60)  # 60 requests per minute per API key
    QUERY_API = (100, 60)  # 100 requests per minute per API key
    WEB_DASHBOARD = (120, 60)  # 120 requests per minute per session

    @classmethod
    def get_limit(cls, endpoint_type: str) -> tuple[int, int]:
        """Get rate limit for endpoint type."""
        return getattr(cls, endpoint_type.upper(), cls.WEB_DASHBOARD)


# Rate limit middleware
async def check_rate_limit(
    request: Request,
    endpoint_type: str,
    identifier: str,
) -> None:
    """
    Check rate limit and raise exception if exceeded.

    Args:
        request: FastAPI request object
        endpoint_type: Type of endpoint (AUTH, PUBLISH_API, etc.)
        identifier: Unique identifier (IP, API key, session ID, etc.)
    """
    if not settings.rate_limit_enabled:
        return

    limiter = RateLimiter()
    limit, window = RateLimitConfig.get_limit(endpoint_type)
    allowed, info = await limiter.is_allowed(endpoint_type, identifier, limit, window)

    # Store rate limit info in request state for response headers
    request.state.rate_limit = info

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMITED",
                "message": "Rate limit exceeded",
                "details": info,
            },
        )


def get_rate_limit_headers(request: Request) -> dict:
    """Get rate limit headers for response."""
    if hasattr(request.state, "rate_limit") and request.state.rate_limit:
        info = request.state.rate_limit
        return {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(info["reset_at"]),
            "Retry-After": str(max(0, info["reset_at"] - int(time.time()))),
        }
    return {}


# Dependency for rate limiting by IP
async def rate_limit_auth(request: Request) -> None:
    """Rate limit for auth endpoints by IP."""
    # Get client IP
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else request.client.host
    await check_rate_limit(request, "AUTH_ENDPOINT", client_ip)


# Dependency for rate limiting by API key
async def rate_limit_publish(request: Request) -> None:
    """Rate limit for publish API by API key."""
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "")
        await check_rate_limit(request, "PUBLISH_API", api_key)


async def rate_limit_query(request: Request) -> None:
    """Rate limit for query API by API key."""
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "")
        await check_rate_limit(request, "QUERY_API", api_key)


# Dependency for rate limiting by session
async def rate_limit_web(request: Request) -> None:
    """Rate limit for web endpoints by session."""
    session_id = request.cookies.get("session_id", "")
    if not session_id:
        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        identifier = forwarded.split(",")[0].strip() if forwarded else request.client.host
    else:
        identifier = session_id
    await check_rate_limit(request, "WEB_DASHBOARD", identifier)
