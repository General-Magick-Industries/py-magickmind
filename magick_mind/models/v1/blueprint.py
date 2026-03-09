"""V1 Blueprint API models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from magick_mind.models.common import PageInfo
from magick_mind.models.v1.personality import (
    BlueprintTrait,
    DyadicConfig,
    GrowthConfig,
    Namespace,
    Visibility,
)


class Blueprint(BaseModel):
    """Blueprint schema — a reusable persona trait template."""

    id: str
    blueprint_id: str
    name: str
    description: str = ""
    category: str
    namespace: Namespace
    owner_id: Optional[str] = None
    traits: list[BlueprintTrait] = Field(default_factory=list)
    default_growth: Optional[GrowthConfig] = None
    default_dyadic: Optional[DyadicConfig] = None
    visibility: Visibility
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""


class CreateBlueprintRequest(BaseModel):
    """Request to create a blueprint."""

    blueprint_id: str
    name: str
    description: Optional[str] = None
    category: str
    namespace: Namespace
    traits: list[BlueprintTrait] = Field(default_factory=list)
    default_growth: Optional[GrowthConfig] = None
    default_dyadic: Optional[DyadicConfig] = None
    visibility: Visibility


class UpdateBlueprintRequest(BaseModel):
    """Request to fully replace a blueprint."""

    name: str
    description: str
    category: str
    traits: list[BlueprintTrait] = Field(default_factory=list)
    default_growth: Optional[GrowthConfig] = None
    default_dyadic: Optional[DyadicConfig] = None
    visibility: Visibility


class PatchBlueprintRequest(BaseModel):
    """Request to partially update a blueprint."""

    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    traits: Optional[list[BlueprintTrait]] = None
    default_growth: Optional[GrowthConfig] = None
    default_dyadic: Optional[DyadicConfig] = None
    visibility: Optional[Visibility] = None


class CloneBlueprintRequest(BaseModel):
    """Request to clone a blueprint."""

    new_owner_id: str
    new_namespace: Namespace
    new_blueprint_id: Optional[str] = None


class ValidateBlueprintRequest(BaseModel):
    """Request to validate a blueprint payload without saving."""

    blueprint_id: str
    name: str
    description: Optional[str] = None
    category: str
    namespace: Namespace
    owner_id: Optional[str] = None
    traits: list[BlueprintTrait] = Field(default_factory=list)
    default_growth: Optional[GrowthConfig] = None
    default_dyadic: Optional[DyadicConfig] = None
    visibility: Visibility


class ValidationError(BaseModel):
    """A single validation error."""

    field: str
    message: str
    trait_ref: Optional[str] = None


class ValidateBlueprintResponse(BaseModel):
    """Response from blueprint validation."""

    valid: bool
    errors: list[ValidationError] = Field(default_factory=list)


class HydratedBlueprintTrait(BaseModel):
    """A blueprint trait enriched with full trait registry data."""

    blueprint_trait: BlueprintTrait
    trait_name: str
    trait_display_name: str
    trait_description: str
    trait_type: str
    trait_category: str


class HydratedBlueprint(BaseModel):
    """A blueprint with hydrated trait definitions."""

    blueprint: Blueprint
    hydrated_traits: list[HydratedBlueprintTrait] = Field(default_factory=list)


class ListBlueprintsResponse(BaseModel):
    """Paginated list of blueprints."""

    data: list[Blueprint] = Field(default_factory=list)
    paging: PageInfo
