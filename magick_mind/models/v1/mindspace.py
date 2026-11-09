"""V1 mindspace API models.

These models mirror the API types for /v1/magickspaces endpoint.
"""

from __future__ import annotations

from typing import Any, ClassVar, Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from magick_mind.models.common import PageInfo
from magick_mind.models.v1.history import HistoryResponse


from magick_mind.models.v1.space_type import (
    MindSpaceType,
    normalize_space_type as _normalize_space_type,
    space_type_or_none,
)

# Vocabulary of the end-user send route. TOOL_* is tool-protocol traffic and
# SIGNAL_* marks an agent's turn lifecycle; neither is speech, and receivers
# dispatch on the type rather than parsing content.
MessageType = Literal[
    "TEXT",
    "VOICE_TRANSCRIPTION",
    "TOOL_CALL",
    "TOOL_RESULT",
    "TOOL_MANIFEST",
    "SIGNAL_START",
    "SIGNAL_END",
    "SIGNAL_ERROR",
]

SIGNAL_MESSAGE_TYPES: frozenset[str] = frozenset(
    {"SIGNAL_START", "SIGNAL_END", "SIGNAL_ERROR"}
)
CONTROL_MESSAGE_TYPES: frozenset[str] = frozenset(
    {"TOOL_CALL", "TOOL_RESULT", "TOOL_MANIFEST"}
)


def is_signal_message(message_type: Optional[str]) -> bool:
    """True for turn-lifecycle indicators (never persisted, never speech)."""
    return message_type is not None and message_type in SIGNAL_MESSAGE_TYPES


def is_control_message(message_type: Optional[str]) -> bool:
    """True for tool-protocol traffic that should not be read as a turn."""
    return message_type is not None and message_type in CONTROL_MESSAGE_TYPES


