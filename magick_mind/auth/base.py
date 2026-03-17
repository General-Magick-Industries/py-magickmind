"""Base authentication provider interface."""

from abc import ABC, abstractmethod
from typing import Dict


class AuthProvider(ABC):
    """Base class for authentication providers."""

    @abstractmethod
    async def get_headers_async(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests (async).

        Returns:
            Dictionary of HTTP headers to include in requests
        """
        ...

    @abstractmethod
    async def refresh_if_needed_async(self) -> None:
        """
        Refresh authentication credentials if needed (async).
        Implementations should handle login and token refresh logic.
        """
        ...

    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Check if the provider is currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        ...

    @abstractmethod
    async def get_token_async(self) -> str:
        """
        Get the raw access token asynchronously.
        Should handle refresh if needed.

        Returns:
            Raw access token string
        """
        ...
