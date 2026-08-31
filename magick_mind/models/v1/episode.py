"""V1 Episode API models."""

from __future__ import annotations

from typing import Optional

from pydantic import AliasChoices, BaseModel, Field, field_validator


class ProcessEpisodeRequest(BaseModel):
    """Request to ingest a message into an agent's episodic memory.

    Service-user path. ``agent_id`` names the memory owner; on the end-user
    route the owner is the token subject and the field is omitted entirely
    (see :class:`EndUserProcessEpisodeRequest`).
    """

    agent_id: Optional[str] = Field(
        default=None,
        description=(
            "Memory owner. Required for a write on the service-user route: the "
            "server rejects both an absent and an empty agent_id (an empty one "
            "is the neutral read lens, never a write owner)."
        ),
    )
    magickspace_id: str
    sender_id: str
    message: str
    message_id: str
    display_name: Optional[str] = None
    is_group: bool = False
    skip_persona: bool = False
    client_message_id: Optional[str] = Field(
        default=None,
        description=(
            "Idempotency key, unique per (magickspace, agent) and stable across "
            "retries; a reused key is deduplicated rather than ingested twice"
        ),
    )


class EndUserProcessEpisodeRequest(BaseModel):
    """Request to ingest a message into the calling agent's episodic memory.

    End-user-JWT path. Identical to :class:`ProcessEpisodeRequest` except that
    the owner comes from the token subject, so no ``agent_id`` is sent.
    """

    magickspace_id: str
    sender_id: str
    message: str
    message_id: str
    display_name: Optional[str] = None
    is_group: bool = False
    skip_persona: bool = False
    client_message_id: Optional[str] = None


class ProcessEpisodeResponse(BaseModel):
    """Response from an episode ingest."""

    message_processed: bool
    deduplicated: bool = Field(
        default=False,
        description=(
            "The send was skipped as a duplicate of an earlier client_message_id; "
            "message_processed stays true"
        ),
    )


class Episode(BaseModel):
    """One episode of an agent's episodic memory."""

    id: str
    mindspace_id: str = Field(
        default="", validation_alias=AliasChoices("mindspace_id", "magickspace_id")
    )
    topic: str = ""
    subtopics: list[str] = Field(default_factory=list)
    summarized_conversation: str = ""
    what_worked: str = ""
    what_to_avoid: str = ""
    participant_ids: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)

    @field_validator("subtopics", "participant_ids", "entities", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []

    @property
    def magickspace_id(self) -> str:
        """The space this episode belongs to (``mindspace_id`` is the wire name)."""
        return self.mindspace_id


class SearchEpisodesResponse(BaseModel):
    """Relevance-ranked recall, rendered server-side as prompt-ready text."""

    memory_content: str = ""


class ListEpisodesByDateRangeResponse(BaseModel):
    """Episodes within an inclusive date window, newest first."""

    data: list[Episode] = Field(default_factory=list)

    @field_validator("data", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []
