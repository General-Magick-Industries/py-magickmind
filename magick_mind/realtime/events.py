"""
Realtime event models for Centrifugo publications from Xavier.

Xavier source of truth: services/xavier/internal/types/broadcast.go

Usage:
    from magick_mind.realtime.events import parse_ws_event, ChatMessageEvent

    event = parse_ws_event(ctx.pub.data)
    match event:
        case ChatMessageEvent(payload=p): handle_chat(p)
        case ImageGenerationEvent(payload=p): handle_artifact(p)
        case UnknownEvent(type=t): logger.warning(f"unhandled: {t}")
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatMessagePayload(BaseModel):
    """Payload for type="chat_message" realtime events."""

    mindspace_id: str
    message_id: str
    task_id: str
    message: str
    reply_to: str | None = None


class ChatMessageEvent(BaseModel):
    """Realtime event: AI chat response."""

    type: str
    payload: ChatMessagePayload


class ArtifactData(BaseModel):
    """Artifact schema for Centrifugo broadcast."""

    id: str
    bucket: str
    key: str
    s3_url: str
    content_type: str
    size_bytes: int
    etag: str
    checksum_sha256: str
    status: str
    created_at: int
    updated_at: int


class ArtifactPayload(BaseModel):
    """Payload for type="image_generation" realtime events."""

    mindspace_id: str
    message_id: str
    task_id: str
    reply_to: str | None = None
    data: ArtifactData | None = None


class ImageGenerationEvent(BaseModel):
    """Realtime event: artifact/image generated."""

    type: str
    payload: ArtifactPayload


class UnknownEvent(BaseModel):
    """Catch-all for unrecognised event types."""

    type: str
    payload: dict[str, Any] = Field(default_factory=dict)


# All known event types — maps type tag to model class
_PARSERS: dict[str, type[ChatMessageEvent] | type[ImageGenerationEvent]] = {
    "chat_message": ChatMessageEvent,
    "image_generation": ImageGenerationEvent,
}

# The union type for consumers to type-hint against
WsEvent = ChatMessageEvent | ImageGenerationEvent | UnknownEvent


def parse_ws_event(
    data: dict[str, Any],
) -> ChatMessageEvent | ImageGenerationEvent | UnknownEvent:
    """
    Parse raw Centrifugo publication data into a typed event.

    Dict dispatch — O(1), no try/except, no Pydantic discriminator magic.
    Unknown types degrade gracefully to UnknownEvent.
    """
    event_type = data.get("type", "")
    model = _PARSERS.get(event_type)
    if model:
        return model.model_validate(data)
    return UnknownEvent(type=event_type, payload=data.get("payload", {}))
