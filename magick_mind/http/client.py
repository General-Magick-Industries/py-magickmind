"""HTTP client for making API requests."""

from __future__ import annotations

import http.client
import json
import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import ValidationError as PydanticValidationError

from magick_mind.auth.base import AuthProvider
from magick_mind.config import SDKConfig
from magick_mind.exceptions import (
    MagickMindError,
    ProblemDetailsException,
    RateLimitError,
    ValidationError,
)
from magick_mind.models.errors import ErrorResponse, ProblemDetails

logger = logging.getLogger(__name__)

# Type alias: All HTTP methods return parsed JSON data, NOT httpx.Response objects.
# This prevents bugs like calling `.json()` on an already-parsed dict.
JSONResponse = Dict[str, Any]


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

    def _handle_response(self, response: httpx.Response) -> JSONResponse:
        """
        Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response data

        Raises:
            ProblemDetailsException: For RFC 7807 errors
            ValidationError: For 400 Bad Request with field errors
            RateLimitError: For rate limiting
            MagickMindError: For malformed responses
        """
        # Success path
        if response.status_code < 400:
            try:
                return response.json()
            except Exception:
                return {}

        # Rate limiting (special case)
        if response.status_code == 429:
            # Try RFC 7807 first
            try:
                error_response = ErrorResponse.model_validate(response.json())
                raise RateLimitError(
                    error_response.error.detail,
                    status_code=429,
                )
            except (json.JSONDecodeError, PydanticValidationError):
                raise RateLimitError(
                    "Rate limit exceeded",
                    status_code=429,
                )

        # Parse error response
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise MagickMindError(
                f"Non-JSON error response: {response.text[:200]}",
                status_code=response.status_code,
            )

        # RFC 7807 format (98% of Bifrost endpoints)
        if "error" in data and isinstance(data["error"], dict):
            try:
                error_response = ErrorResponse.model_validate(data)
                problem = error_response.error

                # Raise ValidationError for 400 with field errors
                if problem.status == 400 and problem.errors:
                    raise ValidationError(problem, raw_response=data)

                # Generic ProblemDetailsException
                raise ProblemDetailsException(problem, raw_response=data)

            except PydanticValidationError as e:
                # Malformed RFC 7807 response
                logger.warning("Malformed RFC 7807 response: %s", e)
                raise MagickMindError(
                    f"Malformed error response: {data.get('error', {}).get('detail', 'Unknown error')}",
                    status_code=response.status_code,
                )

        # Fallback: OpenAI middleware format {"code": 401, "message": "..."}
        if "code" in data and "message" in data:
            logger.debug("Received legacy error format from OpenAI middleware")
            # Convert to RFC 7807 structure
            problem = ProblemDetails(
                type="about:blank",
                title=http.client.responses.get(data["code"], "Error"),
                status=data["code"],
                detail=data["message"],
            )
            raise ProblemDetailsException(problem, raw_response=data)

        # Unknown format
        raise MagickMindError(
            f"Unknown error response format: {data}",
            status_code=response.status_code,
        )

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> JSONResponse:
        """
        Make a GET request.

        Args:
            path: API endpoint path
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If JWT token is invalid (auto-refreshed if expired)
            ProblemDetailsException: For API errors (4xx, 5xx) following RFC 7807
            ValidationError: For 400 Bad Request with field-level errors
            RateLimitError: For 429 Too Many Requests
            MagickMindError: For unexpected errors or malformed responses

        Example:
            >>> response = client.http.get("/v1/mindspaces")
            >>> print(response['data'])
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
    ) -> JSONResponse:
        """
        Make a POST request.

        Args:
            path: API endpoint path
            json: Request body as dictionary
            headers: Additional headers

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If JWT token is invalid (auto-refreshed if expired)
            ProblemDetailsException: For API errors (4xx, 5xx) following RFC 7807
            ValidationError: For 400 Bad Request with field-level validation errors
            RateLimitError: For 429 Too Many Requests
            MagickMindError: For unexpected errors or malformed responses

        Example:
            >>> response = client.http.post(
            ...     "/v1/magickmind/chat",
            ...     json={"message": "Hello", "mindspace_id": "mind-123"}
            ... )
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
    ) -> JSONResponse:
        """
        Make a PUT request.

        Args:
            path: API endpoint path
            json: Request body as dictionary
            headers: Additional headers

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If JWT token is invalid (auto-refreshed if expired)
            ProblemDetailsException: For API errors (4xx, 5xx) following RFC 7807
            ValidationError: For 400 Bad Request with field-level validation errors
            RateLimitError: For 429 Too Many Requests
            MagickMindError: For unexpected errors or malformed responses
        """
        # Refresh auth if needed
        self.auth.refresh_if_needed()

        url = self._build_url(path)
        request_headers = self._get_headers(headers)

        response = self._client.put(url, json=json, headers=request_headers)
        return self._handle_response(response)

    def delete(
        self, path: str, headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        """
        Make a DELETE request.

        Args:
            path: API endpoint path
            headers: Additional headers

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If JWT token is invalid (auto-refreshed if expired)
            ProblemDetailsException: For API errors (4xx, 5xx) following RFC 7807
            ValidationError: For 400 Bad Request with field-level validation errors
            RateLimitError: For 429 Too Many Requests
            MagickMindError: For unexpected errors or malformed responses
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
