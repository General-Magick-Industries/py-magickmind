"""
Trait models for Magick Mind SDK v1 API.

Mirrors the /v1/traits endpoint request/response schemas.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from magick_mind.models.common import PageInfo


TraitType = Literal["NUMERIC", "CATEGORICAL", "MULTILABEL"]
TraitNamespace = Literal["SYSTEM", "USER", "ORG", "PROMOTED"]
LockType = Literal["HARD", "SOFT"]
TraitVisibility = Literal["PRIVATE", "ORG", "PUBLIC"]


class NumericConfig(BaseModel):
    min: float
    max: float
    default: float


class CategoricalConfig(BaseModel):
    options: list[str]
    default: str


class MultilabelConfig(BaseModel):
    options: list[str]
    max_selections: int
    default: list[str]


class Trait(BaseModel):
    """A trait definition in the Magick Mind API."""

    id: str
    name: str
    namespace: TraitNamespace
    owner_id: Optional[str] = None
    category: str
    display_name: str
    description: str
    type: TraitType
    numeric_config: Optional[NumericConfig] = None
    categorical_config: Optional[CategoricalConfig] = None
    multilabel_config: Optional[MultilabelConfig] = None
    default_lock: Optional[LockType] = None
    default_learning_rate: float
    supports_dyadic: bool
    visibility: TraitVisibility
    created_at: str
    updated_at: str


class CreateTraitRequest(BaseModel):
    """Request schema for creating a trait."""

    model_config = ConfigDict(extra="forbid")

    name: str
    namespace: TraitNamespace
    category: str
    display_name: str
    type: TraitType
    visibility: TraitVisibility
    description: Optional[str] = None
    numeric_config: Optional[NumericConfig] = None
    categorical_config: Optional[CategoricalConfig] = None
    multilabel_config: Optional[MultilabelConfig] = None
    default_lock: Optional[LockType] = None
    default_learning_rate: float = 0.0
    supports_dyadic: bool = False


class UpdateTraitRequest(BaseModel):
    """
    Request schema for fully replacing a trait (PUT).

    Note: `name` and `namespace` are immutable after creation and cannot be changed.
    """

    model_config = ConfigDict(extra="forbid")

    category: str
    display_name: str
    description: str
    type: TraitType
    default_learning_rate: float
    supports_dyadic: bool
    visibility: TraitVisibility
    numeric_config: Optional[NumericConfig] = None
    categorical_config: Optional[CategoricalConfig] = None
    multilabel_config: Optional[MultilabelConfig] = None
    default_lock: Optional[LockType] = None


class PatchTraitRequest(BaseModel):
    """
    Request schema for partially updating a trait (PATCH).

    Note: `name` and `namespace` are immutable after creation and cannot be changed.
    """

    category: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TraitType] = None
    numeric_config: Optional[NumericConfig] = None
    categorical_config: Optional[CategoricalConfig] = None
    multilabel_config: Optional[MultilabelConfig] = None
    default_lock: Optional[LockType] = None
    default_learning_rate: Optional[float] = None
    supports_dyadic: Optional[bool] = None
    visibility: Optional[TraitVisibility] = None


class ListTraitsResponse(BaseModel):
    """Response schema for listing traits."""

    data: list[Trait] = Field(default_factory=list)
    paging: PageInfo
