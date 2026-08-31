"""V1 episode resource implementation."""

from __future__ import annotations

from typing import Optional

from magick_mind.exceptions import MagickMindError, hint_by_status
from magick_mind.models.v1.episode import (
    EndUserProcessEpisodeRequest,
    ListEpisodesByDateRangeResponse,
    ProcessEpisodeRequest,
    ProcessEpisodeResponse,
    SearchEpisodesResponse,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes

_OWN_ROUTE_401_HINT = (
    "hint: this route needs a valid, unrevoked end-user JWT; with service-user "
    "credentials use the non-_own method with agent_id=..."
)


class EpisodeResourceV1(BaseResource):
    """
    Episode resource client for V1 API.

    Writes to and reads from an agent's episodic memory. Every operation has
    two routes, chosen by which credential the client holds:

    - :meth:`process` / :meth:`search` / :meth:`list_range` -- service-user
      credentials, memory owner named by ``agent_id``.
    - :meth:`process_own` / :meth:`search_own` / :meth:`list_range_own` --
      the agent's own end-user JWT, where the owner is the token subject and
      no ``agent_id`` is sent.

    Reads answer different questions: :meth:`search` ranks by relevance and
    cannot filter on time, so a question about *when* goes to
    :meth:`list_range`, which returns an inclusive date window newest first.

    Ingest both sides of a conversation: the inbound message and the agent's
    own reply. Capturing only inbound messages stores half the conversation.

    Callers generally want ingest to be best-effort -- a memory outage should
    not stop an agent from replying -- so wrap these calls in a handler that
    logs and continues rather than propagating.

    Example:
        await client.v1.episode.process(
            magickspace_id="ms-1",
            sender_id="eu-1",
            message="hello",
            message_id="msg-1",
            agent_id="agent-1",
        )
    """

    async def process(
        self,
        *,
        agent_id: str,
        magickspace_id: str,
        sender_id: str,
        message: str,
        message_id: str,
        display_name: Optional[str] = None,
        is_group: bool = False,
        skip_persona: bool = False,
        client_message_id: Optional[str] = None,
    ) -> ProcessEpisodeResponse:
        """
        Ingest a message into an agent's episodic memory (service-user path).

        Args:
            agent_id: Memory owner. Required -- a write always needs an owner, and
                no credential reaching this route supplies one implicitly. Use
                :meth:`process_own` when the agent is the token subject.
            magickspace_id: Magickspace the message belongs to
            sender_id: Who sent the message; must be a participant of the
                magickspace and reference a readable end user
            message: Message text
            message_id: Caller-supplied message ID
            display_name: Sender display name; the server falls back to the end
                user's own name when omitted
            is_group: Whether the message came from a group conversation
            skip_persona: Skip persona resolution when building the episode
            client_message_id: Idempotency key, stable across retries and unique
                per (magickspace, agent); a reused key is deduplicated

        Returns:
            ProcessEpisodeResponse indicating whether the message was processed

        Raises:
            MagickMindError: 400 if agent_id is empty, 401 with an end-user JWT,
                403 if the sender is not a participant or the agent is not
                readable, 404 if the magickspace does not exist
        """
        request = ProcessEpisodeRequest(
            agent_id=agent_id,
            magickspace_id=magickspace_id,
            sender_id=sender_id,
            message=message,
            message_id=message_id,
            display_name=display_name,
            is_group=is_group,
            skip_persona=skip_persona,
            client_message_id=client_message_id,
        )
        try:
            response = await self._http.post(
                Routes.EPISODES_PROCESS,
                json=request.model_dump(exclude_none=True),
            )
        except MagickMindError as exc:
            hints = {
                400: "hint: agent_id must be a non-empty agent id on this route",
                403: (
                    "hint: the sender must be a participant of this magickspace, "
                    "and agent_id must be visible to these credentials; holding an "
                    "end-user JWT, use process_own()"
                ),
                404: "hint: magickspace not found",
                401: (
                    "hint: this route needs service-user credentials; an end-user "
                    "JWT is signed differently and fails verification here -- use "
                    "process_own() with that token"
                ),
            }
            hint_by_status(exc, hints)
        return ProcessEpisodeResponse.model_validate(response)

    async def process_own(
        self,
        *,
        magickspace_id: str,
        sender_id: str,
        message: str,
        message_id: str,
        display_name: Optional[str] = None,
        is_group: bool = False,
        skip_persona: bool = False,
        client_message_id: Optional[str] = None,
    ) -> ProcessEpisodeResponse:
        """
        Ingest a message into the calling agent's episodic memory (end-user JWT).

        The agent is the token subject, so no ``agent_id`` is sent. Use
        :meth:`process` when calling with service-user credentials on behalf of
        a named agent.

        Args:
            magickspace_id: Magickspace the message belongs to
            sender_id: Who sent the message; must be a participant of the
                magickspace and reference a readable end user
            message: Message text
            message_id: Caller-supplied message ID
            display_name: Sender display name; the server falls back to the end
                user's own name when omitted
            is_group: Whether the message came from a group conversation
            skip_persona: Skip persona resolution when building the episode
            client_message_id: Idempotency key, stable across retries and unique
                per (magickspace, agent); a reused key is deduplicated

        Returns:
            ProcessEpisodeResponse indicating whether the message was processed

        Raises:
            MagickMindError: 401 with service-user credentials or a revoked
                token, 403 if the sender is not a participant, 404 if the
                magickspace does not exist
        """
        request = EndUserProcessEpisodeRequest(
            magickspace_id=magickspace_id,
            sender_id=sender_id,
            message=message,
            message_id=message_id,
            display_name=display_name,
            is_group=is_group,
            skip_persona=skip_persona,
            client_message_id=client_message_id,
        )
        try:
            response = await self._http.post(
                Routes.EPISODES_PROCESS_OWN,
                json=request.model_dump(exclude_none=True),
            )
        except MagickMindError as exc:
            hints = {
                401: (
                    "hint: this route needs a valid, unrevoked end-user JWT; with "
                    "service-user credentials use process(agent_id=...)"
                ),
                403: (
                    "hint: the sender must be a participant of this magickspace "
                    "and reference a readable end user"
                ),
                404: "hint: magickspace not found",
            }
            hint_by_status(exc, hints)
        return ProcessEpisodeResponse.model_validate(response)

    async def search(
        self,
        query: str,
        *,
        agent_id: Optional[str] = None,
        magickspace_id: Optional[str] = None,
        magickspace_ids: Optional[list[str]] = None,
        user_id: Optional[str] = None,
        participant_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> SearchEpisodesResponse:
        """
        Search episodic memory by relevance (service-user path).

        Args:
            query: Free-text query
            agent_id: Memory lens -- an agent's id, ``"__neutral__"`` for the
                space's unowned memory, or omitted for every owner
            magickspace_id: Scope to one magickspace; omitted = user-wide
            magickspace_ids: Scope to several magickspaces
            user_id: Restrict to memories involving this user
            participant_id: Restrict to memories involving this participant
            limit: Maximum episodes to fold into the result

        Returns:
            SearchEpisodesResponse whose ``memory_content`` is prompt-ready text
        """
        params = _search_params(
            query,
            magickspace_id=magickspace_id,
            magickspace_ids=magickspace_ids,
            user_id=user_id,
            participant_id=participant_id,
            limit=limit,
        )
        if agent_id is not None:
            params["agent_id"] = agent_id
        response = await self._http.get(Routes.EPISODES_SEARCH, params=params)
        return SearchEpisodesResponse.model_validate(response)

    async def search_own(
        self,
        query: str,
        *,
        magickspace_id: Optional[str] = None,
        magickspace_ids: Optional[list[str]] = None,
        user_id: Optional[str] = None,
        participant_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> SearchEpisodesResponse:
        """
        Search the calling agent's episodic memory by relevance (end-user JWT).

        The lens is fixed to the token subject, so there is no ``agent_id``.
        See :meth:`search` for the other parameters.
        """
        params = _search_params(
            query,
            magickspace_id=magickspace_id,
            magickspace_ids=magickspace_ids,
            user_id=user_id,
            participant_id=participant_id,
            limit=limit,
        )
        try:
            response = await self._http.get(Routes.EPISODES_SEARCH_OWN, params=params)
        except MagickMindError as exc:
            hint_by_status(exc, {401: _OWN_ROUTE_401_HINT})
        return SearchEpisodesResponse.model_validate(response)

    async def list_range(
        self,
        *,
        date_start: str,
        date_end: str,
        agent_id: Optional[str] = None,
        magickspace_id: Optional[str] = None,
        participant_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> ListEpisodesByDateRangeResponse:
        """
        List episodes in a date window, newest first (service-user path).

        Use this rather than :meth:`search` when the question is about time:
        search ranks by relevance and cannot filter on it.

        Args:
            date_start: ``YYYY-MM-DD``, inclusive
            date_end: ``YYYY-MM-DD``, inclusive
            agent_id: Memory lens, as in :meth:`search`
            magickspace_id: Scope to one magickspace
            participant_id: Restrict to memories involving this participant
            limit: 1..200 (server default 50)
        """
        params = _range_params(
            date_start,
            date_end,
            magickspace_id=magickspace_id,
            participant_id=participant_id,
            limit=limit,
        )
        if agent_id is not None:
            params["agent_id"] = agent_id
        response = await self._http.get(Routes.EPISODES_RANGE, params=params)
        return ListEpisodesByDateRangeResponse.model_validate(response)

    async def list_range_own(
        self,
        *,
        date_start: str,
        date_end: str,
        magickspace_id: Optional[str] = None,
        participant_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> ListEpisodesByDateRangeResponse:
        """
        List the calling agent's episodes in a date window, newest first
        (end-user JWT). See :meth:`list_range`.
        """
        params = _range_params(
            date_start,
            date_end,
            magickspace_id=magickspace_id,
            participant_id=participant_id,
            limit=limit,
        )
        try:
            response = await self._http.get(Routes.EPISODES_RANGE_OWN, params=params)
        except MagickMindError as exc:
            hint_by_status(exc, {401: _OWN_ROUTE_401_HINT})
        return ListEpisodesByDateRangeResponse.model_validate(response)


def _search_params(
    query: str,
    *,
    magickspace_id: Optional[str],
    magickspace_ids: Optional[list[str]],
    user_id: Optional[str],
    participant_id: Optional[str],
    limit: Optional[int],
) -> dict[str, object]:
    params: dict[str, object] = {"q": query}
    if magickspace_id is not None:
        params["mindspace_id"] = magickspace_id
    if magickspace_ids:
        params["mindspace_ids"] = magickspace_ids
    if user_id is not None:
        params["user_id"] = user_id
    if participant_id is not None:
        params["participant_id"] = participant_id
    if limit is not None:
        params["limit"] = limit
    return params


def _range_params(
    date_start: str,
    date_end: str,
    *,
    magickspace_id: Optional[str],
    participant_id: Optional[str],
    limit: Optional[int],
) -> dict[str, object]:
    params: dict[str, object] = {"date_start": date_start, "date_end": date_end}
    if magickspace_id is not None:
        params["mindspace_id"] = magickspace_id
    if participant_id is not None:
        params["participant_id"] = participant_id
    if limit is not None:
        params["limit"] = limit
    return params
