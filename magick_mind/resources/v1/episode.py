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
        magickspace_id: str,
        sender_id: str,
        message: str,
        message_id: str,
        *,
        agent_id: Optional[str] = None,
        display_name: str = "",
        is_group: bool = False,
        skip_persona: bool = False,
    ) -> ProcessEpisodeResponse:
        """
        Ingest a message into an agent's episodic memory (service-user path).

        Args:
            magickspace_id: Magickspace the message belongs to
            sender_id: Who sent the message
            message: Message text
            message_id: Caller-supplied message ID
            agent_id: Memory owner; omit only when the credential itself
                identifies the agent
            display_name: Optional sender display name
            is_group: Whether the message came from a group conversation
            skip_persona: Skip persona processing for this message

        Returns:
            ProcessEpisodeResponse indicating whether the message was processed
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
                403: (
                    "hint: agent_id is not visible to these credentials; holding "
                    "an end-user JWT, use process_own()"
                ),
            }
            if exc.status_code is not None and exc.status_code in hints:
                reraise_with_hint(exc, hints[exc.status_code])
            raise
        return ProcessEpisodeResponse.model_validate(response)

    async def process_own(
        self,
        magickspace_id: str,
        sender_id: str,
        message: str,
        message_id: str,
        *,
        display_name: str = "",
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
            sender_id: Who sent the message
            message: Message text
            message_id: Caller-supplied message ID
            display_name: Optional sender display name
            is_group: Whether the message came from a group conversation
            skip_persona: Skip persona processing for this message

        Returns:
            ProcessEpisodeResponse indicating whether the message was processed
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
                    "hint: this route needs an end-user JWT; with service-user "
                    "credentials use process(agent_id=...)"
                ),
                403: "hint: end-user token revoked or not permitted",
            }
            if exc.status_code is not None and exc.status_code in hints:
                reraise_with_hint(exc, hints[exc.status_code])
            raise
        return ProcessEpisodeResponse.model_validate(response)
