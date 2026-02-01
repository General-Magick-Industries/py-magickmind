"""
Project models for Magick Mind SDK v1 API.

Mirrors Bifrost's /v1/projects endpoint request/response schemas.
"""

from typing import TYPE_CHECKING, Optional, List

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from magick_mind.models.v1.end_user import PageInfo


class Project(BaseModel):
    """
    Project schema from Bifrost.

    Represents an agentic SaaS project with associated corpus IDs.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    corpus_ids: Optional[list[str]] = Field(
        None,
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


class GetProjectListResponse(BaseModel):
    """
    Response schema for listing projects.

    Matches Bifrost's {data: list[Project], paging: PageInfo} structure.
    """

    data: list[Project] = Field(..., description="List of projects")
    paging: "PageInfo" = Field(..., description="Pagination information")


GetProjectListResponse.model_rebuild()


class UpdateProjectRequest(BaseModel):
    """
    Request schema for updating a project.

    Both name and corpus_ids are REQUIRED (matching Bifrost API).
    """

    name: str = Field(..., description="Project name (required)")
    description: Optional[str] = Field(
        None, description="Project description (optional, max 256 chars)"
    )
    corpus_ids: list[str] = Field(
        ..., description="List of corpus IDs to associate with project (required)"
    )
