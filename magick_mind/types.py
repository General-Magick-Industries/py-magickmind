"""Type definitions for Magick Mind SDK."""

from typing import TypedDict, NotRequired


class LoginRequest(TypedDict):
    """Request body for /v1/auth/login"""

    email: str
    password: str


class TokenResponse(TypedDict):
    """Response from /v1/auth/login"""

    success: bool
    message: str
    access_token: str
    expires_in: int
    refresh_expires_in: int
    refresh_token: str
    token_type: str
    id_token: str
    scope: str
    session_state: NotRequired[str]


class BaseResponse(TypedDict):
    """Base response structure"""

    success: bool
    message: str
