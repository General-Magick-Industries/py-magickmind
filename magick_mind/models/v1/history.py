"""
History models for Magick Mind SDK v1 API.

Mirrors Bifrost's /v1/mindspaces/messages endpoint response.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatHistoryMessage(BaseModel):
    """
    Individual chat history message from Bifrost.

    Maps to ChatHistory from Xavier's chat_history_service.proto.
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
    artifact_ids: Optional[list[str]] = Field(
        None, description="Artifact IDs attached to this message"
    )
    created_at: Optional[str] = Field(
        None, alias="create_at", description="Creation timestamp (RFC3339)"
    )
    updated_at: Optional[str] = Field(
        None, alias="update_at", description="Update timestamp (RFC3339)"
    )


class HistoryResponse(BaseModel):
    """
    Response from Bifrost's /v1/mindspaces/messages endpoint.

    Includes chat histories and pagination cursors.
    Three modes:
    - Latest: Get most recent messages (returns last_id)
    - Forward: Get messages after a point (returns next_after_id, has_more)
    - Backward: Get messages before a point (returns next_before_id, has_older)
    """

    chat_histories: list[ChatHistoryMessage] = Field(
        default_factory=list, description="List of chat messages"
    )

    # Cursor fields (populated based on query mode)
    last_id: Optional[str] = Field(
        default=None, description="Last message ID (for latest mode)"
    )
    next_after_id: Optional[str] = Field(
        default=None, description="Cursor for forward pagination"
    )
    next_before_id: Optional[str] = Field(
        default=None, description="Cursor for backward pagination"
    )
    has_more: bool = Field(
        default=False, description="True if more messages exist forward"
    )
    has_older: bool = Field(
        default=False, description="True if more messages exist backward"
    )
