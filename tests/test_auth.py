"""Auth lifecycle tests."""

from __future__ import annotations

import pytest
import time_machine
from pytest_httpx import HTTPXMock

from magick_mind.auth.email_password import EmailPasswordAuth, compute_token_expiry
from magick_mind.exceptions import AuthenticationError

BASE_URL = "https://api.test"

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


class TestComputeTokenExpiry:
    """Pure function tests — no mocking, no I/O."""

    def test_subtracts_buffer(self):
        access_exp, refresh_exp = compute_token_expiry(
            expires_in=3600,
            refresh_expires_in=86400,
            current_time=1000.0,
        )
        assert access_exp == 1000.0 + 3600 - 10  # buffer=10
        assert refresh_exp == 1000.0 + 86400 - 10

    def test_clamps_to_zero(self):
        """Token with expires_in < buffer should clamp to current_time."""
        access_exp, _ = compute_token_expiry(
            expires_in=5,
            refresh_expires_in=86400,
            current_time=1000.0,
        )
        assert access_exp == 1000.0  # max(5-10, 0) = 0

    def test_custom_buffer(self):
        access_exp, _ = compute_token_expiry(
            expires_in=100,
            refresh_expires_in=200,
            current_time=0.0,
            buffer_seconds=50.0,
        )
        assert access_exp == 50.0  # 0 + max(100-50, 0)


class TestAuthLifecycle:
    """Full auth lifecycle tests with time control."""

    @pytest.fixture
    def auth_mock(self, httpx_mock: HTTPXMock) -> HTTPXMock:
        """Mock auth endpoints."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/auth/login",
            method="POST",
            json=AUTH_RESPONSE,
        )
        return httpx_mock

    @time_machine.travel(0, tick=False)
    def test_login_on_first_get_headers(self, auth_mock):
        """First get_headers() triggers login."""
        auth = EmailPasswordAuth(email="a@b.com", password="p", base_url=BASE_URL)
        headers = auth.get_headers()
        assert headers["Authorization"] == "Bearer test-access-token"

    @time_machine.travel(0, tick=False)
    def test_auto_refresh_when_expired(self, auth_mock):
        """Access token expires → triggers refresh (not re-login)."""
        auth_mock.add_response(
            url=f"{BASE_URL}/v1/auth/refresh",
            method="POST",
            json={
                **AUTH_RESPONSE,
                "access_token": "refreshed-token",
                "refresh_token": "new-refresh",
            },
        )

        auth = EmailPasswordAuth(email="a@b.com", password="p", base_url=BASE_URL)

        with time_machine.travel(0, tick=False) as t:
            auth.get_headers()  # triggers login
            assert auth._access_token == "test-access-token"

            t.shift(
                3595
            )  # jump past access token expiry (3600 - 10 buffer = 3590 is the expiry)
            auth.refresh_if_needed()
            assert auth._access_token == "refreshed-token"

    @time_machine.travel(0, tick=False)
    def test_relogin_when_both_expired(self, httpx_mock: HTTPXMock):
        """Both tokens expired → triggers full re-login."""
        # First login
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/auth/login",
            method="POST",
            json={**AUTH_RESPONSE, "expires_in": 60, "refresh_expires_in": 120},
        )
        # Second login (after both expire)
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/auth/login",
            method="POST",
            json={**AUTH_RESPONSE, "access_token": "relogin-token"},
        )

        auth = EmailPasswordAuth(email="a@b.com", password="p", base_url=BASE_URL)

        with time_machine.travel(0, tick=False) as t:
            auth.get_headers()  # first login
            t.shift(200)  # past both expiries
            auth.refresh_if_needed()
            assert auth._access_token == "relogin-token"

    def test_invalid_credentials_raises(self, httpx_mock: HTTPXMock):
        """401 from login → AuthenticationError."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/auth/login",
            method="POST",
            status_code=401,
        )

        auth = EmailPasswordAuth(email="bad@b.com", password="wrong", base_url=BASE_URL)
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            auth.get_headers()

    def test_empty_email_raises(self):
        """Empty email raises ValueError."""
        with pytest.raises(ValueError, match="Email and password are required"):
            EmailPasswordAuth(email="", password="pass", base_url=BASE_URL)

    def test_empty_password_raises(self):
        """Empty password raises ValueError."""
        with pytest.raises(ValueError, match="Email and password are required"):
            EmailPasswordAuth(email="a@b.com", password="", base_url=BASE_URL)
