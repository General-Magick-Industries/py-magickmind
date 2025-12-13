"""V1 chat resource implementation."""

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.chat import ChatSendRequest, ChatSendResponse
from magick_mind.resources.base import BaseResource

if TYPE_CHECKING:
    from magick_mind.http import HTTPClient


class ChatResourceV1(BaseResource):
    """
    Chat resource client for V1 API.

    Provides typed interface for sending chat messages to mindspaces.

    Example:
        response = client.v1.chat.send(
            api_key="sk-...",
            mindspace_id="mind-123",
            message="Hello!",
            sender_id="user-456"
        )
        print(response.content.content)  # AI response text
    """

    def send(
        self,
        api_key: str,
        mindspace_id: str,
        message: str,
        sender_id: str,
        reply_to_message_id: Optional[str] = None,
        fast_brain_model_id: Optional[str] = None,
        model_ids: Optional[list[str]] = None,
        compute_power: Optional[int] = None,
    ) -> ChatSendResponse:
        """
        Send a chat message to a mindspace and get AI response.

        Args:
            api_key: API key for LLM access
            mindspace_id: Mindspace/chat conversation ID
            message: User message text to send
            sender_id: End-user identifier
            reply_to_message_id: Optional ID of message being replied to
            fast_brain_model_id: Optional model override
            model_ids: Optional alternative model IDs
            compute_power: Optional compute power setting

        Returns:
            ChatSendResponse with AI-generated response

        Raises:
            HTTPError: If the API request fails
            ValidationError: If response doesn't match expected schema

        Example:
            response = chat.send(
                api_key="sk-test",
                mindspace_id="mind-123",
                message="What's the weather?",
                sender_id="user-456",
                fast_brain_model_id="openrouter/meta-llama/llama-4-maverick"
            )
            print(f"AI: {response.content.content}")
            print(f"Message ID: {response.content.message_id}")
        """
        # Build and validate request
        request = ChatSendRequest(
            api_key=api_key,
            mindspace_id=mindspace_id,
            message=message,
            sender_id=sender_id,
            reply_to_message_id=reply_to_message_id,
            fast_brain_model_id=fast_brain_model_id,
            model_ids=model_ids,
            compute_power=compute_power,
        )

        # Make API call
        response = self._http.post(
            "/v1/magickmind/chat", json=request.model_dump(exclude_none=True)
        )

        # Parse and validate response
        return ChatSendResponse.model_validate(response.json())
