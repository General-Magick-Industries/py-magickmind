"""Chat resource implementation (version-aware)."""

from typing import TYPE_CHECKING

from .base import BaseResource

if TYPE_CHECKING:
    from ..http import HTTPClient
    from ..models.v1.chat import ChatSendResponse as ChatSendResponseV1
    from ..models.v2.chat import ChatSendResponse as ChatSendResponseV2


class ChatResource(BaseResource):
    """
    Chat resource client.

    Handles chat message sending with version-aware request/response models.
    """

    def __init__(self, http_client: "HTTPClient", version: str = "v1"):
        """
        Initialize chat resource.

        Args:
            http_client: HTTP client for API requests
            version: API version to use ("v1", "v2", etc.)
        """
        super().__init__(http_client)
        self.version = version

    def send(self, api_key: str, message: str, chat_id: str, sender_id: str, **kwargs):
        """
        Send a chat message.

        Args:
            api_key: API key for LLM access
            message: User message to send
            chat_id: Chat conversation ID
            sender_id: User/sender identifier
            **kwargs: Version-specific parameters

        Returns:
            ChatSendResponse (v1 or v2 depending on version)

        Example (v1):
            response = client.v1.chat.send(
                api_key="sk-...",
                message="Hello!",
                chat_id="chat-123",
                sender_id="user-456"
            )
            print(response.text)

        Example (v2):
            response = client.v2.chat.send(
                api_key="sk-...",
                message="Hello!",
                chat_id="chat-123",
                sender_id="user-456",
                temperature=0.7,
                context={"topic": "weather"}
            )
            print(response.content[0].text)
        """
        if self.version == "v1":
            return self._send_v1(api_key, message, chat_id, sender_id, **kwargs)
        elif self.version == "v2":
            return self._send_v2(api_key, message, chat_id, sender_id, **kwargs)
        else:
            raise ValueError(f"Unsupported API version: {self.version}")

    def _send_v1(
        self, api_key: str, message: str, chat_id: str, sender_id: str, **kwargs
    ) -> "ChatSendResponseV1":
        """Send chat message using v1 API."""
        from ..models.v1.chat import ChatSendRequest, ChatSendResponse

        # Build request
        request = ChatSendRequest(
            api_key=api_key,
            message=message,
            chat_id=chat_id,
            sender_id=sender_id,
            fast_brain_id=kwargs.get(
                "fast_brain_id", "openrouter/meta-llama/llama-4-maverick"
            ),
        )

        # Make request
        response = self._http.post("/v1/magickmind/chat", json=request.model_dump())

        # Parse and validate response
        return ChatSendResponse.model_validate(response.json())

    def _send_v2(
        self, api_key: str, message: str, chat_id: str, sender_id: str, **kwargs
    ) -> "ChatSendResponseV2":
        """Send chat message using v2 API."""
        from ..models.v2.chat import ChatSendRequest, ChatSendResponse, ChatContent

        # Build request (v2 structure)
        request = ChatSendRequest(
            api_key=api_key,
            chat_id=chat_id,
            sender_id=sender_id,
            content=ChatContent(text=message),
            temperature=kwargs.get("temperature", 0.2),
            context=kwargs.get("context", {}),
            fast_brain_id=kwargs.get(
                "fast_brain_id", "openrouter/meta-llama/llama-4-maverick"
            ),
        )

        # Make request
        response = self._http.post("/v2/magickmind/chat", json=request.model_dump())

        # Parse and validate response
        return ChatSendResponse.model_validate(response.json())
