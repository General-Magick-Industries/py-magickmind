"""Base class for API resource clients."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..http import HTTPClient


class BaseResource:
    """
    Base class for all resource clients.

    Resource clients encapsulate API endpoints for specific domains
    (e.g., chat, history, users, mindspaces).

    For a complete implementation example, see docs/contributing/resource_implementation_guide/

    Example:
        class ChatResourceV1(BaseResource):
            def send(self, api_key: str, message: str, **kwargs):
                return self._http.post("/v1/magickmind/chat", json={...})
    """

    def __init__(self, http_client: "HTTPClient"):
        """
        Initialize resource client.

        Args:
            http_client: HTTP client for making API requests
        """
        self._http = http_client
