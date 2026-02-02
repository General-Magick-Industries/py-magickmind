"""Pydantic models for API requests and responses."""

# Models are organized by version
# Each version has its own submodule with request/response schemas

# RFC 7807 error models (version-agnostic)
from magick_mind.models.errors import (
    ErrorResponse,
    ProblemDetails,
    ValidationErrorField,
)

__all__ = [
    "ErrorResponse",
    "ProblemDetails",
    "ValidationErrorField",
]
