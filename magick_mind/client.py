"""Main Magick Mind SDK client."""

from typing import Optional

from magick_mind.auth import AuthProvider, EmailPasswordAuth
from magick_mind.config import SDKConfig
from magick_mind.http import HTTPClient


class MagickMind:
    """
    Main client for the Magick Mind SDK.

    This is the primary interface for interacting with the Bifrost Magick Mind API.

    Currently provides:
    - Authentication (email/password with JWT, automatic refresh)
    - HTTP client for making authenticated requests

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
    """

    def __init__(
        self,
        base_url: str,
        email: str,
        password: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        """
        Initialize the Magick Mind client.

        Args:
            base_url: Base URL of the Bifrost API (e.g., https://bifrost.example.com)
            email: User email for authentication
            password: User password for authentication
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates

        Raises:
            ValueError: If authentication parameters are invalid
        """
        if not email or not password:
            raise ValueError("Email and password are required for authentication")

        # Create configuration
        self.config = SDKConfig(
            base_url=base_url, timeout=timeout, verify_ssl=verify_ssl
        )

        # Create authentication provider (email/password with JWT)
        self.auth: AuthProvider = EmailPasswordAuth(
            email=email, password=password, base_url=base_url, timeout=timeout
        )

        # Create HTTP client (private, accessed via property)
        self._http = HTTPClient(config=self.config, auth=self.auth)

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

    def test_connection(self) -> bool:
        """
        Test the connection to the API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # This assumes there's a health check or similar endpoint
            # Update the endpoint based on what's actually available
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
        return self.auth.is_authenticated()

    def close(self) -> None:
        """Close the client and cleanup resources."""
        self._http.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"MagickMind(base_url='{self.config.base_url}', auth='EmailPassword')"
