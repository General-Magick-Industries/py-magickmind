"""V1 chat API models.

REST models only. Realtime event models live in magick_mind.realtime.events.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_serializer


class ConfigSchema(BaseModel):
    """Configuration for chat request."""

    fast_model_id: str = Field(..., description="Model ID for fast brain")
    smart_model_ids: list[str] = Field(..., description="Model IDs for smart brain")
    compute_power: int = Field(default=0, description="Compute power setting (0-100)")


class ChatSendRequest(BaseModel):
    """
    Request to send a chat message to a mindspace.

    Example:
        request = ChatSendRequest(
            api_key="sk-...",
            mindspace_id="mind-123",
            message="Hello!",
            enduser_id="user-456",
            config=ConfigSchema(
                fast_model_id="gpt-4",
                smart_model_ids=["gpt-4"],
                compute_power=50,
            ),
        )
    """

    api_key: str = Field(..., description="API key for LLM access")
    mindspace_id: str = Field(..., description="Mindspace/chat conversation ID")
    message: str = Field(..., description="User message text to send")
    enduser_id: str = Field(..., description="End-user identifier")
    config: ConfigSchema = Field(..., description="Model configuration")
    reply_to_message_id: str | None = Field(
        default=None, description="ID of message being replied to"
    )
    additional_context: str | None = Field(
        default=None, description="Additional context for the message"
    )
    artifact_ids: list[str] | None = Field(
        default=None, description="List of artifact IDs to attach to message"
    )

    @field_serializer("artifact_ids")
    def serialize_artifact_ids(self, v: list[str] | None) -> list[str]:
        """API requires this field; default to empty list if not provided."""
        return v or []


# ---------------------------------------------------------------------------
# REST response models (Bifrost /v1/chat/magickmind)
# ---------------------------------------------------------------------------


class ChatAck(BaseModel):
    """
    REST acknowledgement payload from Bifrost POST /v1/chat/magickmind.

    Bifrost ChatSchema: { message_id, content, reply_to }

    The message_id is useful for registering reply anchors before the
    realtime event arrives via Centrifugo.

    NOTE: This does NOT contain the AI response text — that arrives via
    Centrifugo realtime as a WsEvent/ChatMessagePayload.
    """

    message_id: str | None = Field(None, description="Generated message ID")
    content: str | None = Field(None, description="Placeholder content field")
    reply_to: str | None = Field(
        default=None, description="ID of message being replied to"
    )


class ChatSendResponse(BaseModel):
    """
    Response from Bifrost POST /v1/chat/magickmind.

    This is an acknowledgement only. The actual AI response text arrives
    via Centrifugo realtime — subscribe via client.realtime and handle
    WsEvent events with type="chat_message".
    """

    content: ChatAck | None = Field(
        default=None, description="REST acknowledgement payload"
    )
