"""Custom exceptions for Magick Mind SDK."""

from __future__ import annotations

import logging
from typing import Any, Mapping, NoReturn, Optional

from magick_mind.models.errors import ProblemDetails, ValidationErrorField

logger: logging.Logger = logging.getLogger(__name__)


class MagickMindError(Exception):
    """Base exception for all Magick Mind SDK errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        self.hint: Optional[str] = None
        super().__init__(self.message)

    def _base_str(self) -> str:
        """The message without any SDK hint. Subclasses override to add detail."""
        return self.message

    def __str__(self) -> str:
        base = self._base_str()
        return f"{base} ({self.hint})" if self.hint else base


def reraise_with_hint(exc: MagickMindError, hint: str) -> NoReturn:
    """Re-raise ``exc`` with an SDK ``hint`` attached, preserving its exact type.

    The hint is stored on ``exc.hint`` and surfaced by ``__str__``. It is
    deliberately kept out of ``detail``/``problem``, which hold the server's own
    RFC 7807 payload -- overwriting those would make the SDK's guidance
    indistinguishable from what the API actually said.

    The exception object is re-raised as-is, so its type and every field
    survive: a caller catching :class:`ProblemDetailsException`,
    :class:`ValidationError`, or :class:`AuthenticationError` still matches.
    Applying a hint twice replaces the first rather than stacking.
    """
    exc.hint = hint
    # args feeds repr() and traceback formatting, which bypass __str__; message
    # stays the server's own text so __str__ can append the hint exactly once.
    exc.args = (str(exc),)
    raise exc


class AuthenticationError(MagickMindError):
    """Raised when authentication fails."""

    pass


def hint_by_status(exc: MagickMindError, hints: Mapping[int, str]) -> NoReturn:
    """Re-raise an API error with the hint registered for its status, if any.

    Credential errors raised by the auth provider itself (an
    :class:`AuthenticationError` from token rotation) pass through untouched:
    their status is a verdict on the token, not on the route, and a
    route-specific hint would misdiagnose them.
    """
    if isinstance(exc, AuthenticationError):
        raise exc
    if exc.status_code is not None and exc.status_code in hints:
        reraise_with_hint(exc, hints[exc.status_code])
    raise exc


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
        raw_response: Optional[dict[str, Any]] = None,
    ):
        self.type_uri: str = problem.type
        self.title: str = problem.title
        self.status: int = problem.status
        self.detail: str = problem.detail
        self.instance: Optional[str] = problem.instance
        self.request_id: Optional[str] = problem.request_id
        self.validation_errors: list[ValidationErrorField] = problem.errors
        self.problem: ProblemDetails = problem

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
        self.response_data: Optional[dict[str, Any]] = raw_response

    def _base_str(self) -> str:
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

    def __init__(
        self, problem: ProblemDetails, raw_response: Optional[dict[str, Any]] = None
    ):
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
