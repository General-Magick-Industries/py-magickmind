"""Tests for V1 mindspace models."""

import pytest
from pydantic import ValidationError

from magick_mind.models.v1.mindspace import (
    CreateMindSpaceRequest,
    CreateMindSpaceResponse,
    GetMindSpaceListResponse,
    GetMindSpaceResponse,
    MindSpace,
    UpdateMindSpaceRequest,
    UpdateMindSpaceResponse,
)


class TestMindSpace:
    """Tests for MindSpace schema model."""

    def test_valid_mindspace_schema(self):
        """Test MindSpace validates with all fields."""
        mindspace = MindSpace(
            id="mind-123",
            name="Engineering Team",
            description="Team workspace",
            project_id="proj-456",
            corpus_ids=["corp-1", "corp-2"],
            user_ids=["user-1", "user-2"],
            type="group",
            created_by="user-1",
            updated_by="user-1",
            created_at="2025-12-16T09:00:00Z",
            updated_at="2025-12-16T09:00:00Z",
        )

        assert mindspace.id == "mind-123"
        assert mindspace.name == "Engineering Team"
        assert mindspace.type == "group"
        assert len(mindspace.corpus_ids) == 2
        assert len(mindspace.user_ids) == 2

    def test_mindspace_type_validation_accepts_private(self):
        """Test MindSpace accepts 'private' type."""
        mindspace = MindSpace(
            id="mind-456",
            name="My Space",
            description="Private space",
            project_id="proj-123",
            type="private",
            created_by="user-1",
            updated_by="user-1",
            created_at="2025-12-16T09:00:00Z",
            updated_at="2025-12-16T09:00:00Z",
        )
        assert mindspace.type == "private"

    def test_mindspace_type_validation_accepts_group(self):
        """Test MindSpace accepts 'group' type."""
        mindspace = MindSpace(
            id="mind-789",
            name="Team Space",
            description="Group space",
            project_id="proj-123",
            type="group",
            created_by="user-1",
            updated_by="user-1",
            created_at="2025-12-16T09:00:00Z",
            updated_at="2025-12-16T09:00:00Z",
        )
        assert mindspace.type == "group"

    def test_mindspace_type_validation_rejects_invalid(self):
        """Test MindSpace rejects invalid type values."""
        with pytest.raises(ValidationError) as exc_info:
            MindSpace(
                id="mind-invalid",
                name="Invalid",
                description="Invalid type",
                project_id="proj-123",
                type="invalid",  # Invalid type
                created_by="user-1",
                updated_by="user-1",
                created_at="2025-12-16T09:00:00Z",
                updated_at="2025-12-16T09:00:00Z",
            )

        errors = exc_info.value.errors()
        assert any("type" in str(error["loc"]) for error in errors)


