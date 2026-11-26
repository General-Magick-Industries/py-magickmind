"""V1 blueprint resource implementation."""

from __future__ import annotations

from typing import Optional

from magick_mind.models.v1.blueprint import (
    Blueprint,
    CloneBlueprintRequest,
    CreateBlueprintRequest,
    ListBlueprintsResponse,
    PatchBlueprintRequest,
    SetBlueprintVisibilityRequest,
    UpdateBlueprintRequest,
)
from magick_mind.models.v1.personality import (
    BlueprintTrait,
    DyadicConfig,
    GrowthConfig,
    Visibility,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes


class BlueprintResourceV1(BaseResource):
    """
    Blueprint resource client for V1 API.

    Blueprints are reusable persona trait templates that define traits,
    growth behavior, and dyadic learning config. Only the owner can change
    a blueprint; anyone can read or clone a PUBLIC one.

    Example:
        # Create a blueprint
        bp = await client.v1.blueprint.create(
            blueprint_id="friendly-bot",
            name="Friendly Bot",
            category="social",
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
        visibility: Visibility,
        description: Optional[str] = None,
        traits: Optional[list[BlueprintTrait]] = None,
        default_growth: Optional[GrowthConfig] = None,
        default_dyadic: Optional[DyadicConfig] = None,
    ) -> Blueprint:
        """
        Create a new blueprint owned by the caller.

        Args:
            blueprint_id: Blueprint key, unique per owner
            name: Blueprint name
            category: Blueprint category
            visibility: PRIVATE or PUBLIC
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
        blueprint_id: str,
        owner_id: Optional[str] = None,
    ) -> Blueprint:
        """
        Get a blueprint by its key (owner + blueprint_id).

        Args:
            blueprint_id: Blueprint key
            owner_id: Owner ID; defaults to the authenticated caller

        Returns:
            Blueprint
        """
        params = {"blueprint_id": blueprint_id}
        if owner_id is not None:
            params["owner_id"] = owner_id
        response = await self._http.get(Routes.BLUEPRINTS_BY_KEY, params=params)
        return Blueprint.model_validate(response)

    async def list(
        self,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> ListBlueprintsResponse:
        """
        List blueprints with cursor pagination.

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
        clear_default_growth: bool = False,
        clear_default_dyadic: bool = False,
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
            clear_default_growth: Remove the default growth config
            clear_default_dyadic: Remove the default dyadic config

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
            clear_default_growth=clear_default_growth or None,
            clear_default_dyadic=clear_default_dyadic or None,
        )
        response = await self._http.patch(
            Routes.blueprint(blueprint_id),
            json=request.model_dump(exclude_none=True),
        )
        return Blueprint.model_validate(response)

    async def set_visibility(
        self, blueprint_id: str, visibility: Visibility
    ) -> Blueprint:
        """
        Switch a blueprint between PRIVATE and PUBLIC.

        Args:
            blueprint_id: Internal blueprint ID
            visibility: PRIVATE or PUBLIC

        Returns:
            Blueprint
        """
        request = SetBlueprintVisibilityRequest(visibility=visibility)
        response = await self._http.patch(
            Routes.blueprint_visibility(blueprint_id),
            json=request.model_dump(),
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
        new_blueprint_id: Optional[str] = None,
    ) -> Blueprint:
        """
        Clone a blueprint (your own, or anyone's PUBLIC one) into a new
        PRIVATE blueprint owned by the caller.

        Args:
            blueprint_id: Source blueprint internal ID
            new_blueprint_id: Optional key for the copy (generated if omitted)

        Returns:
            Blueprint (the cloned copy)
        """
        request = CloneBlueprintRequest(new_blueprint_id=new_blueprint_id)
        response = await self._http.post(
            Routes.blueprint_clone(blueprint_id),
            json=request.model_dump(exclude_none=True),
        )
        return Blueprint.model_validate(response)
