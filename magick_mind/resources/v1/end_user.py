"""
End user resource for Magick Mind SDK v1 API.

Provides methods for CRUD operations on end users in the agentic SaaS backend.
"""

from __future__ import annotations

from typing import Optional


from magick_mind.exceptions import MagickMindError, hint_by_status
from magick_mind.models.v1.end_user import (
    AttachPersonaRequest,
    CreateEndUserRequest,
    EndUser,
    MintEndUserTokenRequest,
    MintEndUserTokenResponse,
    ParticipantType,
    QueryEndUserResponse,
    RefreshEndUserTokenRequest,
    RevokeEndUserTokenRequest,
    RevokeEndUserTokenResponse,
    SetAgentPersonaVersionRequest,
    UpdateEndUserRequest,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes


class EndUserResourceV1(BaseResource):
    """
    End user resource for managing end users in agentic SaaS applications.

    End users represent the actual users of applications built on the Magick Mind
    platform in a multi-tenant architecture. An end user of participant type
    ``AGENT`` is an agent identity: attach a persona with :meth:`attach_persona`,
    mint its credential with :meth:`mint_token`, and the agent process keeps that
    credential alive with :meth:`refresh_own_token`.
    """

    async def create(
        self,
        name: str,
        external_id: Optional[str] = None,
        *,
        persona_id: Optional[str] = None,
        participant_type: Optional[ParticipantType] = None,
    ) -> EndUser:
        """
        Create a new end user.

        Args:
            name: End user name (required)
            external_id: Optional external ID for mapping to external systems
            persona_id: Persona to attach at creation (agents)
            participant_type: ``"HUMAN"`` (server default) or ``"AGENT"``

        Returns:
            Created EndUser object

        Example:
            agent = await client.v1.end_user.create(
                name="Aria", participant_type="AGENT", persona_id="p-1"
            )
        """
        request = CreateEndUserRequest(
            name=name,
            external_id=external_id,
            persona_id=persona_id,
            participant_type=participant_type,
        )

        response = await self._http.post(
            Routes.END_USERS, json=request.model_dump(exclude_none=True)
        )
        return EndUser(**response)

    async def attach_persona(
        self, agent_id: str, *, persona_id: str, version_id: str
    ) -> EndUser:
        """
        Permanently attach a persona, at a given version, to an agent.

        Service-user credentials only: an agent must not be able to switch
        which persona it runs. Change the version later with
        :meth:`set_persona_version`.
        """
        request = AttachPersonaRequest(persona_id=persona_id, version_id=version_id)
        response = await self._http.post(
            Routes.end_user_persona(agent_id), json=request.model_dump()
        )
        return EndUser(**response)

    async def set_persona_version(self, agent_id: str, *, version_id: str) -> EndUser:
        """Change an agent's active version within its attached persona."""
        request = SetAgentPersonaVersionRequest(version_id=version_id)
        response = await self._http.patch(
            Routes.end_user_persona_version(agent_id), json=request.model_dump()
        )
        return EndUser(**response)

    async def get(self, end_user_id: str) -> EndUser:
        """
        Get an end user by ID.

        Args:
            end_user_id: The end user ID to retrieve

        Returns:
            EndUser object

        Example:
            end_user = await client.v1.end_user.get(end_user_id="user-123")
            print(f"End user name: {end_user.name}")
        """
        response = await self._http.get(Routes.end_user(end_user_id))
        return EndUser(**response)

    async def query(
        self,
        name: Optional[str] = None,
        external_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        participant_type: Optional[ParticipantType] = None,
    ) -> list[EndUser]:
        """
        Query end users with optional filters.

        All parameters are optional. If no filters are provided, returns all
        accessible end users.

        Args:
            name: Filter by end user name (optional)
            external_id: Filter by external ID (optional)
            cursor: Pagination cursor (optional)
            limit: Maximum number of results to return (optional)
            order: Sort order (optional)
            participant_type: ``"HUMAN"`` or ``"AGENT"`` (optional)

        Returns:
            List of EndUser objects matching the query

        Example:
            # Search by name
            end_users = await client.v1.end_user.query(name="John")
            for user in end_users:
                print(f"- {user.name}")

            # Search by external ID
            user = await client.v1.end_user.query(external_id="ext-789")
        """
        params = {}
        if name is not None:
            params["name"] = name
        if external_id is not None:
            params["external_id"] = external_id
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order
        if participant_type is not None:
            params["participant_type"] = participant_type

        response = await self._http.get(Routes.END_USERS, params=params)
        query_response = QueryEndUserResponse(**response)
        return query_response.data

    async def update(
        self,
        end_user_id: str,
        name: Optional[str] = None,
        external_id: Optional[str] = None,
    ) -> EndUser:
        """
        Update an existing end user.

        All update fields are optional. Only provided fields will be updated.

        Args:
            end_user_id: The end user ID to update
            name: New end user name (optional)
            external_id: New external ID (optional)

        Returns:
            Updated EndUser object

        Example:
            updated = await client.v1.end_user.update(
                end_user_id="user-123",
                name="Jane Doe",
                external_id="new-ext-id"
            )
            print(f"Updated end user: {updated.name}")
        """
        request = UpdateEndUserRequest(
            name=name,
            external_id=external_id,
        )

        response = await self._http.put(
            Routes.end_user(end_user_id), json=request.model_dump(exclude_none=True)
        )
        return EndUser(**response)

    async def delete(self, end_user_id: str) -> None:
        """
        Delete an end user.

        Args:
            end_user_id: The end user ID to delete

        Example:
            await client.v1.end_user.delete(end_user_id="user-123")
            print("End user deleted successfully")
        """
        await self._http.delete(Routes.end_user(end_user_id))

    async def mint_token(
        self,
        subject_id: str,
        *,
        ttl_seconds: Optional[int] = None,
        supervised: bool = False,
    ) -> MintEndUserTokenResponse:
        """
        Mint a scoped JWT for an end user.

        Called with service-user credentials. The returned token has the end user
        as its subject and can be handed to an agent acting on that user's behalf --
        e.g. to call the id-less persona prepare route
        (``client.v1.persona.prepare_for_own_agent()``).

        The subject must be an end user belonging to the calling service user;
        otherwise the server responds 404 (unknown) or 403 (wrong tenant). Minting
        must also be enabled server-side, or the call returns 503.

        Args:
            subject_id: End user ID the token represents
            ttl_seconds: Optional token lifetime; server default applies if omitted
            supervised: The caller will rotate the token out of band. A supervised
                token is barred from ``refresh_own_token``, so the agent cannot
                extend a lifetime its supervisor cannot end. Hand it to
                ``MagickMind.from_token(..., refresh=False)``.

        Returns:
            MintEndUserTokenResponse with the token, its expiry, and token type
        """
        request = MintEndUserTokenRequest(
            subject_id=subject_id,
            ttl_seconds=ttl_seconds,
            supervised=supervised,
        )
        try:
            response = await self._http.post(
                Routes.END_USER_TOKENS,
                json=request.model_dump(exclude_none=True, exclude_defaults=True),
            )
        except MagickMindError as exc:
            hints = {
                400: (
                    "hint: ttl_seconds must be greater than zero and within the "
                    "server's maximum"
                ),
                403: (
                    f"hint: subject_id must be an end user owned by the calling "
                    f"service user; {subject_id!r} is in another tenant"
                ),
                404: (
                    f"hint: subject_id must be an end user owned by the calling "
                    f"service user; {subject_id!r} is unknown"
                ),
                503: "hint: end-user token minting is not configured on this server",
            }
            hint_by_status(exc, hints)
        return MintEndUserTokenResponse.model_validate(response)

    async def refresh_own_token(
        self, *, ttl_seconds: Optional[int] = None
    ) -> MintEndUserTokenResponse:
        """
        Exchange the presented end-user JWT for a fresh one (end-user JWT).

        This is rotation, not exchange: the presented token is revoked as the
        new one is issued, so the caller must switch to the returned token at
        once. :class:`~magick_mind.auth.EndUserTokenAuth` does this
        automatically; call this directly only when managing the credential
        by hand.

        Args:
            ttl_seconds: Lifetime of the new token; server default if omitted

        Raises:
            MagickMindError: 401 if the token is expired or revoked, 403 if it
                is supervised (rotation belongs to the supervisor), 400 if
                ``ttl_seconds`` exceeds the server cap
        """
        request = RefreshEndUserTokenRequest(ttl_seconds=ttl_seconds)
        try:
            response = await self._http.post(
                Routes.END_USER_TOKENS_REFRESH,
                json=request.model_dump(exclude_none=True),
            )
        except MagickMindError as exc:
            hints = {
                400: "hint: ttl_seconds must be within the server's maximum",
                401: "hint: the presented end-user token is expired or revoked",
                403: (
                    "hint: a supervised token cannot refresh itself; its "
                    "supervisor mints replacements"
                ),
            }
            hint_by_status(exc, hints)
        return MintEndUserTokenResponse.model_validate(response)

    async def revoke_own_token(
        self, *, disconnect: Optional[bool] = None
    ) -> RevokeEndUserTokenResponse:
        """
        Revoke the calling agent's tokens (end-user JWT).

        Args:
            disconnect: Also drop the agent's live realtime connections;
                server default is true
        """
        request = RevokeEndUserTokenRequest(disconnect=disconnect)
        response = await self._http.post(
            Routes.END_USER_TOKENS_REVOKE,
            json=request.model_dump(exclude_none=True),
        )
        return RevokeEndUserTokenResponse.model_validate(response)
