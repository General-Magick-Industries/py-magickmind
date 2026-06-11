"""V1 magickspace API models.

These models mirror the API types for /v1/magickspaces endpoint.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from magick_mind.models.common import PageInfo
from magick_mind.models.v1.history import HistoryResponse


# Type alias for magickspace type enum (uppercase to match apidog)
MagickSpaceType = Literal["PRIVATE", "GROUP"]

# The API returns proto enum .String() values with MINDSPACE_TYPE_ prefix.
# We normalize to short form for SDK consumers.
_TYPE_NORMALIZE: dict[str, MagickSpaceType] = {
    "PRIVATE": "PRIVATE",
    "GROUP": "GROUP",
    "MINDSPACE_TYPE_PRIVATE": "PRIVATE",
    "MINDSPACE_TYPE_GROUP": "GROUP",
}


class MagickSpace(BaseModel):
    """
    MagickSpace schema model.

    Represents a magickspace container that can be private (single user)
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

    id: str = Field(..., description="MagickSpace ID")
    name: str = Field(..., description="MagickSpace name")
    description: Optional[str] = Field(None, description="MagickSpace description")
    project_id: str = Field(..., description="Associated project ID")
    corpus_ids: list[str] = Field(
        default_factory=list,
        description="List of corpus IDs attached to this magickspace",
    )
    participant_ids: list[str] = Field(
        default_factory=list,
        description="List of participant IDs with access to this magickspace",
    )
    type: MagickSpaceType = Field(
        ..., description="MagickSpace type: 'PRIVATE' or 'GROUP'"
    )
    created_by: Optional[str] = Field(
        None, description="User ID who created the magickspace"
    )
    updated_by: Optional[str] = Field(
        None, description="User ID who last updated the magickspace"
    )
    created_at: Optional[str] = Field(None, description="Creation timestamp (RFC3339)")
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
        """Normalize proto enum names (MINDSPACE_TYPE_PRIVATE → PRIVATE)."""
        if isinstance(v, str) and v in _TYPE_NORMALIZE:
            return _TYPE_NORMALIZE[v]
        return v


class CreateMagickSpaceRequest(BaseModel):
    """
    Request to create a new magickspace.
    """

    name: Optional[str] = Field(
        None, description="MagickSpace name (Relaxed)", max_length=100
    )
    type: Optional[MagickSpaceType] = Field(
        None, description="MagickSpace type (Relaxed)"
    )
    description: Optional[str] = Field(
        default=None, description="MagickSpace description", max_length=256
    )
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    corpus_ids: list[str] = Field(
        default_factory=list, description="List of corpus IDs to attach"
    )
    participant_ids: list[str] = Field(
        default_factory=list, description="List of participant IDs to grant access"
    )


class GetMagickSpaceListResponse(BaseModel):
    """
    Response from listing magickspaces.

    Uses standardized pagination format: {data: [], paging: {}}.
    """

    data: list[MagickSpace] = Field(
        default_factory=list, description="List of magickspaces"
    )
    paging: PageInfo = Field(..., description="Pagination information")

    @field_validator("data", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []

    @property
    def magickspaces(self) -> list[MagickSpace]:
        """Alias for data field (backward compatibility)."""
        return self.data


class UpdateMagickSpaceRequest(BaseModel):
    """
    Request to update an existing magickspace.
    """

    name: Optional[str] = Field(
        None, description="MagickSpace name (Relaxed)", max_length=100
    )
    description: Optional[str] = Field(
        default=None, description="MagickSpace description", max_length=256
    )
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    corpus_ids: list[str] = Field(
        default_factory=list, description="List of corpus IDs to attach"
    )
    participant_ids: list[str] = Field(
        default_factory=list, description="List of participant IDs to grant access"
    )


class AddMagickSpaceUsersRequest(BaseModel):
    """
    Request to add participants to an existing magickspace.
    """

    participant_ids: list[str] = Field(
        ..., description="List of participant IDs to add to the magickspace"
    )


# Reuse HistoryResponse for messages endpoint since it's the same structure
MagickSpaceMessagesResponse = HistoryResponse


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
    """A single chat history message."""

    id: str
    magickspace_id: str
    sent_by_user_id: str
    content: str
    reply_to_message_id: Optional[str] = None
    status: str = ""
    message_type: str = ""
    create_at: Optional[str] = None
    update_at: Optional[str] = None


class SendMessageRequest(BaseModel):
    """Request for sending a message to a magickspace."""

    content: str = Field(..., description="Message content text")
    sender_id: str = Field(..., description="ID of the user sending the message")
    reply_to_message_id: Optional[str] = Field(
        None, description="ID of message being replied to"
    )
    artifact_ids: list[str] = Field(
        default_factory=list, description="Artifact IDs to attach"
    )
    message_type: str = Field("TEXT", description="Message type (default: TEXT)")
    broadcast: bool = Field(
        True, description="Whether to broadcast via Centrifugo (default: true)"
    )


class ContextPrepareResponse(BaseModel):
    """Response from composable context retrieval."""

    magickspace_id: str
    participant_id: str
    chat_history: list[ChatHistoryItem] = Field(default_factory=list)
    corpus: list[CorpusChunk] = Field(default_factory=list)
    fetcher: str = ""

    @field_validator("chat_history", "corpus", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []


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
