"""Main Magick Mind SDK client."""

from __future__ import annotations

from typing import Optional

from magick_mind.auth import AuthProvider, EmailPasswordAuth
from magick_mind.config import SDKConfig
from magick_mind.exceptions import MagickMindError
from magick_mind.http import HTTPClient
from magick_mind.realtime import RealtimeClient


class MagickMind:
    """
    Main client for the Magick Mind SDK.

    This is the primary interface for interacting with the Bifrost Magick Mind API.

    Provides:
    - Authentication (email/password with JWT, automatic refresh)
    - Typed resources (v1.chat, etc.) with Pydantic validation
    - HTTP client for direct API access
    - Realtime client for WebSocket connections (async)

    Example:
        # Initialize client
        client = MagickMind(
            email="user@example.com",
            password="your_password",
            base_url="https://bifrost.example.com"
        )

        # Use typed resources (recommended)
        response = client.v1.chat.send(
            api_key="sk-...",
            mindspace_id="mind-123",
            message="Hello!",
            sender_id="user-456"
        )
        print(response.content.content)  # AI response

        # Or use convenience alias
        response = client.chat.send(...)

        # Use HTTP client directly for experimental endpoints
        response = client.http.post("/experimental/endpoint", json={...})

        # Use Realtime client (in async context)
        async def main():
            await client.realtime.connect()
            await client.realtime.subscribe(target_user_id="user-456")
    """

    def __init__(
        self,
        base_url: str,
        email: str,
        password: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        ws_endpoint: Optional[str] = None,
    ):
        """
        Initialize the Magick Mind client.

        Args:
            base_url: Base URL of the Bifrost API (e.g., https://bifrost.example.com)
            email: User email for authentication
            password: User password for authentication
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            ws_endpoint: WebSocket URL (Required for .realtime usage)
        """
        if not email or not password:
            raise ValueError("Email and password are required for authentication")

        # Create configuration
        self.config = SDKConfig(
            base_url=base_url,
            timeout=timeout,
            verify_ssl=verify_ssl,
            ws_endpoint=ws_endpoint,
        )

        # Create authentication provider (email/password with JWT)
        self.auth: AuthProvider = EmailPasswordAuth(
            email=email, password=password, base_url=base_url, timeout=timeout
        )

        # Create HTTP client (private, accessed via property)
        self._http = HTTPClient(config=self.config, auth=self.auth)

        # Create Realtime client (private, accessed via property)
        self._realtime = RealtimeClient(auth=self.auth, ws_url=ws_endpoint)

        # Initialize typed resources
        from magick_mind.resources import V1Resources

        self.v1 = V1Resources(self._http)

        # Convenience alias for default version
        self.chat = self.v1.chat
        self.mindspace = self.v1.mindspace

    @property
    def http(self) -> HTTPClient:
        """
        Low-level HTTP client bound to this MagickMind instance.

        Features:
        - Uses same base_url and configuration
        - Automatically attaches authentication tokens
        - Applies centralized error mapping
        - Auto-refreshes expired tokens

        Intended for:
        - Bifrost developers testing new endpoints
        - Power users needing direct API access
        - Experimenting with endpoints before implementing resources

        Example:
            # Test a new endpoint directly
            response = client.http.post(
                "/experimental/new-feature",
                json={"test": "data"}
            )

            # Quick one-off calls
            response = client.http.get("/v1/status")

        Returns:
            HTTPClient: Configured HTTP client instance
        """
        return self._http

    @property
    def realtime(self) -> RealtimeClient:
        """
        Realtime WebSocket client.

        Note: This client is ASYNC. You must use it within an async context.

        Features:
        - Authenticated WebSocket connection
        - RPC subscriptions (Bifrost specific)
        - Handling disconnects/reconnects (via centrifuge-python)

        Returns:
            RealtimeClient: Configured async realtime client
        """
        return self._realtime

    async def get_user_id(self) -> str:
        """
        The authenticated user's ID (JWT ``sub`` claim).

        Useful for subscribing to your own realtime events::

            user_id = await client.get_user_id()
            await client.realtime.subscribe(target_user_id=user_id)

        Raises:
            MagickMindError: If the current token does not contain a ``sub`` claim
                or cannot be decoded.
        """
        from magick_mind.realtime.client import _extract_jwt_sub

        token = await self.auth.get_token_async()
        uid = _extract_jwt_sub(token)
        if not uid:
            raise MagickMindError("Failed to extract user_id from JWT token")
        return uid

    async def test_connection(self) -> bool:
        """Test the connection to the API."""
        try:
            # This assumes there's a health check or similar endpoint
            response = await self.http.get("/health")
            return response.get("success", False)
        except Exception:
            return False

    def is_authenticated(self) -> bool:
        """
        Check if the client is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self.auth.is_authenticated()

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        await self._http.close()
        await self._realtime.disconnect()

    async def __aenter__(self) -> MagickMind:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"MagickMind(base_url='{self.config.base_url}', auth='EmailPassword')"