class TestCreateMindSpaceRequest:
    """Tests for CreateMindSpaceRequest model."""

    def test_valid_request_with_required_fields(self):
        """Test CreateMindSpaceRequest validates with required fields only."""
        request = CreateMindSpaceRequest(name="My Workspace", type="private")

        assert request.name == "My Workspace"
        assert request.type == "private"
        assert request.description is None
        assert request.project_id is None
        assert request.corpus_ids == []
        assert request.user_ids == []

    def test_valid_request_with_all_fields(self):
        """Test CreateMindSpaceRequest validates with all fields."""
        request = CreateMindSpaceRequest(
            name="Engineering Team",
            type="group",
            description="Team collaboration space",
            project_id="proj-123",
            corpus_ids=["corp-1", "corp-2"],
            user_ids=["user-1", "user-2", "user-3"],
        )

        assert request.name == "Engineering Team"
        assert request.type == "group"
        assert request.description == "Team collaboration space"
        assert request.project_id == "proj-123"
        assert len(request.corpus_ids) == 2
        assert len(request.user_ids) == 3

    def test_missing_required_fields_raises_validation_error(self):
        """Test CreateMindSpaceRequest raises ValidationError when required fields missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateMindSpaceRequest()

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "name" in error_fields
        assert "type" in error_fields

    def test_type_enum_validation(self):
        """Test type field validates enum values."""
        # Valid: private
        request1 = CreateMindSpaceRequest(name="Space 1", type="private")
        assert request1.type == "private"

        # Valid: group
        request2 = CreateMindSpaceRequest(name="Space 2", type="group")
        assert request2.type == "group"

        # Invalid: other value
        with pytest.raises(ValidationError):
            CreateMindSpaceRequest(name="Space 3", type="invalid")

    def test_model_dump_excludes_none(self):
        """Test model_dump excludes None values when exclude_none=True."""
        request = CreateMindSpaceRequest(name="Test", type="private")

        dumped = request.model_dump(exclude_none=True)
        assert "name" in dumped
        assert "type" in dumped
        assert "description" not in dumped
        assert "project_id" not in dumped


class TestCreateMindSpaceResponse:
    """Tests for CreateMindSpaceResponse model."""

    def test_valid_response_parsing(self):
        """Test CreateMindSpaceResponse parses bifrost API response."""
        response_data = {
            "success": True,
            "message": "Mindspace created successfully",
            "mindspace": {
                "id": "mind-123",
                "name": "My Workspace",
                "description": "Test workspace",
                "project_id": "proj-456",
                "corpus_ids": ["corp-1"],
                "user_ids": ["user-1"],
                "type": "private",
                "created_by": "user-1",
                "updated_by": "user-1",
                "created_at": "2025-12-16T09:00:00Z",
                "updated_at": "2025-12-16T09:00:00Z",
            },
        }

        response = CreateMindSpaceResponse.model_validate(response_data)

        assert response.success is True
        assert response.message == "Mindspace created successfully"
        assert response.mindspace.id == "mind-123"
        assert response.mindspace.name == "My Workspace"
        assert response.mindspace.type == "private"


class TestGetMindSpaceResponse:
    """Tests for GetMindSpaceResponse model."""

    def test_valid_response_parsing(self):
        """Test GetMindSpaceResponse parses bifrost API response."""
        response_data = {
            "success": True,
            "message": "Mindspace retrieved successfully",
            "mindspace": {
                "id": "mind-789",
                "name": "Team Workspace",
                "description": "Team collaboration",
                "project_id": "proj-123",
                "corpus_ids": ["corp-1", "corp-2"],
                "user_ids": ["user-1", "user-2"],
                "type": "group",
                "created_by": "user-1",
                "updated_by": "user-2",
                "created_at": "2025-12-16T08:00:00Z",
                "updated_at": "2025-12-16T09:00:00Z",
            },
        }

        response = GetMindSpaceResponse.model_validate(response_data)

        assert response.success is True
        assert response.mindspace.id == "mind-789"
        assert response.mindspace.type == "group"
        assert len(response.mindspace.corpus_ids) == 2


class TestGetMindSpaceListResponse:
    """Tests for GetMindSpaceListResponse model."""

    def test_valid_list_response_parsing(self):
        """Test GetMindSpaceListResponse parses bifrost API response."""
        response_data = {
            "success": True,
            "message": "Mindspaces retrieved successfully",
            "mindspaces": [
                {
                    "id": "mind-1",
                    "name": "Space 1",
                    "description": "First space",
                    "project_id": "proj-1",
                    "corpus_ids": [],
                    "user_ids": ["user-1"],
                    "type": "private",
                    "created_by": "user-1",
                    "updated_by": "user-1",
                    "created_at": "2025-12-16T09:00:00Z",
                    "updated_at": "2025-12-16T09:00:00Z",
                },
                {
                    "id": "mind-2",
                    "name": "Space 2",
                    "description": "Second space",
                    "project_id": "proj-2",
                    "corpus_ids": ["corp-1"],
                    "user_ids": ["user-1", "user-2"],
                    "type": "group",
                    "created_by": "user-1",
                    "updated_by": "user-1",
                    "created_at": "2025-12-16T09:00:00Z",
                    "updated_at": "2025-12-16T09:00:00Z",
                },
            ],
        }

        response = GetMindSpaceListResponse.model_validate(response_data)

        assert response.success is True
        assert len(response.mindspaces) == 2
        assert response.mindspaces[0].type == "private"
        assert response.mindspaces[1].type == "group"

    def test_empty_list_response(self):
        """Test GetMindSpaceListResponse handles empty list."""
        response_data = {
            "success": True,
            "message": "No mindspaces found",
            "mindspaces": [],
        }

        response = GetMindSpaceListResponse.model_validate(response_data)

        assert response.success is True
        assert len(response.mindspaces) == 0


class TestUpdateMindSpaceRequest:
    """Tests for UpdateMindSpaceRequest model."""

    def test_valid_update_request(self):
        """Test UpdateMindSpaceRequest validates correctly."""
        request = UpdateMindSpaceRequest(
            name="Updated Name",
            description="Updated description",
            project_id="proj-new",
            corpus_ids=["corp-1", "corp-2", "corp-3"],
            user_ids=["user-1", "user-2"],
        )

        assert request.name == "Updated Name"
        assert request.description == "Updated description"
        assert len(request.corpus_ids) == 3

    def test_update_request_with_minimal_fields(self):
        """Test UpdateMindSpaceRequest with only required field."""
        request = UpdateMindSpaceRequest(name="Minimal Update")

        assert request.name == "Minimal Update"
        assert request.description is None


class TestUpdateMindSpaceResponse:
    """Tests for UpdateMindSpaceResponse model."""

    def test_valid_update_response_parsing(self):
        """Test UpdateMindSpaceResponse parses bifrost API response."""
        response_data = {
            "success": True,
            "message": "Mindspace updated successfully",
            "mindspace": {
                "id": "mind-123",
                "name": "Updated Workspace",
                "description": "Updated description",
                "project_id": "proj-456",
                "corpus_ids": ["corp-1", "corp-2"],
                "user_ids": ["user-1", "user-2"],
                "type": "group",
                "created_by": "user-1",
                "updated_by": "user-2",
                "created_at": "2025-12-16T08:00:00Z",
                "updated_at": "2025-12-16T10:00:00Z",
            },
        }

        response = UpdateMindSpaceResponse.model_validate(response_data)

        assert response.success is True
        assert response.mindspace.name == "Updated Workspace"
        assert response.mindspace.updated_by == "user-2"
