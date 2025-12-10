"""Common Pydantic models used across versions."""

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """Base response structure from Bifrost API."""
    success: bool
    message: str
