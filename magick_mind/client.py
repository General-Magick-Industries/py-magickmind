"""Main Magick Mind SDK client."""

from typing import Optional

from magick_mind.auth import AuthProvider, EmailPasswordAuth
from magick_mind.config import SDKConfig
from magick_mind.http import HTTPClient
from magick_mind.realtime import RealtimeClient


class MagickMind:
    """
    Main client for the Magick Mind SDK.

    This is the primary interface for interacting with the Bifrost Magick Mind API.

    Currently provides:
    - Authentication (email/password with JWT, automatic refresh)
    - HTTP client for making authenticated requests
    - Realtime client for WebSocket connections (async)

    Example:
        # Initialize client
        client = MagickMind(
            email="user@example.com",
            password="your_password",
            base_url="https://bifrost.example.com"
        )

        # Use HTTP client directly
        response = client.http.post(
            "/v1/magickmind/chat",
            json={
                "api_key": "sk-...",
                "message": "Hello!",
                "chat_id": "123",
                "sender_id": "user-456"
            }
        )

        # See docs/contributing/resource_implementation_guide/ for how to add
        # typed resources like client.v1.chat.send(...)
        response = client.http.post("/v1/magickmind/chat", ...)

        # Use Realtime client (in async context)
        async def main():
            # Pass handler to connect() to receive server-side publications
            await client.realtime.connect(events=MyHandler())
            # Subscribe via RPC
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

    def test_connection(self) -> bool:
        """Test the connection to the API."""
        try:
            # This assumes there's a health check or similar endpoint
            response = self.http.get("/health")
            return response.get("success", False)
        except Exception:
            return False

    def is_authenticated(self) -> bool:
        """
        Check if the client is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        """Check if the client is authenticated."""
        return self.auth.is_authenticated()

    def close(self) -> None:
        """Close the client and cleanup resources."""
        self._http.close()
        # Realtime client might need async close?
        # But close() here is typically sync.
        # User should probably manage realtime lifecycle themselves if async.

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"MagickMind(base_url='{self.config.base_url}', auth='EmailPassword')"
