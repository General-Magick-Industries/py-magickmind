"""
API Keys resource for Magick Mind SDK v1 API.

Provides methods for managing API keys for authenticated requests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.api_keys import (
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    DeleteApiKeyResponse,
    ListApiKeysResponse,
    UpdateApiKeyRequest,
    UpdateApiKeyResponse,
)
from magick_mind.routes import Routes

if TYPE_CHECKING:
    import httpx


class ApiKeysResourceV1:
    """Resource client for API key operations."""

    def __init__(self, http_client: httpx.Client):
        """
        Initialize the API keys resource.

        Args:
            http_client: Authenticated httpx client
        """
        self.http = http_client

    def create(
        self,
        user_id: str,
        project_id: str,
        models: list[str],
        key_alias: str,
        duration: Optional[str] = None,
        team_id: Optional[str] = None,
        max_budget: Optional[float] = None,
    ) -> CreateApiKeyResponse:
        """
        Create a new API key.

        Args:
            user_id: User ID that owns this key
            project_id: Project ID to associate with
            models: List of allowed model names
            key_alias: Human-readable key name
            duration: Optional validity duration (e.g., '30d', '1y')
            team_id: Optional team ID
            max_budget: Optional spending limit

        Returns:
            CreateApiKeyResponse with the new API key

        Raises:
            httpx.HTTPStatusError: If the request fails

        Example:
            >>> response = client.v1.api_keys.create(
            ...     user_id="user-123",
            ...     project_id="proj-456",
            ...     models=["gpt-4", "gpt-3.5-turbo"],
            ...     key_alias="Production Key",
            ...     duration="90d",
            ...     max_budget=100.0
            ... )
            >>> print(f"API Key: {response.key.key}")
        """
        payload = CreateApiKeyRequest(
            user_id=user_id,
            project_id=project_id,
            models=models,
            key_alias=key_alias,
            duration=duration,
            team_id=team_id,
            max_budget=max_budget,
        )

        resp = self.http.post(Routes.KEYS, json=payload.model_dump(exclude_none=True))
        resp.raise_for_status()

        return CreateApiKeyResponse(**resp.json())

    def list(self, user_id: str) -> ListApiKeysResponse:
        """
        List all API keys for a user.

        Args:
            user_id: User ID to list keys for

        Returns:
            ListApiKeysResponse with list of API keys

        Raises:
            httpx.HTTPStatusError: If the request fails

        Example:
            >>> response = client.v1.api_keys.list(user_id="user-123")
            >>> for key in response.keys:
            ...     print(f"{key.key_alias}: {key.key_id}")
        """
        resp = self.http.get(Routes.KEYS, params={"user_id": user_id})
        resp.raise_for_status()

        return ListApiKeysResponse(**resp.json())

    def update(
        self,
        key: str,
        models: list[str],
        key_alias: str,
        duration: Optional[str] = None,
        max_budget: Optional[float] = None,
    ) -> UpdateApiKeyResponse:
        """
        Update an existing API key.

        Args:
            key: The API key to update
            models: Updated list of allowed models
            key_alias: Updated key alias/name
            duration: Optional updated validity duration
            max_budget: Optional updated spending limit

        Returns:
            UpdateApiKeyResponse with updated key details

        Raises:
            httpx.HTTPStatusError: If the request fails

        Example:
            >>> response = client.v1.api_keys.update(
            ...     key="sk-...",
            ...     models=["gpt-4", "claude-3"],
            ...     key_alias="Updated Production Key",
            ...     max_budget=200.0
            ... )
        """
        payload = UpdateApiKeyRequest(
            key=key,
            models=models,
            key_alias=key_alias,
            duration=duration,
            max_budget=max_budget,
        )

        resp = self.http.put(Routes.KEYS, json=payload.model_dump(exclude_none=True))
        resp.raise_for_status()

        return UpdateApiKeyResponse(**resp.json())

    def delete(self, key_id: str) -> DeleteApiKeyResponse:
        """
        Delete an API key.

        Args:
            key_id: The key ID to delete

        Returns:
            DeleteApiKeyResponse with confirmation

        Raises:
            httpx.HTTPStatusError: If the request fails

        Example:
            >>> response = client.v1.api_keys.delete(key_id="key-abc-123")
            >>> print(response.message)
        """
        payload = {"key_id": key_id}

        resp = self.http.delete(Routes.KEYS, json=payload)
        resp.raise_for_status()

        return DeleteApiKeyResponse(**resp.json())
