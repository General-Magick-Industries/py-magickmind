"""V1 chat resource implementation."""

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.chat import (
    ChatSendRequest,
    ChatSendResponse,
    ConfigSchema,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes

if TYPE_CHECKING:
    pass


class ChatResourceV1(BaseResource):
    """
    Chat resource client for V1 API.

    Provides typed interface for sending chat messages to mindspaces.

    Example:
        response = await client.v1.chat.send(
            api_key="sk-...",
            mindspace_id="mind-123",
            message="Hello!",
            enduser_id="user-456",
            fast_model_id="gpt-4",
            smart_model_ids=["gpt-4"],
            compute_power=50,
        )
        print(response.content.content)  # AI response text
    """

    async def send(
        self,
        api_key: str,
        mindspace_id: str,
        message: str,
        enduser_id: str,
        fast_model_id: str = "",
        smart_model_ids: Optional[list[str]] = None,
        compute_power: int = 0,
        config: Optional[ConfigSchema] = None,
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
            fast_model_id: Model ID for fast brain
            smart_model_ids: Model IDs for smart brain
            compute_power: Compute power setting (0-100), defaults to 0
            config: Optional ConfigSchema override — if provided, used directly and
                the flat model params (fast_model_id, smart_model_ids, compute_power)
                are ignored. Useful for advanced callers who already have a ConfigSchema.
            reply_to_message_id: Optional ID of message being replied to
            additional_context: Optional additional context for the message
            artifact_ids: Optional list of artifact IDs to attach to message

        Returns:
            ChatSendResponse with AI-generated response

        Raises:
            ValidationError: If message is empty, mindspace_id invalid, or required fields missing
            ProblemDetailsException: If mindspace not found (404), permission denied (403),
                or server error (500+). Always includes request_id for support.
            RateLimitError: If API rate limit exceeded (429)
            AuthenticationError: If JWT token is invalid or expired (auto-refreshed transparently)

        Example:
            # Basic chat with flat params (preferred)
            response = await chat.send(
                api_key="sk-test",
                mindspace_id="mind-123",
                message="What's the weather?",
                enduser_id="user-456",
                fast_model_id="gpt-4",
                smart_model_ids=["gpt-4"],
            )

            # Chat with attached artifacts
            response = await chat.send(
                api_key="sk-test",
                mindspace_id="mind-123",
                message="Analyze these documents",
                enduser_id="user-456",
                fast_model_id="gpt-4",
                smart_model_ids=["gpt-4"],
                compute_power=80,
                artifact_ids=["art-123", "art-456"],
            )

            # Advanced: pass a pre-built ConfigSchema directly
            response = await chat.send(
                api_key="sk-test",
                mindspace_id="mind-123",
                message="Hello",
                enduser_id="user-456",
                config=ConfigSchema(fast_model_id="gpt-4", smart_model_ids=["gpt-4"]),
            )

            print(f"AI: {response.content.content}")
            print(f"Message ID: {response.content.message_id}")
        """
        # Resolve config: explicit override takes precedence over flat params
        resolved_config = config or ConfigSchema(
            fast_model_id=fast_model_id,
            smart_model_ids=smart_model_ids or [],
            compute_power=compute_power,
        )

        # Build and validate request
        request = ChatSendRequest(
            api_key=api_key,
            mindspace_id=mindspace_id,
            message=message,
            enduser_id=enduser_id,
            config=resolved_config,
            reply_to_message_id=reply_to_message_id,
            additional_context=additional_context,
            artifact_ids=artifact_ids,
        )

        # Make API call
        response = await self._http.post(
            Routes.CHAT, json=request.model_dump(exclude_none=True)
        )

        # Parse and validate response
        return ChatSendResponse.model_validate(response)
