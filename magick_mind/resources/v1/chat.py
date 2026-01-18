"""V1 chat resource implementation."""

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.chat import (
    ChatSendRequest,
    ChatSendResponse,
    ConfigSchema,
)
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
            enduser_id="user-456",
            config=ConfigSchema(
                fast_model_id="gpt-4",
                smart_model_ids=["gpt-4"],
                compute_power=50,
            ),
        )
        print(response.content.content)  # AI response text
    """

    def send(
        self,
        api_key: str,
        mindspace_id: str,
        message: str,
        enduser_id: str,
        config: ConfigSchema,
        reply_to_message_id: Optional[str] = None,
        additional_context: Optional[str] = None,
        artifact_ids: Optional[list[str]] = None,
    ) -> ChatSendResponse:
        """
        Send a chat message to a mindspace and get AI response.

        Args:
            api_key: API key for LLM access
            mindspace_id: Mindspace/chat conversation ID
            message: User message text to send
            enduser_id: End-user identifier
            config: Model configuration (fast_model_id, smart_model_ids, compute_power)
            reply_to_message_id: Optional ID of message being replied to
            additional_context: Optional additional context for the message
            artifact_ids: Optional list of artifact IDs to attach to message

        Returns:
            ChatSendResponse with AI-generated response

        Raises:
            HTTPError: If the API request fails
            ValidationError: If response doesn't match expected schema

        Example:
            # Basic chat with config
            response = chat.send(
                api_key="sk-test",
                mindspace_id="mind-123",
                message="What's the weather?",
                enduser_id="user-456",
                config=ConfigSchema(
                    fast_model_id="gpt-4",
                    smart_model_ids=["gpt-4"],
                ),
            )

            # Chat with attached artifacts
            response = chat.send(
                api_key="sk-test",
                mindspace_id="mind-123",
                message="Analyze these documents",
                enduser_id="user-456",
                config=ConfigSchema(
                    fast_model_id="gpt-4",
                    smart_model_ids=["gpt-4"],
                    compute_power=80,
                ),
                artifact_ids=["art-123", "art-456"],
            )

            print(f"AI: {response.content.content}")
            print(f"Message ID: {response.content.message_id}")
        """
        # Build and validate request
        request = ChatSendRequest(
            api_key=api_key,
            mindspace_id=mindspace_id,
            message=message,
            enduser_id=enduser_id,
            config=config,
            reply_to_message_id=reply_to_message_id,
            additional_context=additional_context,
            artifact_ids=artifact_ids,
        )

        # Make API call
        response = self._http.post(
            "/v1/magickmind/chat", json=request.model_dump(exclude_none=True)
        )

        # Parse and validate response
        return ChatSendResponse.model_validate(response.json())
