"""Authentication-related Pydantic models."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request model for /v1/auth/login."""

    email: str
    password: str


class RefreshRequest(BaseModel):
    """Request model for /v1/auth/refresh."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Response model from /v1/auth/login."""

    access_token: str
    expires_in: int
    refresh_expires_in: int
    refresh_token: str
    token_type: str
    id_token: str
    not_before_policy: int = Field(..., alias="not-before-policy")
    session_state: str
    scope: str
