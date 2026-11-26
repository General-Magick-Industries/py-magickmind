"""V1 Blueprint API models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from magick_mind.models.common import PageInfo
from magick_mind.models.v1.personality import (
    BlueprintTrait,
    DyadicConfig,
    GrowthConfig,
    Visibility,
)


class Blueprint(BaseModel):
    """Blueprint schema — a reusable persona trait template."""

    id: str
    blueprint_id: str
    name: str
    description: str = ""
    category: str
    owner_id: Optional[str] = None
    traits: list[BlueprintTrait] = Field(default_factory=list)
    default_growth: Optional[GrowthConfig] = None
    default_dyadic: Optional[DyadicConfig] = None
    visibility: Visibility
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    revision: int = 0

    @field_validator("traits", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []


class CreateBlueprintRequest(BaseModel):
    """Request to create a blueprint."""

    blueprint_id: str
    name: str
    description: Optional[str] = None
    category: str
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
    """Request to partially update a blueprint.

    Visibility is changed through its own route; see SetBlueprintVisibilityRequest.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    traits: Optional[list[BlueprintTrait]] = None
    default_growth: Optional[GrowthConfig] = None
    default_dyadic: Optional[DyadicConfig] = None
    clear_default_growth: Optional[bool] = None
    clear_default_dyadic: Optional[bool] = None


class SetBlueprintVisibilityRequest(BaseModel):
    """Request to switch a blueprint between PRIVATE and PUBLIC."""

    visibility: Visibility


class CloneBlueprintRequest(BaseModel):
    """Request to clone a blueprint into the caller's own blueprints."""

    new_blueprint_id: Optional[str] = None


class ListBlueprintsResponse(BaseModel):
    """Paginated list of blueprints."""

    data: list[Blueprint] = Field(default_factory=list)
    paging: PageInfo

    @field_validator("data", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []
