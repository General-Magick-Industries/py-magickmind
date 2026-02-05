"""V1 mindspace API models.

These models mirror the bifrost API types for /v1/mindspaces endpoint.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from magick_mind.models.common import BaseResponse, PageInfo
from magick_mind.models.v1.history import HistoryResponse


# Type alias for mindspace type enum (uppercase to match apidog)
MindSpaceType = Literal["PRIVATE", "GROUP"]


class MindSpace(BaseModel):
    """
    Mindspace schema model.

    Represents a mindspace container that can be private (single user)
    or group (multiple users), with attached corpus for knowledge.

    Example:
        {
            "id": "mind-123",
            "name": "Engineering Team",
            "description": "Team workspace",
            "project_id": "proj-456",
            "corpus_ids": ["corp-1", "corp-2"],
            "user_ids": ["user-1", "user-2"],
            "type": "GROUP",
            "created_by": "user-1",
            "updated_by": "user-1",
            "created_at": "2025-12-16T09:00:00Z",
            "updated_at": "2025-12-16T09:00:00Z"
        }
    """

    id: str = Field(..., description="Mindspace ID")
    name: str = Field(..., description="Mindspace name")
    description: Optional[str] = Field(None, description="Mindspace description")
    project_id: str = Field(..., description="Associated project ID")
    corpus_ids: list[str] = Field(
        default_factory=list,
        description="List of corpus IDs attached to this mindspace",
    )
    user_ids: list[str] = Field(
        default_factory=list,
        description="List of user IDs with access to this mindspace",
    )
    type: MindSpaceType = Field(..., description="Mindspace type: 'PRIVATE' or 'GROUP'")
    created_by: Optional[str] = Field(
        None, description="User ID who created the mindspace"
    )
    updated_by: Optional[str] = Field(
        None, description="User ID who last updated the mindspace"
    )
    created_at: Optional[str] = Field(None, description="Creation timestamp (RFC3339)")
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp (RFC3339)"
    )


class CreateMindSpaceRequest(BaseModel):
    """
    Request to create a new mindspace.
    """

    name: Optional[str] = Field(
        None, description="Mindspace name (Relaxed)", max_length=100
    )
    type: Optional[MindSpaceType] = Field(None, description="Mindspace type (Relaxed)")
    description: Optional[str] = Field(
        default=None, description="Mindspace description", max_length=256
    )
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    corpus_ids: list[str] = Field(
        default_factory=list, description="List of corpus IDs to attach"
    )
    user_ids: list[str] = Field(
        default_factory=list, description="List of user IDs to grant access"
    )


class GetMindSpaceListResponse(BaseModel):
    """
    Response from listing mindspaces.

    Uses standardized Bifrost pagination format: {data: [], paging: {}}.
    """

    data: list[MindSpace] = Field(
        default_factory=list, description="List of mindspaces"
    )
    paging: PageInfo = Field(..., description="Pagination information")

    @property
    def mindspaces(self) -> list[MindSpace]:
        """Alias for data field (backward compatibility)."""
        return self.data


class UpdateMindSpaceRequest(BaseModel):
    """
    Request to update an existing mindspace.
    """

    name: Optional[str] = Field(
        None, description="Mindspace name (Relaxed)", max_length=100
    )
    description: Optional[str] = Field(
        default=None, description="Mindspace description", max_length=256
    )
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    corpus_ids: list[str] = Field(
        default_factory=list, description="List of corpus IDs to attach"
    )
    user_ids: list[str] = Field(
        default_factory=list, description="List of user IDs to grant access"
    )


class AddMindSpaceUsersRequest(BaseModel):
    """
    Request to add users to an existing mindspace.
    """

    user_ids: list[str] = Field(
        ..., description="List of user IDs to add to the mindspace"
    )


# Reuse HistoryResponse for messages endpoint since it's the same structure
MindspaceMessagesResponse = HistoryResponse
