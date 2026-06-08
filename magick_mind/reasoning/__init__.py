"""Cortex v2 Reason SDK surface."""

from magick_mind.reasoning.client import Client, ReasonStream
from magick_mind.reasoning.events import (
    ReasonCompleteEvent,
    ReasonEvent,
    ReasonFailedEvent,
    ReasonThinkingEvent,
    ReasonTokenEvent,
    parse_reason_event,
    parse_sse_text,
)
from magick_mind.reasoning.models import (
    ChatMessage,
    ImageResult,
    LLM,
    MCTS,
    ModelConfig,
    ReasonResponse,
    RLM,
    Singular,
    UsageStats,
)

__all__ = [
    "Client",
    "ReasonStream",
    "ReasonEvent",
    "ReasonTokenEvent",
    "ReasonThinkingEvent",
    "ReasonCompleteEvent",
    "ReasonFailedEvent",
    "parse_reason_event",
    "parse_sse_text",
    "ChatMessage",
    "ImageResult",
    "LLM",
    "MCTS",
    "ModelConfig",
    "ReasonResponse",
    "RLM",
    "Singular",
    "UsageStats",
]
