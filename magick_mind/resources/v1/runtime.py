"""V1 runtime resource implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.runtime import EffectivePersonality
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes

if TYPE_CHECKING:
    pass


class RuntimeResourceV1(BaseResource):
    """
    Runtime resource client for V1 API.

    Provides access to effective personality computation and cache management.

    Example:
        # Get effective personality (global)
        personality = await client.v1.runtime.get_effective_personality("agent-123")

        # Get effective personality (dyadic — for a specific user)
        personality = await client.v1.runtime.get_effective_personality(
            "agent-123", user_id="user-456"
        )

        # Invalidate cached personality
        await client.v1.runtime.invalidate_cache("agent-123")
    """

    async def get_effective_personality(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
    ) -> EffectivePersonality:
        """
        Get the effective (blended) personality of an agent.

        Merges the authored traits of the agent's persona version with
        globally and dyadically learned values.

        Args:
            agent_id: Agent (end user) ID
            user_id: Optional user ID for dyadic mode

        Returns:
            EffectivePersonality with blended trait values and source breakdown
        """
        params = {}
        if user_id is not None:
            params["user_id"] = user_id

        response = await self._http.get(
            Routes.runtime_effective_personality(agent_id),
            params=params if params else None,
        )
        return EffectivePersonality.model_validate(response)

    async def invalidate_cache(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Invalidate the cached effective personality for an agent.

        Args:
            agent_id: Agent (end user) ID
            user_id: Optional user ID to invalidate a specific dyad cache
        """
        body: dict[str, str] = {"agent_id": agent_id}
        if user_id is not None:
            body["user_id"] = user_id

        await self._http.post(Routes.RUNTIME_INVALIDATE_CACHE, json=body)
