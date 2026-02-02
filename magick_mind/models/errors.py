"""RFC 7807 Problem Details error models for Bifrost API responses.

This module defines Pydantic models for parsing RFC 7807 compliant error
responses from the Bifrost API.

See: https://datatracker.ietf.org/doc/html/rfc7807
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ValidationErrorField(BaseModel):
    """RFC 7807 field-level validation error.

    Represents a single field validation error, typically used in 400 Bad Request
    responses with field-specific validation failures.

    Attributes:
        field: The field name that failed validation
        message: Human-readable error message for this field
        code: Optional error code (e.g., "required", "invalid_format")
    """

    field: str
    message: str
    code: str | None = None


class ProblemDetails(BaseModel):
    """RFC 7807 Problem Details structure.

    Standard structure for HTTP API error responses. This is the Pydantic model
    representing the data structure, NOT the exception class.

    The exception class that wraps this is ProblemDetailsException (created in task 02).

    Attributes:
        type: URI reference identifying the problem type (default: "about:blank")
        title: Short, human-readable summary of the problem type
        status: HTTP status code (400-599)
        detail: Human-readable explanation specific to this occurrence
        instance: URI reference identifying the specific occurrence (e.g., request path)
        request_id: Trace ID for debugging (Bifrost extension field)
        errors: List of field-level validation errors (Bifrost extension field)

    Additional fields are allowed per RFC 7807 extension mechanism.
    """

    type: str = "about:blank"
    title: str
    status: int = Field(ge=400, le=599)
    detail: str
    instance: str | None = None
    request_id: str | None = None
    errors: list[ValidationErrorField] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class ErrorResponse(BaseModel):
    """Bifrost error response wrapper.

    Wraps the RFC 7807 ProblemDetails in an "error" envelope as returned by Bifrost.

    Bifrost returns: {"error": {...problem details...}}

    Attributes:
        error: The RFC 7807 problem details
    """

    error: ProblemDetails
