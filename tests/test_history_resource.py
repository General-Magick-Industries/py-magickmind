"""Tests for history resource."""

import pytest
from unittest.mock import Mock, patch

from magick_mind import MagickMind
from magick_mind.models.v1.history import HistoryResponse
from magick_mind.resources.v1.history import HistoryResourceV1


class TestHistoryResourceV1:
    """Tests for HistoryResourceV1."""

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        return Mock()

    @pytest.fixture
    def history_resource(self, mock_http_client):
        """Create HistoryResourceV1 instance with mock HTTP client."""
        return HistoryResourceV1(mock_http_client)

    def test_get_messages_latest(self, history_resource, mock_http_client):
        """Test getting latest messages."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "chat_histories": [
                {
                    "id": "msg-1",
                    "mindspace_id": "mind-123",
                    "sent_by_user_id": "user-456",
                    "content": "Hello!",
                    "status": "sent",
                    "create_at": "2024-01-01T10:00:00Z",
                    "update_at": "2024-01-01T10:00:00Z",
                }
            ],
            "last_id": "msg-1",
        }
        mock_http_client.get.return_value = mock_response

        result = history_resource.get_messages(mindspace_id="mind-123", limit=50)

        assert isinstance(result, HistoryResponse)
        assert len(result.chat_histories) == 1
        assert result.chat_histories[0].id == "msg-1"
        assert result.last_id == "msg-1"
        assert result.next_after_id is None
        assert result.has_more is False

        # Verify API call
        mock_http_client.get.assert_called_once_with(
            "/v1/mindspaces/messages",
            params={"mindspace_id": "mind-123", "limit": 50},
        )

    def test_get_messages_forward_pagination(self, history_resource, mock_http_client):
        """Test forward pagination with after_id."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "chat_histories": [
                {
                    "id": "msg-2",
                    "mindspace_id": "mind-123",
                    "sent_by_user_id": "user-456",
                    "content": "World!",
                    "status": "sent",
                    "create_at": "2024-01-01T10:01:00Z",
                    "update_at": "2024-01-01T10:01:00Z",
                }
            ],
            "next_after_id": "msg-2",
            "has_more": True,
        }
        mock_http_client.get.return_value = mock_response

        result = history_resource.get_messages(
            mindspace_id="mind-123", after_id="msg-1", limit=50
        )

        assert len(result.chat_histories) == 1
        assert result.chat_histories[0].id == "msg-2"
        assert result.next_after_id == "msg-2"
        assert result.has_more is True
        assert result.last_id is None

        mock_http_client.get.assert_called_once_with(
            "/v1/mindspaces/messages",
            params={"mindspace_id": "mind-123", "after_id": "msg-1", "limit": 50},
        )

    def test_get_messages_backward_pagination(self, history_resource, mock_http_client):
        """Test backward pagination with before_id."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "chat_histories": [
                {
                    "id": "msg-0",
                    "mindspace_id": "mind-123",
                    "sent_by_user_id": "user-456",
                    "content": "First!",
                    "status": "sent",
                    "create_at": "2024-01-01T09:59:00Z",
                    "update_at": "2024-01-01T09:59:00Z",
                }
            ],
            "next_before_id": "msg-0",
            "has_older": True,
        }
        mock_http_client.get.return_value = mock_response

        result = history_resource.get_messages(
            mindspace_id="mind-123", before_id="msg-1", limit=50
        )

        assert len(result.chat_histories) == 1
        assert result.chat_histories[0].id == "msg-0"
        assert result.next_before_id == "msg-0"
        assert result.has_older is True

        mock_http_client.get.assert_called_once_with(
            "/v1/mindspaces/messages",
            params={"mindspace_id": "mind-123", "before_id": "msg-1", "limit": 50},
        )

    def test_get_messages_empty(self, history_resource, mock_http_client):
        """Test getting empty results."""
        mock_response = Mock()
        mock_response.json.return_value = {"chat_histories": []}
        mock_http_client.get.return_value = mock_response

        result = history_resource.get_messages(mindspace_id="mind-123")

        assert len(result.chat_histories) == 0
        assert result.last_id is None

    def test_get_messages_with_reply_to(self, history_resource, mock_http_client):
        """Test message with reply_to_message_id."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "chat_histories": [
                {
                    "id": "msg-2",
                    "mindspace_id": "mind-123",
                    "sent_by_user_id": "user-456",
                    "content": "Reply!",
                    "reply_to_message_id": "msg-1",
                    "status": "sent",
                    "create_at": "2024-01-01T10:01:00Z",
                    "update_at": "2024-01-01T10:01:00Z",
                }
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = history_resource.get_messages(mindspace_id="mind-123")

        assert result.chat_histories[0].reply_to_message_id == "msg-1"

    def test_get_messages_both_cursors_error(self, history_resource):
        """Test that providing both after_id and before_id raises error."""
        with pytest.raises(
            ValueError, match="Cannot specify both after_id and before_id"
        ):
            history_resource.get_messages(
                mindspace_id="mind-123",
                after_id="msg-1",
                before_id="msg-2",
            )

    def test_get_messages_with_artifacts(self, history_resource, mock_http_client):
        """Test message with artifact_ids (future-proofing)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "chat_histories": [
                {
                    "id": "msg-1",
                    "mindspace_id": "mind-123",
                    "sent_by_user_id": "user-456",
                    "content": "Check this file",
                    "status": "sent",
                    "artifact_ids": ["artifact-123", "artifact-456"],
                    "create_at": "2024-01-01T10:00:00Z",
                    "update_at": "2024-01-01T10:00:00Z",
                }
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = history_resource.get_messages(mindspace_id="mind-123")

        assert result.chat_histories[0].artifact_ids == ["artifact-123", "artifact-456"]

    def test_get_messages_default_limit(self, history_resource, mock_http_client):
        """Test default limit parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {"chat_histories": []}
        mock_http_client.get.return_value = mock_response

        history_resource.get_messages(mindspace_id="mind-123")

        # Check that default limit is 50
        call_args = mock_http_client.get.call_args
        assert call_args[1]["params"]["limit"] == 50


class TestHistoryResourceIntegration:
    """Integration tests for history resource with MagickMind client."""

    @patch("magick_mind.auth.email_password.EmailPasswordAuth._login")
    def test_client_history_access(self, mock_login):
        """Test client.v1.history is accessible."""
        mock_login.return_value = None

        client = MagickMind(
            base_url="https://test.com",
            email="test@example.com",
            password="password123",
        )

        assert isinstance(client.v1.history, HistoryResourceV1)
