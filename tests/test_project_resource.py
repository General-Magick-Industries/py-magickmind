"""Tests for project resource."""

import pytest
from unittest.mock import Mock, patch

from magick_mind import MagickMind
from magick_mind.models.v1.project import Project
from magick_mind.resources.v1.project import ProjectResourceV1


class TestProjectResourceV1:
    """Tests for ProjectResourceV1."""

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        return Mock()

    @pytest.fixture
    def project_resource(self, mock_http_client):
        """Create ProjectResourceV1 instance with mock HTTP client."""
        return ProjectResourceV1(mock_http_client)

    def test_create_project(self, project_resource, mock_http_client):
        """Test creating a new project."""
        # HTTP client returns dict directly (not Mock with .json())
        mock_http_client.post.return_value = {
            "id": "proj-123",
            "name": "My Project",
            "description": "A test project",
            "corpus_ids": ["corpus-1", "corpus-2"],
            "created_by": "user-456",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
        }

        result = project_resource.create(
            name="My Project",
            description="A test project",
            corpus_ids=["corpus-1", "corpus-2"],
        )

        assert isinstance(result, Project)
        assert result.id == "proj-123"
        assert result.name == "My Project"
        assert result.description == "A test project"
        assert result.corpus_ids == ["corpus-1", "corpus-2"]
        assert result.created_by == "user-456"

        # Verify API call
        mock_http_client.post.assert_called_once_with(
            "/v1/projects",
            json={
                "name": "My Project",
                "description": "A test project",
                "corpus_ids": ["corpus-1", "corpus-2"],
            },
        )

    def test_create_project_minimal(self, project_resource, mock_http_client):
        """Test creating project with only required fields."""
        mock_http_client.post.return_value = {
            "id": "proj-456",
            "name": "Minimal Project",
            "description": "",
            "corpus_ids": [],
            "created_by": "user-789",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
        }

        result = project_resource.create(name="Minimal Project")

        assert result.name == "Minimal Project"
        assert result.description == ""
        assert result.corpus_ids == []

        # Verify that defaults were sent
        call_args = mock_http_client.post.call_args
        assert call_args[1]["json"]["description"] == ""
        assert call_args[1]["json"]["corpus_ids"] == []

    def test_get_project(self, project_resource, mock_http_client):
        """Test getting a project by ID."""
        mock_http_client.get.return_value = {
            "id": "proj-123",
            "name": "Retrieved Project",
            "description": "Test",
            "corpus_ids": ["corpus-1"],
            "created_by": "user-456",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
        }

        result = project_resource.get(project_id="proj-123")

        assert isinstance(result, Project)
        assert result.id == "proj-123"
        assert result.name == "Retrieved Project"

        # Verify API call
        mock_http_client.get.assert_called_once_with("/v1/projects/proj-123")

    def test_list_projects_all(self, project_resource, mock_http_client):
        """Test listing all projects."""
        mock_http_client.get.return_value = {
            "data": [
                {
                    "id": "proj-1",
                    "name": "Project 1",
                    "description": "First",
                    "corpus_ids": [],
                    "created_by": "user-1",
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                },
                {
                    "id": "proj-2",
                    "name": "Project 2",
                    "description": "Second",
                    "corpus_ids": ["corpus-1"],
                    "created_by": "user-2",
                    "created_at": "2024-01-01T11:00:00Z",
                    "updated_at": "2024-01-01T11:00:00Z",
                },
            ],
            "paging": {
                "cursors": {"after": "cursor-123", "before": None},
                "has_more": True,
                "has_previous": False,
            },
        }

        result = project_resource.list()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(p, Project) for p in result)
        assert result[0].id == "proj-1"
        assert result[1].id == "proj-2"

        # Verify API call
        mock_http_client.get.assert_called_once_with("/v1/projects", params={})

    def test_list_projects_by_user(self, project_resource, mock_http_client):
        """Test listing projects filtered by creator user ID."""
        mock_http_client.get.return_value = {
            "data": [
                {
                    "id": "proj-1",
                    "name": "User Project",
                    "description": "Created by specific user",
                    "corpus_ids": [],
                    "created_by": "user-123",
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                }
            ],
            "paging": {
                "cursors": {"after": None, "before": None},
                "has_more": False,
                "has_previous": False,
            },
        }

        result = project_resource.list(created_by_user_id="user-123")

        assert len(result) == 1
        assert result[0].created_by == "user-123"

        # Verify API call with filter
        mock_http_client.get.assert_called_once_with(
            "/v1/projects", params={"user_id": "user-123"}
        )

    def test_list_projects_empty(self, project_resource, mock_http_client):
        """Test listing projects when none exist."""
        mock_http_client.get.return_value = {
            "data": [],
            "paging": {
                "cursors": {"after": None, "before": None},
                "has_more": False,
                "has_previous": False,
            },
        }

        result = project_resource.list()

        assert result == []

    def test_update_project(self, project_resource, mock_http_client):
        """Test updating a project."""
        mock_http_client.put.return_value = {
            "id": "proj-123",
            "name": "Updated Project",
            "description": "Updated description",
            "corpus_ids": ["corpus-1", "corpus-2", "corpus-3"],
            "created_by": "user-456",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T11:00:00Z",
        }

        result = project_resource.update(
            project_id="proj-123",
            name="Updated Project",
            description="Updated description",
            corpus_ids=["corpus-1", "corpus-2", "corpus-3"],
        )

        assert isinstance(result, Project)
        assert result.id == "proj-123"
        assert result.name == "Updated Project"
        assert result.description == "Updated description"
        assert len(result.corpus_ids) == 3
        assert result.updated_at == "2024-01-01T11:00:00Z"

        # Verify API call
        mock_http_client.put.assert_called_once_with(
            "/v1/projects/proj-123",
            json={
                "name": "Updated Project",
                "description": "Updated description",
                "corpus_ids": ["corpus-1", "corpus-2", "corpus-3"],
            },
        )

    def test_update_project_minimal(self, project_resource, mock_http_client):
        """Test updating project with only required fields."""
        mock_http_client.put.return_value = {
            "id": "proj-123",
            "name": "New Name",
            "description": "",
            "corpus_ids": [],
            "created_by": "user-456",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T11:00:00Z",
        }

        result = project_resource.update(project_id="proj-123", name="New Name")

        assert result.name == "New Name"
        assert result.description == ""
        assert result.corpus_ids == []

    def test_delete_project(self, project_resource, mock_http_client):
        """Test deleting a project."""
        # Delete typically returns no content or success message
        mock_http_client.delete.return_value = {}

        # Should not raise any exception
        project_resource.delete(project_id="proj-123")

        # Verify API call
        mock_http_client.delete.assert_called_once_with("/v1/projects/proj-123")


class TestProjectResourceIntegration:
    """Integration tests for project resource with MagickMind client."""

    @patch("magick_mind.auth.email_password.EmailPasswordAuth._login")
    def test_client_project_access(self, mock_login):
        """Test client.v1.project is accessible."""
        mock_login.return_value = None

        client = MagickMind(
            base_url="https://test.com",
            email="test@example.com",
            password="password123",
        )

        assert isinstance(client.v1.project, ProjectResourceV1)
