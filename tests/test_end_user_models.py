"""Tests for end user models."""

import pytest

from magick_mind.models.v1.end_user import (
    CreateEndUserRequest,
    EndUser,
    QueryEndUserResponse,
    UpdateEndUserRequest,
)


class TestEndUser:
    """Tests for EndUser model."""

    def test_end_user_with_all_fields(self):
        """Test EndUser with all fields populated."""
        data = {
            "id": "user-123",
            "name": "John Doe",
            "external_id": "ext-789",
            "tenant_id": "tenant-456",
            "created_by": "admin-001",
            "updated_by": "admin-002",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T11:00:00Z",
        }

        end_user = EndUser(**data)

        assert end_user.id == "user-123"
        assert end_user.name == "John Doe"
        assert end_user.external_id == "ext-789"
        assert end_user.tenant_id == "tenant-456"
        assert end_user.created_by == "admin-001"
        assert end_user.updated_by == "admin-002"
        assert end_user.created_at == "2024-01-01T10:00:00Z"
        assert end_user.updated_at == "2024-01-01T11:00:00Z"

    def test_end_user_with_optional_fields_none(self):
        """Test EndUser with optional fields set to None."""
        data = {
            "id": "user-123",
            "name": "Jane Doe",
            "tenant_id": "tenant-456",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
        }

        end_user = EndUser(**data)

        assert end_user.external_id is None
        assert end_user.created_by is None
        assert end_user.updated_by is None

    def test_end_user_missing_required_fields(self):
        """Test EndUser raises error when required fields are missing."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            EndUser(name="John")


class TestCreateEndUserRequest:
    """Tests for CreateEndUserRequest model."""

    def test_create_request_with_all_fields(self):
        """Test CreateEndUserRequest with all fields."""
        request = CreateEndUserRequest(
            name="John Doe",
            external_id="ext-789",
            tenant_id="tenant-456",
            actor_id="admin-123",
        )

        assert request.name == "John Doe"
        assert request.external_id == "ext-789"
        assert request.tenant_id == "tenant-456"
        assert request.actor_id == "admin-123"

    def test_create_request_without_external_id(self):
        """Test CreateEndUserRequest with optional external_id omitted."""
        request = CreateEndUserRequest(
            name="Jane Doe", tenant_id="tenant-456", actor_id="admin-123"
        )

        assert request.external_id is None

    def test_create_request_missing_required_fields(self):
        """Test CreateEndUserRequest with relaxed optional fields."""
        # With relaxed spec, only name is functionally required
        request = CreateEndUserRequest(name="John")
        assert request.name == "John"
        assert request.tenant_id is None  # Now Optional
        assert request.actor_id is None  # Now Optional


class TestQueryEndUserResponse:
    """Tests for QueryEndUserResponse model."""

    def test_query_response_with_users(self):
        """Test QueryEndUserResponse with multiple end users."""
        users_data = [
            {
                "id": "user-1",
                "name": "User 1",
                "tenant_id": "tenant-1",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z",
            },
            {
                "id": "user-2",
                "name": "User 2",
                "tenant_id": "tenant-1",
                "created_at": "2024-01-01T11:00:00Z",
                "updated_at": "2024-01-01T11:00:00Z",
            },
        ]

        response = QueryEndUserResponse(
            end_users=[EndUser(**data) for data in users_data]
        )

        assert len(response.end_users) == 2
        assert all(isinstance(user, EndUser) for user in response.end_users)
        assert response.end_users[0].id == "user-1"
        assert response.end_users[1].id == "user-2"

    def test_query_response_empty(self):
        """Test QueryEndUserResponse with empty list."""
        response = QueryEndUserResponse(end_users=[])

        assert response.end_users == []


class TestUpdateEndUserRequest:
    """Tests for UpdateEndUserRequest model."""

    def test_update_request_all_fields(self):
        """Test UpdateEndUserRequest with all fields."""
        request = UpdateEndUserRequest(
            name="Updated Name",
            external_id="new-ext-id",
            tenant_id="new-tenant-id",
        )

        assert request.name == "Updated Name"
        assert request.external_id == "new-ext-id"
        assert request.tenant_id == "new-tenant-id"

    def test_update_request_partial(self):
        """Test UpdateEndUserRequest with partial fields."""
        request = UpdateEndUserRequest(name="Updated Name")

        assert request.name == "Updated Name"
        assert request.external_id is None
        assert request.tenant_id is None

    def test_update_request_empty(self):
        """Test UpdateEndUserRequest with all None (valid for updates)."""
        request = UpdateEndUserRequest()

        assert request.name is None
        assert request.external_id is None
        assert request.tenant_id is None
