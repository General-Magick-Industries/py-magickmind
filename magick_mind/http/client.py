"""HTTP client for making API requests."""

from typing import Any, Dict, Optional
import httpx

from ..auth.base import AuthProvider
from ..config import SDKConfig
from ..exceptions import APIError, RateLimitError


class HTTPClient:
    """
    HTTP client wrapper for making authenticated API requests.

    Handles:
    - Authentication header injection
    - Error handling and response parsing
    - Retry logic
    - Request/response logging
    """

    def __init__(self, config: SDKConfig, auth: AuthProvider):
        """
        Initialize HTTP client.

        Args:
            config: SDK configuration
            auth: Authentication provider
        """
        self.config = config
        self.auth = auth
        self._client = httpx.Client(
            timeout=config.timeout,
            verify=config.verify_ssl,
        )

    def _get_headers(
        self, extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Build request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Add auth headers
        auth_headers = self.auth.get_headers()
        headers.update(auth_headers)

        # Add any extra headers
        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        base = self.config.normalized_base_url()
        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base}{path}"

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response data

        Raises:
            APIError: For API errors
            RateLimitError: For rate limiting
        """
        # Check for rate limiting
        if response.status_code == 429:
            raise RateLimitError(
                "Rate limit exceeded",
                status_code=429,
                response_data=response.json() if response.text else None,
            )

        # Check for other errors
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get(
                    "message", f"HTTP {response.status_code} error"
                )
            except Exception:
                message = f"HTTP {response.status_code} error"
                error_data = None

            raise APIError(
                message, status_code=response.status_code, response_data=error_data
            )

        # Parse successful response
        try:
            return response.json()
        except Exception:
            return {}

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a GET request.

        Args:
            path: API endpoint path
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data as dictionary
        """
        # Refresh auth if needed
        self.auth.refresh_if_needed()

        url = self._build_url(path)
        request_headers = self._get_headers(headers)

        response = self._client.get(url, params=params, headers=request_headers)
        return self._handle_response(response)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request.

        Args:
            path: API endpoint path
            json: Request body as dictionary
            headers: Additional headers

        Returns:
            Response data as dictionary
        """
        # Refresh auth if needed
        self.auth.refresh_if_needed()

        url = self._build_url(path)
        request_headers = self._get_headers(headers)

        response = self._client.post(url, json=json, headers=request_headers)
        return self._handle_response(response)

    def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a PUT request.

        Args:
            path: API endpoint path
            json: Request body as dictionary
            headers: Additional headers

        Returns:
            Response data as dictionary
        """
        # Refresh auth if needed
        self.auth.refresh_if_needed()

        url = self._build_url(path)
        request_headers = self._get_headers(headers)

        response = self._client.put(url, json=json, headers=request_headers)
        return self._handle_response(response)

    def delete(
        self, path: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make a DELETE request.

        Args:
            path: API endpoint path
            headers: Additional headers

        Returns:
            Response data as dictionary
        """
        # Refresh auth if needed
        self.auth.refresh_if_needed()

        url = self._build_url(path)
        request_headers = self._get_headers(headers)

        response = self._client.delete(url, headers=request_headers)
        return self._handle_response(response)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
