"""Typed streaming events for the Cortex v2 Reason API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Iterable


EVENT_PAYLOAD_KEYS: dict[str, str] = {
    "reason.started": "started",
    "reason.completed": "completed",
    "reason.failed": "failed",
    "reason.mcts.started": "mcts_started",
    "reason.mcts.candidate_started": "mcts_candidate_started",
    "reason.mcts.candidate_completed": "mcts_candidate_completed",
    "reason.mcts.rating_started": "mcts_rating_started",
    "reason.mcts.rating_completed": "mcts_rating_completed",
    "reason.mcts.aggregate_started": "mcts_aggregate_started",
    "reason.rlm.sub_started": "rlm_sub_started",
    "reason.rlm.sub_completed": "rlm_sub_completed",
    "reason.rlm.repl_step": "rlm_repl_step",
    "reason.answer.delta": "answer_chunk",
    "reason.answer.complete": "answer_complete",
    "reason.degradation": "degradation",
    "reason.mcts.iteration.started": "mcts_iteration_started",
    "reason.mcts.iteration.completed": "mcts_iteration_completed",
    "reason.mcts.final.ranking.completed": "mcts_final_ranking_completed",
    "reason.trace.emitted": "trace_emitted",
}

THINKING_PREFIXES = ("reason.mcts.", "reason.rlm.", "reason.started", "reason.trace.")


@dataclass(frozen=True)
class ReasonEvent:
    """Base class for a typed Reason stream event."""

    type: str
    trace_id: str | None
    payload: dict[str, Any]
    data: dict[str, Any]

    @property
    def content(self) -> str:
        """Token content for token events, otherwise an empty string."""
        return ""

    def is_token(self) -> bool:
        return False

    def is_thinking(self) -> bool:
        return self.type.startswith(THINKING_PREFIXES)


@dataclass(frozen=True)
class ReasonTokenEvent(ReasonEvent):
    """Incremental answer token/chunk."""

    @property
    def content(self) -> str:
        return str(self.payload.get("content", ""))

    def is_token(self) -> bool:
        return True

    def is_thinking(self) -> bool:
        return False


@dataclass(frozen=True)
class ReasonCompleteEvent(ReasonEvent):
    """Terminal success event."""

    def is_thinking(self) -> bool:
        return False


@dataclass(frozen=True)
class ReasonFailedEvent(ReasonEvent):
    """Terminal failure event."""

    @property
    def error_code(self) -> str | None:
        value = self.payload.get("error_code")
        return str(value) if value is not None else None

    @property
    def message(self) -> str | None:
        value = self.payload.get("message")
        return str(value) if value is not None else None

    def is_thinking(self) -> bool:
        return False


@dataclass(frozen=True)
class ReasonThinkingEvent(ReasonEvent):
    """Progress or trace event suitable for thinking/progress UIs."""


def parse_reason_event(event_type: str, data: dict[str, Any]) -> ReasonEvent:
    """Parse one SSE frame into a typed event object."""
    payload_key = EVENT_PAYLOAD_KEYS.get(event_type)
    payload = data.get(payload_key, {}) if payload_key else {}
    if not isinstance(payload, dict):
        payload = {"value": payload}

    trace_id = data.get("trace_id")
    trace_id = str(trace_id) if trace_id is not None else None

    kwargs = {
        "type": event_type,
        "trace_id": trace_id,
        "payload": payload,
        "data": data,
    }
    if event_type == "reason.answer.delta":
        return ReasonTokenEvent(**kwargs)
    if event_type in {"reason.answer.complete", "reason.completed"}:
        return ReasonCompleteEvent(**kwargs)
    if event_type == "reason.failed":
        return ReasonFailedEvent(**kwargs)
    if event_type.startswith(THINKING_PREFIXES) or event_type == "reason.degradation":
        return ReasonThinkingEvent(**kwargs)
    return ReasonEvent(**kwargs)


async def iter_sse_events(lines: AsyncIterator[str]) -> AsyncIterator[ReasonEvent]:
    """Yield typed events from an async iterator of SSE lines."""
    event_type = "message"
    data_lines: list[str] = []

    async for line in lines:
        if line == "":
            if data_lines:
                yield _parse_sse_frame(event_type, data_lines)
            event_type = "message"
            data_lines = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_type = line.removeprefix("event:").strip()
            continue
        if line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())

    if data_lines:
        yield _parse_sse_frame(event_type, data_lines)


def parse_sse_text(text: str) -> list[ReasonEvent]:
    """Parse a complete SSE payload. Mainly useful for tests."""
    frames: list[ReasonEvent] = []
    event_type = "message"
    data_lines: list[str] = []

    for line in text.splitlines():
        if line == "":
            if data_lines:
                frames.append(_parse_sse_frame(event_type, data_lines))
            event_type = "message"
            data_lines = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_type = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())

    if data_lines:
        frames.append(_parse_sse_frame(event_type, data_lines))
    return frames


def _parse_sse_frame(event_type: str, data_lines: Iterable[str]) -> ReasonEvent:
    data_text = "\n".join(data_lines)
    if data_text == "[DONE]":
        return ReasonCompleteEvent(
            type="reason.answer.complete",
            trace_id=None,
            payload={},
            data={},
        )
    data = json.loads(data_text)
    if not isinstance(data, dict):
        data = {"value": data}
    return parse_reason_event(event_type, data)
