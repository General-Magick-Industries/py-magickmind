"""Tests for V1 chat models."""

import pytest
from pydantic import ValidationError

from magick_mind.models.v1.chat import (
    ChatPayload,
    ChatSendRequest,
    ChatSendResponse,
    ConfigSchema,
)


class TestConfigSchema:
    """Tests for ConfigSchema model."""

    def test_valid_config_with_defaults(self):
        """Test ConfigSchema with default compute_power."""
        config = ConfigSchema(
            fast_model_id="gpt-4",
            smart_model_ids=["gpt-4", "gpt-4-turbo"],
        )

        assert config.fast_model_id == "gpt-4"
        assert config.smart_model_ids == ["gpt-4", "gpt-4-turbo"]
        assert config.compute_power == 0  # default

    def test_valid_config_with_compute_power(self):
        """Test ConfigSchema with explicit compute_power."""
        config = ConfigSchema(
            fast_model_id="gpt-4",
            smart_model_ids=["gpt-4"],
            compute_power=80,
        )

        assert config.compute_power == 80

    def test_missing_required_fields(self):
        """Test ConfigSchema raises ValidationError for missing fields."""
        with pytest.raises(ValidationError) as exc_info:
            ConfigSchema()

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "fast_model_id" in error_fields
        assert "smart_model_ids" in error_fields


class TestChatSendRequest:
    """Tests for ChatSendRequest model."""

    @pytest.fixture
    def valid_config(self):
        """Create a valid ConfigSchema for tests."""
        return ConfigSchema(
            fast_model_id="gpt-4",
            smart_model_ids=["gpt-4"],
            compute_power=50,
        )

    def test_valid_request_with_required_fields(self, valid_config):
        """Test ChatSendRequest validates with all required fields."""
        request = ChatSendRequest(
            api_key="sk-test-key",
            mindspace_id="mind-123",
            message="Hello, world!",
            enduser_id="user-456",
            config=valid_config,
        )

        assert request.api_key == "sk-test-key"
        assert request.mindspace_id == "mind-123"
        assert request.message == "Hello, world!"
        assert request.enduser_id == "user-456"
        assert request.config.fast_model_id == "gpt-4"
        assert request.reply_to_message_id is None
        assert request.additional_context is None
        assert request.artifact_ids is None

    def test_valid_request_with_optional_fields(self, valid_config):
        """Test ChatSendRequest validates with optional fields."""
        request = ChatSendRequest(
            api_key="sk-test-key",
            mindspace_id="mind-123",
            message="Hello!",
            enduser_id="user-456",
            config=valid_config,
            reply_to_message_id="msg-789",
            additional_context="Some context",
            artifact_ids=["art-123", "art-456"],
        )

        assert request.reply_to_message_id == "msg-789"
        assert request.additional_context == "Some context"
        assert request.artifact_ids == ["art-123", "art-456"]

    def test_missing_required_field_raises_validation_error(self):
        """Test ChatSendRequest raises ValidationError when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            ChatSendRequest(api_key="sk-test")

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "mindspace_id" in error_fields
        assert "message" in error_fields
        assert "enduser_id" in error_fields
        assert "config" in error_fields

    def test_model_dump_excludes_none(self, valid_config):
        """Test model_dump excludes None values when exclude_none=True."""
        request = ChatSendRequest(
            api_key="sk-test",
            mindspace_id="mind-123",
            message="Hello",
            enduser_id="user-456",
            config=valid_config,
        )

        dumped = request.model_dump(exclude_none=True)
        assert "api_key" in dumped
        assert "config" in dumped
        assert "reply_to_message_id" not in dumped
        assert "additional_context" not in dumped


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

    def test_chat_payload_with_relaxed_fields(self):
        """Test ChatPayload validates with optional fields as None (relaxed spec)."""
        payload = ChatPayload()

        assert payload.message_id is None
        assert payload.task_id is None
        assert payload.content is None


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
