"""V1 magickspace resource implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.magickspace import (
    AddMagickSpaceUsersRequest,
    ChatHistoryItem,
    ChatHistoryParams,
    ContextPrepareResponse,
    CorpusParams,
    CreateMagickSpaceRequest,
    FetcherParams,
    GetMagickSpaceListResponse,
    LivekitJoinResponse,
    LivekitTokenResponse,
    MagickSpace,
    MagickSpaceType,
    MagickSpaceMessagesResponse,
    SendMessageRequest,
    UpdateMagickSpaceRequest,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes

if TYPE_CHECKING:
    pass


class MagickSpacesResourceV1(BaseResource):
    """
    MagickSpace resource client for V1 API.

    Provides typed interface for managing magickspaces (organizational containers
    for chat conversations, corpus, and users).

    Example:
        # Create a private magickspace
        magickspace = await client.v1.magickspaces.create(
            name="My Workspace",
            type="private",
            description="Personal workspace",
            corpus_ids=["corp-123"]
        )

        # List all magickspaces
        magickspaces = await client.v1.magickspaces.list(user_id="user-456")

        # Get messages from magickspace
        messages = await client.v1.magickspaces.get_messages("mind-123", limit=50)
    """

    async def create(
        self,
        name: str,
        type: MagickSpaceType,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        corpus_ids: Optional[list[str]] = None,
        participant_ids: Optional[list[str]] = None,
    ) -> MagickSpace:
        """
        Create a new magickspace.
        Args:
            name: MagickSpace name (max 100 characters)
            type: MagickSpace type - either "PRIVATE" or "GROUP"
            description: Optional description (max 256 characters)
            project_id: Optional associated project ID
            corpus_ids: Optional list of corpus IDs to attach
            participant_ids: Optional list of participant IDs to grant access

        Returns:
            MagickSpace

        Raises:
            HTTPError: If the API request fails
            ValidationError: If parameters are invalid

        Example:
            # Create a group magickspace
            magickspace = await client.v1.magickspaces.create(
                name="Engineering Team",
                type="GROUP",
                description="Team collaboration space",
                corpus_ids=["corp-1", "corp-2"],
                participant_ids=["user-1", "user-2"]
            )
            print(f"Created magickspace: {magickspace.id}")
        """
        # Build and validate request
        request = CreateMagickSpaceRequest(
            name=name,
            type=type,
            description=description,
            project_id=project_id,
            corpus_ids=corpus_ids or [],
            participant_ids=participant_ids or [],
        )

        # Make API call
        response = await self._http.post(
            Routes.MAGICKSPACES, json=request.model_dump(exclude_none=True)
        )

        return MagickSpace.model_validate(response)

    async def get(self, magickspace_id: str) -> MagickSpace:
        """
        Get a magickspace by ID.

        Args:
            magickspace_id: MagickSpace ID to retrieve

        Returns:
            MagickSpace

        Raises:
            HTTPError: If the API request fails or magickspace not found

        Example:
            magickspace = await client.v1.magickspaces.get("mind-123")
            print(f"MagickSpace: {magickspace.name}")
            print(f"Type: {magickspace.type}")
            print(f"Corpus: {magickspace.corpus_ids}")
        """
        response_data = await self._http.get(Routes.magickspace(magickspace_id))
        return MagickSpace.model_validate(response_data)

    async def list(
        self,
        participant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        type: Optional[MagickSpaceType] = None,
        name: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> GetMagickSpaceListResponse:
        """
        List magickspaces, optionally filtered by various parameters.

        Args:
            participant_id: Optional participant ID to filter magickspaces
            project_id: Optional project ID to filter magickspaces
            type: Optional magickspace type filter ("PRIVATE" or "GROUP")
            name: Optional name filter
            cursor: Optional pagination cursor
            limit: Optional maximum number of results to return
            order: Optional sort order

        Returns:
            GetMagickSpaceListResponse with list of magickspaces

        Raises:
            HTTPError: If the API request fails

        Example:
            # List all magickspaces for a participant
            response = await client.v1.magickspaces.list(participant_id="user-456")
            for ms in response.magickspaces:
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

        response_data = await self._http.get(Routes.MAGICKSPACES, params=params)
        return GetMagickSpaceListResponse.model_validate(response_data)

    async def update(
        self,
        magickspace_id: str,
        name: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        corpus_ids: Optional[list[str]] = None,
        participant_ids: Optional[list[str]] = None,
    ) -> MagickSpace:
        """
        Update an existing magickspace.

        Args:
            magickspace_id: MagickSpace ID to update
            name: Updated magickspace name (max 100 characters)
            description: Updated description (max 256 characters)
            project_id: Updated associated project ID
            corpus_ids: Updated list of corpus IDs
            participant_ids: Updated list of participant IDs

        Returns:
            MagickSpace

        Raises:
            HTTPError: If the API request fails or magickspace not found
            ValidationError: If parameters are invalid

        Example:
            # Update magickspace to add more corpus
            magickspace = await client.v1.magickspaces.update(
                magickspace_id="mind-123",
                name="Engineering Team",
                corpus_ids=["corp-1", "corp-2", "corp-3"]
            )
            print(f"Updated: {magickspace.corpus_ids}")
        """
        # Build and validate request
        request = UpdateMagickSpaceRequest(
            name=name,
            description=description,
            project_id=project_id,
            corpus_ids=corpus_ids or [],
            participant_ids=participant_ids or [],
        )

        # Make API call
        response = await self._http.put(
            Routes.magickspace(magickspace_id),
            json=request.model_dump(exclude_none=True),
        )

        # Parse and validate response
        return MagickSpace.model_validate(response)

    async def delete(self, magickspace_id: str) -> None:
        """
        Delete a magickspace.

        Args:
            magickspace_id: MagickSpace ID to delete

        Raises:
            HTTPError: If the API request fails or magickspace not found

        Example:
            await client.v1.magickspaces.delete("mind-123")
            print("MagickSpace deleted successfully")
        """
        await self._http.delete(Routes.magickspace(magickspace_id))

    async def get_messages(
        self,
        magickspace_id: str,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> MagickSpaceMessagesResponse:
        """
        Fetch chat messages from a magickspace with cursor-based pagination.

        Args:
            magickspace_id: MagickSpace to fetch messages from
            cursor: Pagination cursor (from ``paging.cursors.after`` or ``.before``)
            limit: Maximum number of messages to return
            order: Sort order — ``"asc"`` or ``"desc"`` (default: asc)

        Returns:
            MagickSpaceMessagesResponse with messages and pagination cursors

        Raises:
            HTTPError: If the API request fails

        Example:
            # Get latest messages
            messages = await client.v1.magickspaces.get_messages("mind-123")
            for msg in messages.chat_histories:
                print(f"{msg.sent_by_user_id}: {msg.content}")

            # Next page
            if messages.has_more:
                page2 = await client.v1.magickspaces.get_messages(
                    "mind-123",
                    cursor=messages.next_after_id,
                )
        """
        params: dict[str, object] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order

        response_data = await self._http.get(
            Routes.magickspace_messages(magickspace_id),
            params=params if params else None,
        )

        return MagickSpaceMessagesResponse.model_validate(response_data)

    async def send_message(
        self,
        magickspace_id: str,
        *,
        content: str,
        sender_id: str,
        reply_to_message_id: Optional[str] = None,
        artifact_ids: Optional[list[str]] = None,
        message_type: str = "TEXT",
        broadcast: bool = True,
    ) -> ChatHistoryItem:
        """
        Send a message to a magickspace.

        Args:
            magickspace_id: MagickSpace ID to send message to
            content: Message content text
            sender_id: ID of the user sending the message
            reply_to_message_id: Optional ID of message being replied to
            artifact_ids: Optional list of artifact IDs to attach
            message_type: Message type (default: ``"TEXT"``)
            broadcast: Whether to broadcast via Centrifugo (default: True)

        Returns:
            ChatHistoryItem for the created message

        Raises:
            ProblemDetailsException: If the request fails

        Example:
            msg = await client.v1.magickspaces.send_message(
                "mind-123",
                content="Hello, world!",
                sender_id="user-456",
            )
            print(f"Sent message {msg.id}")
        """
        request = SendMessageRequest(
            content=content,
            sender_id=sender_id,
            reply_to_message_id=reply_to_message_id,
            artifact_ids=artifact_ids or [],
            message_type=message_type,
            broadcast=broadcast,
        )
        response = await self._http.post(
            Routes.magickspace_messages(magickspace_id),
            json=request.model_dump(exclude_none=True),
        )
        return ChatHistoryItem.model_validate(response)

    async def add_participants(
        self,
        magickspace_id: str,
        participant_ids: list[str],
    ) -> MagickSpace:
        """
        Add participants to an existing magickspace.

        Args:
            magickspace_id: MagickSpace ID to add participants to
            participant_ids: List of participant IDs to add to the magickspace

        Returns:
            MagickSpace with updated participant list

        Raises:
            HTTPError: If the API request fails or magickspace not found
            ValidationError: If parameters are invalid

        Example:
            # Add participants to a group magickspace
            magickspace = await client.v1.magickspaces.add_participants(
                magickspace_id="mind-123",
                participant_ids=["user-3", "user-4"]
            )
            print(f"Updated participants: {magickspace.participant_ids}")
        """
        # Build and validate request
        request = AddMagickSpaceUsersRequest(participant_ids=participant_ids)

        # Make API call
        response = await self._http.post(
            Routes.magickspace_users(magickspace_id),
            json=request.model_dump(exclude_none=True),
        )

        # Parse and validate response
        return MagickSpace.model_validate(response)

    async def add_users(
        self,
        magickspace_id: str,
        user_ids: list[str],
    ) -> MagickSpace:
        """
        Add users to an existing magickspace.

        .. deprecated::
            Use :meth:`add_participants` instead. This method will be removed in a future version.

        Args:
            magickspace_id: MagickSpace ID to add users to
            user_ids: List of user IDs to add to the magickspace

        Returns:
            MagickSpace with updated participant list
        """
        return await self.add_participants(magickspace_id, participant_ids=user_ids)

    async def prepare_context(
        self,
        magickspace_id: str,
        participant_id: str,
        chat_history: Optional[ChatHistoryParams] = None,
        corpus: Optional[CorpusParams] = None,
        pelican: Optional[FetcherParams] = None,
        api_key: Optional[str] = None,
    ) -> ContextPrepareResponse:
        """
        Retrieve multiple memory sources for a magickspace in a single call.

        Sources are queried in parallel on the server and bundled into one response.

        Args:
            magickspace_id: MagickSpace ID
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
            Routes.magickspace_context(magickspace_id),
            json=body,
            headers=headers if headers else None,
        )
        return ContextPrepareResponse.model_validate(response)

    async def get_livekit_token(
        self,
        magickspace_id: str,
        participant_id: str,
    ) -> LivekitTokenResponse:
        """
        Get a LiveKit access token for joining the magickspace room.

        Args:
            magickspace_id: MagickSpace ID (used as room name)
            participant_id: Participant identity for the token

        Returns:
            LivekitTokenResponse with token and URL
        """
        response = await self._http.post(
            Routes.magickspace_livekit_token(magickspace_id),
            json={"participant_id": participant_id},
        )
        return LivekitTokenResponse.model_validate(response)

    async def livekit_join(
        self,
        magickspace_id: str,
        participant_ids: list[str],
    ) -> LivekitJoinResponse:
        """
        Signal agents to join the LiveKit room for this magickspace.

        Args:
            magickspace_id: MagickSpace ID
            participant_ids: List of participant IDs to signal

        Returns:
            LivekitJoinResponse with list of signaled participants
        """
        response = await self._http.post(
            Routes.magickspace_livekit_join(magickspace_id),
            json={"participant_ids": participant_ids},
        )
        return LivekitJoinResponse.model_validate(response)
