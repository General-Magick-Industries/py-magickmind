"""V1 Persona API models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from magick_mind.models.common import PageInfo
from magick_mind.models.v1.personality import (
    DyadicConfig,
    GrowthConfig,
    TraitConstraint,
)


class Persona(BaseModel):
    """Persona schema."""

    id: str
    artifact_id: Optional[str] = None
    name: str
    role: str
    traits: list[str] = Field(default_factory=list)
    tones: list[str] = Field(default_factory=list)
    background_story: str = ""
    created_by: str = ""
    updated_by: str = ""
    active_version: Optional[str] = None


class CreatePersonaRequest(BaseModel):
    """Request to create a persona. Note: created_by is NOT included."""

    artifact_id: Optional[str] = None
    name: str
    role: str
    traits: list[str] = Field(default_factory=list)
    tones: list[str] = Field(default_factory=list)
    background_story: str = ""


class UpdatePersonaRequest(BaseModel):
    """Request to update a persona."""

    artifact_id: Optional[str] = None
    name: str
    role: str
    traits: list[str] = Field(default_factory=list)
    tones: list[str] = Field(default_factory=list)
    background_story: str = ""


class CreatePersonaFromBlueprintRequest(BaseModel):
    """Request to create a persona from a blueprint with optional overrides."""

    blueprint_id: str
    name: str
    role: str
    background_story: Optional[str] = None
    artifact_id: Optional[str] = None
    trait_overrides: list[TraitConstraint] = Field(default_factory=list)
    additional_traits: list[TraitConstraint] = Field(default_factory=list)
    remove_traits: list[str] = Field(default_factory=list)
    growth_override: Optional[GrowthConfig] = None
    dyadic_override: Optional[DyadicConfig] = None


# --- Persona Versioning ---
class PersonaVersion(BaseModel):
    """A version snapshot of a persona's trait config."""

    id: str
    persona_id: str
    version: str
    constraints: list[TraitConstraint] = Field(default_factory=list)
    growth: Optional[GrowthConfig] = None
    dyadic: Optional[DyadicConfig] = None
    created_at: str = ""
    is_active: bool = False


class CreatePersonaVersionRequest(BaseModel):
    """Request to create a new persona version."""

    version: str
    constraints: list[TraitConstraint] = Field(default_factory=list)
    growth: Optional[GrowthConfig] = None
    dyadic: Optional[DyadicConfig] = None


class SetActiveVersionRequest(BaseModel):
    """Request to set the active version."""

    version: str


class PersonaWithVersion(BaseModel):
    """Response containing both persona and its initial version."""

    persona: Persona
    version: PersonaVersion


class PreparePersonaRequest(BaseModel):
    """Request to prepare a persona's system prompt."""

    user_id: Optional[str] = None


class PreparePersonaResponse(BaseModel):
    """Response containing the generated system prompt."""

    system_prompt: str


class ListPersonaVersionsResponse(BaseModel):
    """Paginated list of persona versions."""

    data: list[PersonaVersion] = Field(default_factory=list)
    paging: PageInfo
