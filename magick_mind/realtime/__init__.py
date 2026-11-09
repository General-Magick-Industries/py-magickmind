"""Realtime module for WebSocket connections using Centrifugo."""

from .client import RealtimeClient
from .handler import EventRouter
from magick_mind.realtime.events import (
    MAGICKSPACE_MESSAGE,
    ArtifactData,
    ArtifactPayload,
    ChatMessageEvent,
    ChatMessagePayload,
    EventContext,
    ImageGenerationEvent,
    MagickspaceMessageEvent,
    MagickspaceMessagePayload,
    UnknownEvent,
    WsEvent,
    dispatch_key,
    parse_ws_event,
)

__all__ = [
    "RealtimeClient",
    "EventRouter",
    "MAGICKSPACE_MESSAGE",
    "ArtifactData",
    "ArtifactPayload",
    "ChatMessageEvent",
    "ChatMessagePayload",
    "EventContext",
    "ImageGenerationEvent",
    "MagickspaceMessageEvent",
    "MagickspaceMessagePayload",
    "UnknownEvent",
    "WsEvent",
    "dispatch_key",
    "parse_ws_event",
]
