"""V1 blueprint resource implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.blueprint import (
    Blueprint,
    CloneBlueprintRequest,
    CreateBlueprintRequest,
    HydratedBlueprint,
    ListBlueprintsResponse,
    PatchBlueprintRequest,
    UpdateBlueprintRequest,
    ValidateBlueprintRequest,
    ValidateBlueprintResponse,
)
from magick_mind.models.v1.personality import (
    BlueprintTrait,
    DyadicConfig,
    GrowthConfig,
    Namespace,
    Visibility,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes

if TYPE_CHECKING:
    pass


class BlueprintResourceV1(BaseResource):
    """
    Blueprint resource client for V1 API.

    Blueprints are reusable persona trait templates that define traits,
    growth behavior, and dyadic learning config.

    Example:
        # Create a blueprint
        bp = await client.v1.blueprint.create(
            blueprint_id="friendly-bot",
            name="Friendly Bot",
            category="social",
            namespace="USER",
            visibility="PRIVATE",
        )

        # List blueprints
        response = await client.v1.blueprint.list()
        for bp in response.data:
            print(bp.name)
    """

    async def create(
        self,
        blueprint_id: str,
        name: str,
        category: str,
        namespace: Namespace,
        visibility: Visibility,
        description: Optional[str] = None,
        traits: Optional[list[BlueprintTrait]] = None,
        default_growth: Optional[GrowthConfig] = None,
        default_dyadic: Optional[DyadicConfig] = None,
    ) -> Blueprint:
        """
        Create a new blueprint.

        Args:
            blueprint_id: Unique blueprint identifier
            name: Blueprint name
            category: Blueprint category
            namespace: Namespace (SYSTEM, USER, or ORG)
            visibility: Visibility (PRIVATE, ORG, or PUBLIC)
            description: Optional description
            traits: Optional list of blueprint traits
            default_growth: Optional default growth configuration
            default_dyadic: Optional default dyadic configuration

        Returns:
            Blueprint
        """
        request = CreateBlueprintRequest(
            blueprint_id=blueprint_id,
            name=name,
            description=description,
            category=category,
            namespace=namespace,
            traits=traits or [],
            default_growth=default_growth,
            default_dyadic=default_dyadic,
            visibility=visibility,
        )
        response = await self._http.post(
            Routes.BLUEPRINTS, json=request.model_dump(exclude_none=True)
        )
        return Blueprint.model_validate(response)

    async def get(self, blueprint_id: str) -> Blueprint:
        """
        Get a blueprint by internal ID.

        Args:
            blueprint_id: Internal blueprint ID

        Returns:
            Blueprint
        """
        response = await self._http.get(Routes.blueprint(blueprint_id))
        return Blueprint.model_validate(response)

    async def get_by_key(
        self,
        namespace: str,
        owner_id: str,
        blueprint_id: str,
    ) -> Blueprint:
        """
        Get a blueprint by its composite key (namespace + owner_id + blueprint_id).

        Args:
            namespace: Blueprint namespace
            owner_id: Owner ID
            blueprint_id: Blueprint ID within the namespace

        Returns:
            Blueprint
        """
        params = {
            "namespace": namespace,
            "owner_id": owner_id,
            "blueprint_id": blueprint_id,
        }
        response = await self._http.get(Routes.BLUEPRINTS_BY_KEY, params=params)
        return Blueprint.model_validate(response)

    async def list(
        self,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> ListBlueprintsResponse:
        """
        List all blueprints with cursor pagination.

        Args:
            cursor: Pagination cursor
            limit: Maximum number of results
            order: Sort order (ASC or DESC)

        Returns:
            ListBlueprintsResponse with data and paging
        """
        params: dict[str, object] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order

        response = await self._http.get(
            Routes.BLUEPRINTS, params=params if params else None
        )
        return ListBlueprintsResponse.model_validate(response)

    async def update(
        self,
        blueprint_id: str,
        name: str,
        description: str,
        category: str,
        visibility: Visibility,
        traits: Optional[list[BlueprintTrait]] = None,
        default_growth: Optional[GrowthConfig] = None,
        default_dyadic: Optional[DyadicConfig] = None,
    ) -> Blueprint:
        """
        Full replace update of a blueprint.

        Args:
            blueprint_id: Internal blueprint ID
            name: Updated name
            description: Updated description
            category: Updated category
            visibility: Updated visibility
            traits: Updated traits list
            default_growth: Updated growth config
            default_dyadic: Updated dyadic config

        Returns:
            Blueprint
        """
        request = UpdateBlueprintRequest(
            name=name,
            description=description,
            category=category,
            traits=traits or [],
            default_growth=default_growth,
            default_dyadic=default_dyadic,
            visibility=visibility,
        )
        response = await self._http.put(
            Routes.blueprint(blueprint_id),
            json=request.model_dump(exclude_none=True),
        )
        return Blueprint.model_validate(response)

    async def patch(
        self,
        blueprint_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        traits: Optional[list[BlueprintTrait]] = None,
        default_growth: Optional[GrowthConfig] = None,
        default_dyadic: Optional[DyadicConfig] = None,
        visibility: Optional[Visibility] = None,
    ) -> Blueprint:
        """
        Partial update of a blueprint. Only provided fields are updated.

        Args:
            blueprint_id: Internal blueprint ID
            name: Optional updated name
            description: Optional updated description
            category: Optional updated category
            traits: Optional updated traits
            default_growth: Optional updated growth config
            default_dyadic: Optional updated dyadic config
            visibility: Optional updated visibility

        Returns:
            Blueprint
        """
        request = PatchBlueprintRequest(
            name=name,
            description=description,
            category=category,
            traits=traits,
            default_growth=default_growth,
            default_dyadic=default_dyadic,
            visibility=visibility,
        )
        response = await self._http.patch(
            Routes.blueprint(blueprint_id),
            json=request.model_dump(exclude_none=True),
        )
        return Blueprint.model_validate(response)

    async def delete(self, blueprint_id: str) -> None:
        """
        Delete a blueprint.

        Args:
            blueprint_id: Internal blueprint ID
        """
        await self._http.delete(Routes.blueprint(blueprint_id))

    async def clone(
        self,
        blueprint_id: str,
        new_owner_id: str,
        new_namespace: Namespace,
        new_blueprint_id: Optional[str] = None,
    ) -> Blueprint:
        """
        Clone a blueprint to a new owner/namespace.

        Args:
            blueprint_id: Source blueprint internal ID
            new_owner_id: New owner ID
            new_namespace: New namespace
            new_blueprint_id: Optional new blueprint ID (auto-generated if omitted)

        Returns:
            Blueprint (the cloned copy)
        """
        request = CloneBlueprintRequest(
            new_owner_id=new_owner_id,
            new_namespace=new_namespace,
            new_blueprint_id=new_blueprint_id,
        )
        response = await self._http.post(
            Routes.blueprint_clone(blueprint_id),
            json=request.model_dump(exclude_none=True),
        )
        return Blueprint.model_validate(response)

    async def validate(
        self,
        blueprint_id: str,
        name: str,
        category: str,
        namespace: Namespace,
        visibility: Visibility,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
        traits: Optional[list[BlueprintTrait]] = None,
        default_growth: Optional[GrowthConfig] = None,
        default_dyadic: Optional[DyadicConfig] = None,
    ) -> ValidateBlueprintResponse:
        """
        Validate a blueprint payload without saving.

        Args:
            blueprint_id: Blueprint identifier
            name: Blueprint name
            category: Category
            namespace: Namespace
            visibility: Visibility
            description: Optional description
            owner_id: Optional owner ID
            traits: Optional traits
            default_growth: Optional growth config
            default_dyadic: Optional dyadic config

        Returns:
            ValidateBlueprintResponse with valid flag and any errors
        """
        request = ValidateBlueprintRequest(
            blueprint_id=blueprint_id,
            name=name,
            description=description,
            category=category,
            namespace=namespace,
            owner_id=owner_id,
            traits=traits or [],
            default_growth=default_growth,
            default_dyadic=default_dyadic,
            visibility=visibility,
        )
        response = await self._http.post(
            Routes.BLUEPRINTS_VALIDATE,
            json=request.model_dump(exclude_none=True),
        )
        return ValidateBlueprintResponse.model_validate(response)

    async def hydrate(self, blueprint_id: str) -> HydratedBlueprint:
        """
        Get a blueprint with full trait definitions from the Trait Registry.

        Args:
            blueprint_id: Internal blueprint ID

        Returns:
            HydratedBlueprint with enriched trait data
        """
        response = await self._http.get(Routes.blueprint_hydrate(blueprint_id))
        return HydratedBlueprint.model_validate(response)
