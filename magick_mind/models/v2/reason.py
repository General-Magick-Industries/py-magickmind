"""Typed request and response models for the Cortex v2 Reason API."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Mapping, Protocol, TypeAlias

from pydantic import BaseModel, ConfigDict, Field


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


class ImageSize(str, Enum):
    """Output size for image-generation models.

    Values are the Reason API wire names accepted by Cortex.
    """

    SIZE_1024 = "IMAGE_SIZE_1024X1024"
    SIZE_1536 = "IMAGE_SIZE_1536X1536"
    SIZE_2048 = "IMAGE_SIZE_2048X2048"


@dataclass(frozen=True)
class ModelConfig:
    """Model configuration sent to Cortex.

    ``image_size`` is ignored unless the model is an image-generation model.
    """

    model: str
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    reasoning_effort: str | None = None
    image_size: ImageSize | None = None

    def to_dict(self) -> dict[str, Any]:
        return _compact(
            {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "reasoning_effort": self.reasoning_effort,
                "image_config": (
                    {"size": self.image_size.value}
                    if self.image_size is not None
                    else None
                ),
            }
        )


ModelLike: TypeAlias = str | ModelConfig
NodeConfig: TypeAlias = WireSerializable | Mapping[str, Any]
AlgorithmConfig: TypeAlias = WireSerializable | Mapping[str, Any]


def _model_slot(value: ModelLike | None) -> dict[str, Any] | None:
    """Serialize a model slot (string id or ``ModelConfig``) to a wire dict."""
    if value is None:
        return None
    if isinstance(value, ModelConfig):
        return value.to_dict()
    return {"model": value}


@dataclass(frozen=True)
class LLM:
    """Single LLM node."""

    model: ModelLike
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    reasoning_effort: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.model, ModelConfig) and any(
            value is not None
            for value in (
                self.temperature,
                self.max_tokens,
                self.top_p,
                self.reasoning_effort,
            )
        ):
            raise ValueError(
                "LLM model parameters cannot be passed alongside ModelConfig"
            )

    def to_dict(self) -> dict[str, Any]:
        if isinstance(self.model, ModelConfig):
            config = self.model.to_dict()
        else:
            config = ModelConfig(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                reasoning_effort=self.reasoning_effort,
            ).to_dict()
        return {"llm": {"model_config": config}}


@dataclass(frozen=True)
class RLM:
    """Recursive language model node.

    Field names mirror the Reason API wire format. Each model slot accepts a
    model-id string or a :class:`ModelConfig`. ``image_model_config`` enables the
    image-generation RLM path; ``max_iterations`` is clamped server-side to
    ``[1, 50]``.
    """

    main_model_config: ModelLike
    sub_model_config: ModelLike | None = None
    image_model_config: ModelLike | None = None
    max_iterations: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rlm": _compact(
                {
                    "main_model_config": _model_slot(self.main_model_config),
                    "sub_model_config": _model_slot(self.sub_model_config),
                    "image_model_config": _model_slot(self.image_model_config),
                    "max_iterations": self.max_iterations,
                }
            )
        }


@dataclass(frozen=True)
class Lambda:
    """Lambda RLM node.

    Field names mirror the Reason API wire format (the wire key is ``lambda``;
    this class is named ``Lambda`` because ``lambda`` is a Python keyword).
    Each model slot accepts a model-id string or a :class:`ModelConfig`.
    ``main_model_config`` drives reduce/compose calls; ``sub_model_config``
    drives leaf calls and falls back to ``main_model_config`` if unset.
    ``context_window_chars`` (default 100000) must be positive and
    ``accuracy_target`` (default 0.80) must be in (0, 1]; both are validated
    server-side.
    """

    main_model_config: ModelLike
    sub_model_config: ModelLike | None = None
    context_window_chars: int | None = None
    accuracy_target: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lambda": _compact(
                {
                    "main_model_config": _model_slot(self.main_model_config),
                    "sub_model_config": _model_slot(self.sub_model_config),
                    "context_window_chars": self.context_window_chars,
                    "accuracy_target": self.accuracy_target,
                }
            )
        }


@dataclass(frozen=True)
class Singular:
    """Singular Reason algorithm."""

    node: NodeConfig

    def to_dict(self) -> dict[str, Any]:
        return {"singular": {"node": _serialize(self.node)}}


@dataclass(frozen=True)
class MCTS:
    """MCTS Reason algorithm."""

    nodes: list[NodeConfig]
    rating_model: ModelLike
    aggregator_model: ModelLike
    iterations: int = 4

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
    degradations: list[str] = Field(default_factory=list)

    @property
    def content(self) -> str | None:
        """Text answer convenience alias."""
        return self.text_answer


MessageRole = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    """Chat message accepted by the Reason API."""

    role: MessageRole | str
    content: str
