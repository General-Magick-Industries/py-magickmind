"""
Magick Mind SDK - Python client for the Magick Mind AI platform.

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
    ChatAck,
    ChatSendRequest,
    ChatSendResponse,
    ChatHistoryMessage,
    HistoryResponse,
)
from magick_mind.realtime.events import (
    ArtifactData,
    ArtifactPayload,
    ChatMessageEvent,
    ChatMessagePayload,
    ImageGenerationEvent,
    UnknownEvent,
    WsEvent,
    parse_ws_event,
)

__version__ = "0.2.0"

__all__ = [
    "MagickMind",
    "AuthenticationError",
    "MagickMindError",
    "ProblemDetailsException",
    "RateLimitError",
    "TokenExpiredError",
    "ValidationError",
    "ChatSendRequest",
    "ChatAck",
    "ChatMessagePayload",
    "ChatMessageEvent",
    "ChatSendResponse",
    "ChatHistoryMessage",
    "HistoryResponse",
    "ArtifactData",
    "ArtifactPayload",
    "ImageGenerationEvent",
    "UnknownEvent",
    "WsEvent",
    "parse_ws_event",
]
