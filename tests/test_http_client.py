"""Tests for HTTP client error handling with RFC 7807 support.

Tests the _handle_response() method to ensure it correctly parses:
1. RFC 7807 error responses (primary format)
2. OpenAI middleware fallback format
3. Malformed responses
4. Rate limiting (429)
"""

from __future__ import annotations

import json
from unittest.mock import Mock

import httpx
import pytest

from magick_mind.exceptions import (
    MagickMindError,
    ProblemDetailsException,
    RateLimitError,
    ValidationError,
)
from magick_mind.http.client import HTTPClient


class TestHTTPClientSuccessPath:
    """Test successful response handling."""

    def test_handle_response_success_with_json(self):
        """Test successful response with JSON body."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}

        client = HTTPClient(Mock(), Mock())
        result = client._handle_response(mock_response)

        assert result == {"data": "success"}

    def test_handle_response_success_empty_body(self):
        """Test successful response with empty body."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 204
        mock_response.json.side_effect = Exception("No content")

        client = HTTPClient(Mock(), Mock())
        result = client._handle_response(mock_response)

        assert result == {}


class TestHTTPClientRFC7807Parsing:
    """Test RFC 7807 error response parsing."""

    def test_handle_response_rfc7807_404(self):
        """Test RFC 7807 format for 404 Not Found."""
        error_data = {
            "error": {
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "detail": "Mindspace not found",
                "instance": "/v1/mindspace/ms-123",
                "request_id": "req-abc123",
            }
        }

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = error_data

        client = HTTPClient(Mock(), Mock())

        with pytest.raises(ProblemDetailsException) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert exc.status == 404
        assert exc.title == "Not Found"
        assert exc.detail == "Mindspace not found"
        assert exc.instance == "/v1/mindspace/ms-123"
        assert exc.request_id == "req-abc123"
        assert exc.type_uri == "about:blank"

    def test_handle_response_rfc7807_validation_error(self):
        """Test RFC 7807 format for 400 Bad Request with field errors."""
        error_data = {
            "error": {
                "type": "about:blank",
                "title": "Validation Error",
                "status": 400,
                "detail": "Invalid request parameters",
                "request_id": "req-xyz789",
                "errors": [
                    {
                        "field": "name",
                        "message": "Name is required",
                        "code": "required",
                    },
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "invalid_format",
                    },
                ],
            }
        }

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = error_data

        client = HTTPClient(Mock(), Mock())

        with pytest.raises(ValidationError) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert exc.status == 400
        assert exc.title == "Validation Error"
        assert len(exc.validation_errors) == 2
        assert exc.validation_errors[0].field == "name"
        assert exc.validation_errors[0].message == "Name is required"
        assert exc.validation_errors[1].field == "email"

        # Test get_field_errors() helper
        field_errors = exc.get_field_errors()
        assert "name" in field_errors
        assert "email" in field_errors
        assert field_errors["name"] == ["Name is required"]
        assert field_errors["email"] == ["Invalid email format"]

    def test_handle_response_rfc7807_500_internal_error(self):
        """Test RFC 7807 format for 500 Internal Server Error."""
        error_data = {
            "error": {
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred",
                "request_id": "req-error500",
            }
        }

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.return_value = error_data

        client = HTTPClient(Mock(), Mock())

        with pytest.raises(ProblemDetailsException) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert exc.status == 500
        assert exc.title == "Internal Server Error"


class TestHTTPClientRateLimiting:
    """Test rate limiting (429) handling."""

    def test_handle_response_rate_limit_rfc7807(self):
        """Test 429 rate limit with RFC 7807 format."""
        error_data = {
            "error": {
                "type": "about:blank",
                "title": "Too Many Requests",
                "status": 429,
                "detail": "Rate limit exceeded. Try again in 60 seconds.",
                "request_id": "req-rate-limit",
            }
        }

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.json.return_value = error_data

        client = HTTPClient(Mock(), Mock())

        with pytest.raises(RateLimitError) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert exc.status_code == 429
        assert "Rate limit exceeded" in exc.message

    def test_handle_response_rate_limit_fallback(self):
        """Test 429 rate limit with non-JSON fallback."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        mock_response.text = "Rate limit exceeded"

        client = HTTPClient(Mock(), Mock())

        with pytest.raises(RateLimitError) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert exc.status_code == 429
        assert "Rate limit exceeded" in exc.message


class TestHTTPClientOpenAIMiddlewareFallback:
    """Test OpenAI middleware legacy format fallback."""

    def test_handle_response_openai_middleware_401(self):
        """Test OpenAI middleware format: {"code": 401, "message": "..."}"""
        error_data = {"code": 401, "message": "Unauthorized access"}

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.json.return_value = error_data

        client = HTTPClient(Mock(), Mock())

        with pytest.raises(ProblemDetailsException) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert exc.status == 401
        assert exc.detail == "Unauthorized access"
        assert exc.title == "Unauthorized"  # from http.client.responses

    def test_handle_response_openai_middleware_403(self):
        """Test OpenAI middleware format for 403 Forbidden."""
        error_data = {"code": 403, "message": "Access forbidden"}

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = error_data

        client = HTTPClient(Mock(), Mock())

        with pytest.raises(ProblemDetailsException) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert exc.status == 403
        assert exc.detail == "Access forbidden"
        assert exc.title == "Forbidden"


class TestHTTPClientMalformedResponses:
    """Test handling of malformed error responses."""

    def test_handle_response_malformed_rfc7807_missing_fields(self):
        """Test malformed RFC 7807 response missing required fields."""
        error_data = {
            "error": {
                # Missing required fields: title, status, detail
                "type": "about:blank"
            }
        }

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = error_data

        client = HTTPClient(Mock(), Mock())

        with pytest.raises(MagickMindError) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert "Malformed error response" in exc.message

    def test_handle_response_malformed_json(self):
        """Test non-JSON error response."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "<html>Internal Server Error</html>"

        client = HTTPClient(Mock(), Mock())

        with pytest.raises(MagickMindError) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert "Non-JSON error response" in exc.message
        assert exc.status_code == 500

    def test_handle_response_unknown_format(self):
        """Test unknown error response format."""
        error_data = {"unknown_field": "some value", "another": 123}

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = error_data

        client = HTTPClient(Mock(), Mock())

        with pytest.raises(MagickMindError) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert "Unknown error response format" in exc.message


class TestHTTPClientEdgeCases:
    """Test edge cases."""

    def test_handle_response_400_without_field_errors(self):
        """Test 400 without field errors raises ProblemDetailsException, not ValidationError."""
        error_data = {
            "error": {
                "type": "about:blank",
                "title": "Bad Request",
                "status": 400,
                "detail": "Invalid request",
                # No errors array
            }
        }

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = error_data

        client = HTTPClient(Mock(), Mock())

        # Should raise ProblemDetailsException, NOT ValidationError
        with pytest.raises(ProblemDetailsException) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert exc.status == 400
        # Should NOT be ValidationError
        assert not isinstance(exc, ValidationError)

    def test_handle_response_400_with_empty_errors_array(self):
        """Test 400 with empty errors array."""
        error_data = {
            "error": {
                "type": "about:blank",
                "title": "Bad Request",
                "status": 400,
                "detail": "Invalid request",
                "errors": [],  # Empty array
            }
        }

        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = error_data

        client = HTTPClient(Mock(), Mock())

        # Empty errors array → ProblemDetailsException, not ValidationError
        with pytest.raises(ProblemDetailsException) as exc_info:
            client._handle_response(mock_response)

        exc = exc_info.value
        assert not isinstance(exc, ValidationError)
