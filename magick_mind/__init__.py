"""
Magick Mind SDK - Python client for Bifrost Magick Mind AI platform.

Simple, powerful SDK for authentication and interaction with the Magick Mind API.
"""

from magick_mind.client import MagickMind
from magick_mind.exceptions import (
    APIError,
    AuthenticationError,
    MagickMindError,
    TokenExpiredError,
)
from magick_mind.models.v1.chat import ChatPayload, ChatSendRequest, ChatSendResponse

__version__ = "0.0.1"

__all__ = [
    "MagickMind",
    "MagickMindError",
    "AuthenticationError",
    "APIError",
    "TokenExpiredError",
    "ChatSendRequest",
    "ChatSendResponse",
    "ChatPayload",
]
