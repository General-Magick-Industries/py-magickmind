"""
Magick Mind SDK - Python client for the Magick Mind AI platform.

Simple, powerful SDK for authentication and interaction with the Magick Mind API.
"""

from magick_mind.auth import EndUserTokenAuth, StaticTokenAuth
from magick_mind.client import MagickMind
from magick_mind.exceptions import (
    AuthenticationError,
    MagickMindError,
    ProblemDetailsException,
    RateLimitError,
    TokenExpiredError,
    ValidationError,
)
from magick_mind.models.v2.reason import (
    AlgorithmConfig,
    ChatMessage,
    LLM,
    MCTS,
    ModelConfig,
    ModelLike,
    NodeConfig,
    ReasonResponse,
    RLM,
    Singular,
)
from magick_mind.resources.v2.events import (
    ReasonCompleteEvent,
    ReasonEvent,
    ReasonFailedEvent,
    ReasonThinkingEvent,
    ReasonTokenEvent,
)
from magick_mind.resources.v2.reason import Client, ReasonResourceV2, ReasonStream
from magick_mind.models.v1 import (
    ChatAck,
    ChatSendRequest,
    ChatSendResponse,
    ChatHistoryMessage,
    HistoryResponse,
    MessageType,
    is_control_message,
    is_signal_message,
)
from magick_mind.realtime.events import (
    MAGICKSPACE_MESSAGE,
    ArtifactData,
    ArtifactPayload,
    ChatMessageEvent,
    ChatMessagePayload,
    ImageGenerationEvent,
    MagickspaceMessageEvent,
    MagickspaceMessagePayload,
    UnknownEvent,
    WsEvent,
    parse_ws_event,
)

__version__ = "0.4.1"

__all__ = [
    "Client",
    "MagickMind",
    "EndUserTokenAuth",
    "StaticTokenAuth",
    "MessageType",
    "is_signal_message",
    "is_control_message",
    "LLM",
    "MCTS",
    "RLM",
    "Singular",
    "AlgorithmConfig",
    "ModelLike",
    "ModelConfig",
    "NodeConfig",
    "ReasonResponse",
    "ReasonResourceV2",
    "ReasonStream",
    "ReasonEvent",
    "ReasonTokenEvent",
    "ReasonThinkingEvent",
    "ReasonCompleteEvent",
    "ReasonFailedEvent",
    "AuthenticationError",
    "MagickMindError",
    "ProblemDetailsException",
    "RateLimitError",
    "TokenExpiredError",
    "ValidationError",
    "ChatMessage",
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
    "MAGICKSPACE_MESSAGE",
    "MagickspaceMessageEvent",
    "MagickspaceMessagePayload",
    "UnknownEvent",
    "WsEvent",
    "parse_ws_event",
]
