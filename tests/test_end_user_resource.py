"""Tests for end user resource."""

import pytest
from unittest.mock import Mock, patch

from magick_mind import MagickMind
from magick_mind.models.v1.end_user import EndUser
from magick_mind.resources.v1.end_user import EndUserResourceV1


class TestEndUserResourceV1:
    """Tests for EndUserResourceV1."""

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        return Mock()

    @pytest.fixture
    def end_user_resource(self, mock_http_client):
        """Create EndUserResourceV1 instance with mock HTTP client."""
        return EndUserResourceV1(mock_http_client)

    def test_create_end_user(self, end_user_resource, mock_http_client):
        """Test creating a new end user."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "end_user": {
                "id": "user-123",
                "name": "John Doe",
                "external_id": "ext-789",
                "tenant_id": "tenant-456",
                "created_by": "admin-001",
                "updated_by": None,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z",
            }
        }
        mock_http_client.post.return_value = mock_response

        result = end_user_resource.create(
            name="John Doe",
            tenant_id="tenant-456",
            actor_id="admin-001",
            external_id="ext-789",
        )

        assert isinstance(result, EndUser)
        assert result.id == "user-123"
        assert result.name == "John Doe"
        assert result.external_id == "ext-789"
        assert result.tenant_id == "tenant-456"
        assert result.created_by == "admin-001"

        # Verify API call
        mock_http_client.post.assert_called_once_with(
            "/v1/end-users",
            json={
                "name": "John Doe",
                "tenant_id": "tenant-456",
                "actor_id": "admin-001",
                "external_id": "ext-789",
            },
        )

    def test_create_end_user_without_external_id(
        self, end_user_resource, mock_http_client
    ):
        """Test creating end user without optional external_id."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "end_user": {
                "id": "user-456",
                "name": "Jane Doe",
                "external_id": None,
                "tenant_id": "tenant-789",
                "created_by": "admin-002",
                "updated_by": None,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z",
            }
        }
        mock_http_client.post.return_value = mock_response

        result = end_user_resource.create(
            name="Jane Doe",
            tenant_id="tenant-789",
            actor_id="admin-002",
        )

        assert result.name == "Jane Doe"
        assert result.external_id is None

        # Verify that None was sent for external_id
        call_args = mock_http_client.post.call_args
        assert call_args[1]["json"]["external_id"] is None

    def test_get_end_user(self, end_user_resource, mock_http_client):
        """Test getting an end user by ID."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "end_user": {
                "id": "user-123",
                "name": "Retrieved User",
                "external_id": "ext-001",
                "tenant_id": "tenant-456",
                "created_by": "admin-001",
                "updated_by": None,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z",
            }
        }
        mock_http_client.get.return_value = mock_response

        result = end_user_resource.get(end_user_id="user-123")

        assert isinstance(result, EndUser)
        assert result.id == "user-123"
        assert result.name == "Retrieved User"

        # Verify API call
        mock_http_client.get.assert_called_once_with("/v1/end-users/user-123")

    def test_query_end_users_all(self, end_user_resource, mock_http_client):
        """Test querying all end users without filters."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "end_users": [
                {
                    "id": "user-1",
                    "name": "User 1",
                    "external_id": None,
                    "tenant_id": "tenant-1",
                    "created_by": "admin-1",
                    "updated_by": None,
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                },
                {
                    "id": "user-2",
                    "name": "User 2",
                    "external_id": "ext-002",
                    "tenant_id": "tenant-2",
                    "created_by": "admin-2",
                    "updated_by": None,
                    "created_at": "2024-01-01T11:00:00Z",
                    "updated_at": "2024-01-01T11:00:00Z",
                },
            ]
        }
        mock_http_client.get.return_value = mock_response

        result = end_user_resource.query()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(u, EndUser) for u in result)
        assert result[0].id == "user-1"
        assert result[1].id == "user-2"

        # Verify API call with no filters
        mock_http_client.get.assert_called_once_with("/v1/end-users", params={})

    def test_query_end_users_by_tenant(self, end_user_resource, mock_http_client):
        """Test querying end users filtered by tenant_id."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "end_users": [
                {
                    "id": "user-1",
                    "name": "Tenant User 1",
                    "external_id": None,
                    "tenant_id": "tenant-123",
                    "created_by": "admin-1",
                    "updated_by": None,
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                }
            ]
        }
        mock_http_client.get.return_value = mock_response

        result = end_user_resource.query(tenant_id="tenant-123")

        assert len(result) == 1
        assert result[0].tenant_id == "tenant-123"

        # Verify API call with filter
        mock_http_client.get.assert_called_once_with(
            "/v1/end-users", params={"tenant_id": "tenant-123"}
        )

    def test_query_end_users_by_external_id(self, end_user_resource, mock_http_client):
        """Test querying end users filtered by external_id."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "end_users": [
                {
                    "id": "user-1",
                    "name": "External User",
                    "external_id": "ext-789",
                    "tenant_id": "tenant-456",
                    "created_by": "admin-1",
                    "updated_by": None,
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                }
            ]
        }
        mock_http_client.get.return_value = mock_response

        result = end_user_resource.query(external_id="ext-789")

        assert len(result) == 1
        assert result[0].external_id == "ext-789"

        # Verify API call
        mock_http_client.get.assert_called_once_with(
            "/v1/end-users", params={"external_id": "ext-789"}
        )

    def test_query_end_users_multiple_filters(
        self, end_user_resource, mock_http_client
    ):
        """Test querying with multiple filters."""
        mock_response = Mock()
        mock_response.json.return_value = {"end_users": []}
        mock_http_client.get.return_value = mock_response

        end_user_resource.query(
            name="John Doe", tenant_id="tenant-123", actor_id="admin-456"
        )

        # Verify all filters were included
        mock_http_client.get.assert_called_once_with(
            "/v1/end-users",
            params={
                "name": "John Doe",
                "tenant_id": "tenant-123",
                "actor_id": "admin-456",
            },
        )

    def test_query_end_users_empty(self, end_user_resource, mock_http_client):
        """Test querying end users when none match."""
        mock_response = Mock()
        mock_response.json.return_value = {"end_users": []}
        mock_http_client.get.return_value = mock_response

        result = end_user_resource.query()

        assert result == []

    def test_update_end_user(self, end_user_resource, mock_http_client):
        """Test updating an end user."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "end_user": {
                "id": "user-123",
                "name": "Updated Name",
                "external_id": "new-ext-id",
                "tenant_id": "tenant-456",
                "created_by": "admin-001",
                "updated_by": "admin-002",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T11:00:00Z",
            }
        }
        mock_http_client.put.return_value = mock_response

        result = end_user_resource.update(
            end_user_id="user-123",
            name="Updated Name",
            external_id="new-ext-id",
        )

        assert isinstance(result, EndUser)
        assert result.id == "user-123"
        assert result.name == "Updated Name"
        assert result.external_id == "new-ext-id"
        assert result.updated_by == "admin-002"
        assert result.updated_at == "2024-01-01T11:00:00Z"

        # Verify API call - should exclude None values
        mock_http_client.put.assert_called_once()
        call_args = mock_http_client.put.call_args
        assert call_args[0][0] == "/v1/end-users/user-123"
        assert "name" in call_args[1]["json"]
        assert "external_id" in call_args[1]["json"]

    def test_update_end_user_partial(self, end_user_resource, mock_http_client):
        """Test updating end user with only some fields."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "end_user": {
                "id": "user-123",
                "name": "New Name Only",
                "external_id": "ext-original",
                "tenant_id": "tenant-456",
                "created_by": "admin-001",
                "updated_by": "admin-003",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T11:00:00Z",
            }
        }
        mock_http_client.put.return_value = mock_response

        result = end_user_resource.update(end_user_id="user-123", name="New Name Only")

        assert result.name == "New Name Only"

        # Verify only name was sent (exclude_none=True)
        call_args = mock_http_client.put.call_args
        json_data = call_args[1]["json"]
        assert "name" in json_data
        assert json_data["name"] == "New Name Only"

    def test_delete_end_user(self, end_user_resource, mock_http_client):
        """Test deleting an end user."""
        # Delete typically returns no content
        mock_http_client.delete.return_value = Mock()

        # Should not raise any exception
        end_user_resource.delete(end_user_id="user-123")

        # Verify API call
        mock_http_client.delete.assert_called_once_with("/v1/end-users/user-123")


class TestEndUserResourceIntegration:
    """Integration tests for end user resource with MagickMind client."""

    @patch("magick_mind.auth.email_password.EmailPasswordAuth._login")
    def test_client_end_user_access(self, mock_login):
        """Test client.v1.end_user is accessible."""
        mock_login.return_value = None

        client = MagickMind(
            base_url="https://test.com",
            email="test@example.com",
            password="password123",
        )

        assert isinstance(client.v1.end_user, EndUserResourceV1)
