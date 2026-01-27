"""v1 chat API models."""

from pydantic import BaseModel, Field


class ChatSendRequest(BaseModel):
    """
    Request to send a chat message (v1 API).

    Example:
        request = ChatSendRequest(
            api_key="sk-...",
            message="Hello!",
            chat_id="chat-123",
            sender_id="user-456"
        )
    """

    api_key: str = Field(..., description="API key for LLM access")
    message: str = Field(..., description="User message to send")
    chat_id: str = Field(..., description="Chat conversation ID")
    sender_id: str = Field(..., description="User/sender identifier")
    fast_brain_id: str = Field(
        default="openrouter/meta-llama/llama-4-maverick",
        description="Model to use for chat",
    )


class ChatSendResponse(BaseModel):
    """
    Response from sending a chat message (v1 API).

    Example:
        {
            "success": true,
            "message": "Chat sent successfully",
            "message_id": "msg-789",
            "text": "Hello! How can I help you?",
            "done": true
        }
    """

    success: bool = Field(..., description="Whether request succeeded")
    message: str = Field(..., description="Status message")
    message_id: str = Field(..., description="Generated message ID")
    text: str = Field(..., description="AI response text")
    done: bool = Field(default=True, description="Whether response is complete")
