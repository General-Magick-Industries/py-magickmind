"""V2 API resources."""

from magick_mind.resources.v2.events import (
    ReasonCompleteEvent,
    ReasonEvent,
    ReasonFailedEvent,
    ReasonThinkingEvent,
    ReasonTokenEvent,
    parse_reason_event,
    parse_sse_text,
)
from magick_mind.resources.v2.reason import (
    Client,
    HTTPReasonStream,
    ReasonResourceV2,
    ReasonStream,
)

__all__ = [
    "Client",
    "HTTPReasonStream",
    "ReasonResourceV2",
    "ReasonStream",
    "ReasonEvent",
    "ReasonTokenEvent",
    "ReasonThinkingEvent",
    "ReasonCompleteEvent",
    "ReasonFailedEvent",
    "parse_reason_event",
    "parse_sse_text",
]
