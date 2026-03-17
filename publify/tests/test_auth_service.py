"""Tests for authentication service."""
import pytest

from app.services.auth_service import (
    APIKeyManager,
    UserManager,
    generate_api_key,
    hash_password,
    verify_password,
)


def test_hash_password():
    """Test password hashing."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_verify_password():
    """Test password verification."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_generate_api_key():
    """Test API key generation."""
    key = generate_api_key()

    assert key.startswith("pk_test_") or key.startswith("pk_live_")
    assert len(key) > 40


@pytest.mark.asyncio
async def test_create_user(db_session):
    """Test user creation."""
    user = await UserManager.create_user(db_session, "testuser", "password123")

    assert user.id is not None
    assert user.username == "testuser"
    assert user.password_hash != "password123"


@pytest.mark.asyncio
async def test_get_user_by_username(db_session):
    """Test getting user by username."""
    await UserManager.create_user(db_session, "testuser", "password123")
    user = await UserManager.get_user_by_username(db_session, "testuser")

    assert user is not None
    assert user.username == "testuser"


@pytest.mark.asyncio
async def test_authenticate_user(db_session):
    """Test user authentication."""
    await UserManager.create_user(db_session, "testuser", "password123")
    user = await UserManager.authenticate_user(db_session, "testuser", "password123")

    assert user is not None
    assert user.username == "testuser"

    # Test wrong password
    wrong_user = await UserManager.authenticate_user(db_session, "testuser", "wrongpassword")
    assert wrong_user is None


@pytest.mark.asyncio
async def test_create_api_key(db_session):
    """Test API key creation."""
    user = await UserManager.create_user(db_session, "testuser", "password123")
    api_key = await APIKeyManager.create_api_key(db_session, user.id, "Test Key")

    assert api_key.id is not None
    assert api_key.name == "Test Key"
    assert api_key.key.startswith("pk_test_")
    assert api_key.is_active is True


@pytest.mark.asyncio
async def test_revoke_api_key(db_session):
    """Test API key revocation."""
    user = await UserManager.create_user(db_session, "testuser", "password123")
    api_key = await APIKeyManager.create_api_key(db_session, user.id, "Test Key")

    result = await APIKeyManager.revoke_api_key(db_session, api_key.id, user.id)
    assert result is True

    # Verify it's revoked
    db_session.expire_all()
    revoked_key = await APIKeyManager.get_api_key(db_session, api_key.key)
    assert revoked_key is None  # get_api_key only returns active keys
