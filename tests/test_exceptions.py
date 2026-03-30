"""Tests for RFC 7807 exception classes."""

from __future__ import annotations

import logging

import pytest

from magick_mind.exceptions import (
    MagickMindError,
    ProblemDetailsException,
    ValidationError,
)
from magick_mind.models.errors import ProblemDetails, ValidationErrorField


class TestProblemDetailsException:
    """Tests for ProblemDetailsException."""

    def test_construction_from_problem_details(self):
        """Test constructing exception from ProblemDetails model."""
        problem = ProblemDetails(
            type="https://example.com/errors/not-found",
            title="Resource Not Found",
            status=404,
            detail="The requested mindspace does not exist",
            instance="/v1/mindspace/ms-123",
            request_id="req-abc-123",
        )

        exc = ProblemDetailsException(problem)

        assert exc.type_uri == "https://example.com/errors/not-found"
        assert exc.title == "Resource Not Found"
        assert exc.status == 404
        assert exc.detail == "The requested mindspace does not exist"
        assert exc.instance == "/v1/mindspace/ms-123"
        assert exc.request_id == "req-abc-123"
        assert exc.validation_errors == []
        assert exc.problem == problem

    def test_construction_with_raw_response(self):
        """Test storing raw response data."""
        problem = ProblemDetails(
            title="Bad Request", status=400, detail="Invalid input"
        )
        raw = {
            "error": {"title": "Bad Request", "status": 400, "detail": "Invalid input"}
        }

        exc = ProblemDetailsException(problem, raw_response=raw)

        assert exc.response_data == raw

    def test_logging_with_request_id(self, caplog):
        """Test that exception logs with request_id."""
        problem = ProblemDetails(
            title="Server Error",
            status=500,
            detail="Internal error occurred",
            request_id="req-xyz-789",
            instance="/v1/chat",
        )

        with caplog.at_level(logging.DEBUG):
            ProblemDetailsException(problem)

        assert len(caplog.records) == 1
        log_msg = caplog.records[0].message
        assert "Server Error" in log_msg
        assert "[500]" in log_msg
        assert "Internal error occurred" in log_msg
        assert "request_id=req-xyz-789" in log_msg
        assert "instance=/v1/chat" in log_msg

    def test_logging_without_request_id(self, caplog):
        """Test logging when request_id is None."""
        problem = ProblemDetails(
            title="Unauthorized", status=401, detail="Missing token"
        )

        with caplog.at_level(logging.DEBUG):
            ProblemDetailsException(problem)

        assert len(caplog.records) == 1
        log_msg = caplog.records[0].message
        assert "request_id=none" in log_msg
        assert "instance=none" in log_msg

    def test_str_representation_basic(self):
        """Test __str__ without validation errors or request_id."""
        problem = ProblemDetails(
            title="Not Found", status=404, detail="Resource does not exist"
        )

        exc = ProblemDetailsException(problem)

        assert str(exc) == "[404] Not Found: Resource does not exist"

    def test_str_representation_with_request_id(self):
        """Test __str__ includes request_id when present."""
        problem = ProblemDetails(
            title="Server Error",
            status=500,
            detail="Something went wrong",
            request_id="req-123",
        )

        exc = ProblemDetailsException(problem)

        expected = "[500] Server Error: Something went wrong (request_id: req-123)"
        assert str(exc) == expected

    def test_str_representation_with_validation_errors(self):
        """Test __str__ includes validation errors."""
        problem = ProblemDetails(
            title="Validation Failed",
            status=400,
            detail="Invalid request data",
            errors=[
                ValidationErrorField(field="email", message="Invalid email format"),
                ValidationErrorField(field="password", message="Too short"),
            ],
        )

        exc = ProblemDetailsException(problem)

        result = str(exc)
        assert "[400] Validation Failed: Invalid request data" in result
        assert "Validation errors (2):" in result
        assert "  - email: Invalid email format" in result
        assert "  - password: Too short" in result

    def test_repr_representation(self):
        """Test __repr__ output."""
        problem = ProblemDetails(
            title="Bad Request",
            status=400,
            detail="Invalid data",
            request_id="req-456",
        )

        exc = ProblemDetailsException(problem)

        assert (
            repr(exc)
            == "ProblemDetailsException(status=400, title='Bad Request', request_id='req-456')"
        )

    def test_repr_without_request_id(self):
        """Test __repr__ when request_id is None."""
        problem = ProblemDetails(title="Not Found", status=404, detail="Missing")

        exc = ProblemDetailsException(problem)

        assert (
            repr(exc)
            == "ProblemDetailsException(status=404, title='Not Found', request_id=None)"
        )

    def test_inherits_from_magickmind_error(self):
        """Test that ProblemDetailsException inherits from MagickMindError."""
        problem = ProblemDetails(title="Error", status=500, detail="Something failed")

        exc = ProblemDetailsException(problem)

        assert isinstance(exc, MagickMindError)
        assert exc.status_code == 500
        assert exc.message == "Something failed"


