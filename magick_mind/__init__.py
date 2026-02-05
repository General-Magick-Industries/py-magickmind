"""
Magick Mind SDK - Python client for Bifrost Magick Mind AI platform.

Simple, powerful SDK for authentication and interaction with the Magick Mind API.
"""

from magick_mind.client import MagickMind
from magick_mind.exceptions import (
    AuthenticationError,
    MagickMindError,
    ProblemDetailsException,
    RateLimitError,
    TokenExpiredError,
    ValidationError,
)
from magick_mind.models.v1 import (
    ChatPayload,
    ChatSendRequest,
    ChatSendResponse,
    ChatHistoryMessage,
    HistoryResponse,
)

__version__ = "0.1.0"

__all__ = [
    "MagickMind",
    "AuthenticationError",
    "MagickMindError",
    "ProblemDetailsException",
    "RateLimitError",
    "TokenExpiredError",
    "ValidationError",
    "ChatSendRequest",
    "ChatPayload",
    "ChatSendResponse",
    "ChatHistoryMessage",
    "HistoryResponse",
]
