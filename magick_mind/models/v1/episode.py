"""V1 Episode API models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProcessEpisodeRequest(BaseModel):
    """Request to ingest a message into an agent's episodic memory.

    Service-user path. ``agent_id`` names the memory owner; on the end-user
    route the owner is the token subject and the field is omitted entirely
    (see :class:`EndUserProcessEpisodeRequest`).
    """

    agent_id: Optional[str] = Field(
        default=None, description="Memory owner; omit to use the token subject"
    )
    magickspace_id: str
    sender_id: str
    message: str
    message_id: str
    display_name: str = ""
    is_group: bool = False
    skip_persona: bool = False


class EndUserProcessEpisodeRequest(BaseModel):
    """Request to ingest a message into the calling agent's episodic memory.

    End-user-JWT path. Identical to :class:`ProcessEpisodeRequest` except that
    the owner comes from the token subject, so no ``agent_id`` is sent.
    """

    magickspace_id: str
    sender_id: str
    message: str
    message_id: str
    display_name: str = ""
    is_group: bool = False
    skip_persona: bool = False


class ProcessEpisodeResponse(BaseModel):
    """Response from an episode ingest."""

    message_processed: bool = False
