"""V1 personality system models shared across Blueprint, Persona, and Runtime."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# --- Enums ---
Namespace = Literal["SYSTEM", "USER", "ORG"]
Visibility = Literal["PRIVATE", "ORG", "PUBLIC"]
GrowthType = Literal["FIXED", "EXPANDING", "CORRUPTING", "REDEEMING", "TRANSCENDING"]
LockType = Literal["HARD", "SOFT"]
TriggerDirection = Literal["toward_target", "away_from_target", "normal"]


# --- Value types ---
class TraitValue(BaseModel):
    """A polymorphic trait value (numeric, string, or multi-label)."""

    numeric_value: Optional[float] = None
    string_value: Optional[str] = None
    string_list_value: list[str] = Field(default_factory=list)


class Constraint(BaseModel):
    """Bounds and rules for a trait constraint."""

    target: Optional[TraitValue] = None
    min_bound: Optional[float] = None
    max_bound: Optional[float] = None
    allowed_values: list[str] = Field(default_factory=list)
    learning_rate: Optional[float] = None


class TraitConstraint(BaseModel):
    """A trait reference with optional lock, value, and constraint."""

    trait_ref: str
    lock: Optional[LockType] = None
    value: Optional[TraitValue] = None
    constraint: Optional[Constraint] = None


# --- Growth config ---
class DomainRates(BaseModel):
    """Growth rates per personality domain."""

    identity: float
    narrative: float
    behavior: float


class GrowthTrigger(BaseModel):
    """Event that modifies growth rate for specific traits."""

    id: str
    condition: str
    affected_traits: list[str] = Field(default_factory=list)
    rate_multiplier: float
    direction: TriggerDirection


class GoalState(BaseModel):
    """Target personality state with attraction dynamics."""

    id: str
    description: str
    trait_targets: dict[str, float] = Field(default_factory=dict)
    attraction_strength: float


class Boundary(BaseModel):
    """Hard limits on trait evolution."""

    trait_ref: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    excluded_values: list[str] = Field(default_factory=list)
    reason: str


class GrowthConfig(BaseModel):
    """Configuration for personality growth/evolution."""

    type: GrowthType
    domain_rates: Optional[DomainRates] = None
    triggers: list[GrowthTrigger] = Field(default_factory=list)
    goal_states: list[GoalState] = Field(default_factory=list)
    boundaries: list[Boundary] = Field(default_factory=list)


class DyadicConfig(BaseModel):
    """Configuration for relationship-specific personality adaptation."""

    enabled: bool
    max_relationships: int = 0
    learnable_traits: list[str] = Field(default_factory=list)
    initial_weight: float = 0.0
    max_weight: float = 0.0
    confidence_threshold: int = 0


# --- Blueprint-specific ---
class BlueprintTrait(BaseModel):
    """A trait slot within a blueprint."""

    trait_ref: str
    required: bool = False
    default: Optional[TraitConstraint] = None
