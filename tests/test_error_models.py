"""Tests for RFC 7807 error models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from magick_mind.models.errors import (
    ErrorResponse,
    ProblemDetails,
    ValidationErrorField,
)


class TestValidationErrorField:
    """Test ValidationErrorField model."""

    def test_required_fields(self):
        """Field and message are required."""
        field = ValidationErrorField(field="email", message="Invalid format")
        assert field.field == "email"
        assert field.message == "Invalid format"
        assert field.code is None

    def test_with_code(self):
        """Code field is optional."""
        field = ValidationErrorField(
            field="password", message="Too short", code="min_length"
        )
        assert field.field == "password"
        assert field.message == "Too short"
        assert field.code == "min_length"

    def test_missing_required_field(self):
        """Missing required fields should raise validation error."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ValidationErrorField(field="email")  # Missing message

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("message",) for e in errors)


class TestProblemDetails:
    """Test ProblemDetails model."""

    def test_minimal_problem_details(self):
        """Minimal valid problem details."""
        problem = ProblemDetails(
            title="Not Found", status=404, detail="Resource not found"
        )
        assert problem.type == "about:blank"  # Default
        assert problem.title == "Not Found"
        assert problem.status == 404
        assert problem.detail == "Resource not found"
        assert problem.instance is None
        assert problem.request_id is None
        assert problem.errors == []

    def test_full_problem_details(self):
        """Full problem details with all fields."""
        problem = ProblemDetails(
            type="https://api.example.com/errors/not-found",
            title="Not Found",
            status=404,
            detail="Mindspace ms-123 not found",
            instance="/v1/mindspaces/ms-123",
            request_id="trace-abc-123",
            errors=[
                ValidationErrorField(
                    field="mindspace_id",
                    message="Invalid format",
                    code="invalid_format",
                )
            ],
        )
        assert problem.type == "https://api.example.com/errors/not-found"
        assert problem.title == "Not Found"
        assert problem.status == 404
        assert problem.detail == "Mindspace ms-123 not found"
        assert problem.instance == "/v1/mindspaces/ms-123"
        assert problem.request_id == "trace-abc-123"
        assert len(problem.errors) == 1
        assert problem.errors[0].field == "mindspace_id"

    def test_status_validation_min(self):
        """Status must be >= 400."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProblemDetails(
                title="Invalid",
                status=200,  # Too low
                detail="Test",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("status",) for e in errors)

    def test_status_validation_max(self):
        """Status must be <= 599."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ProblemDetails(
                title="Invalid",
                status=600,  # Too high
                detail="Test",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("status",) for e in errors)

    def test_status_validation_valid_range(self):
        """Status within 400-599 should be valid."""
        # Test boundaries
        ProblemDetails(title="Bad Request", status=400, detail="Test")
        ProblemDetails(title="Server Error", status=599, detail="Test")

        # Test common codes
        ProblemDetails(title="Not Found", status=404, detail="Test")
        ProblemDetails(title="Internal Error", status=500, detail="Test")

    def test_extra_fields_allowed(self):
        """Additional fields should be allowed (RFC 7807 extension)."""
        problem = ProblemDetails(
            title="Rate Limited",
            status=429,
            detail="Too many requests",
            retry_after=60,  # Extension field
            rate_limit_reset=1234567890,  # Extension field
        )
        assert problem.title == "Rate Limited"
        # Extra fields stored in model
        assert problem.model_extra["retry_after"] == 60
        assert problem.model_extra["rate_limit_reset"] == 1234567890

    def test_empty_errors_list_default(self):
        """Errors field defaults to empty list."""
        problem = ProblemDetails(title="Error", status=400, detail="Test")
        assert problem.errors == []
        assert isinstance(problem.errors, list)


class TestErrorResponse:
    """Test ErrorResponse wrapper model."""

    def test_error_response_wrapper(self):
        """ErrorResponse wraps ProblemDetails."""
        problem = ProblemDetails(
            title="Not Found", status=404, detail="Resource not found"
        )
        response = ErrorResponse(error=problem)

        assert response.error == problem
        assert response.error.title == "Not Found"
        assert response.error.status == 404

    def test_error_response_from_dict(self):
        """Parse ErrorResponse from API response dict."""
        api_response = {
            "error": {
                "type": "about:blank",
                "title": "Bad Request",
                "status": 400,
                "detail": "Invalid request",
                "instance": "/v1/test",
                "request_id": "req-123",
                "errors": [{"field": "name", "message": "Required field missing"}],
            }
        }

        response = ErrorResponse.model_validate(api_response)
        assert response.error.title == "Bad Request"
        assert response.error.status == 400
        assert response.error.detail == "Invalid request"
        assert response.error.instance == "/v1/test"
        assert response.error.request_id == "req-123"
        assert len(response.error.errors) == 1
        assert response.error.errors[0].field == "name"
        assert response.error.errors[0].message == "Required field missing"

    def test_nested_validation(self):
        """Nested validation errors should propagate."""
        with pytest.raises(PydanticValidationError) as exc_info:
            ErrorResponse(
                error={
                    "title": "Error",
                    "status": 200,  # Invalid status
                    "detail": "Test",
                }
            )

        errors = exc_info.value.errors()
        # Should have nested validation error for status
        assert any("status" in str(e["loc"]) for e in errors)
