"""
End user models for Magick Mind SDK v1 API.

Mirrors Bifrost's /v1/end-users endpoint request/response schemas.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from magick_mind.models.common import Cursors, PageInfo


class EndUser(BaseModel):
    """
    End user schema from Bifrost.

    Represents an end user in a multi-tenant agentic SaaS application.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="End user ID")
    name: str = Field(..., description="End user name")
    external_id: Optional[str] = Field(
        default=None,
        description="Optional external ID for mapping to external systems",
    )
    tenant_id: str = Field(..., description="Tenant ID this end user belongs to")
    created_by: Optional[str] = Field(default=None, description="User ID of creator")
    updated_by: Optional[str] = Field(
        default=None, description="User ID of last updater"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO8601)")


class CreateEndUserRequest(BaseModel):
    """
    Request schema for creating a new end user.
    """

    name: str = Field(..., description="End user name (required)")
    external_id: Optional[str] = Field(
        default=None,
        description="Optional external ID for mapping to external systems",
    )
    tenant_id: Optional[str] = Field(None, description="Tenant ID (Relaxed)")
    actor_id: Optional[str] = Field(None, description="Actor ID (Relaxed)")


class QueryEndUserResponse(BaseModel):
    """
    Response schema for querying end users.

    Uses new pagination pattern: {data: [], paging: {}}
    """

    data: list[EndUser] = Field(
        default_factory=list, description="List of end users matching the query"
    )
    paging: PageInfo = Field(..., description="Pagination information")


class UpdateEndUserRequest(BaseModel):
    """
    Request schema for updating an end user.
    """

    name: Optional[str] = Field(default=None, description="End user name (optional)")
    external_id: Optional[str] = Field(
        default=None,
        description="External ID for mapping to external systems (optional)",
    )
    tenant_id: Optional[str] = Field(None, description="Tenant ID (Relaxed)")
