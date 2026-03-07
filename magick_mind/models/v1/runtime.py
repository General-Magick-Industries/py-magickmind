"""V1 Runtime API models — effective personality computation."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from magick_mind.models.v1.personality import LockType, TraitValue


class EffectiveSources(BaseModel):
    """Breakdown of where a trait's effective value comes from."""

    authored: Optional[TraitValue] = None
    global_learned: Optional[TraitValue] = None
    dyadic_learned: Optional[TraitValue] = None
    lock: Optional[LockType] = None
    was_clamped: bool = False


class EffectiveTrait(BaseModel):
    """A single trait with its blended value and source breakdown."""

    trait_ref: str
    value: TraitValue
    sources: EffectiveSources


class EffectivePersonality(BaseModel):
    """The computed effective personality of a persona."""

    persona_id: str
    user_id: Optional[str] = None
    traits: list[EffectiveTrait] = Field(default_factory=list)
    computed_at: str
    ttl_seconds: int
