"""
API Keys resource for Magick Mind SDK v1 API.

Provides methods for managing API keys for authenticated requests.
"""

from __future__ import annotations

from typing import Optional

from magick_mind.models.v1.api_keys import (
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    DeleteApiKeyResponse,
    ListApiKeysResponse,
    UpdateApiKeyRequest,
    UpdateApiKeyResponse,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes


class ApiKeysResourceV1(BaseResource):
    """Resource client for API key operations."""

    async def create(
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
            ProblemDetailsException: If the request fails

        Example:
            >>> response = await client.v1.api_keys.create(
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

        resp = await self._http.post(
            Routes.KEYS, json=payload.model_dump(exclude_none=True)
        )

        return CreateApiKeyResponse(**resp)

    async def list(self, user_id: str) -> ListApiKeysResponse:
        """
        List all API keys for a user.

        Args:
            user_id: User ID to list keys for

        Returns:
            ListApiKeysResponse with list of API keys

        Raises:
            ProblemDetailsException: If the request fails

        Example:
            >>> response = await client.v1.api_keys.list(user_id="user-123")
            >>> for key in response.keys:
            ...     print(f"{key.key_alias}: {key.key_id}")
        """
        resp = await self._http.get(Routes.KEYS, params={"user_id": user_id})

        return ListApiKeysResponse(**resp)

    async def update(
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
            ProblemDetailsException: If the request fails

        Example:
            >>> response = await client.v1.api_keys.update(
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

        resp = await self._http.put(
            Routes.KEYS, json=payload.model_dump(exclude_none=True)
        )

        return UpdateApiKeyResponse(**resp)

    async def delete(self, key_id: str) -> DeleteApiKeyResponse:
        """
        Delete an API key.

        Args:
            key_id: The key ID to delete

        Returns:
            DeleteApiKeyResponse with confirmation

        Raises:
            ProblemDetailsException: If the request fails

        Example:
            >>> response = await client.v1.api_keys.delete(key_id="key-abc-123")
            >>> print(response.message)
        """
        # DELETE with a JSON body — HTTPClient.delete() doesn't support a body,
        # so we drop down to the underlying httpx client and use _handle_response.
        await self._http.auth.refresh_if_needed_async()
        url = self._http._build_url(Routes.KEYS)
        headers = await self._http._get_headers()
        raw = await self._http._client.request(
            "DELETE",
            url,
            json={"key_id": key_id},
            headers=headers,
        )
        resp = self._http._handle_response(raw)

        return DeleteApiKeyResponse(**resp)
