"""Authentication service for password hashing, sessions, and API keys."""
import secrets
import uuid
from datetime import datetime, timedelta

from passlib.context import CryptContext
from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import APIKey, User

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    """Generate a unique API key."""
    prefix = "pk_test_" if settings.is_development else "pk_live_"
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}{random_part}"


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


class SessionManager:
    """Manager for user sessions using Redis."""

    def __init__(self) -> None:
        self.redis: Redis | None = None

    def get_redis(self) -> Redis:
        """Get Redis connection (lazy initialization)."""
        if self.redis is None:
            self.redis = Redis.from_url(settings.redis_url, decode_responses=True)
        return self.redis

    async def create_session(self, user_id: int) -> str:
        """Create a new session and return the session ID."""
        session_id = generate_session_id()
        redis = self.get_redis()
        ttl = settings.session_expire_days * 86400  # Convert days to seconds
        redis.setex(f"session:{session_id}", ttl, str(user_id))
        return session_id

    async def get_user_id(self, session_id: str) -> int | None:
        """Get user ID from session ID."""
        redis = self.get_redis()
        user_id = redis.get(f"session:{session_id}")
        return int(user_id) if user_id else None

    async def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        redis = self.get_redis()
        redis.delete(f"session:{session_id}")


class APIKeyManager:
    """Manager for API key operations."""

    @staticmethod
    async def create_api_key(db: AsyncSession, user_id: int, name: str) -> APIKey:
        """Create a new API key for a user."""
        api_key = APIKey(
            user_id=user_id,
            key=generate_api_key(),
            name=name,
            is_active=True,
        )
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        return api_key

    @staticmethod
    async def get_api_key(db: AsyncSession, key: str) -> APIKey | None:
        """Get API key by key value."""
        result = await db.execute(
            select(APIKey).where(APIKey.key == key, APIKey.is_active == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_last_used(db: AsyncSession, api_key: APIKey) -> None:
        """Update the last used timestamp of an API key."""
        api_key.last_used = datetime.now()
        await db.commit()

    @staticmethod
    async def revoke_api_key(db: AsyncSession, api_key_id: int, user_id: int) -> bool:
        """Revoke an API key."""
        result = await db.execute(
            select(APIKey).where(
                APIKey.id == api_key_id, APIKey.user_id == user_id
            )
        )
        api_key = result.scalar_one_or_none()
        if api_key:
            api_key.is_active = False
            await db.commit()
            return True
        return False

    @staticmethod
    async def list_user_api_keys(db: AsyncSession, user_id: int) -> list[APIKey]:
        """List all API keys for a user."""
        result = await db.execute(
            select(APIKey).where(APIKey.user_id == user_id).order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())


class UserManager:
    """Manager for user operations."""

    @staticmethod
    async def create_user(db: AsyncSession, username: str, password: str) -> User:
        """Create a new user."""
        user = User(
            username=username,
            password_hash=hash_password(password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
        """Get user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, username: str, password: str
    ) -> User | None:
        """Authenticate a user with username and password."""
        user = await UserManager.get_user_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user


# Global instances
session_manager = SessionManager()
api_key_manager = APIKeyManager()
user_manager = UserManager()
