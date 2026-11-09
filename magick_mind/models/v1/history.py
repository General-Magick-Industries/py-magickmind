"""
History models for Magick Mind SDK v1 API.

Mirrors the /v1/magickspaces/messages endpoint response.
"""

from typing import ClassVar, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from magick_mind.models.common import Cursors, PageInfo
from magick_mind.models.v1.space_type import MindSpaceType, space_type_or_none


class ChatHistoryMessage(BaseModel):
    """
    Individual chat history message from the API.

    Maps to ChatHistoryItem from the magickmind.api.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, description="Message ID")
    mindspace_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("magickspace_id", "mindspace_id"),
        description="Magickspace this message belongs to",
    )
    sent_by_user_id: Optional[str] = Field(
        None, description="User who sent the message"
    )
    sent_by_user_name: Optional[str] = Field(
        None, description="Sender display name, joined best-effort"
    )
    magickspace_type: Optional[MindSpaceType] = Field(
        default=None, description="PRIVATE or GROUP of the containing space"
    )
    content: Optional[str] = Field(default=None, description="Message content/text")
    reply_to_message_id: Optional[str] = Field(
        default=None, description="ID of message being replied to"
    )
    artifact_ids: list[str] = Field(default_factory=list)
    message_type: Optional[str] = Field(
        default=None, description="TEXT, TOOL_*, SIGNAL_*"
    )
    client_message_id: Optional[str] = Field(
        None, description="Sender's idempotency key"
    )
    status: Optional[str] = Field(default=None, description="Message status")

    @field_validator("artifact_ids", mode="before")
    @classmethod
    def _coerce_null_list(cls, v: object) -> object:
        return v if v is not None else []

    @field_validator("magickspace_type", mode="before")
    @classmethod
    def _normalize_type(cls, v: object) -> object:
        return space_type_or_none(v)

    @property
    def magickspace_id(self) -> Optional[str]:
        """The space this message belongs to (``mindspace_id`` is the legacy name)."""
        return self.mindspace_id

    created_at: Optional[str] = Field(
        None, alias="create_at", description="Creation timestamp (RFC3339)"
    )
    updated_at: Optional[str] = Field(
        None, alias="update_at", description="Update timestamp (RFC3339)"
    )


class HistoryResponse(BaseModel):
    """
    Response from the /v1/magickspaces/messages endpoint.

    Uses standardized pagination format:
    {
        "data": [...],
        "paging": {
            "cursors": {"after": "...", "before": "..."},
            "has_more": true,
            "has_previous": false
        }
    }
    """

    data: list[ChatHistoryMessage] = Field(
        default_factory=list, description="List of chat messages"
    )
    paging: PageInfo = Field(
        default_factory=lambda: PageInfo(
            cursors=Cursors(after=None, before=None),
            has_more=False,
            has_previous=False,
        ),
        description="Pagination information",
    )

    # Computed convenience properties for backward compatibility
    @property
    def chat_histories(self) -> list[ChatHistoryMessage]:
        """Alias for data field (backward compatibility)."""
        return self.data

    @property
    def has_more(self) -> bool:
        """True if more messages exist forward."""
        return self.paging.has_more

    @property
    def has_older(self) -> bool:
        """True if more messages exist backward."""
        return self.paging.has_previous

    @property
    def next_after_id(self) -> Optional[str]:
        """Cursor for forward pagination."""
        return self.paging.cursors.after if self.paging.cursors else None

    @property
    def next_before_id(self) -> Optional[str]:
        """Cursor for backward pagination."""
        return self.paging.cursors.before if self.paging.cursors else None
