"""v2 chat API models (hypothetical future version)."""

from typing import List, Literal
from pydantic import BaseModel, Field


class ChatContent(BaseModel):
    """Content block for v2 API."""
    type: Literal["text"] = "text"
    text: str


class ChatSendRequest(BaseModel):
    """
    Request to send a chat message (v2 API).
    
    V2 changes:
    - Message is now a 'content' object (supports future multimodal)
    - Added optional 'context' parameter
    - Added 'temperature' parameter
    
    Example:
        request = ChatSendRequest(
            api_key="sk-...",
            chat_id="chat-123",
            sender_id="user-456",
            content=ChatContent(text="Hello!"),
            temperature=0.7,
            context={"previous_topic": "weather"}
        )
    """
    api_key: str = Field(..., description="API key for LLM access")
    chat_id: str = Field(..., description="Chat conversation ID")
    sender_id: str = Field(..., description="User/sender identifier")
    content: ChatContent = Field(..., description="Message content")
    temperature: float = Field(default=0.2, description="Model temperature")
    context: dict = Field(default_factory=dict, description="Additional context")
    fast_brain_id: str = Field(
        default="openrouter/meta-llama/llama-4-maverick",
        description="Model to use for chat"
    )


class ChatSendResponse(BaseModel):
    """
    Response from sending a chat message (v2 API).
    
    V2 changes:
    - 'message_id' → 'id'
    - 'text' → 'content' (array of content blocks)
    - Added 'sources' array for citations
    
    Example:
        {
            "success": true,
            "message": "Chat sent successfully",
            "id": "msg-789",
            "role": "assistant",
            "content": [{"type": "text", "text": "Hello!"}],
            "sources": [...],
            "done": true
        }
    """
    success: bool = Field(..., description="Whether request succeeded")
    message: str = Field(..., description="Status message")
    id: str = Field(..., description="Generated message ID")
    role: Literal["assistant"] = "assistant"
    content: List[ChatContent] = Field(..., description="Response content blocks")
    sources: List[dict] = Field(default_factory=list, description="Citation sources")
    done: bool = Field(default=True, description="Whether response is complete")
