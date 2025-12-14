"""
End user resource for Magick Mind SDK v1 API.

Provides methods for CRUD operations on end users in the agentic SaaS backend.
"""

from __future__ import annotations

from typing import Optional


from magick_mind.models.v1.end_user import (
    CreateEndUserRequest,
    CreateEndUserResponse,
    EndUser,
    GetEndUserResponse,
    QueryEndUserResponse,
    UpdateEndUserRequest,
    UpdateEndUserResponse,
)
from magick_mind.resources.base import BaseResource


class EndUserResourceV1(BaseResource):
    """
    End user resource for managing end users in agentic SaaS applications.

    End users represent the actual users of applications built on the bifrost
    platform in a multi-tenant architecture.
    """

    def create(
        self,
        name: str,
        tenant_id: str,
        actor_id: str,
        external_id: Optional[str] = None,
    ) -> EndUser:
        """
        Create a new end user.

        Args:
            name: End user name (required)
            tenant_id: Tenant ID this end user belongs to (required)
            actor_id: Actor ID performing the action (required)
            external_id: Optional external ID for mapping to external systems

        Returns:
            Created EndUser object

        Example:
            end_user = client.v1.end_user.create(
                name="John Doe",
                tenant_id="tenant-123",
                actor_id="user-456",
                external_id="ext-789"
            )
            print(f"Created end user: {end_user.id}")
        """
        request = CreateEndUserRequest(
            name=name,
            tenant_id=tenant_id,
            actor_id=actor_id,
            external_id=external_id,
        )

        response = self._http.post("/v1/end-users", json=request.model_dump())
        create_response = CreateEndUserResponse(**response.json())
        return create_response.end_user

    def get(self, end_user_id: str) -> EndUser:
        """
        Get an end user by ID.

        Args:
            end_user_id: The end user ID to retrieve

        Returns:
            EndUser object

        Example:
            end_user = client.v1.end_user.get(end_user_id="user-123")
            print(f"End user name: {end_user.name}")
        """
        response = self._http.get(f"/v1/end-users/{end_user_id}")
        get_response = GetEndUserResponse(**response.json())
        return get_response.end_user

    def query(
        self,
        name: Optional[str] = None,
        external_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> list[EndUser]:
        """
        Query end users with optional filters.

        All parameters are optional. If no filters are provided, returns all
        accessible end users.

        Args:
            name: Filter by end user name (optional)
            external_id: Filter by external ID (optional)
            tenant_id: Filter by tenant ID (optional)
            actor_id: Filter by actor ID (optional)

        Returns:
            List of EndUser objects matching the query

        Example:
            # Get all end users for a tenant
            end_users = client.v1.end_user.query(tenant_id="tenant-123")
            for user in end_users:
                print(f"- {user.name}")

            # Search by external ID
            user = client.v1.end_user.query(external_id="ext-789")
        """
        params = {}
        if name is not None:
            params["name"] = name
        if external_id is not None:
            params["external_id"] = external_id
        if tenant_id is not None:
            params["tenant_id"] = tenant_id
        if actor_id is not None:
            params["actor_id"] = actor_id

        response = self._http.get("/v1/end-users", params=params)
        query_response = QueryEndUserResponse(**response.json())
        return query_response.end_users

    def update(
        self,
        end_user_id: str,
        name: Optional[str] = None,
        external_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> EndUser:
        """
        Update an existing end user.

        All update fields are optional. Only provided fields will be updated.

        Args:
            end_user_id: The end user ID to update
            name: New end user name (optional)
            external_id: New external ID (optional)
            tenant_id: New tenant ID (optional)

        Returns:
            Updated EndUser object

        Example:
            updated = client.v1.end_user.update(
                end_user_id="user-123",
                name="Jane Doe",
                external_id="new-ext-id"
            )
            print(f"Updated end user: {updated.name}")
        """
        request = UpdateEndUserRequest(
            name=name,
            external_id=external_id,
            tenant_id=tenant_id,
        )

        response = self._http.put(
            f"/v1/end-users/{end_user_id}", json=request.model_dump(exclude_none=True)
        )
        update_response = UpdateEndUserResponse(**response.json())
        return update_response.end_user

    def delete(self, end_user_id: str) -> None:
        """
        Delete an end user.

        Args:
            end_user_id: The end user ID to delete

        Example:
            client.v1.end_user.delete(end_user_id="user-123")
            print("End user deleted successfully")
        """
        self._http.delete(f"/v1/end-users/{end_user_id}")
