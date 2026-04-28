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
from magick_mind.models.v1.mindspace import MindSpaceType
from magick_mind.models.v1.artifact import ArtifactStatusEnum
from magick_mind.models.v1.personality import (
    GrowthType,
    LockType,
    Namespace,
    TriggerDirection,
    Visibility,
)
from magick_mind.models.v1.trait import TraitNamespace, TraitType, TraitVisibility
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

__version__ = "0.3.0"

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
    "MindSpaceType",
    "ArtifactStatusEnum",
    "Namespace",
    "Visibility",
    "GrowthType",
    "TriggerDirection",
    "LockType",
    "TraitNamespace",
    "TraitType",
    "TraitVisibility",
    "ArtifactData",
    "ArtifactPayload",
    "ImageGenerationEvent",
    "UnknownEvent",
    "WsEvent",
    "parse_ws_event",
]
