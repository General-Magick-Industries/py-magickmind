"""Tests for V1 chat models."""

import pytest
from pydantic import ValidationError

from magick_mind.models.v1.chat import ChatPayload, ChatSendRequest, ChatSendResponse


class TestChatSendRequest:
    """Tests for ChatSendRequest model."""

    def test_valid_request_with_required_fields(self):
        """Test ChatSendRequest validates with all required fields."""
        request = ChatSendRequest(
            api_key="sk-test-key",
            mindspace_id="mind-123",
            message="Hello, world!",
            sender_id="user-456",
        )

        assert request.api_key == "sk-test-key"
        assert request.mindspace_id == "mind-123"
        assert request.message == "Hello, world!"
        assert request.sender_id == "user-456"
        assert request.reply_to_message_id is None
        assert request.fast_brain_model_id is None
        assert request.model_ids is None
        assert request.compute_power is None

    def test_valid_request_with_optional_fields(self):
        """Test ChatSendRequest validates with optional fields."""
        request = ChatSendRequest(
            api_key="sk-test-key",
            mindspace_id="mind-123",
            message="Hello!",
            sender_id="user-456",
            reply_to_message_id="msg-789",
            fast_brain_model_id="openrouter/meta-llama/llama-4-maverick",
            model_ids=["model-1", "model-2"],
            compute_power=100,
        )

        assert request.reply_to_message_id == "msg-789"
        assert request.fast_brain_model_id == "openrouter/meta-llama/llama-4-maverick"
        assert request.model_ids == ["model-1", "model-2"]
        assert request.compute_power == 100

    def test_missing_required_field_raises_validation_error(self):
        """Test ChatSendRequest raises ValidationError when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSendRequest(api_key="sk-test")

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "mindspace_id" in error_fields
        assert "message" in error_fields
        assert "sender_id" in error_fields

    def test_model_dump_excludes_none(self):
        """Test model_dump excludes None values when exclude_none=True."""
        request = ChatSendRequest(
            api_key="sk-test",
            mindspace_id="mind-123",
            message="Hello",
            sender_id="user-456",
        )

        dumped = request.model_dump(exclude_none=True)
        assert "api_key" in dumped
        assert "reply_to_message_id" not in dumped
        assert "fast_brain_model_id" not in dumped


class TestChatPayload:
    """Tests for ChatPayload model."""

    def test_valid_chat_payload(self):
        """Test ChatPayload validates correctly."""
        payload = ChatPayload(
            message_id="msg-789",
            task_id="task-123",
            content="Hello! How can I help you?",
            reply_to=None,
        )

        assert payload.message_id == "msg-789"
        assert payload.task_id == "task-123"
        assert payload.content == "Hello! How can I help you?"
        assert payload.reply_to is None

    def test_chat_payload_with_reply_to(self):
        """Test ChatPayload with reply_to set."""
        payload = ChatPayload(
            message_id="msg-790",
            task_id="task-124",
            content="This is a reply",
            reply_to="msg-789",
        )

        assert payload.reply_to == "msg-789"


class TestChatSendResponse:
    """Tests for ChatSendResponse model."""

    def test_valid_response_parsing(self):
        """Test ChatSendResponse parses bifrost API response."""
        response_data = {
            "success": True,
            "message": "Chat request processed successfully",
            "content": {
                "message_id": "msg-789",
                "task_id": "task-123",
                "content": "Hello! How can I help you?",
                "reply_to": None,
            },
        }

        response = ChatSendResponse.model_validate(response_data)

        assert response.success is True
        assert response.message == "Chat request processed successfully"
        assert response.content is not None
        assert response.content.message_id == "msg-789"
        assert response.content.task_id == "task-123"
        assert response.content.content == "Hello! How can I help you?"
        assert response.content.reply_to is None

    def test_response_without_content(self):
        """Test ChatSendResponse handles missing content (error case)."""
        response_data = {
            "success": False,
            "message": "Invalid API key",
        }

        response = ChatSendResponse.model_validate(response_data)

        assert response.success is False
        assert response.message == "Invalid API key"
        assert response.content is None

    def test_response_with_reply_to(self):
        """Test ChatSendResponse with reply_to field."""
        response_data = {
            "success": True,
            "message": "Chat request processed successfully",
            "content": {
                "message_id": "msg-790",
                "task_id": "task-124",
                "content": "This is a reply",
                "reply_to": "msg-789",
            },
        }

        response = ChatSendResponse.model_validate(response_data)
        assert response.content.reply_to == "msg-789"
