"""
Project models for Magick Mind SDK v1 API.

Mirrors Bifrost's /v1/projects endpoint request/response schemas.
"""

from pydantic import BaseModel, ConfigDict, Field


class Project(BaseModel):
    """
    Project schema from Bifrost.

    Represents an agentic SaaS project with associated corpus IDs.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    corpus_ids: list[str] = Field(
        default_factory=list,
        description="List of corpus IDs associated with this project",
    )
    created_by: str = Field(..., description="User ID of creator")
    created_at: str = Field(..., description="Creation timestamp (ISO8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO8601)")


class CreateProjectRequest(BaseModel):
    """
    Request schema for creating a new project.
    """

    name: str = Field(..., description="Project name (required)")
    description: str = Field(
        default="", description="Project description (optional, max 256 chars)"
    )
    corpus_ids: list[str] = Field(
        default_factory=list, description="List of corpus IDs to associate with project"
    )


class CreateProjectResponse(BaseModel):
    """
    Response schema for project creation.
    """

    project: Project = Field(..., description="Created project")


class GetProjectResponse(BaseModel):
    """
    Response schema for getting a single project.
    """

    project: Project = Field(..., description="Retrieved project")


class GetProjectListResponse(BaseModel):
    """
    Response schema for listing projects.
    """

    projects: list[Project] = Field(
        default_factory=list, description="List of projects"
    )


class UpdateProjectRequest(BaseModel):
    """
    Request schema for updating a project.
    """

    name: str = Field(..., description="Project name (required)")
    description: str = Field(
        default="", description="Project description (optional, max 256 chars)"
    )
    corpus_ids: list[str] = Field(
        default_factory=list, description="List of corpus IDs to associate with project"
    )


class UpdateProjectResponse(BaseModel):
    """
    Response schema for project update.
    """

    project: Project = Field(..., description="Updated project")
