"""
End user resource for Magick Mind SDK v1 API.

Provides methods for CRUD operations on end users in the agentic SaaS backend.
"""

from __future__ import annotations

from typing import Optional


from magick_mind.models.v1.end_user import (
    CreateEndUserRequest,
    EndUser,
    QueryEndUserResponse,
    UpdateEndUserRequest,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes


class EndUserResourceV1(BaseResource):
    """
    End user resource for managing end users in agentic SaaS applications.

    End users represent the actual users of applications built on the Magick Mind
    platform in a multi-tenant architecture.
    """

    async def create(
        self,
        name: str,
        external_id: Optional[str] = None,
    ) -> EndUser:
        """
        Create a new end user.

        Args:
            name: End user name (required)
            external_id: Optional external ID for mapping to external systems

        Returns:
            Created EndUser object

        Example:
            end_user = await client.v1.end_user.create(
                name="John Doe",
                external_id="ext-789"
            )
            print(f"Created end user: {end_user.id}")
        """
        request = CreateEndUserRequest(
            name=name,
            external_id=external_id,
        )

        response = await self._http.post(Routes.END_USERS, json=request.model_dump())
        return EndUser(**response)

    async def get(self, end_user_id: str) -> EndUser:
        """
        Get an end user by ID.

        Args:
            end_user_id: The end user ID to retrieve

        Returns:
            EndUser object

        Example:
            end_user = await client.v1.end_user.get(end_user_id="user-123")
            print(f"End user name: {end_user.name}")
        """
        response = await self._http.get(Routes.end_user(end_user_id))
        return EndUser(**response)

    async def query(
        self,
        name: Optional[str] = None,
        external_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> list[EndUser]:
        """
        Query end users with optional filters.

        All parameters are optional. If no filters are provided, returns all
        accessible end users.

        Args:
            name: Filter by end user name (optional)
            external_id: Filter by external ID (optional)
            cursor: Pagination cursor (optional)
            limit: Maximum number of results to return (optional)
            order: Sort order (optional)

        Returns:
            List of EndUser objects matching the query

        Example:
            # Search by name
            end_users = await client.v1.end_user.query(name="John")
            for user in end_users:
                print(f"- {user.name}")

            # Search by external ID
            user = await client.v1.end_user.query(external_id="ext-789")
        """
        params = {}
        if name is not None:
            params["name"] = name
        if external_id is not None:
            params["external_id"] = external_id
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order

        response = await self._http.get(Routes.END_USERS, params=params)
        query_response = QueryEndUserResponse(**response)
        return query_response.data

    async def update(
        self,
        end_user_id: str,
        name: Optional[str] = None,
        external_id: Optional[str] = None,
    ) -> EndUser:
        """
        Update an existing end user.

        All update fields are optional. Only provided fields will be updated.

        Args:
            end_user_id: The end user ID to update
            name: New end user name (optional)
            external_id: New external ID (optional)

        Returns:
            Updated EndUser object

        Example:
            updated = await client.v1.end_user.update(
                end_user_id="user-123",
                name="Jane Doe",
                external_id="new-ext-id"
            )
            print(f"Updated end user: {updated.name}")
        """
        request = UpdateEndUserRequest(
            name=name,
            external_id=external_id,
        )

        response = await self._http.put(
            Routes.end_user(end_user_id), json=request.model_dump(exclude_none=True)
        )
        return EndUser(**response)

    async def delete(self, end_user_id: str) -> None:
        """
        Delete an end user.

        Args:
            end_user_id: The end user ID to delete

        Example:
            await client.v1.end_user.delete(end_user_id="user-123")
            print("End user deleted successfully")
        """
        await self._http.delete(Routes.end_user(end_user_id))
