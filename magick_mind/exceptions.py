"""Custom exceptions for Magick Mind SDK."""

from __future__ import annotations

import logging

from magick_mind.models.errors import ProblemDetails

logger = logging.getLogger(__name__)


class MagickMindError(Exception):
    """Base exception for all Magick Mind SDK errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(MagickMindError):
    """Raised when authentication fails."""

    pass


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""

    pass


class RateLimitError(MagickMindError):
    """Raised when rate limit is exceeded."""

    pass


class ProblemDetailsException(MagickMindError):
    """RFC 7807 Problem Details error from the Magick Mind API."""

    def __init__(
        self,
        problem: ProblemDetails,
        raw_response: dict | None = None,
    ):
        self.type_uri = problem.type
        self.title = problem.title
        self.status = problem.status
        self.detail = problem.detail
        self.instance = problem.instance
        self.request_id = problem.request_id
        self.validation_errors = problem.errors
        self.problem = problem  # Full Pydantic model

        # Log with request_id for tracing
        logger.debug(
            "API error: %s [%d] %s (request_id=%s, instance=%s)",
            self.title,
            self.status,
            self.detail,
            self.request_id or "none",
            self.instance or "none",
        )

        super().__init__(self.detail, status_code=self.status)
        self.response_data = raw_response

    def __str__(self) -> str:
        msg = f"[{self.status}] {self.title}: {self.detail}"
        if self.request_id:
            msg += f" (request_id: {self.request_id})"
        if self.validation_errors:
            msg += f"\nValidation errors ({len(self.validation_errors)}):"
            for err in self.validation_errors:
                msg += f"\n  - {err.field}: {err.message}"
        return msg

    def __repr__(self) -> str:
        return f"ProblemDetailsException(status={self.status}, title={self.title!r}, request_id={self.request_id!r})"


class ValidationError(ProblemDetailsException):
    """400 Bad Request with field-level validation errors."""

    def __init__(self, problem: ProblemDetails, raw_response: dict | None = None):
        if problem.status != 400:
            raise ValueError(
                f"ValidationError must have status 400, got {problem.status}"
            )
        if not problem.errors:
            logger.warning("ValidationError created without field errors")
        super().__init__(problem, raw_response)

    def get_field_errors(self) -> dict[str, list[str]]:
        """
        Get errors grouped by field name for UI display.

        Note: Returns simplified dict[field, messages]. Access validation_errors
        directly if you need error codes (e.g., "required", "invalid_format").
        """
        errors_by_field: dict[str, list[str]] = {}
        for err in self.validation_errors:
            if err.field not in errors_by_field:
                errors_by_field[err.field] = []
            errors_by_field[err.field].append(err.message)
        return errors_by_field
