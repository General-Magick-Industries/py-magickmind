"""
Realtime event models for Centrifugo publications.

Two publishers share the ``chat_message`` wire type:

- Xavier (legacy chat orchestrator): ``{mindspace_id, message_id, task_id,
  message}`` -- parsed as :class:`ChatMessageEvent`.
- Bifrost magickspace fan-out: a stored :class:`ChatHistoryItem` plus the
  sender's per-turn ``tools`` and ``context`` -- parsed as
  :class:`MagickspaceMessageEvent` and dispatched under the SDK-side key
  :data:`MAGICKSPACE_MESSAGE`.

Usage:
    from magick_mind.realtime.events import parse_ws_event, MagickspaceMessageEvent

    event = parse_ws_event(ctx.pub.data)
    match event:
        case MagickspaceMessageEvent(payload=p): handle_turn(p)
        case ChatMessageEvent(payload=p): handle_chat(p)
        case UnknownEvent(type=t): logger.warning(f"unhandled: {t}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, ClassVar, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from magick_mind.models.v1.mindspace import (
    ChatHistoryItem,
    is_control_message,
    is_signal_message,
)
from magick_mind.models.v1.space_type import normalize_space_type

_CHANNEL_RE = re.compile(
    r"^(?P<family>personal|user):(?P<target>[^#]+)#(?P<service>.+)$"
)

MAGICKSPACE_MESSAGE = "magickspace_message"


@dataclass(frozen=True, slots=True)
class EventContext:
    """SDK-derived metadata about where a realtime event came from.

    Attributes:
        channel: Raw Centrifugo channel string.
        target_user_id: The end-user ID the channel belongs to, for both
            ``personal:<target>#<service>`` and ``user:<id>#<id>``.
        publisher_user_id: Centrifugo's own record of which connection
            published, when the server attaches it. Unlike the payload's
            ``sent_by_user_id``, this cannot be chosen by the publisher; it is
            empty for publications Bifrost makes server-side.
    """

    channel: str
    target_user_id: str
    publisher_user_id: str = ""

    @classmethod
    def from_channel(cls, channel: str, publisher_user_id: str = "") -> EventContext:
        """Parse a ``personal:`` or ``user:`` channel string."""
        m = _CHANNEL_RE.match(channel)
        target = m.group("target") if m else ""
        return cls(
            channel=channel, target_user_id=target, publisher_user_id=publisher_user_id
        )


class ChatMessagePayload(BaseModel):
    """Payload for type="chat_message" realtime events (Xavier)."""

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

    mindspace_id: str = Field(
        validation_alias=AliasChoices("magickspace_id", "mindspace_id")
    )
    message_id: str
    task_id: str
    message: str
    reply_to: str | None = None

    @property
    def magickspace_id(self) -> str:
        """The space this reply belongs to (``mindspace_id`` is the legacy name)."""
        return self.mindspace_id


class ChatMessageEvent(BaseModel):
    """Realtime event: AI chat response."""

    type: str
    payload: ChatMessagePayload


class MagickspaceMessagePayload(ChatHistoryItem):
    """A magickspace fan-out: the stored message plus wire-only turn extras.

    ``sent_by_user_id``, ``sent_by_user_name`` and ``magickspace_type`` are
    stamped by Bifrost from its own records, but they travel in the payload;
    :attr:`EventContext.publisher_user_id` is the only publisher-independent
    identity Centrifugo offers.
    """

    # An unknown space type must not take down the agent's only event channel,
    # so the fan-out payload normalizes without the strict Literal the REST
    # models apply.
    magickspace_type: Optional[str] = Field(  # type: ignore[assignment]
        default=None, description="PRIVATE or GROUP, as stamped by the server"
    )
    tools: Optional[list[dict[str, Any]]] = Field(
        default=None, description="The sender's live tool manifest for this turn"
    )
    context: Optional[dict[str, str]] = Field(
        default=None, description="Per-turn key/value context from the sender"
    )

    @field_validator("magickspace_type", mode="before")
    @classmethod
    def _normalize_type(cls, v: object) -> object:
        return normalize_space_type(v) if v else None

    @property
    def is_signal(self) -> bool:
        """A turn-lifecycle indicator, not speech."""
        return is_signal_message(self.message_type)

    @property
    def is_control(self) -> bool:
        """Tool-protocol traffic, not a turn to answer."""
        return is_control_message(self.message_type)


class MagickspaceMessageEvent(BaseModel):
    """Realtime event: a message fanned out to a magickspace participant."""

    type: str
    payload: MagickspaceMessagePayload


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


_PARSERS: dict[str, type[ChatMessageEvent] | type[ImageGenerationEvent]] = {
    "chat_message": ChatMessageEvent,
    "image_generation": ImageGenerationEvent,
}

WsEvent = (
    ChatMessageEvent | MagickspaceMessageEvent | ImageGenerationEvent | UnknownEvent
)


def dispatch_key(event: WsEvent) -> str:
    """The key handlers register under: the wire type, except that magickspace
    fan-out shares ``chat_message`` with Xavier and so gets its own."""
    if isinstance(event, MagickspaceMessageEvent):
        return MAGICKSPACE_MESSAGE
    return event.type


def _is_magickspace_payload(payload: Any) -> bool:
    return isinstance(payload, dict) and "sent_by_user_id" in payload


def parse_ws_event(data: dict[str, Any]) -> WsEvent:
    """
    Parse raw Centrifugo publication data into a typed event.

    Unknown types degrade gracefully to UnknownEvent.
    """
    event_type = data.get("type", "")
    if event_type == "chat_message" and _is_magickspace_payload(data.get("payload")):
        return MagickspaceMessageEvent.model_validate(data)
    model = _PARSERS.get(event_type)
    if model:
        return model.model_validate(data)
    return UnknownEvent(type=event_type, payload=data.get("payload", {}))
