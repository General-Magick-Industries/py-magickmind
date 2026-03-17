"""Basic smoke tests for SDK structure."""

import base64
import json
from unittest.mock import AsyncMock, patch

import pytest
from magick_mind import MagickMind
from magick_mind.exceptions import MagickMindError


def _make_fake_jwt(sub: str) -> str:
    """Build a minimal fake JWT with the given sub claim."""
    header = (
        base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    )
    payload_bytes = json.dumps({"sub": sub, "exp": 9999999999}).encode()
    payload = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode()
    return f"{header}.{payload}.fakesig"


def test_client_requires_credentials():
    """Test that client requires email and password."""
    with pytest.raises(ValueError, match="Email and password are required"):
        MagickMind(base_url="https://test.com", email="", password="")


def test_client_initialization():
    """Test that client initializes with valid credentials."""
    client = MagickMind(
        base_url="https://test.com", email="test@example.com", password="password123"
    )

    assert client.config.base_url == "https://test.com"
    assert client.config.normalized_base_url() == "https://test.com"


def test_client_repr():
    """Test string representation of client."""
    client = MagickMind(
        base_url="https://test.com", email="test@example.com", password="password123"
    )

    repr_str = repr(client)
    assert "MagickMind" in repr_str
    assert "EmailPassword" in repr_str


async def test_client_context_manager():
    """Test client can be used as async context manager."""
    async with MagickMind(
        base_url="https://test.com", email="test@example.com", password="password123"
    ) as client:
        assert client is not None


async def test_user_id_returns_sub_from_jwt():
    """get_user_id() extracts the 'sub' claim from the current JWT."""
    client = MagickMind(
        base_url="https://test.com", email="test@example.com", password="password123"
    )
    fake_token = _make_fake_jwt("user-abc-123")
    with patch.object(
        client.auth, "get_token_async", new=AsyncMock(return_value=fake_token)
    ):
        assert await client.get_user_id() == "user-abc-123"


async def test_user_id_raises_on_invalid_token():
    """get_user_id() raises MagickMindError when the JWT has no 'sub' claim."""
    client = MagickMind(
        base_url="https://test.com", email="test@example.com", password="password123"
    )
    # A JWT payload with no 'sub' field
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(b'{"exp":9999}').rstrip(b"=").decode()
    bad_token = f"{header}.{payload}.sig"
    with patch.object(
        client.auth, "get_token_async", new=AsyncMock(return_value=bad_token)
    ):
        with pytest.raises(MagickMindError, match="Failed to extract user_id"):
            await client.get_user_id()


async def test_user_id_raises_on_garbage_token():
    """get_user_id() raises MagickMindError when the token is not a valid JWT."""
    client = MagickMind(
        base_url="https://test.com", email="test@example.com", password="password123"
    )
    with patch.object(
        client.auth, "get_token_async", new=AsyncMock(return_value="not.a.jwt")
    ):
        with pytest.raises(MagickMindError, match="Failed to extract user_id"):
            await client.get_user_id()