class MindSpace(BaseModel):
    """
    Mindspace schema model.

    Represents a mindspace container that can be private (single user)
    or group (multiple users), with attached corpus for knowledge.

    Example:
        {
            "id": "mind-123",
            "name": "Engineering Team",
            "description": "Team workspace",
            "project_id": "proj-456",
            "corpus_ids": ["corp-1", "corp-2"],
            "participant_ids": ["user-1", "user-2"],
            "type": "GROUP",
            "created_by": "user-1",
            "updated_by": "user-1",
            "created_at": "2025-12-16T09:00:00Z",
            "updated_at": "2025-12-16T09:00:00Z"
        }
    """

    id: str = Field(..., description="Mindspace ID")
    name: str = Field(..., description="Mindspace name")
    description: Optional[str] = Field(
        default=None, description="Mindspace description"
    )
    project_id: str = Field(..., description="Associated project ID")
    corpus_ids: list[str] = Field(
        default_factory=list,
        description="List of corpus IDs attached to this mindspace",
    )
    participant_ids: list[str] = Field(
        default_factory=list,
        description="List of participant IDs with access to this mindspace",
    )
    type: MindSpaceType = Field(..., description="Mindspace type: 'PRIVATE' or 'GROUP'")
    created_by: Optional[str] = Field(
        None, description="User ID who created the mindspace"
    )
    updated_by: Optional[str] = Field(
        None, description="User ID who last updated the mindspace"
    )
    created_at: Optional[str] = Field(
        default=None, description="Creation timestamp (RFC3339)"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp (RFC3339)"
    )

    @field_validator("corpus_ids", "participant_ids", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        """The API returns null for empty Go slices; coerce to []."""
        return v if v is not None else []

    @field_validator("type", mode="before")
    @classmethod
    def _normalize_type(cls, v: object) -> object:
        """Normalize proto enum names (MAGICKSPACE_TYPE_PRIVATE → PRIVATE)."""
        return _normalize_space_type(v)


class CreateMindSpaceRequest(BaseModel):
    """
    Request to create a new mindspace.
    """

    name: Optional[str] = Field(
        None, description="Mindspace name (Relaxed)", max_length=100
    )
    type: Optional[MindSpaceType] = Field(
        default=None, description="Mindspace type (Relaxed)"
    )
    description: Optional[str] = Field(
        default=None, description="Mindspace description", max_length=256
    )
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    corpus_ids: list[str] = Field(
        default_factory=list, description="List of corpus IDs to attach"
    )
    participant_ids: list[str] = Field(
        default_factory=list, description="List of participant IDs to grant access"
    )


class GetMindSpaceListResponse(BaseModel):
    """
    Response from listing mindspaces.

    Uses standardized pagination format: {data: [], paging: {}}.
    """

    data: list[MindSpace] = Field(
        default_factory=list, description="List of mindspaces"
    )
    paging: PageInfo = Field(..., description="Pagination information")

    @field_validator("data", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []

    @property
    def mindspaces(self) -> list[MindSpace]:
        """Alias for data field (backward compatibility)."""
        return self.data


class UpdateMindSpaceRequest(BaseModel):
    """
    Request to update an existing mindspace.
    """

    name: Optional[str] = Field(
        None, description="Mindspace name (Relaxed)", max_length=100
    )
    description: Optional[str] = Field(
        default=None, description="Mindspace description", max_length=256
    )
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    corpus_ids: list[str] = Field(
        default_factory=list, description="List of corpus IDs to attach"
    )
    participant_ids: list[str] = Field(
        default_factory=list, description="List of participant IDs to grant access"
    )


class AddMindSpaceUsersRequest(BaseModel):
    """
    Request to add participants to an existing mindspace.
    """

    participant_ids: list[str] = Field(
        ..., description="List of participant IDs to add to the mindspace"
    )


# Reuse HistoryResponse for messages endpoint since it's the same structure
MindspaceMessagesResponse = HistoryResponse


class ChatHistoryParams(BaseModel):
    """Parameters for chat history retrieval."""

    limit: Optional[int] = 20


class CorpusParams(BaseModel):
    """Parameters for corpus search."""

    query: str


class FetcherParams(BaseModel):
    """Parameters for Pelican episodic memory search."""

    query: str


class CorpusChunk(BaseModel):
    """A chunk of corpus content."""

    content: str


class ChatHistoryItem(BaseModel):
    """A single chat history message, as stored, returned from a send, and
    carried on the realtime fan-out."""

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

    id: str
    magickspace_id: str = Field(
        validation_alias=AliasChoices("magickspace_id", "mindspace_id")
    )
    sent_by_user_id: str
    sent_by_user_name: Optional[str] = Field(
        None, description="Sender display name, joined best-effort; never stored"
    )
    magickspace_type: Optional[MindSpaceType] = Field(
        None, description="PRIVATE or GROUP, stamped for agent-side gating"
    )
    content: str = ""
    reply_to_message_id: Optional[str] = None
    artifact_ids: list[str] = Field(default_factory=list)
    status: str = ""
    message_type: str = ""
    client_message_id: Optional[str] = None
    deduplicated: bool = Field(
        False,
        description=(
            "Set on a send that reused a client_message_id: this is the ORIGINAL "
            "message and the new content was discarded"
        ),
    )
    create_at: Optional[str] = None
    update_at: Optional[str] = None

    @field_validator("artifact_ids", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []

    @field_validator("magickspace_type", mode="before")
    @classmethod
    def _normalize_type(cls, v: object) -> object:
        return space_type_or_none(v)

    @property
    def mindspace_id(self) -> str:
        """Deprecated alias for :attr:`magickspace_id`."""
        return self.magickspace_id


class SendMessageRequest(BaseModel):
    """Request for sending a message to a mindspace."""

    content: str = Field(..., description="Message content text")
    sender_id: str = Field(..., description="ID of the user sending the message")
    reply_to_message_id: Optional[str] = Field(
        None, description="ID of message being replied to"
    )
    artifact_ids: list[str] = Field(
        default_factory=list, description="Artifact IDs to attach"
    )
    message_type: str = Field(
        default="TEXT", description="Message type (default: TEXT)"
    )
    broadcast: bool = Field(
        True, description="Whether to broadcast via Centrifugo (default: true)"
    )
    record_neutral_memory: bool = Field(
        False, description="Also write to the space's unowned episodic memory"
    )
    client_message_id: Optional[str] = Field(
        None,
        description=(
            "Idempotency key, unique per (magickspace, sender); a reused key "
            "returns the original message and drops the new content"
        ),
    )


class EndUserSendMessageRequest(BaseModel):
    """Request for sending a message as the calling agent (end-user JWT).

    Carries no ``sender_id``: the sender is the token subject. ``tools`` and
    ``context`` ride the fan-out only and are never persisted.
    """

    content: Optional[str] = Field(
        None, description="Message text; may be omitted for attachment-only sends"
    )
    reply_to_message_id: Optional[str] = None
    artifact_ids: list[str] = Field(default_factory=list)
    message_type: MessageType = "TEXT"
    broadcast: bool = True
    tools: Optional[list[dict[str, Any]]] = Field(
        None, description="The sender's live tool manifest for this turn (max 32)"
    )
    context: Optional[dict[str, str]] = Field(
        None, description="Per-turn key/value context replayed into the agent prompt"
    )


class CorpusInfo(BaseModel):
    """One entry of the corpus catalog a space's conversations can draw from."""

    id: str
    name: str = ""
    description: str = ""


class ContextPrepareResponse(BaseModel):
    """Response from composable context retrieval."""

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

    magickspace_id: str = Field(
        validation_alias=AliasChoices("magickspace_id", "mindspace_id")
    )
    magickspace_type: Optional[MindSpaceType] = None
    participant_id: str
    chat_history: list[ChatHistoryItem] = Field(default_factory=list)
    corpus: list[CorpusChunk] = Field(default_factory=list)
    corpora: list[CorpusInfo] = Field(
        default_factory=list,
        description="Catalog of the space's bound corpora, queryable by id",
    )
    fetcher: str = ""

    @field_validator("chat_history", "corpus", "corpora", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []

    @field_validator("magickspace_type", mode="before")
    @classmethod
    def _normalize_type(cls, v: object) -> object:
        return space_type_or_none(v)

    @property
    def mindspace_id(self) -> str:
        """Deprecated alias for :attr:`magickspace_id`."""
        return self.magickspace_id


class LivekitTokenResponse(BaseModel):
    """Response containing a LiveKit access token."""

    token: str
    url: str


class LivekitJoinResponse(BaseModel):
    """Response from signalling agents to join LiveKit room."""

    signaled: list[str] = Field(default_factory=list)

    @field_validator("signaled", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []
