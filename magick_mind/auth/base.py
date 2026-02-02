"""Base authentication provider interface."""

from abc import ABC, abstractmethod
from typing import Dict


class AuthProvider(ABC):
    """Base class for authentication providers."""

    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            Dictionary of HTTP headers to include in requests
        """
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Check if the provider is currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        pass

    @abstractmethod
    def get_token(self) -> str:
        """
        Get the raw access token.
        Should handle refresh if needed.

        Returns:
            Raw access token string
        """
        pass

    async def get_token_async(self) -> str:
        """
        Get the raw access token asynchronously.
        Override in subclasses that support async.
        """
        return self.get_token()

    def refresh_if_needed(self) -> None:
        """
        Refresh authentication credentials if needed.
        Override this method in subclasses that support token refresh.
        """
        pass
