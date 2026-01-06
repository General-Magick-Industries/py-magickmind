"""V1 chat API models.

These models mirror the bifrost API types for /v1/magickmind/chat endpoint.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from magick_mind.models.common import BaseResponse


class ChatSendRequest(BaseModel):
    """
    Request to send a chat message to a mindspace.

    Example:
        request = ChatSendRequest(
            api_key="sk-...",
            mindspace_id="mind-123",
            message="Hello!",
            enduser_id="user-456",
            fast_brain_model_id="openrouter/meta-llama/llama-4-maverick",
            model_ids=["model-1"],
            artifact_ids=["art-123", "art-456"],
        )
    """

    api_key: str = Field(..., description="API key for LLM access")
    mindspace_id: str = Field(..., description="Mindspace/chat conversation ID")
    message: str = Field(..., description="User message text to send")
    enduser_id: str = Field(..., description="End-user identifier")
    reply_to_message_id: Optional[str] = Field(
        default=None, description="ID of message being replied to"
    )
    fast_brain_model_id: str = Field(
        ...,
        description="Model ID for fast brain (e.g., 'openrouter/meta-llama/llama-4-maverick')",
    )
    model_ids: list[str] = Field(..., description="List of model IDs to use")
    artifact_ids: Optional[list[str]] = Field(
        default=None, description="List of artifact IDs to attach to message"
    )
    compute_power: Optional[int] = Field(
        default=None, description="Compute power setting"
    )

    # =========================================================================
    # Serializers: Transform None → default values for API contract compliance
    # SDK users can omit these fields, but API expects them in the payload
    # =========================================================================

    @field_serializer("artifact_ids")
    def serialize_artifact_ids(self, v: list[str] | None) -> list[str]:
        """API requires this field; default to empty list if not provided."""
        return v or []

    @field_serializer("compute_power")
    def serialize_compute_power(self, v: int | None) -> int:
        """API requires this field; default to 0 if not provided."""
        return v or 0


class ChatPayload(BaseModel):
    """
    Chat response payload schema.

    Flexible data container for chat response with message metadata.
    Can be extended to support various response formats.
    """

    message_id: str = Field(..., description="Generated message ID")
    task_id: str = Field(..., description="Associated task ID")
    content: str = Field(..., description="AI response text")
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
