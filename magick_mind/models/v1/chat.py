"""V1 chat API models.

These models mirror the bifrost API types for /v1/magickmind/chat endpoint.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from magick_mind.models.common import BaseResponse


class ConfigSchema(BaseModel):
    """
    Configuration for chat request.

    Contains model selection and compute settings.
    """

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
    reply_to_message_id: Optional[str] = Field(
        default=None, description="ID of message being replied to"
    )
    additional_context: Optional[str] = Field(
        default=None, description="Additional context for the message"
    )
    artifact_ids: Optional[list[str]] = Field(
        default=None, description="List of artifact IDs to attach to message"
    )

    # =========================================================================
    # Serializers: Transform None → default values for API contract compliance
    # SDK users can omit these fields, but API expects them in the payload
    # =========================================================================

    @field_serializer("artifact_ids")
    def serialize_artifact_ids(self, v: list[str] | None) -> list[str]:
        """API requires this field; default to empty list if not provided."""
        return v or []


class ChatPayload(BaseModel):
    """
    Chat response payload schema.

    Flexible data container for chat response with message metadata.
    Can be extended to support various response formats.
    """

    message_id: Optional[str] = Field(
        None, description="Generated message ID (Relaxed)"
    )
    task_id: Optional[str] = Field(None, description="Associated task ID (Relaxed)")
    content: Optional[str] = Field(None, description="AI response text (Relaxed)")
    reply_to: Optional[str] = Field(
        default=None, description="ID of message being replied to"
    )


class ChatSendResponse(BaseResponse):
    """
    Response from sending a chat message.

    Example:
        {
            "success": true,
            "message": "Chat request processed successfully",
            "content": {
                "message_id": "msg-789",
                "task_id": "task-123",
                "content": "Hello! How can I help you?",
                "reply_to": null
            }
        }
    """

    content: Optional[ChatPayload] = Field(
        default=None, description="Chat response payload"
    )
