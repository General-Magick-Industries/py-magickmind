"""V1 mindspace resource implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.mindspace import (
    AddMindSpaceUsersRequest,
    ChatHistoryParams,
    ContextPrepareResponse,
    CorpusParams,
    CreateMindSpaceRequest,
    FetcherParams,
    GetMindSpaceListResponse,
    LivekitJoinResponse,
    LivekitTokenResponse,
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
        mindspace = await client.v1.mindspace.create(
            name="My Workspace",
            type="private",
            description="Personal workspace",
            corpus_ids=["corp-123"]
        )

        # List all mindspaces
        mindspaces = await client.v1.mindspace.list(user_id="user-456")

        # Get messages from mindspace
        messages = await client.v1.mindspace.get_messages(
            mindspace_id="mind-123",
            limit=50
        )
    """

    async def create(
        self,
        name: str,
        type: MindSpaceType,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        corpus_ids: Optional[list[str]] = None,
        participant_ids: Optional[list[str]] = None,
    ) -> MindSpace:
        """
        Create a new mindspace.
        Args:
            name: Mindspace name (max 100 characters)
            type: Mindspace type - either "PRIVATE" or "GROUP"
            description: Optional description (max 256 characters)
            project_id: Optional associated project ID
            corpus_ids: Optional list of corpus IDs to attach
            participant_ids: Optional list of participant IDs to grant access

        Returns:
            MindSpace

        Raises:
            HTTPError: If the API request fails
            ValidationError: If parameters are invalid

        Example:
            # Create a group mindspace
            mindspace = await client.v1.mindspace.create(
                name="Engineering Team",
                type="GROUP",
                description="Team collaboration space",
                corpus_ids=["corp-1", "corp-2"],
                participant_ids=["user-1", "user-2"]
            )
            print(f"Created mindspace: {mindspace.id}")
        """
        # Build and validate request
        request = CreateMindSpaceRequest(
            name=name,
            type=type,
            description=description,
            project_id=project_id,
            corpus_ids=corpus_ids or [],
            participant_ids=participant_ids or [],
        )

        # Make API call
        response = await self._http.post(
            Routes.MINDSPACES, json=request.model_dump(exclude_none=True)
        )

        return MindSpace.model_validate(response)

    async def get(self, mindspace_id: str) -> MindSpace:
        """
        Get a mindspace by ID.

        Args:
            mindspace_id: Mindspace ID to retrieve

        Returns:
            MindSpace

        Raises:
            HTTPError: If the API request fails or mindspace not found

        Example:
            mindspace = await client.v1.mindspace.get("mind-123")
            print(f"Mindspace: {mindspace.name}")
            print(f"Type: {mindspace.type}")
            print(f"Corpus: {mindspace.corpus_ids}")
        """
        response_data = await self._http.get(Routes.mindspace(mindspace_id))
        return MindSpace.model_validate(response_data)

    async def list(
        self,
        participant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        type: Optional[MindSpaceType] = None,
        name: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> GetMindSpaceListResponse:
        """
        List mindspaces, optionally filtered by various parameters.

        Args:
            participant_id: Optional participant ID to filter mindspaces
            project_id: Optional project ID to filter mindspaces
            type: Optional mindspace type filter ("PRIVATE" or "GROUP")
            name: Optional name filter
            cursor: Optional pagination cursor
            limit: Optional maximum number of results to return
            order: Optional sort order

        Returns:
            GetMindSpaceListResponse with list of mindspaces

        Raises:
            HTTPError: If the API request fails

        Example:
            # List all mindspaces for a participant
            response = await client.v1.mindspace.list(participant_id="user-456")
            for ms in response.mindspaces:
                print(f"- {ms.name} ({ms.type})")
        """
        params: dict[str, object] = {}
        if participant_id is not None:
            params["participant_id"] = participant_id
        if project_id is not None:
            params["project_id"] = project_id
        if type is not None:
            params["type"] = type
        if name is not None:
            params["name"] = name
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order

        response_data = await self._http.get(Routes.MINDSPACES, params=params)
        return GetMindSpaceListResponse.model_validate(response_data)

    async def update(
        self,
        mindspace_id: str,
        name: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        corpus_ids: Optional[list[str]] = None,
        participant_ids: Optional[list[str]] = None,
    ) -> MindSpace:
        """
        Update an existing mindspace.

        Args:
            mindspace_id: Mindspace ID to update
            name: Updated mindspace name (max 100 characters)
            description: Updated description (max 256 characters)
            project_id: Updated associated project ID
            corpus_ids: Updated list of corpus IDs
            participant_ids: Updated list of participant IDs

        Returns:
            MindSpace

        Raises:
            HTTPError: If the API request fails or mindspace not found
            ValidationError: If parameters are invalid

        Example:
            # Update mindspace to add more corpus
            mindspace = await client.v1.mindspace.update(
                mindspace_id="mind-123",
                name="Engineering Team",
                corpus_ids=["corp-1", "corp-2", "corp-3"]
            )
            print(f"Updated: {mindspace.corpus_ids}")
        """
        # Build and validate request
        request = UpdateMindSpaceRequest(
            name=name,
            description=description,
            project_id=project_id,
            corpus_ids=corpus_ids or [],
            participant_ids=participant_ids or [],
        )

        # Make API call
        response = await self._http.put(
            Routes.mindspace(mindspace_id),
            json=request.model_dump(exclude_none=True),
        )

        # Parse and validate response
        return MindSpace.model_validate(response)

    async def delete(self, mindspace_id: str) -> None:
        """
        Delete a mindspace.

        Args:
            mindspace_id: Mindspace ID to delete

        Raises:
            HTTPError: If the API request fails or mindspace not found

        Example:
            await client.v1.mindspace.delete("mind-123")
            print("Mindspace deleted successfully")
        """
        await self._http.delete(Routes.mindspace(mindspace_id))

    async def get_messages(
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
            messages = await client.v1.mindspace.get_messages(
                mindspace_id="mind-123"
            )
            for msg in messages.chat_histories:
                print(f"{msg.sent_by_user_id}: {msg.content}")

            # Forward pagination (newer messages)
            if messages.has_more:
                more = await client.v1.mindspace.get_messages(
                    mindspace_id="mind-123",
                    after_id=messages.next_after_id,
                    limit=50
                )

            # Backward pagination (older messages)
            if messages.has_older:
                older = await client.v1.mindspace.get_messages(
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
        response_data = await self._http.get(Routes.MINDSPACE_MESSAGES, params=params)

        # Parse and return
        return MindspaceMessagesResponse.model_validate(response_data)

    async def add_participants(
        self,
        mindspace_id: str,
        participant_ids: list[str],
    ) -> MindSpace:
        """
        Add participants to an existing mindspace.

        Args:
            mindspace_id: Mindspace ID to add participants to
            participant_ids: List of participant IDs to add to the mindspace

        Returns:
            MindSpace with updated participant list

        Raises:
            HTTPError: If the API request fails or mindspace not found
            ValidationError: If parameters are invalid

        Example:
            # Add participants to a group mindspace
            mindspace = await client.v1.mindspace.add_participants(
                mindspace_id="mind-123",
                participant_ids=["user-3", "user-4"]
            )
            print(f"Updated participants: {mindspace.participant_ids}")
        """
        # Build and validate request
        request = AddMindSpaceUsersRequest(participant_ids=participant_ids)

        # Make API call
        response = await self._http.post(
            Routes.mindspace_users(mindspace_id),
            json=request.model_dump(exclude_none=True),
        )

        # Parse and validate response
        return MindSpace.model_validate(response)

    async def add_users(
        self,
        mindspace_id: str,
        user_ids: list[str],
    ) -> MindSpace:
        """
        Add users to an existing mindspace.

        .. deprecated::
            Use :meth:`add_participants` instead. This method will be removed in a future version.

        Args:
            mindspace_id: Mindspace ID to add users to
            user_ids: List of user IDs to add to the mindspace

        Returns:
            MindSpace with updated participant list
        """
        return await self.add_participants(mindspace_id, participant_ids=user_ids)

    async def prepare_context(
        self,
        mindspace_id: str,
        participant_id: str,
        chat_history: Optional[ChatHistoryParams] = None,
        corpus: Optional[CorpusParams] = None,
        pelican: Optional[FetcherParams] = None,
        api_key: Optional[str] = None,
    ) -> ContextPrepareResponse:
        """
        Retrieve multiple memory sources for a mindspace in a single call.

        Sources are queried in parallel on the server and bundled into one response.

        Args:
            mindspace_id: Mindspace ID
            participant_id: Participant ID (required)
            chat_history: Chat history params (limit)
            corpus: Corpus search params (query)
            pelican: Pelican episodic memory params (query). Requires api_key.
            api_key: API key required when using pelican fetcher (sent as x-api-key header)

        Returns:
            ContextPrepareResponse
        """
        body: dict[str, object] = {"participant_id": participant_id}
        if chat_history:
            body["chat_history"] = chat_history.model_dump(exclude_none=True)
        if corpus:
            body["corpus"] = corpus.model_dump()
        if pelican:
            body["pelican"] = pelican.model_dump()

        headers = {}
        if api_key:
            headers["x-api-key"] = api_key

        response = await self._http.post(
            Routes.mindspace_context(mindspace_id),
            json=body,
            headers=headers if headers else None,
        )
        return ContextPrepareResponse.model_validate(response)

    async def get_livekit_token(
        self,
        mindspace_id: str,
        participant_id: str,
    ) -> LivekitTokenResponse:
        """
        Get a LiveKit access token for joining the mindspace room.

        Args:
            mindspace_id: Mindspace ID (used as room name)
            participant_id: Participant identity for the token

        Returns:
            LivekitTokenResponse with token and URL
        """
        response = await self._http.post(
            Routes.mindspace_livekit_token(mindspace_id),
            json={"participant_id": participant_id},
        )
        return LivekitTokenResponse.model_validate(response)

    async def livekit_join(
        self,
        mindspace_id: str,
        participant_ids: list[str],
    ) -> LivekitJoinResponse:
        """
        Signal agents to join the LiveKit room for this mindspace.

        Args:
            mindspace_id: Mindspace ID
            participant_ids: List of participant IDs to signal

        Returns:
            LivekitJoinResponse with list of signaled participants
        """
        response = await self._http.post(
            Routes.mindspace_livekit_join(mindspace_id),
            json={"participant_ids": participant_ids},
        )
        return LivekitJoinResponse.model_validate(response)
