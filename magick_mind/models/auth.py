"""Authentication-related Pydantic models."""

from typing import Optional
from pydantic import BaseModel, Field
from magick_mind.models.common import BaseResponse


class LoginRequest(BaseModel):
    """Request model for /v1/auth/login."""

    email: str
    password: str


class TokenResponse(BaseResponse):
    """Response model from /v1/auth/login."""

    access_token: str
    expires_in: int
    refresh_expires_in: int
    refresh_token: str
    token_type: str
    id_token: str
    scope: str
    session_state: Optional[str] = None
