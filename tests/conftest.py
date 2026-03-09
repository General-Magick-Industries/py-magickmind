"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock


BASE_URL = "https://api.test"

# Standard auth response for mocking login
AUTH_RESPONSE = {
    "access_token": "test-access-token",
    "refresh_token": "test-refresh-token",
    "expires_in": 3600,
    "refresh_expires_in": 86400,
    "token_type": "Bearer",
    "id_token": "test-id-token",
    "not-before-policy": 0,
    "session_state": "test-session-state",
    "scope": "openid profile email",
}


@pytest.fixture
def base_url() -> str:
    """Base URL for testing."""
    return BASE_URL


@pytest.fixture
def test_credentials():
    """Test credentials."""
    return {"email": "test@example.com", "password": "testpass123"}


@pytest.fixture
def auth_response() -> dict[str, str | int]:
    """Standard auth response payload."""
    return AUTH_RESPONSE.copy()


@pytest.fixture
def mock_auth(httpx_mock: HTTPXMock) -> HTTPXMock:
    """Pre-configure auth login mock. Returns httpx_mock for further configuration."""
    httpx_mock.add_response(
        url=f"{BASE_URL}/v1/auth/login",
        method="POST",
        json=AUTH_RESPONSE,
    )
    return httpx_mock


@pytest.fixture
def client(mock_auth):
    """Create a fully wired MagickMind client with mocked auth.

    Usage:
        def test_something(client, mock_auth):
            mock_auth.add_response(url="...", json={...})
            result = client.chat.send(...)
    """
    from magick_mind import MagickMind

    return MagickMind(
        base_url=BASE_URL,
        email="test@test.com",
        password="testpass",
    )
