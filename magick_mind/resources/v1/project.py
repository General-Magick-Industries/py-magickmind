"""
Project resource for Magick Mind SDK v1 API.

Provides methods for CRUD operations on projects in the agentic SaaS backend.
"""

from __future__ import annotations

from typing import Optional


from magick_mind.models.v1.project import (
    CreateProjectRequest,
    GetProjectListResponse,
    Project,
    UpdateProjectRequest,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes


class ProjectResourceV1(BaseResource):
    """
    Project resource for managing agentic SaaS projects.

    Projects organize corpus and other resources for multi-tenant backends.
    """

    def create(
        self,
        name: str,
        description: str = "",
        corpus_ids: Optional[list[str]] = None,
    ) -> Project:
        """
        Create a new project.

        Args:
            name: Project name (required)
            description: Project description (optional, max 256 chars)
            corpus_ids: List of corpus IDs to associate with project

        Returns:
            Created Project object

        Example:
            project = client.v1.project.create(
                name="My Agentic App",
                description="An AI-powered assistant",
                corpus_ids=["corpus-123"]
            )
            print(f"Created project: {project.id}")
        """
        request = CreateProjectRequest(
            name=name,
            description=description,
            corpus_ids=corpus_ids or [],
        )

        response = self._http.post(Routes.PROJECTS, json=request.model_dump())
        return Project.model_validate(response)

    def get(self, project_id: str) -> Project:
        """
        Get a project by ID.

        Args:
            project_id: The project ID to retrieve

        Returns:
            Project object

        Example:
            project = client.v1.project.get(project_id="proj-123")
            print(f"Project name: {project.name}")
        """
        response = self._http.get(Routes.project(project_id))
        return Project.model_validate(response)

    def list(self, created_by_user_id: Optional[str] = None) -> list[Project]:
        """
        List projects, optionally filtered by creator user ID.

        Args:
            created_by_user_id: Optional user ID to filter projects created by this user

        Returns:
            List of Project objects

        Example:
            # List all accessible projects
            projects = client.v1.project.list()

            # List projects created by specific user
            user_projects = client.v1.project.list(created_by_user_id="user-123")
            for project in user_projects:
                print(f"- {project.name}")
        """
        params = {}
        if created_by_user_id:
            params["user_id"] = created_by_user_id

        response = self._http.get(Routes.PROJECTS, params=params)
        list_response = GetProjectListResponse.model_validate(response)
        return [Project.model_validate(p) for p in list_response.data]

    def update(
        self,
        project_id: str,
        name: str,
        description: str = "",
        corpus_ids: Optional[list[str]] = None,
    ) -> Project:
        """
        Update an existing project.

        Args:
            project_id: The project ID to update
            name: New project name (required)
            description: New project description (optional, max 256 chars)
            corpus_ids: New list of corpus IDs to associate with project

        Returns:
            Updated Project object

        Example:
            updated = client.v1.project.update(
                project_id="proj-123",
                name="Updated Name",
                description="Updated description",
                corpus_ids=["corpus-123", "corpus-456"]
            )
            print(f"Updated project: {updated.name}")
        """
        request = UpdateProjectRequest(
            name=name,
            description=description,
            corpus_ids=corpus_ids or [],
        )

        response = self._http.put(Routes.project(project_id), json=request.model_dump())
        return Project(**response)
        return Project(**response)

    def delete(self, project_id: str) -> None:
        """
        Delete a project.

        Args:
            project_id: The project ID to delete

        Example:
            client.v1.project.delete(project_id="proj-123")
            print("Project deleted successfully")
        """
        self._http.delete(Routes.project(project_id))
