"""Tests for V1 chat resource."""

import time
import pytest
from unittest.mock import Mock, patch
import httpx

from magick_mind import MagickMind
from magick_mind.models.v1.chat import ChatSendResponse
from magick_mind.resources.v1.chat import ChatResourceV1


class TestChatResourceV1:
    """Tests for ChatResourceV1."""

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        mock_client = Mock()
        return mock_client

    @pytest.fixture
    def chat_resource(self, mock_http_client):
        """Create ChatResourceV1 instance with mock HTTP client."""
        return ChatResourceV1(mock_http_client)

    def test_send_makes_correct_api_call(self, chat_resource, mock_http_client):
        """Test send() makes correct POST request to chat endpoint."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Chat request processed successfully",
            "content": {
                "message_id": "msg-789",
                "task_id": "task-123",
                "content": "Hello! How can I help you?",
                "reply_to": None,
            },
        }
        mock_http_client.post.return_value = mock_response

        # Make request
        response = chat_resource.send(
            api_key="sk-test",
            mindspace_id="mind-123",
            message="Hello!",
            enduser_id="user-456",
        )

        # Verify HTTP call
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == "/v1/magickmind/chat"

        # Verify request body
        request_body = call_args[1]["json"]
        assert request_body["api_key"] == "sk-test"
        assert request_body["mindspace_id"] == "mind-123"
        assert request_body["message"] == "Hello!"
        assert request_body["enduser_id"] == "user-456"

        # Verify response
        assert isinstance(response, ChatSendResponse)
        assert response.success is True
        assert response.content.message_id == "msg-789"
        assert response.content.content == "Hello! How can I help you?"

    def test_send_with_optional_parameters(self, chat_resource, mock_http_client):
        """Test send() includes optional parameters in request."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Chat request processed successfully",
            "content": {
                "message_id": "msg-790",
                "task_id": "task-124",
                "content": "Reply text",
                "reply_to": "msg-789",
            },
        }
        mock_http_client.post.return_value = mock_response

        response = chat_resource.send(
            api_key="sk-test",
            mindspace_id="mind-123",
            message="This is a reply",
            enduser_id="user-456",
            reply_to_message_id="msg-789",
            fast_brain_model_id="openrouter/meta-llama/llama-4-maverick",
            model_ids=["model-1", "model-2"],
            compute_power=100,
        )

        # Verify request includes optional fields
        request_body = mock_http_client.post.call_args[1]["json"]
        assert request_body["reply_to_message_id"] == "msg-789"
        assert (
            request_body["fast_brain_model_id"]
            == "openrouter/meta-llama/llama-4-maverick"
        )
        assert request_body["model_ids"] == ["model-1", "model-2"]
        assert request_body["compute_power"] == 100

        # Verify response has reply_to
        assert response.content.reply_to == "msg-789"

    def test_send_excludes_none_values(self, chat_resource, mock_http_client):
        """Test send() excludes None values from request body."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Chat request processed successfully",
            "content": {
                "message_id": "msg-789",
                "task_id": "task-123",
                "content": "Response",
                "reply_to": None,
            },
        }
        mock_http_client.post.return_value = mock_response

        chat_resource.send(
            api_key="sk-test",
            mindspace_id="mind-123",
            message="Hello",
            enduser_id="user-456",
        )

        # Verify request body doesn't include None values
        request_body = mock_http_client.post.call_args[1]["json"]
        assert "reply_to_message_id" not in request_body
        assert "fast_brain_model_id" not in request_body
        assert "model_ids" not in request_body
        assert "compute_power" not in request_body


class TestChatResourceIntegration:
    """Integration tests for chat resource with MagickMind client."""

    @patch("magick_mind.auth.EmailPasswordAuth._login")
    def test_client_chat_alias(self, mock_login):
        """Test client.chat is aliased to client.v1.chat."""
        # Mock authentication to do nothing (skip actual HTTP login)
        mock_login.return_value = None

        # Create client
        client = MagickMind(
            base_url="https://test.com",
            email="test@example.com",
            password="password123",
        )

        # Verify chat alias
        assert client.chat is client.v1.chat
        assert isinstance(client.chat, ChatResourceV1)

    @patch("magick_mind.http.HTTPClient.post")
    @patch("magick_mind.auth.EmailPasswordAuth._login")
    def test_end_to_end_chat_send(self, mock_login, mock_post):
        """Test end-to-end flow of sending chat message."""
        # Mock authentication to do nothing (skip actual HTTP login)
        mock_login.return_value = None

        # Mock chat response
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "message": "Chat request processed successfully",
            "content": {
                "message_id": "msg-789",
                "task_id": "task-123",
                "content": "AI response here",
                "reply_to": None,
            },
        }
        mock_post.return_value = mock_response

        # Create client
        client = MagickMind(
            base_url="https://test.com",
            email="test@example.com",
            password="password123",
        )

        # Manually set auth token to bypass auth checks
        client.auth._access_token = "fake-token"
        client.auth._token_expires_at = time.time() + 3600

        # Send chat message via v1 resource
        response = client.v1.chat.send(
            api_key="sk-test",
            mindspace_id="mind-123",
            message="Hello AI!",
            enduser_id="user-456",
        )

        # Verify response
        assert response.success is True
        assert response.content.message_id == "msg-789"
        assert response.content.content == "AI response here"

        # Verify the same works via alias
        response2 = client.chat.send(
            api_key="sk-test",
            mindspace_id="mind-123",
            message="Hello again!",
            enduser_id="user-456",
        )
        assert response2.success is True
