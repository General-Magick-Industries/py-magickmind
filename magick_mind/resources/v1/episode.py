"""V1 episode resource implementation."""

from __future__ import annotations

from typing import Optional

from magick_mind.exceptions import MagickMindError, reraise_with_hint
from magick_mind.models.v1.episode import (
    EndUserProcessEpisodeRequest,
    ProcessEpisodeRequest,
    ProcessEpisodeResponse,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes


class EpisodeResourceV1(BaseResource):
    """
    Episode resource client for V1 API.

    Ingests messages into an agent's episodic memory. Two routes, chosen by
    which credential the client holds:

    - :meth:`process` -- service-user credentials, memory owner named by
      ``agent_id`` in the body.
    - :meth:`process_own` -- the agent's own end-user JWT, where the owner is
      the token subject and no ``agent_id`` is sent.

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
            if exc.status_code is not None and exc.status_code in hints:
                reraise_with_hint(exc, hints[exc.status_code])
            raise
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
            if exc.status_code is not None and exc.status_code in hints:
                reraise_with_hint(exc, hints[exc.status_code])
            raise
        return ProcessEpisodeResponse.model_validate(response)
