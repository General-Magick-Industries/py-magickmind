"""
End user models for Magick Mind SDK v1 API.

Mirrors the /v1/end-users and /v1/end-user endpoint request/response schemas.
"""

from typing import ClassVar, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from magick_mind.models.common import PageInfo

ParticipantType = Literal["HUMAN", "AGENT"]


class EndUser(BaseModel):
    """
    End user schema from the platform.

    Represents an end user in a multi-tenant agentic SaaS application. An
    end user with ``participant_type == "AGENT"`` is an agent identity; its
    persona binding is ``persona_id`` plus ``active_persona_version_id``.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="End user ID")
    name: str = Field(..., description="End user name")
    external_id: Optional[str] = Field(
        default=None,
        description="Optional external ID for mapping to external systems",
    )
    persona_id: Optional[str] = Field(
        default=None, description="Persona permanently attached to this agent"
    )
    active_persona_version_id: Optional[str] = Field(
        default=None, description="Active version within the attached persona"
    )
    participant_type: Optional[str] = Field(default=None, description="HUMAN or AGENT")
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
    persona_id: Optional[str] = Field(
        default=None, description="Persona to attach at creation (agents)"
    )
    participant_type: Optional[ParticipantType] = Field(
        default=None, description="HUMAN (default) or AGENT"
    )


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


class AttachPersonaRequest(BaseModel):
    """Permanently attach a persona (at a given version) to an agent."""

    persona_id: str
    version_id: str


class SetAgentPersonaVersionRequest(BaseModel):
    """Change an agent's active version within its attached persona."""

    version_id: str


class MintEndUserTokenRequest(BaseModel):
    """Request schema for minting a scoped end-user JWT."""

    subject_id: str = Field(
        ..., description="End user ID the token is minted for (the token subject)"
    )
    ttl_seconds: Optional[int] = Field(
        default=None,
        description="Token lifetime in seconds; server default applies if omitted",
    )
    supervised: bool = Field(
        default=False,
        description=(
            "The caller owns the token lifecycle and will rotate it out of band; "
            "such a token is barred from the self-refresh route"
        ),
    )


class MintEndUserTokenResponse(BaseModel):
    """Response containing a minted end-user JWT."""

    token: str = Field(..., description="The signed end-user JWT")
    expires_at: str = Field(..., description="Expiry timestamp (RFC3339)")
    token_type: str = Field(default="Bearer", description="Token type, e.g. 'Bearer'")
    expires_in: Optional[int] = Field(
        default=None,
        description="Lifetime in seconds, for scheduling rotation without a clock",
    )


class RefreshEndUserTokenRequest(BaseModel):
    """Request schema for rotating the presented end-user JWT."""

    ttl_seconds: Optional[int] = Field(
        default=None,
        description="Lifetime of the new token; server default applies if omitted",
    )


class RevokeEndUserTokenRequest(BaseModel):
    """Request schema for revoking the calling agent's tokens."""

    disconnect: Optional[bool] = Field(
        default=None,
        description="Also drop live realtime connections (server default: true)",
    )


class RevokeEndUserTokenResponse(BaseModel):
    """Response from revoking the calling agent's tokens."""

    revoked: bool
    disconnected: bool = False
