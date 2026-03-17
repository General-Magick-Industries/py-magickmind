"""
Trait resource for Magick Mind SDK v1 API.

Provides CRUD operations for trait definitions.
"""

from __future__ import annotations

from typing import Optional

from magick_mind.models.v1.trait import (
    CategoricalConfig,
    CreateTraitRequest,
    ListTraitsResponse,
    LockType,
    MultilabelConfig,
    NumericConfig,
    PatchTraitRequest,
    Trait,
    TraitNamespace,
    TraitType,
    TraitVisibility,
    UpdateTraitRequest,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes


class TraitResourceV1(BaseResource):
    """Trait resource for managing trait definitions."""

    async def create(
        self,
        name: str,
        namespace: TraitNamespace,
        category: str,
        display_name: str,
        type: TraitType,
        visibility: TraitVisibility,
        description: Optional[str] = None,
        numeric_config: Optional[NumericConfig] = None,
        categorical_config: Optional[CategoricalConfig] = None,
        multilabel_config: Optional[MultilabelConfig] = None,
        default_lock: Optional[LockType] = None,
        default_learning_rate: float = 0.0,
        supports_dyadic: bool = False,
    ) -> Trait:
        """
        Create a new trait.

        Note: `TraitNamespace` includes `PROMOTED` which is not available in Blueprint namespace.

        Args:
            name: Trait name
            namespace: One of SYSTEM, USER, ORG, PROMOTED
            category: Trait category
            display_name: Human-readable display name
            type: One of NUMERIC, CATEGORICAL, MULTILABEL
            visibility: One of PRIVATE, ORG, PUBLIC
            description: Optional description
            numeric_config: Config for NUMERIC traits
            categorical_config: Config for CATEGORICAL traits
            multilabel_config: Config for MULTILABEL traits
            default_lock: One of HARD, SOFT
            default_learning_rate: Default learning rate (default 0.0)
            supports_dyadic: Whether trait supports dyadic interactions (default False)

        Returns:
            Created Trait object
        """
        request = CreateTraitRequest(
            name=name,
            namespace=namespace,
            category=category,
            display_name=display_name,
            type=type,
            visibility=visibility,
            description=description,
            numeric_config=numeric_config,
            categorical_config=categorical_config,
            multilabel_config=multilabel_config,
            default_lock=default_lock,
            default_learning_rate=default_learning_rate,
            supports_dyadic=supports_dyadic,
        )
        response = await self._http.post(
            Routes.TRAITS, json=request.model_dump(exclude_none=True)
        )
        return Trait(**response)

    async def get(self, trait_id: str) -> Trait:
        """
        Get a trait by ID.

        Args:
            trait_id: The trait ID to retrieve

        Returns:
            Trait object
        """
        response = await self._http.get(Routes.trait(trait_id))
        return Trait(**response)

    async def list(
        self,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> list[Trait]:
        """
        List traits with optional pagination.

        Args:
            cursor: Pagination cursor
            limit: Max results to return
            order: Sort order, ASC or DESC

        Returns:
            List of Trait objects
        """
        params: dict = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order
        response = await self._http.get(Routes.TRAITS, params=params)
        return ListTraitsResponse(**response).data

    async def update(
        self,
        trait_id: str,
        category: str,
        display_name: str,
        description: str,
        type: TraitType,
        default_learning_rate: float,
        supports_dyadic: bool,
        visibility: TraitVisibility,
        numeric_config: Optional[NumericConfig] = None,
        categorical_config: Optional[CategoricalConfig] = None,
        multilabel_config: Optional[MultilabelConfig] = None,
        default_lock: Optional[LockType] = None,
    ) -> Trait:
        """
        Fully replace a trait (PUT).

        Note: `name` and `namespace` are immutable after creation and cannot be changed.

        Args:
            trait_id: The trait ID to update
            category: Trait category
            display_name: Human-readable display name
            description: Trait description
            type: One of NUMERIC, CATEGORICAL, MULTILABEL
            default_learning_rate: Default learning rate
            supports_dyadic: Whether trait supports dyadic interactions
            visibility: One of PRIVATE, ORG, PUBLIC
            numeric_config: Config for NUMERIC traits
            categorical_config: Config for CATEGORICAL traits
            multilabel_config: Config for MULTILABEL traits
            default_lock: One of HARD, SOFT

        Returns:
            Updated Trait object
        """
        request = UpdateTraitRequest(
            category=category,
            display_name=display_name,
            description=description,
            type=type,
            default_learning_rate=default_learning_rate,
            supports_dyadic=supports_dyadic,
            visibility=visibility,
            numeric_config=numeric_config,
            categorical_config=categorical_config,
            multilabel_config=multilabel_config,
            default_lock=default_lock,
        )
        response = await self._http.put(
            Routes.trait(trait_id), json=request.model_dump(exclude_none=True)
        )
        return Trait(**response)

    async def patch(
        self,
        trait_id: str,
        category: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        type: Optional[TraitType] = None,
        numeric_config: Optional[NumericConfig] = None,
        categorical_config: Optional[CategoricalConfig] = None,
        multilabel_config: Optional[MultilabelConfig] = None,
        default_lock: Optional[LockType] = None,
        default_learning_rate: Optional[float] = None,
        supports_dyadic: Optional[bool] = None,
        visibility: Optional[TraitVisibility] = None,
    ) -> Trait:
        """
        Partially update a trait (PATCH).

        Note: `name` and `namespace` are immutable after creation and cannot be changed.

        Args:
            trait_id: The trait ID to patch
            category: Trait category
            display_name: Human-readable display name
            description: Trait description
            type: One of NUMERIC, CATEGORICAL, MULTILABEL
            numeric_config: Config for NUMERIC traits
            categorical_config: Config for CATEGORICAL traits
            multilabel_config: Config for MULTILABEL traits
            default_lock: One of HARD, SOFT
            default_learning_rate: Default learning rate
            supports_dyadic: Whether trait supports dyadic interactions
            visibility: One of PRIVATE, ORG, PUBLIC

        Returns:
            Updated Trait object
        """
        request = PatchTraitRequest(
            category=category,
            display_name=display_name,
            description=description,
            type=type,
            numeric_config=numeric_config,
            categorical_config=categorical_config,
            multilabel_config=multilabel_config,
            default_lock=default_lock,
            default_learning_rate=default_learning_rate,
            supports_dyadic=supports_dyadic,
            visibility=visibility,
        )
        response = await self._http.patch(
            Routes.trait(trait_id), json=request.model_dump(exclude_none=True)
        )
        return Trait(**response)

    async def delete(self, trait_id: str) -> None:
        """
        Delete a trait.

        Args:
            trait_id: The trait ID to delete
        """
        await self._http.delete(Routes.trait(trait_id))
