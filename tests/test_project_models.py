"""Tests for project models."""

import pytest
from pydantic import ValidationError

from magick_mind.models.common import Cursors, PageInfo
from magick_mind.models.v1.project import (
    CreateProjectRequest,
    GetProjectListResponse,
    Project,
    UpdateProjectRequest,
)


class TestProject:
    """Tests for Project model."""

    def test_valid_project(self):
        """Test creating a valid project."""
        project = Project(
            id="proj-123",
            name="My Project",
            description="A test project",
            corpus_ids=["corpus-1", "corpus-2"],
            created_by="user-456",
            created_at="2024-01-01T10:00:00Z",
            updated_at="2024-01-01T10:00:00Z",
        )

        assert project.id == "proj-123"
        assert project.name == "My Project"
        assert project.description == "A test project"
        assert project.corpus_ids == ["corpus-1", "corpus-2"]
        assert project.created_by == "user-456"
        assert project.created_at == "2024-01-01T10:00:00Z"
        assert project.updated_at == "2024-01-01T10:00:00Z"

    def test_project_without_corpus_ids(self):
        """Test project with empty corpus_ids list."""
        project = Project(
            id="proj-123",
            name="My Project",
            description="Test",
            corpus_ids=[],
            created_by="user-456",
            created_at="2024-01-01T10:00:00Z",
            updated_at="2024-01-01T10:00:00Z",
        )

        assert project.corpus_ids == []

    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            Project(  # type: ignore[call-arg]
                id="proj-123",
                # Missing name, description, created_by, timestamps
            )


class TestCreateProjectRequest:
    """Tests for CreateProjectRequest model."""

    def test_valid_create_request(self):
        """Test creating a valid project creation request."""
        request = CreateProjectRequest(
            name="New Project",
            description="A new project",
            corpus_ids=["corpus-1"],
        )

        assert request.name == "New Project"
        assert request.description == "A new project"
        assert request.corpus_ids == ["corpus-1"]

    def test_create_request_minimal(self):
        """Test creating request with only required fields."""
        request = CreateProjectRequest(name="Minimal Project")

        assert request.name == "Minimal Project"
        assert request.description == ""
        assert request.corpus_ids == []

    def test_create_request_without_corpus_ids(self):
        """Test create request defaults to empty corpus_ids."""
        request = CreateProjectRequest(
            name="Project",
            description="Description",
        )

        assert request.corpus_ids == []

    def test_missing_name(self):
        """Test that missing name raises validation error."""
        with pytest.raises(ValidationError):
            CreateProjectRequest(description="No name")  # type: ignore[call-arg]


class TestGetProjectListResponse:
    """Tests for GetProjectListResponse model."""

    def test_valid_list_response(self):
        """Test creating a valid project list response."""
        projects = [
            Project(
                id=f"proj-{i}",
                name=f"Project {i}",
                description=f"Description {i}",
                corpus_ids=[f"corpus-{i}"],
                created_by="user-456",
                created_at="2024-01-01T10:00:00Z",
                updated_at="2024-01-01T10:00:00Z",
            )
            for i in range(3)
        ]

        paging = PageInfo(
            cursors=Cursors(after="cursor-123", before="cursor-0"),
            has_more=True,
            has_previous=False,
        )

        response = GetProjectListResponse(data=projects, paging=paging)

        assert len(response.data) == 3
        assert response.data[0].id == "proj-0"
        assert response.data[2].id == "proj-2"
        assert response.paging.cursors.after == "cursor-123"
        assert response.paging.has_more is True

    def test_empty_list_response(self):
        """Test creating an empty project list response."""
        paging = PageInfo(
            cursors=Cursors(after=None, before=None),
            has_more=False,
            has_previous=False,
        )

        response = GetProjectListResponse(data=[], paging=paging)

        assert response.data == []
        assert response.paging.has_more is False


class TestUpdateProjectRequest:
    """Tests for UpdateProjectRequest model."""

    def test_valid_update_request(self):
        """Test creating a valid project update request."""
        request = UpdateProjectRequest(
            name="Updated Project",
            description="Updated description",
            corpus_ids=["corpus-1", "corpus-2"],
        )

        assert request.name == "Updated Project"
        assert request.description == "Updated description"
        assert request.corpus_ids == ["corpus-1", "corpus-2"]

    def test_update_request_minimal(self):
        """Test update request with minimal required fields."""
        # Intentionally omitting description to test it's optional
        request = UpdateProjectRequest(name="Updated Name", corpus_ids=[])  # type: ignore[call-arg]

        assert request.name == "Updated Name"
        assert request.description is None
        assert request.corpus_ids == []

    def test_missing_name(self):
        """Test that missing name raises validation error."""
        with pytest.raises(ValidationError):
            UpdateProjectRequest(description="No name")  # type: ignore[call-arg]
