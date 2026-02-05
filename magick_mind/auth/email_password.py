"""Email/password authentication provider."""

import time
from typing import Dict, Optional
import httpx

from magick_mind.auth.base import AuthProvider
from magick_mind.exceptions import AuthenticationError, TokenExpiredError
from magick_mind.models.auth import LoginRequest, RefreshRequest, TokenResponse
from magick_mind.routes import Routes


import logging

logger = logging.getLogger(__name__)


class EmailPasswordAuth(AuthProvider):
    """
    Email/password authentication using bifrost's /v1/auth/login endpoint.

    Automatically handles token refresh when the access token expires.

    Example:
        auth = EmailPasswordAuth(
            email="user@example.com",
            password="your_password",
            base_url="https://bifrost.example.com"
        )
        # Login happens automatically on first request
        headers = auth.get_headers()
    """

    def __init__(self, email: str, password: str, base_url: str, timeout: float = 30.0):
        """
        Initialize email/password authentication.

        Args:
            email: User email address
            password: User password
            base_url: Base URL of the Bifrost API
            timeout: Request timeout in seconds
        """
        if not email or not password:
            raise ValueError("Email and password are required")

        self.email = email
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Token storage
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._refresh_expires_at: float = 0.0

    def get_headers(self) -> Dict[str, str]:
        """
        Get authorization header with access token.
        Automatically logs in or refreshes token if needed.
        """
        self.refresh_if_needed()

        if not self._access_token:
            raise AuthenticationError(
                "Not authenticated. Failed to obtain access token."
            )

        return {"Authorization": f"Bearer {self._access_token}"}

    def is_authenticated(self) -> bool:
        """Check if currently authenticated with a valid token."""
        return bool(self._access_token) and time.time() < self._token_expires_at

    def get_token(self) -> str:
        """Get raw access token, refreshing if needed."""
        self.refresh_if_needed()
        if not self._access_token:
            raise AuthenticationError(
                "Not authenticated. Failed to obtain access token."
            )
        return self._access_token

    def refresh_if_needed(self) -> None:
        """
        Refresh authentication if needed.

        Logic:
        1. If no access token, perform login
        2. If access token expired but refresh token valid, refresh
        3. If both expired, perform login
        """
        current_time = time.time()

        # No token yet - need to login
        if not self._access_token:
            self._login()
            return

        # Access token still valid
        if current_time < self._token_expires_at:
            return

        # Access token expired - try refresh if refresh token is valid
        if self._refresh_token and current_time < self._refresh_expires_at:
            try:
                self._refresh()
                return
            except Exception:
                # Refresh failed, fall back to login
                pass

        # Refresh not available or failed - do full login
        self._login()

    def _login(self) -> None:
        """Perform login to get initial tokens."""
        login_url = f"{self.base_url}{Routes.AUTH_LOGIN}"

        payload = LoginRequest(email=self.email, password=self.password)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(login_url, json=payload.model_dump())
                response.raise_for_status()

                # Parse and validate response (flat TokenResponse, no wrapper)
                data = TokenResponse(**response.json())
                self._store_tokens(data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid email or password", status_code=401)
            raise AuthenticationError(
                f"Login failed: {str(e)}", status_code=e.response.status_code
            )
        except httpx.RequestError as e:
            raise AuthenticationError(f"Network error during login: {str(e)}")

    def _refresh(self) -> None:
        """Refresh the access token using the refresh token."""
        # Note: Bifrost might have a refresh endpoint, but if not,
        # we'll just re-login. This can be updated when the endpoint is available.
        refresh_url = f"{self.base_url}{Routes.AUTH_REFRESH}"

        if not self._refresh_token:
            raise TokenExpiredError("No refresh token available")

        try:
            refresh_req = RefreshRequest(refresh_token=self._refresh_token)
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(refresh_url, json=refresh_req.model_dump())
                response.raise_for_status()

                # Parse and validate response (flat TokenResponse, no wrapper)
                data = TokenResponse(**response.json())
                self._store_tokens(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise TokenExpiredError("Refresh token expired or invalid")
            raise AuthenticationError(
                f"Token refresh failed: {str(e)}", status_code=e.response.status_code
            )
        except httpx.RequestError as e:
            raise AuthenticationError(f"Network error during token refresh: {str(e)}")

    def _store_tokens(self, token_data: TokenResponse) -> None:
        """Store tokens and calculate expiration times."""
        current_time = time.time()

        # Access via attributes (Pydantic model)
        self._access_token = token_data.access_token
        self._refresh_token = token_data.refresh_token

        # Add buffer of 10 seconds to avoid edge cases
        # Default fallback values handled by Pydantic model structure if strict
        # But here fields are required except options.
        # API should ensure these exist.
        expires_in = token_data.expires_in - 10
        self._token_expires_at = current_time + max(expires_in, 0)

        refresh_expires_in = token_data.refresh_expires_in - 10
        self._refresh_expires_at = current_time + max(refresh_expires_in, 0)

    async def get_token_async(self) -> str:
        """Get raw access token asynchronously, refreshing if needed."""
        await self.refresh_if_needed_async()
        if not self._access_token:
            raise AuthenticationError(
                "Not authenticated. Failed to obtain access token."
            )
        return self._access_token

    async def refresh_if_needed_async(self) -> None:
        """Async version of refresh_if_needed."""
        current_time = time.time()

        if not self._access_token:
            await self._login_async()
            return

        if current_time < self._token_expires_at:
            return

        if self._refresh_token and current_time < self._refresh_expires_at:
            try:
                await self._refresh_async()
                return
            except Exception:
                pass

        await self._login_async()

    async def _login_async(self) -> None:
        """Async login."""
        login_url = f"{self.base_url}{Routes.AUTH_LOGIN}"
        payload = LoginRequest(email=self.email, password=self.password)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(login_url, json=payload.model_dump())
                response.raise_for_status()

                # Parse and validate response (flat TokenResponse, no wrapper)
                data = TokenResponse(**response.json())
                self._store_tokens(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid email or password", status_code=401)
            raise AuthenticationError(
                f"Login failed: {str(e)}", status_code=e.response.status_code
            )
        except httpx.RequestError as e:
            raise AuthenticationError(f"Network error during login: {str(e)}")

    async def _refresh_async(self) -> None:
        """Async refresh."""
        refresh_url = f"{self.base_url}{Routes.AUTH_REFRESH}"
        if not self._refresh_token:
            raise TokenExpiredError("No refresh token available")

        try:
            refresh_req = RefreshRequest(refresh_token=self._refresh_token)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(refresh_url, json=refresh_req.model_dump())
                response.raise_for_status()

                # Parse and validate response (flat TokenResponse, no wrapper)
                data = TokenResponse(**response.json())
                self._store_tokens(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise TokenExpiredError("Refresh token expired or invalid")
            raise AuthenticationError(
                f"Token refresh failed: {str(e)}", status_code=e.response.status_code
            )
        except httpx.RequestError as e:
            raise AuthenticationError(f"Network error during token refresh: {str(e)}")

    async def get_headers_async(self) -> Dict[str, str]:
        """
        Async version of get_headers.
        """
        await self.refresh_if_needed_async()
        if not self._access_token:
            raise AuthenticationError("Not authenticated.")
        return {"Authorization": f"Bearer {self._access_token}"}