class TestValidationError:
    """Tests for ValidationError subclass."""

    def test_construction_with_status_400(self):
        """Test ValidationError accepts status 400."""
        problem = ProblemDetails(
            title="Validation Failed",
            status=400,
            detail="Invalid fields",
            errors=[
                ValidationErrorField(field="name", message="Required"),
            ],
        )

        exc = ValidationError(problem)

        assert exc.status == 400
        assert exc.title == "Validation Failed"
        assert len(exc.validation_errors) == 1

    def test_rejects_non_400_status(self):
        """Test ValidationError raises ValueError for non-400 status."""
        problem = ProblemDetails(
            title="Server Error", status=500, detail="Internal error"
        )

        with pytest.raises(ValueError, match="ValidationError must have status 400"):
            ValidationError(problem)

    def test_warns_when_no_field_errors(self, caplog):
        """Test warning logged when ValidationError created without field errors."""
        problem = ProblemDetails(
            title="Bad Request", status=400, detail="Invalid data", errors=[]
        )

        with caplog.at_level(logging.WARNING):
            ValidationError(problem)

        warning_logs = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_logs) == 1
        assert "ValidationError created without field errors" in warning_logs[0].message

    def test_get_field_errors_groups_by_field(self):
        """Test get_field_errors() groups messages by field name."""
        problem = ProblemDetails(
            title="Validation Failed",
            status=400,
            detail="Multiple errors",
            errors=[
                ValidationErrorField(field="email", message="Invalid format"),
                ValidationErrorField(field="email", message="Already exists"),
                ValidationErrorField(field="password", message="Too short"),
            ],
        )

        exc = ValidationError(problem)
        field_errors = exc.get_field_errors()

        assert field_errors == {
            "email": ["Invalid format", "Already exists"],
            "password": ["Too short"],
        }

    def test_get_field_errors_returns_empty_dict(self):
        """Test get_field_errors() returns empty dict when no errors."""
        problem = ProblemDetails(
            title="Bad Request", status=400, detail="Invalid", errors=[]
        )

        exc = ValidationError(problem)
        field_errors = exc.get_field_errors()

        assert field_errors == {}

    def test_get_field_errors_preserves_order(self):
        """Test get_field_errors() preserves message order per field."""
        problem = ProblemDetails(
            title="Validation Failed",
            status=400,
            detail="Errors",
            errors=[
                ValidationErrorField(field="name", message="First error"),
                ValidationErrorField(field="name", message="Second error"),
                ValidationErrorField(field="name", message="Third error"),
            ],
        )

        exc = ValidationError(problem)
        field_errors = exc.get_field_errors()

        assert field_errors["name"] == ["First error", "Second error", "Third error"]

    def test_inherits_from_problem_details_exception(self):
        """Test ValidationError inherits from ProblemDetailsException."""
        problem = ProblemDetails(
            title="Validation Failed",
            status=400,
            detail="Invalid",
            errors=[ValidationErrorField(field="test", message="Error")],
        )

        error = ValidationError(problem)

        assert isinstance(error, ProblemDetailsException)
        assert isinstance(error, MagickMindError)
