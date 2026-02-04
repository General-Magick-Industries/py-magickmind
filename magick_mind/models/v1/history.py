"""
History models for Magick Mind SDK v1 API.

Mirrors Bifrost's /v1/mindspaces/messages endpoint response.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from magick_mind.models.common import Cursors, PageInfo


class ChatHistoryMessage(BaseModel):
    """
    Individual chat history message from Bifrost.

    Maps to ChatHistoryItem from Bifrost's magickmind.api.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, description="Message ID")
    mindspace_id: Optional[str] = Field(
        None, description="Mindspace this message belongs to"
    )
    sent_by_user_id: Optional[str] = Field(
        None, description="User who sent the message"
    )
    content: Optional[str] = Field(None, description="Message content/text")
    reply_to_message_id: Optional[str] = Field(
        default=None, description="ID of message being replied to"
    )
    status: Optional[str] = Field(None, description="Message status")
    created_at: Optional[str] = Field(
        None, alias="create_at", description="Creation timestamp (RFC3339)"
    )
    updated_at: Optional[str] = Field(
        None, alias="update_at", description="Update timestamp (RFC3339)"
    )


class HistoryResponse(BaseModel):
    """
    Response from Bifrost's /v1/mindspaces/messages endpoint.

    Uses standardized Bifrost pagination format:
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
