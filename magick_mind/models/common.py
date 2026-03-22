"""Common Pydantic models used across versions."""

from typing import Optional

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response structure from Magick Mind API."""

    success: bool
    message: str


class Cursors(BaseModel):
    """Pagination cursors for paginated responses."""

    after: Optional[str] = Field(default=None, description="Cursor for next page")
    before: Optional[str] = Field(default=None, description="Cursor for previous page")


class PageInfo(BaseModel):
    """Pagination information for paginated responses."""

    cursors: Cursors = Field(
        default_factory=lambda: Cursors(after=None, before=None),
        description="Pagination cursors",
    )
    has_more: bool = Field(default=False, description="Whether there are more results")
    has_previous: bool = Field(
        default=False, description="Whether there are previous results"
    )
