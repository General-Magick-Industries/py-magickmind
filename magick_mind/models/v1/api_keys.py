"""
API Keys models for Magick Mind SDK v1 API.

Provides Pydantic models for creating and managing API keys
for authenticating requests to the Bifrost backend.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiKey(BaseModel):
    """
    API key metadata (does not include the actual key value).

    Represents an API key for making authenticated requests.
    """

    model_config = ConfigDict(extra="allow")

    key_id: str = Field(..., description="Unique key identifier")
    key_alias: str = Field(..., description="Human-readable key alias/name")
    user_id: str = Field(..., description="Owner user ID")
    project_id: str = Field(..., description="Associated project ID")
    update_at: str = Field(..., description="Last update timestamp")
    create_at: str = Field(..., description="Creation timestamp")


class KeyResponse(BaseModel):
    """
    Response containing the actual API key value.

    Only returned when creating or updating a key.
    """

    model_config = ConfigDict(extra="allow")

    key: str = Field(..., description="The actual API key (only shown once)")
    key_alias: str = Field(..., description="Key alias/name")
    key_id: str = Field(..., description="Key identifier")
    expires: str = Field(..., description="Expiration timestamp")


class CreateApiKeyRequest(BaseModel):
    """Request for creating a new API key."""

    user_id: str = Field(..., description="User ID that owns this key")
    project_id: str = Field(..., description="Project ID to associate with")
    models: list[str] = Field(..., description="List of allowed model names")
    key_alias: str = Field(..., description="Human-readable key name")
    duration: Optional[str] = Field(
        None, description="Key validity duration (e.g., '30d', '1y')"
    )
    team_id: Optional[str] = Field(None, description="Optional team ID")
    max_budget: Optional[float] = Field(None, description="Optional spending limit")


class CreateApiKeyResponse(BaseModel):
    """Response for API key creation."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    key: KeyResponse = Field(..., description="The created API key details")


class ListApiKeysResponse(BaseModel):
    """Response for listing API keys."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    keys: list[ApiKey] = Field(..., description="List of API keys (metadata only)")


class UpdateApiKeyRequest(BaseModel):
    """Request for updating an existing API key."""

    key: str = Field(..., description="The API key to update")
    models: list[str] = Field(..., description="Updated list of allowed models")
    key_alias: str = Field(..., description="Updated key alias/name")
    duration: Optional[str] = Field(None, description="Updated validity duration")
    max_budget: Optional[float] = Field(None, description="Updated spending limit")


class UpdateApiKeyResponse(BaseModel):
    """Response for API key update."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    key: KeyResponse = Field(..., description="The updated API key details")


class DeleteApiKeyRequest(BaseModel):
    """Request for deleting an API key."""

    key_id: str = Field(..., description="Key ID to delete")


class DeleteApiKeyResponse(BaseModel):
    """Response for API key deletion."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Deletion confirmation message")
