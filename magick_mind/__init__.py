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
    RateLimitError,
)
from magick_mind.models.v1 import (
    ChatPayload,
    ChatSendRequest,
    ChatSendResponse,
    ChatHistoryMessage,
    HistoryResponse,
)

__version__ = "0.0.1"

__all__ = [
    "MagickMind",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "TokenExpiredError",
    "ChatSendRequest",
    "ChatPayload",
    "ChatSendResponse",
    "ChatHistoryMessage",
    "HistoryResponse",
]
