"""Tests for V1 mindspace resource."""

import time

import pytest
from unittest.mock import Mock, patch

from magick_mind import MagickMind
from magick_mind.models.v1.mindspace import (
    GetMindSpaceListResponse,
    MindSpace,
    MindSpace,
    MindspaceMessagesResponse,
)
from magick_mind.resources.v1.mindspace import MindspaceResourceV1


class TestMindspaceResourceV1:
    """Tests for MindspaceResourceV1."""

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        mock_client = Mock()
        return mock_client

    @pytest.fixture
    def mindspace_resource(self, mock_http_client):
        """Create MindspaceResourceV1 instance with mock HTTP client."""
        return MindspaceResourceV1(mock_http_client)

    def test_create_makes_correct_api_call(self, mindspace_resource, mock_http_client):
        """Test create() makes correct POST request."""
        # Mock successful response
        mock_http_client.post.return_value = {
            "id": "mind-123",
            "name": "My Workspace",
            "description": "Test workspace",
            "project_id": "proj-456",
            "corpus_ids": ["corp-1"],
            "user_ids": ["user-1"],
            "type": "PRIVATE",
            "created_by": "user-1",
            "updated_by": "user-1",
            "created_at": "2025-12-16T09:00:00Z",
            "updated_at": "2025-12-16T09:00:00Z",
        mock_http_client.post.return_value = {
            "id": "mind-123",
            "name": "My Workspace",
            "description": "Test workspace",
            "project_id": "proj-456",
            "corpus_ids": ["corp-1"],
            "user_ids": ["user-1"],
            "type": "PRIVATE",
            "created_by": "user-1",
            "updated_by": "user-1",
            "created_at": "2025-12-16T09:00:00Z",
            "updated_at": "2025-12-16T09:00:00Z",
        }

        # Make request
        response = mindspace_resource.create(
            name="My Workspace",
            type="PRIVATE",
            description="Test workspace",
            corpus_ids=["corp-1"],
        )

        # Verify HTTP call
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == "/v1/mindspaces"

        # Verify request body
        request_body = call_args[1]["json"]
        assert request_body["name"] == "My Workspace"
        assert request_body["type"] == "PRIVATE"
        assert request_body["description"] == "Test workspace"
        assert request_body["corpus_ids"] == ["corp-1"]

        # Verify response
        assert isinstance(response, MindSpace)
        assert response.id == "mind-123"
        assert response.type == "PRIVATE"
        assert isinstance(response, MindSpace)
        assert response.id == "mind-123"
        assert response.type == "PRIVATE"

    def test_create_group_mindspace(self, mindspace_resource, mock_http_client):
        """Test create() with group mindspace type."""
        mock_http_client.post.return_value = {
            "id": "mind-456",
            "name": "Team Space",
            "description": "Team workspace",
            "project_id": "proj-123",
            "corpus_ids": ["corp-1", "corp-2"],
            "user_ids": ["user-1", "user-2"],
            "type": "GROUP",
            "created_by": "user-1",
            "updated_by": "user-1",
            "created_at": "2025-12-16T09:00:00Z",
            "updated_at": "2025-12-16T09:00:00Z",
        mock_http_client.post.return_value = {
            "id": "mind-456",
            "name": "Team Space",
            "description": "Team workspace",
            "project_id": "proj-123",
            "corpus_ids": ["corp-1", "corp-2"],
            "user_ids": ["user-1", "user-2"],
            "type": "GROUP",
            "created_by": "user-1",
            "updated_by": "user-1",
            "created_at": "2025-12-16T09:00:00Z",
            "updated_at": "2025-12-16T09:00:00Z",
        }

        response = mindspace_resource.create(
            name="Team Space",
            type="GROUP",
            user_ids=["user-1", "user-2"],
        )

        assert response.type == "GROUP"
        assert len(response.user_ids) == 2
        assert response.type == "GROUP"
        assert len(response.user_ids) == 2

    def test_get_makes_correct_api_call(self, mindspace_resource, mock_http_client):
        """Test get() makes correct GET request."""
        mock_http_client.get.return_value = {
            "id": "mind-789",
            "name": "Retrieved Space",
            "description": "Description",
            "project_id": "proj-123",
            "corpus_ids": ["corp-1"],
            "user_ids": ["user-1"],
            "type": "PRIVATE",
            "created_by": "user-1",
            "updated_by": "user-1",
            "created_at": "2025-12-16T09:00:00Z",
            "updated_at": "2025-12-16T09:00:00Z",
        mock_http_client.get.return_value = {
            "id": "mind-789",
            "name": "Retrieved Space",
            "description": "Description",
            "project_id": "proj-123",
            "corpus_ids": ["corp-1"],
            "user_ids": ["user-1"],
            "type": "PRIVATE",
            "created_by": "user-1",
            "updated_by": "user-1",
            "created_at": "2025-12-16T09:00:00Z",
            "updated_at": "2025-12-16T09:00:00Z",
        }

        response = mindspace_resource.get("mind-789")

        # Verify HTTP call
        mock_http_client.get.assert_called_once_with("/v1/mindspaces/mind-789")

        # Verify response
        assert isinstance(response, MindSpace)
        assert response.id == "mind-789"
        assert response.name == "Retrieved Space"
        assert isinstance(response, MindSpace)
        assert response.id == "mind-789"
        assert response.name == "Retrieved Space"

    def test_list_without_filter(self, mindspace_resource, mock_http_client):
        """Test list() without user_id filter."""
        mock_http_client.get.return_value = {
            "data": [
                {
                    "id": "mind-1",
                    "name": "Space 1",
                    "description": "First",
                    "project_id": "proj-1",
                    "corpus_ids": [],
                    "user_ids": ["user-1"],
                    "type": "PRIVATE",
                    "created_by": "user-1",
                    "updated_by": "user-1",
                    "created_at": "2025-12-16T09:00:00Z",
                    "updated_at": "2025-12-16T09:00:00Z",
                },
                {
                    "id": "mind-2",
                    "name": "Space 2",
                    "description": "Second",
                    "project_id": "proj-2",
                    "corpus_ids": ["corp-1"],
                    "user_ids": ["user-1"],
                    "type": "GROUP",
                    "created_by": "user-1",
                    "updated_by": "user-1",
                    "created_at": "2025-12-16T09:00:00Z",
                    "updated_at": "2025-12-16T09:00:00Z",
                },
            ],
            "paging": {
                "cursors": {"after": "mind-2", "before": None},
                "has_more": False,
                "has_previous": False,
            },
        }

        response = mindspace_resource.list()

        # Verify HTTP call with no params
        mock_http_client.get.assert_called_once_with("/v1/mindspaces", params={})

        # Verify response - test new structure and backward compat
        assert isinstance(response, GetMindSpaceListResponse)
        assert len(response.data) == 2
        assert len(response.mindspaces) == 2

    def test_list_with_user_filter(self, mindspace_resource, mock_http_client):
        """Test list() with user_id filter."""
        mock_http_client.get.return_value = {
            "data": [],
            "paging": {
                "cursors": {"after": None, "before": None},
                "has_more": False,
                "has_previous": False,
            },
        }

        response = mindspace_resource.list(user_id="user-123")

        # Verify HTTP call includes user_id param
        call_args = mock_http_client.get.call_args
        assert call_args[0][0] == "/v1/mindspaces"
        assert call_args[1]["params"]["user_id"] == "user-123"

    def test_update_makes_correct_api_call(self, mindspace_resource, mock_http_client):
        """Test update() makes correct PUT request."""
        mock_http_client.put.return_value = {
            "id": "mind-123",
            "name": "Updated Name",
            "description": "Updated description",
            "project_id": "proj-456",
            "corpus_ids": ["corp-1", "corp-2"],
            "user_ids": ["user-1"],
            "type": "PRIVATE",
            "created_by": "user-1",
            "updated_by": "user-2",
            "created_at": "2025-12-16T08:00:00Z",
            "updated_at": "2025-12-16T10:00:00Z",
        mock_http_client.put.return_value = {
            "id": "mind-123",
            "name": "Updated Name",
            "description": "Updated description",
            "project_id": "proj-456",
            "corpus_ids": ["corp-1", "corp-2"],
            "user_ids": ["user-1"],
            "type": "PRIVATE",
            "created_by": "user-1",
            "updated_by": "user-2",
            "created_at": "2025-12-16T08:00:00Z",
            "updated_at": "2025-12-16T10:00:00Z",
        }

        response = mindspace_resource.update(
            mindspace_id="mind-123",
            name="Updated Name",
            description="Updated description",
            corpus_ids=["corp-1", "corp-2"],
        )

        # Verify HTTP call
        mock_http_client.put.assert_called_once()
        call_args = mock_http_client.put.call_args
        assert call_args[0][0] == "/v1/mindspaces/mind-123"

        # Verify request body
        request_body = call_args[1]["json"]
        assert request_body["name"] == "Updated Name"
        assert request_body["description"] == "Updated description"
        assert len(request_body["corpus_ids"]) == 2

        # Verify response
        assert isinstance(response, MindSpace)
        assert response.name == "Updated Name"
        assert response.updated_by == "user-2"
        assert isinstance(response, MindSpace)
        assert response.name == "Updated Name"
        assert response.updated_by == "user-2"

    def test_delete_makes_correct_api_call(self, mindspace_resource, mock_http_client):
        """Test delete() makes correct DELETE request."""
        mindspace_resource.delete("mind-123")

        # Verify HTTP call
        mock_http_client.delete.assert_called_once_with("/v1/mindspaces/mind-123")

    def test_get_messages_latest_mode(self, mindspace_resource, mock_http_client):
        """Test get_messages() in latest mode (no cursors)."""
        mock_http_client.get.return_value = {
            "data": [
                {
                    "id": "msg-1",
                    "mindspace_id": "mind-123",
                    "sent_by_user_id": "user-1",
                    "content": "Hello",
                    "status": "sent",
                    "artifact_ids": [],
                    "create_at": "2025-12-16T09:00:00Z",
                    "update_at": "2025-12-16T09:00:00Z",
                }
            ],
            "paging": {
                "cursors": {"after": None, "before": "msg-1"},
                "has_more": False,
                "has_previous": True,
            },
        }

        response = mindspace_resource.get_messages(mindspace_id="mind-123", limit=50)

        # Verify HTTP call
        call_args = mock_http_client.get.call_args
        assert call_args[0][0] == "/v1/mindspaces/messages"
        params = call_args[1]["params"]
        assert params["mindspace_id"] == "mind-123"
        assert params["limit"] == 50
        assert "after_id" not in params
        assert "before_id" not in params

        # Verify response - test new structure and backward compat
        assert isinstance(response, MindspaceMessagesResponse)
        assert len(response.data) == 1
        assert len(response.chat_histories) == 1
        assert response.has_older is True

    def test_get_messages_forward_mode(self, mindspace_resource, mock_http_client):
        """Test get_messages() in forward mode (after_id provided)."""
        mock_http_client.get.return_value = {
            "data": [],
            "paging": {
                "cursors": {"after": "msg-5", "before": None},
                "has_more": True,
                "has_previous": False,
            },
        }

        response = mindspace_resource.get_messages(
            mindspace_id="mind-123", after_id="msg-1", limit=10
        )

        # Verify after_id in params
        params = mock_http_client.get.call_args[1]["params"]
        assert params["after_id"] == "msg-1"
        assert "before_id" not in params

        assert response.paging.has_more is True
        assert response.has_more is True

    def test_get_messages_backward_mode(self, mindspace_resource, mock_http_client):
        """Test get_messages() in backward mode (before_id provided)."""
        mock_http_client.get.return_value = {
            "data": [],
            "paging": {
                "cursors": {"after": None, "before": "msg-0"},
                "has_more": False,
                "has_previous": True,
            },
        }

        response = mindspace_resource.get_messages(
            mindspace_id="mind-123", before_id="msg-10", limit=10
        )

        # Verify before_id in params
        params = mock_http_client.get.call_args[1]["params"]
        assert params["before_id"] == "msg-10"
        assert "after_id" not in params

        assert response.paging.has_previous is True
        assert response.has_older is True

    def test_get_messages_rejects_both_cursors(
        self, mindspace_resource, mock_http_client
    ):
        """Test get_messages() raises error when both after_id and before_id provided."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            mindspace_resource.get_messages(
                mindspace_id="mind-123",
                after_id="msg-1",
                before_id="msg-10",
            )


class TestMindspaceResourceIntegration:
    """Integration tests for mindspace resource with MagickMind client."""

    @patch("magick_mind.auth.EmailPasswordAuth._login")
    def test_client_mindspace_alias(self, mock_login):
        """Test client.mindspace is aliased to client.v1.mindspace."""
        mock_login.return_value = None

        client = MagickMind(
            base_url="https://test.com",
            email="test@example.com",
            password="password123",
        )

        # Verify mindspace alias
        assert client.mindspace is client.v1.mindspace
        assert isinstance(client.mindspace, MindspaceResourceV1)

    @patch("magick_mind.http.HTTPClient.post")
    @patch("magick_mind.auth.EmailPasswordAuth._login")
    def test_end_to_end_create_mindspace(self, mock_login, mock_post):
        """Test end-to-end flow of creating a mindspace."""
        mock_login.return_value = None

        # Mock create response
        mock_post.return_value = {
            "id": "mind-new",
            "name": "Test Space",
            "description": "Test",
            "project_id": "proj-1",
            "corpus_ids": [],
            "user_ids": ["user-1"],
            "type": "PRIVATE",
            "created_by": "user-1",
            "updated_by": "user-1",
            "created_at": "2025-12-16T09:00:00Z",
            "updated_at": "2025-12-16T09:00:00Z",
        mock_post.return_value = {
            "id": "mind-new",
            "name": "Test Space",
            "description": "Test",
            "project_id": "proj-1",
            "corpus_ids": [],
            "user_ids": ["user-1"],
            "type": "PRIVATE",
            "created_by": "user-1",
            "updated_by": "user-1",
            "created_at": "2025-12-16T09:00:00Z",
            "updated_at": "2025-12-16T09:00:00Z",
        }

        client = MagickMind(
            base_url="https://test.com",
            email="test@example.com",
            password="password123",
        )

        # Manually set auth token (accessing private attrs for test setup)
        client.auth._access_token = "fake-token"  # type: ignore[attr-defined]
        client.auth._token_expires_at = time.time() + 3600  # type: ignore[attr-defined]

        # Create mindspace via v1 resource
        response = client.v1.mindspace.create(name="Test Space", type="PRIVATE")

        assert response.id == "mind-new"
        assert response.id == "mind-new"

        # Verify the same works via alias
        _ = client.mindspace.create(name="Test Space 2", type="GROUP")
