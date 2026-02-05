"""V1 mindspace resource implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.mindspace import (
    AddMindSpaceUsersRequest,
    CreateMindSpaceRequest,
    GetMindSpaceListResponse,
    MindSpace,
    MindSpaceType,
    MindSpace,
    MindSpaceType,
    MindspaceMessagesResponse,
    UpdateMindSpaceRequest,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes

if TYPE_CHECKING:
    from magick_mind.http import HTTPClient


class MindspaceResourceV1(BaseResource):
    """
    Mindspace resource client for V1 API.

    Provides typed interface for managing mindspaces (organizational containers
    for chat conversations, corpus, and users).

    Example:
        # Create a private mindspace
        mindspace = client.v1.mindspace.create(
            name="My Workspace",
            type="private",
            description="Personal workspace",
            corpus_ids=["corp-123"]
        )

        # List all mindspaces
        mindspaces = client.v1.mindspace.list(user_id="user-456")

        # Get messages from mindspace
        messages = client.v1.mindspace.get_messages(
            mindspace_id="mind-123",
            limit=50
        )
    """

    def create(
        self,
        name: str,
        type: MindSpaceType,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        corpus_ids: Optional[list[str]] = None,
        user_ids: Optional[list[str]] = None,
    ) -> MindSpace:
    ) -> MindSpace:
        """
        Create a new mindspace.
        Args:
            name: Mindspace name (max 100 characters)
            type: Mindspace type - either "PRIVATE" or "GROUP"
            type: Mindspace type - either "PRIVATE" or "GROUP"
            description: Optional description (max 256 characters)
            project_id: Optional associated project ID
            corpus_ids: Optional list of corpus IDs to attach
            user_ids: Optional list of user IDs to grant access

        Returns:
            MindSpace
            MindSpace

        Raises:
            HTTPError: If the API request fails
            ValidationError: If parameters are invalid

        Example:
            # Create a group mindspace
            mindspace = client.v1.mindspace.create(
            mindspace = client.v1.mindspace.create(
                name="Engineering Team",
                type="GROUP",
                type="GROUP",
                description="Team collaboration space",
                corpus_ids=["corp-1", "corp-2"],
                user_ids=["user-1", "user-2"]
            )
            print(f"Created mindspace: {mindspace.id}")
            print(f"Created mindspace: {mindspace.id}")
        """
        # Build and validate request
        request = CreateMindSpaceRequest(
            name=name,
            type=type,
            description=description,
            project_id=project_id,
            corpus_ids=corpus_ids or [],
            user_ids=user_ids or [],
        )

        # Make API call
        response = self._http.post(
            Routes.MINDSPACES, json=request.model_dump(exclude_none=True)
        )

        return MindSpace.model_validate(response)

    def get(self, mindspace_id: str) -> MindSpace:
    def get(self, mindspace_id: str) -> MindSpace:
        """
        Get a mindspace by ID.

        Args:
            mindspace_id: Mindspace ID to retrieve

        Returns:
            MindSpace
            MindSpace

        Raises:
            HTTPError: If the API request fails or mindspace not found

        Example:
            mindspace = client.v1.mindspace.get("mind-123")
            print(f"Mindspace: {mindspace.name}")
            print(f"Type: {mindspace.type}")
            print(f"Corpus: {mindspace.corpus_ids}")
            mindspace = client.v1.mindspace.get("mind-123")
            print(f"Mindspace: {mindspace.name}")
            print(f"Type: {mindspace.type}")
            print(f"Corpus: {mindspace.corpus_ids}")
        """
        response_data = self._http.get(Routes.mindspace(mindspace_id))
        return MindSpace.model_validate(response_data)

    def list(self, user_id: Optional[str] = None) -> GetMindSpaceListResponse:
        """
        List mindspaces, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter mindspaces

        Returns:
            GetMindSpaceListResponse with list of mindspaces

        Raises:
            HTTPError: If the API request fails

        Example:
            # List all mindspaces for a user
            response = client.v1.mindspace.list(user_id="user-456")
            for ms in response.mindspaces:
                print(f"- {ms.name} ({ms.type})")
        """
        params = {}
        if user_id:
            params["user_id"] = user_id

        response_data = self._http.get(Routes.MINDSPACES, params=params)
        return GetMindSpaceListResponse.model_validate(response_data)

    def update(
        self,
        mindspace_id: str,
        name: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        corpus_ids: Optional[list[str]] = None,
        user_ids: Optional[list[str]] = None,
    ) -> MindSpace:
    ) -> MindSpace:
        """
        Update an existing mindspace.

        Args:
            mindspace_id: Mindspace ID to update
            name: Updated mindspace name (max 100 characters)
            description: Updated description (max 256 characters)
            project_id: Updated associated project ID
            corpus_ids: Updated list of corpus IDs
            user_ids: Updated list of user IDs

        Returns:
            MindSpace
            MindSpace

        Raises:
            HTTPError: If the API request fails or mindspace not found
            ValidationError: If parameters are invalid

        Example:
            # Update mindspace to add more corpus
            mindspace = client.v1.mindspace.update(
            mindspace = client.v1.mindspace.update(
                mindspace_id="mind-123",
                name="Engineering Team",
                corpus_ids=["corp-1", "corp-2", "corp-3"]
            )
            print(f"Updated: {mindspace.corpus_ids}")
            print(f"Updated: {mindspace.corpus_ids}")
        """
        # Build and validate request
        request = UpdateMindSpaceRequest(
            name=name,
            description=description,
            project_id=project_id,
            corpus_ids=corpus_ids or [],
            user_ids=user_ids or [],
        )

        # Make API call
        response = self._http.put(
            Routes.mindspace(mindspace_id),
            json=request.model_dump(exclude_none=True),
        )

        # Parse and validate response
        return MindSpace.model_validate(response)

    def delete(self, mindspace_id: str) -> None:
        """
        Delete a mindspace.

        Args:
            mindspace_id: Mindspace ID to delete

        Raises:
            HTTPError: If the API request fails or mindspace not found

        Example:
            client.v1.mindspace.delete("mind-123")
            print("Mindspace deleted successfully")
        """
        self._http.delete(Routes.mindspace(mindspace_id))

    def get_messages(
        self,
        mindspace_id: str,
        after_id: Optional[str] = None,
        before_id: Optional[str] = None,
        limit: int = 50,
    ) -> MindspaceMessagesResponse:
        """
        Fetch chat messages from a mindspace with keyset pagination.

        Three modes based on parameters:
        - Latest: Just mindspace_id + limit (most recent messages)
        - Forward: mindspace_id + after_id + limit (messages after a point)
        - Backward: mindspace_id + before_id + limit (messages before a point)

        Args:
            mindspace_id: Mindspace to fetch messages from
            after_id: Get messages after this message ID (forward pagination)
            before_id: Get messages before this message ID (backward pagination)
            limit: Maximum number of messages to return (default: 50)

        Returns:
            MindspaceMessagesResponse with messages and pagination cursors

        Raises:
            ValueError: If both after_id and before_id are provided
            HTTPError: If the API request fails

        Example:
            # Get latest 50 messages
            messages = client.v1.mindspace.get_messages(
                mindspace_id="mind-123"
            )
            for msg in messages.chat_histories:
                print(f"{msg.sent_by_user_id}: {msg.content}")

            # Forward pagination (newer messages)
            if messages.has_more:
                more = client.v1.mindspace.get_messages(
                    mindspace_id="mind-123",
                    after_id=messages.next_after_id,
                    limit=50
                )

            # Backward pagination (older messages)
            if messages.has_older:
                older = client.v1.mindspace.get_messages(
                    mindspace_id="mind-123",
                    before_id=messages.next_before_id,
                    limit=50
                )
        """
        # Validate mutually exclusive parameters
        if after_id and before_id:
            raise ValueError("Cannot specify both after_id and before_id")

        # Build query parameters
        params = {
            "mindspace_id": mindspace_id,
            "limit": limit,
        }

        if after_id:
            params["after_id"] = after_id
        if before_id:
            params["before_id"] = before_id

        # Make request
        response_data = self._http.get(Routes.MINDSPACE_MESSAGES, params=params)

        # Parse and return
        return MindspaceMessagesResponse.model_validate(response_data)

    def add_users(
        self,
        mindspace_id: str,
        user_ids: list[str],
    ) -> MindSpace:
        """
        Add users to an existing mindspace.

        Args:
            mindspace_id: Mindspace ID to add users to
            user_ids: List of user IDs to add to the mindspace

        Returns:
            MindSpace with updated user list

        Raises:
            HTTPError: If the API request fails or mindspace not found
            ValidationError: If parameters are invalid

        Example:
            # Add users to a group mindspace
            mindspace = client.v1.mindspace.add_users(
                mindspace_id="mind-123",
                user_ids=["user-3", "user-4"]
            )
            print(f"Updated users: {mindspace.user_ids}")
        """
        # Build and validate request
        request = AddMindSpaceUsersRequest(user_ids=user_ids)

        # Make API call
        response = self._http.post(
            Routes.mindspace_users(mindspace_id),
            json=request.model_dump(exclude_none=True),
        )

        # Parse and validate response
        return MindSpace.model_validate(response)
