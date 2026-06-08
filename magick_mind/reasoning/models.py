"""Typed request and response models for the Cortex v2 Reason API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Protocol

from pydantic import BaseModel, ConfigDict


class WireSerializable(Protocol):
    """Object that can serialize itself to the Reason API wire format."""

    def to_dict(self) -> dict[str, Any]: ...


def _compact(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def _serialize(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        return dict(value)
    return value


@dataclass(frozen=True)
class ModelConfig:
    """Model configuration sent to Cortex."""

    model: str
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    reasoning_effort: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return _compact(
            {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "reasoning_effort": self.reasoning_effort,
            }
        )


@dataclass(frozen=True)
class LLM:
    """Single LLM node."""

    model: str | ModelConfig

    def to_dict(self) -> dict[str, Any]:
        if isinstance(self.model, ModelConfig):
            config = self.model.to_dict()
        else:
            config = {"model": self.model}
        return {"llm": {"model_config": config}}


@dataclass(frozen=True)
class RLM:
    """Recursive language model node."""

    decomposer_model: str | ModelConfig
    leaf_model: str | ModelConfig | None = None
    synthesizer_model: str | ModelConfig | None = None
    max_depth: int | None = None
    fanout: int | None = None

    def __post_init__(self) -> None:
        unsupported = []
        if self.synthesizer_model is not None:
            unsupported.append("synthesizer_model")
        if self.fanout is not None:
            unsupported.append("fanout")
        if unsupported:
            names = ", ".join(unsupported)
            raise ValueError(
                f"RLM {names} not supported by the current Reason API wire format"
            )

    def to_dict(self) -> dict[str, Any]:
        main_config = (
            self.decomposer_model.to_dict()
            if isinstance(self.decomposer_model, ModelConfig)
            else {"model": self.decomposer_model}
        )
        sub_config = None
        if self.leaf_model is not None:
            sub_config = (
                self.leaf_model.to_dict()
                if isinstance(self.leaf_model, ModelConfig)
                else {"model": self.leaf_model}
            )

        # Cortex currently exposes max_iterations for RLM. Phase 5's draft
        # max_depth name maps to the existing wire field without changing
        # Bifrost or proto contracts.
        return {
            "rlm": _compact(
                {
                    "main_model_config": main_config,
                    "sub_model_config": sub_config,
                    "max_iterations": self.max_depth,
                }
            )
        }


@dataclass(frozen=True)
class Singular:
    """Singular Reason algorithm."""

    node: WireSerializable | Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"singular": {"node": _serialize(self.node)}}


@dataclass(frozen=True)
class MCTS:
    """MCTS Reason algorithm."""

    nodes: list[WireSerializable | Mapping[str, Any]]
    iterations: int
    rating_model: str | ModelConfig
    aggregator_model: str | ModelConfig

    def to_dict(self) -> dict[str, Any]:
        rating_config = (
            self.rating_model.to_dict()
            if isinstance(self.rating_model, ModelConfig)
            else {"model": self.rating_model}
        )
        aggregator_config = (
            self.aggregator_model.to_dict()
            if isinstance(self.aggregator_model, ModelConfig)
            else {"model": self.aggregator_model}
        )
        return {
            "mcts": {
                "nodes": [_serialize(node) for node in self.nodes],
                "iterations": self.iterations,
                "rating_model_config": rating_config,
                "aggregator_model_config": aggregator_config,
            }
        }


class UsageStats(BaseModel):
    """Token, model, and cost metadata returned by Cortex."""

    model_config = ConfigDict(extra="allow")

    input_tokens: int | None = None
    output_tokens: int | None = None
    llm_calls: int | None = None
    litellm_cost_usd: float | None = None
    model_used: str | None = None
    model_provider: str | None = None


class ImageResult(BaseModel):
    """Image output returned by Cortex."""

    model_config = ConfigDict(extra="allow")

    b64_json: str | None = None
    url: str | None = None
    mime_type: str | None = None


class ReasonResponse(BaseModel):
    """Non-streaming Reason API response."""

    model_config = ConfigDict(extra="allow")

    text_answer: str | None = None
    image: ImageResult | None = None
    usage: UsageStats | None = None
    trace: dict[str, Any] | None = None
    trace_id: str | None = None
    success: bool | None = None
    error: str | None = None
    degradations: list[str] = []

    @property
    def content(self) -> str | None:
        """Text answer convenience alias."""
        return self.text_answer


MessageRole = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    """Chat message accepted by the Reason API."""

    role: MessageRole | str
    content: str
