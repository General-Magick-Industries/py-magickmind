"""V1 persona resource implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.persona import (
    CreatePersonaFromBlueprintRequest,
    CreatePersonaRequest,
    CreatePersonaVersionRequest,
    ListPersonaVersionsResponse,
    Persona,
    PersonaVersion,
    PersonaWithVersion,
    PreparePersonaRequest,
    PreparePersonaResponse,
    SetActiveVersionRequest,
    UpdatePersonaRequest,
)
from magick_mind.models.v1.personality import (
    DyadicConfig,
    GrowthConfig,
    TraitConstraint,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes

if TYPE_CHECKING:
    from magick_mind.http import HTTPClient


class PersonaResourceV1(BaseResource):
    """
    Persona resource client for V1 API.

    Provides persona CRUD, blueprint-based creation, and version management.

    Example:
        # Create a persona
        persona = await client.v1.persona.create(
            name="Aria",
            role="assistant",
        )

        # Create from blueprint
        result = await client.v1.persona.create_from_blueprint(
            blueprint_id="bp-123",
            name="Aria",
            role="assistant",
        )
        print(result.persona.id, result.version.version)

        # Version management
        version = await client.v1.persona.create_version(
            persona_id="p-123",
            version="1.1",
        )
        active = await client.v1.persona.get_active_version("p-123")
    """

    # --- Base CRUD ---

    async def create(
        self,
        name: str,
        role: str,
        artifact_id: Optional[str] = None,
        traits: Optional[list[str]] = None,
        tones: Optional[list[str]] = None,
        background_story: str = "",
    ) -> Persona:
        """
        Create a new persona.

        Args:
            name: Persona name
            role: Persona role
            artifact_id: Optional associated artifact ID
            traits: Optional list of trait names
            tones: Optional list of tone names
            background_story: Optional background story

        Returns:
            Persona
        """
        request = CreatePersonaRequest(
            artifact_id=artifact_id,
            name=name,
            role=role,
            traits=traits or [],
            tones=tones or [],
            background_story=background_story,
        )
        response = await self._http.post(
            Routes.PERSONAS, json=request.model_dump(exclude_none=True)
        )
        return Persona.model_validate(response)

    async def get(self, persona_id: str) -> Persona:
        """
        Get a persona by ID.

        Args:
            persona_id: Persona ID

        Returns:
            Persona
        """
        response = await self._http.get(Routes.persona(persona_id))
        return Persona.model_validate(response)

    async def update(
        self,
        persona_id: str,
        name: str,
        role: str,
        artifact_id: Optional[str] = None,
        traits: Optional[list[str]] = None,
        tones: Optional[list[str]] = None,
        background_story: str = "",
    ) -> Persona:
        """
        Update a persona.

        Args:
            persona_id: Persona ID
            name: Updated name
            role: Updated role
            artifact_id: Optional updated artifact ID
            traits: Updated traits list
            tones: Updated tones list
            background_story: Updated background story

        Returns:
            Persona
        """
        request = UpdatePersonaRequest(
            artifact_id=artifact_id,
            name=name,
            role=role,
            traits=traits or [],
            tones=tones or [],
            background_story=background_story,
        )
        response = await self._http.put(
            Routes.persona(persona_id),
            json=request.model_dump(exclude_none=True),
        )
        return Persona.model_validate(response)

    async def delete(self, persona_id: str) -> None:
        """
        Delete a persona.

        Args:
            persona_id: Persona ID
        """
        await self._http.delete(Routes.persona(persona_id))

    async def prepare(
        self,
        persona_id: str,
        *,
        user_id: Optional[str] = None,
    ) -> PreparePersonaResponse:
        """
        Prepare a persona's system prompt.

        Resolves the persona's traits, active version constraints, and optional
        user-specific context into a ready-to-use system prompt string.

        Args:
            persona_id: Persona ID
            user_id: Optional user ID for user-specific prompt context

        Returns:
            PreparePersonaResponse with the system_prompt string
        """
        request = PreparePersonaRequest(user_id=user_id)
        response = await self._http.post(
            Routes.persona_prepare(persona_id),
            json=request.model_dump(exclude_none=True),
        )
        return PreparePersonaResponse.model_validate(response)

    async def create_from_blueprint(
        self,
        blueprint_id: str,
        name: str,
        role: str,
        background_story: Optional[str] = None,
        artifact_id: Optional[str] = None,
        trait_overrides: Optional[list[TraitConstraint]] = None,
        additional_traits: Optional[list[TraitConstraint]] = None,
        remove_traits: Optional[list[str]] = None,
        growth_override: Optional[GrowthConfig] = None,
        dyadic_override: Optional[DyadicConfig] = None,
    ) -> PersonaWithVersion:
        """
        Create a persona from a blueprint with optional overrides.

        Args:
            blueprint_id: Source blueprint ID
            name: Persona name
            role: Persona role
            background_story: Optional background story
            artifact_id: Optional artifact ID
            trait_overrides: Optional trait constraint overrides
            additional_traits: Optional additional trait constraints
            remove_traits: Optional trait refs to remove
            growth_override: Optional growth config override
            dyadic_override: Optional dyadic config override

        Returns:
            PersonaWithVersion containing both the persona and its initial version
        """
        request = CreatePersonaFromBlueprintRequest(
            blueprint_id=blueprint_id,
            name=name,
            role=role,
            background_story=background_story,
            artifact_id=artifact_id,
            trait_overrides=trait_overrides or [],
            additional_traits=additional_traits or [],
            remove_traits=remove_traits or [],
            growth_override=growth_override,
            dyadic_override=dyadic_override,
        )
        response = await self._http.post(
            Routes.PERSONA_FROM_BLUEPRINT,
            json=request.model_dump(exclude_none=True),
        )
        return PersonaWithVersion.model_validate(response)

    # --- Versioning ---

    async def create_version(
        self,
        persona_id: str,
        version: str,
        constraints: Optional[list[TraitConstraint]] = None,
        growth: Optional[GrowthConfig] = None,
        dyadic: Optional[DyadicConfig] = None,
    ) -> PersonaVersion:
        """
        Create a new version for a persona.

        Args:
            persona_id: Persona ID
            version: Version string
            constraints: Optional trait constraints
            growth: Optional growth config
            dyadic: Optional dyadic config

        Returns:
            PersonaVersion
        """
        request = CreatePersonaVersionRequest(
            version=version,
            constraints=constraints or [],
            growth=growth,
            dyadic=dyadic,
        )
        response = await self._http.post(
            Routes.persona_versions(persona_id),
            json=request.model_dump(exclude_none=True),
        )
        return PersonaVersion.model_validate(response)

    async def list_versions(
        self,
        persona_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> ListPersonaVersionsResponse:
        """
        List all versions for a persona.

        Args:
            persona_id: Persona ID
            cursor: Pagination cursor
            limit: Maximum number of results

        Returns:
            ListPersonaVersionsResponse with data and paging
        """
        params: dict[str, object] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit

        response = await self._http.get(
            Routes.persona_versions(persona_id),
            params=params if params else None,
        )
        return ListPersonaVersionsResponse.model_validate(response)

    async def get_version(self, persona_id: str, version: str) -> PersonaVersion:
        """
        Get a specific version by version string.

        Args:
            persona_id: Persona ID
            version: Version string

        Returns:
            PersonaVersion
        """
        response = await self._http.get(Routes.persona_version(persona_id, version))
        return PersonaVersion.model_validate(response)

    async def get_active_version(self, persona_id: str) -> PersonaVersion:
        """
        Get the currently active version.

        Args:
            persona_id: Persona ID

        Returns:
            PersonaVersion (the active one)
        """
        response = await self._http.get(Routes.persona_active_version(persona_id))
        return PersonaVersion.model_validate(response)

    async def set_active_version(self, persona_id: str, version: str) -> PersonaVersion:
        """
        Set a version as active.

        Args:
            persona_id: Persona ID
            version: Version string to activate

        Returns:
            PersonaVersion
        """
        request = SetActiveVersionRequest(version=version)
        response = await self._http.put(
            Routes.persona_active_version(persona_id),
            json=request.model_dump(),
        )
        return PersonaVersion.model_validate(response)
