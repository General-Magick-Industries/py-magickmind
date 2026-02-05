"""Tests for V1 mindspace models."""

import pytest
from pydantic import ValidationError

from magick_mind.models.v1.mindspace import (
    CreateMindSpaceRequest,
    GetMindSpaceListResponse,
    MindSpace,
    UpdateMindSpaceRequest,
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
            type="GROUP",
            created_by="user-1",
            updated_by="user-1",
            created_at="2025-12-16T09:00:00Z",
            updated_at="2025-12-16T09:00:00Z",
        )

        assert mindspace.id == "mind-123"
        assert mindspace.name == "Engineering Team"
        assert mindspace.type == "GROUP"
        assert len(mindspace.corpus_ids) == 2
        assert len(mindspace.user_ids) == 2

    def test_mindspace_type_validation_accepts_private(self):
        """Test MindSpace accepts 'PRIVATE' type."""
        mindspace = MindSpace(
            id="mind-456",
            name="My Space",
            description="Private space",
            project_id="proj-123",
            corpus_ids=[],
            user_ids=["user-1"],
            type="PRIVATE",
            created_by="user-1",
            updated_by="user-1",
            created_at="2025-12-16T09:00:00Z",
            updated_at="2025-12-16T09:00:00Z",
        )
        assert mindspace.type == "PRIVATE"

    def test_mindspace_type_validation_accepts_group(self):
        """Test MindSpace accepts 'GROUP' type."""
        mindspace = MindSpace(
            id="mind-789",
            name="Team Space",
            description="Group space",
            project_id="proj-123",
            corpus_ids=[],
            user_ids=["user-1"],
            type="GROUP",
            created_by="user-1",
            updated_by="user-1",
            created_at="2025-12-16T09:00:00Z",
            updated_at="2025-12-16T09:00:00Z",
        )
        assert mindspace.type == "GROUP"

    def test_mindspace_type_validation_rejects_invalid(self):
        """Test MindSpace rejects invalid type values."""
        with pytest.raises(ValidationError) as exc_info:
            MindSpace(
                id="mind-invalid",
                name="Invalid",
                description="Invalid type",
                project_id="proj-123",
                corpus_ids=[],
                user_ids=["user-1"],
                type="invalid",  # type: ignore[arg-type]  # Intentional invalid type
                created_by="user-1",
                updated_by="user-1",
                created_at="2025-12-16T09:00:00Z",
                updated_at="2025-12-16T09:00:00Z",
            )

        errors = exc_info.value.errors()
        assert any("type" in str(error["loc"]) for error in errors)

    def test_mindspace_with_optional_fields_as_none(self):
        """Test MindSpace with relaxed/optional fields - verifies defaults work."""
        # Intentionally omitting optional fields to test default values
        mindspace = MindSpace(  # type: ignore[call-arg]
            id="mind-123",
            name="Minimal",
            project_id="proj-123",
            type="PRIVATE",
        )
        assert mindspace.description is None
        assert mindspace.corpus_ids == []  # List fields default to empty list, not None
        assert mindspace.user_ids == []  # List fields default to empty list, not None
        assert mindspace.created_by is None


class TestCreateMindSpaceRequest:
    """Tests for CreateMindSpaceRequest model."""

    def test_valid_request_with_name_and_type(self):
        """Test CreateMindSpaceRequest validates with name and type."""
        request = CreateMindSpaceRequest(name="My Workspace", type="PRIVATE")

        assert request.name == "My Workspace"
        assert request.type == "PRIVATE"
        assert request.description is None
        assert request.project_id is None
        assert request.corpus_ids == []
        assert request.user_ids == []

    def test_valid_request_with_all_fields(self):
        """Test CreateMindSpaceRequest validates with all fields."""
        request = CreateMindSpaceRequest(
            name="Engineering Team",
            type="GROUP",
            description="Team collaboration space",
            project_id="proj-123",
            corpus_ids=["corp-1", "corp-2"],
            user_ids=["user-1", "user-2", "user-3"],
        )

        assert request.name == "Engineering Team"
        assert request.type == "GROUP"
        assert request.description == "Team collaboration space"
        assert request.project_id == "proj-123"
        assert len(request.corpus_ids) == 2
        assert len(request.user_ids) == 3

    def test_request_with_relaxed_fields(self):
        """Test CreateMindSpaceRequest allows optional name/type (relaxed for spec)."""
        # Relaxed fields allow creation without name/type (spec-driven)
        request = CreateMindSpaceRequest()  # type: ignore[call-arg]
        assert request.name is None
        assert request.type is None

    def test_type_enum_validation(self):
        """Test type field validates enum values."""
        # Valid: PRIVATE
        request1 = CreateMindSpaceRequest(name="Space 1", type="PRIVATE")
        assert request1.type == "PRIVATE"

        # Valid: GROUP
        request2 = CreateMindSpaceRequest(name="Space 2", type="GROUP")
        assert request2.type == "GROUP"

        # Invalid: lowercase (not matching spec)
        with pytest.raises(ValidationError):
            CreateMindSpaceRequest(name="Space 3", type="private")  # type: ignore[arg-type]

        # Invalid: other value
        with pytest.raises(ValidationError):
            CreateMindSpaceRequest(name="Space 3", type="invalid")  # type: ignore[arg-type]

    def test_model_dump_excludes_none(self):
        """Test model_dump excludes None values when exclude_none=True."""
        request = CreateMindSpaceRequest(name="Test", type="PRIVATE")

        dumped = request.model_dump(exclude_none=True)
        assert "name" in dumped
        assert "type" in dumped
        assert "description" not in dumped
        assert "project_id" not in dumped


class TestGetMindSpaceListResponse:
    """Tests for GetMindSpaceListResponse model with standardized {data, paging} structure."""

    def test_valid_list_response_parsing(self):
        """Test GetMindSpaceListResponse parses bifrost API response."""
        # Uses model_validate which handles dict -> Cursors/PageInfo conversion

        response_data = {
            "data": [
                {
                    "id": "mind-1",
                    "name": "Space 1",
                    "description": "First space",
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
                    "description": "Second space",
                    "project_id": "proj-2",
                    "corpus_ids": ["corp-1"],
                    "user_ids": ["user-1", "user-2"],
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

        response = GetMindSpaceListResponse.model_validate(response_data)

        # Test new structure
        assert len(response.data) == 2
        assert response.data[0].type == "PRIVATE"
        assert response.data[1].type == "GROUP"
        assert response.paging.cursors.after == "mind-2"

        # Test backward compat property
        assert len(response.mindspaces) == 2
        assert response.mindspaces[0].type == "PRIVATE"
        assert response.mindspaces[1].type == "GROUP"

    def test_empty_list_response(self):
        """Test GetMindSpaceListResponse handles empty list."""
        response_data = {
            "data": [],
            "paging": {
                "cursors": {"after": None, "before": None},
                "has_more": False,
                "has_previous": False,
            },
        }

        response = GetMindSpaceListResponse.model_validate(response_data)

        assert len(response.data) == 0
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
