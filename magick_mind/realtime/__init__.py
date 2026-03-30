"""Realtime module for WebSocket connections using Centrifugo."""

from .client import RealtimeClient
from .handler import EventRouter
from magick_mind.realtime.events import (
    ArtifactData,
    ArtifactPayload,
    ChatMessageEvent,
    ChatMessagePayload,
    EventContext,
    ImageGenerationEvent,
    UnknownEvent,
    WsEvent,
    parse_ws_event,
)

__all__ = [
    "RealtimeClient",
    "EventRouter",
    "ArtifactData",
    "ArtifactPayload",
    "ChatMessageEvent",
    "ChatMessagePayload",
    "EventContext",
    "ImageGenerationEvent",
    "UnknownEvent",
    "WsEvent",
    "parse_ws_event",
]
