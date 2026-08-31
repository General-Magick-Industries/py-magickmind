"""V1 mindspace resource implementation."""

from __future__ import annotations

from typing import Any, Optional

from magick_mind.exceptions import MagickMindError, reraise_with_hint
from magick_mind.models.v1.mindspace import (
    AddMindSpaceUsersRequest,
    ChatHistoryItem,
    ChatHistoryParams,
    ContextPrepareResponse,
    CorpusParams,
    CreateMindSpaceRequest,
    EndUserSendMessageRequest,
    FetcherParams,
    GetMindSpaceListResponse,
    LivekitJoinResponse,
    LivekitTokenResponse,
    MessageType,
    MindSpace,
    MindSpaceType,
    MindspaceMessagesResponse,
    SendMessageRequest,
    UpdateMindSpaceRequest,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes

_END_USER_ROUTE_HINTS = {
    401: (
        "hint: this route needs a valid, unrevoked end-user JWT; with "
        "service-user credentials use the non-_own method"
    ),
    403: "hint: the calling agent is not a participant of this magickspace",
    404: "hint: magickspace not found",
}


def _messages_params(
    cursor: Optional[str], limit: Optional[int], order: Optional[str]
) -> Optional[dict[str, object]]:
    params: dict[str, object] = {}
    if cursor is not None:
        params["cursor"] = cursor
    if limit is not None:
        params["limit"] = limit
    if order is not None:
        params["order"] = order
    return params or None


class MindspaceResourceV1(BaseResource):
    """
    Mindspace resource client for V1 API.

    Provides typed interface for managing mindspaces (organizational containers
    for chat conversations, corpus, and users).

    Example:
        # Create a private mindspace
        mindspace = await client.v1.magickspaces.create(
            name="My Workspace",
            type="private",
            description="Personal workspace",
            corpus_ids=["corp-123"]
        )

        # List all mindspaces
        mindspaces = await client.v1.magickspaces.list(user_id="user-456")

        # Get messages from mindspace
        messages = await client.v1.magickspaces.get_messages("mind-123", limit=50)
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
            mindspace = await client.v1.magickspaces.create(
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
            Routes.MAGICKSPACES, json=request.model_dump(exclude_none=True)
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
            mindspace = await client.v1.magickspaces.get("mind-123")
            print(f"Mindspace: {mindspace.name}")
            print(f"Type: {mindspace.type}")
            print(f"Corpus: {mindspace.corpus_ids}")
        """
        response_data = await self._http.get(Routes.magickspace(mindspace_id))
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
            response = await client.v1.magickspaces.list(participant_id="user-456")
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

        response_data = await self._http.get(Routes.MAGICKSPACES, params=params)
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
            mindspace = await client.v1.magickspaces.update(
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
            Routes.magickspace(mindspace_id),
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
            await client.v1.magickspaces.delete("mind-123")
            print("Mindspace deleted successfully")
        """
        await self._http.delete(Routes.magickspace(mindspace_id))

    async def get_messages(
        self,
        mindspace_id: str,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> MindspaceMessagesResponse:
        """
        Fetch chat messages from a mindspace with cursor-based pagination.

        Args:
            mindspace_id: Mindspace to fetch messages from
            cursor: Pagination cursor (from ``paging.cursors.after`` or ``.before``)
            limit: Maximum number of messages to return
            order: Sort order — ``"asc"`` or ``"desc"`` (default: asc)

        Returns:
            MindspaceMessagesResponse with messages and pagination cursors

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
        response_data = await self._http.get(
            Routes.magickspace_messages(mindspace_id),
            params=_messages_params(cursor, limit, order),
        )

        return MindspaceMessagesResponse.model_validate(response_data)

    async def send_message(
        self,
        mindspace_id: str,
        *,
        content: str,
        sender_id: str,
        reply_to_message_id: Optional[str] = None,
        artifact_ids: Optional[list[str]] = None,
        message_type: str = "TEXT",
        broadcast: bool = True,
        record_neutral_memory: bool = False,
        client_message_id: Optional[str] = None,
    ) -> ChatHistoryItem:
        """
        Send a message to a mindspace.

        Note that this service-user route broadcasts to ``personal:`` channels
        only, which agents never hear. A message meant to reach agents must be
        sent as an end user through :meth:`send_own_message`.

        Args:
            mindspace_id: Mindspace ID to send message to
            content: Message content text
            sender_id: ID of the user sending the message
            reply_to_message_id: Optional ID of message being replied to
            artifact_ids: Optional list of artifact IDs to attach
            message_type: Message type (default: ``"TEXT"``)
            broadcast: Whether to broadcast via Centrifugo (default: True)
            record_neutral_memory: Also write to the space's unowned episodic
                memory
            client_message_id: Idempotency key, unique per (magickspace,
                sender). A reused key returns the ORIGINAL message with
                ``deduplicated=True`` and drops the new content; use a UUID.

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
            record_neutral_memory=record_neutral_memory,
            client_message_id=client_message_id,
        )
        response = await self._http.post(
            Routes.magickspace_messages(mindspace_id),
            json=request.model_dump(exclude_none=True),
        )
        return ChatHistoryItem.model_validate(response)

    async def list_own(
        self,
        *,
        project_id: Optional[str] = None,
        type: Optional[MindSpaceType] = None,
        name: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> GetMindSpaceListResponse:
        """
        List the magickspaces the calling agent participates in (end-user JWT).

        The participant is the token subject, so unlike :meth:`list` there is
        no ``participant_id`` to supply.
        """
        params: dict[str, object] = {}
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

        try:
            response = await self._http.get(Routes.END_USER_MAGICKSPACES, params=params)
        except MagickMindError as exc:
            if exc.status_code == 401:
                reraise_with_hint(exc, _END_USER_ROUTE_HINTS[401])
            raise
        return GetMindSpaceListResponse.model_validate(response)

    async def get_own_messages(
        self,
        magickspace_id: str,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> MindspaceMessagesResponse:
        """
        Fetch messages of a magickspace the calling agent participates in
        (end-user JWT). Same pagination as :meth:`get_messages`; ``limit`` is
        capped at 200 server-side.
        """
        try:
            response = await self._http.get(
                Routes.end_user_magickspace_messages(magickspace_id),
                params=_messages_params(cursor, limit, order),
            )
        except MagickMindError as exc:
            if exc.status_code is not None and exc.status_code in _END_USER_ROUTE_HINTS:
                reraise_with_hint(exc, _END_USER_ROUTE_HINTS[exc.status_code])
            raise
        return MindspaceMessagesResponse.model_validate(response)

    async def send_own_message(
        self,
        magickspace_id: str,
        *,
        content: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        artifact_ids: Optional[list[str]] = None,
        message_type: MessageType = "TEXT",
        broadcast: bool = True,
        tools: Optional[list[dict[str, Any]]] = None,
        context: Optional[dict[str, str]] = None,
    ) -> ChatHistoryItem:
        """
        Send a message as the calling agent, fanned out to every participant
        (end-user JWT).

        This is the only send that reaches agents: it publishes to each
        participant's ``user:`` channel as well as the legacy ``personal:``
        channel. The sender is the token subject, so there is no ``sender_id``.

        Args:
            magickspace_id: Magickspace to send to
            content: Message text (max 32 KiB). May be omitted for an
                attachment-only send, or for a ``SIGNAL_*`` indicator; a
                request with neither content nor artifacts is rejected
            reply_to_message_id: Optional ID of the message being replied to
            artifact_ids: Optional artifact IDs to attach (max 64)
            message_type: ``TEXT`` (default), ``VOICE_TRANSCRIPTION``, the
                ``TOOL_*`` protocol types, or a ``SIGNAL_START`` /
                ``SIGNAL_END`` / ``SIGNAL_ERROR`` turn indicator. Signals and
                manifests are fanned out but never persisted
            broadcast: Whether to fan out via Centrifugo (default: True)
            tools: The sender's live tool manifest for this turn, one
                ``{name, description, schema}`` per tool (max 32). Fan-out
                only; never persisted
            context: Per-turn key/value context replayed into the receiving
                agent's prompt (max 32 entries). Fan-out only

        Returns:
            ChatHistoryItem for the created message

        Raises:
            MagickMindError: 401 with service-user credentials or a revoked
                token, 403 if the agent is not a participant, 404 if the
                magickspace does not exist
        """
        request = EndUserSendMessageRequest(
            content=content,
            reply_to_message_id=reply_to_message_id,
            artifact_ids=artifact_ids or [],
            message_type=message_type,
            broadcast=broadcast,
            tools=tools,
            context=context,
        )
        try:
            response = await self._http.post(
                Routes.end_user_magickspace_messages(magickspace_id),
                json=request.model_dump(exclude_none=True),
            )
        except MagickMindError as exc:
            if exc.status_code is not None and exc.status_code in _END_USER_ROUTE_HINTS:
                reraise_with_hint(exc, _END_USER_ROUTE_HINTS[exc.status_code])
            raise
        return ChatHistoryItem.model_validate(response)

    async def prepare_own_context(
        self,
        magickspace_id: str,
        *,
        chat_history: Optional[ChatHistoryParams] = None,
        catalog_corpus_ids: Optional[list[str]] = None,
    ) -> ContextPrepareResponse:
        """
        Retrieve the calling agent's conversation context for a magickspace
        (end-user JWT).

        Returns recent chat history plus the ``corpora`` catalog -- the
        knowledge bases the agent may query with :meth:`~CorpusResourceV1.query_own`.
        The participant is the token subject.

        Args:
            magickspace_id: Magickspace to prepare for
            chat_history: History window (``limit``, 1..200)
            catalog_corpus_ids: Extra corpus ids to resolve into the catalog
                beside the space's own (max 64) -- how an agent's
                activation-granted corpora gain names and descriptions.
                Unknown or cross-tenant ids contribute nothing

        Raises:
            MagickMindError: 401 with service-user credentials, 403 if the
                agent is not a participant, 404 if the magickspace does not
                exist
        """
        body: dict[str, object] = {}
        if chat_history:
            body["chat_history"] = chat_history.model_dump(exclude_none=True)
        if catalog_corpus_ids:
            body["catalog_corpus_ids"] = catalog_corpus_ids

        try:
            response = await self._http.post(
                Routes.end_user_magickspace_context(magickspace_id), json=body
            )
        except MagickMindError as exc:
            if exc.status_code is not None and exc.status_code in _END_USER_ROUTE_HINTS:
                reraise_with_hint(exc, _END_USER_ROUTE_HINTS[exc.status_code])
            raise
        return ContextPrepareResponse.model_validate(response)

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
            mindspace = await client.v1.magickspaces.add_participants(
                mindspace_id="mind-123",
                participant_ids=["user-3", "user-4"]
            )
            print(f"Updated participants: {mindspace.participant_ids}")
        """
        # Build and validate request
        request = AddMindSpaceUsersRequest(participant_ids=participant_ids)

        # Make API call
        response = await self._http.post(
            Routes.magickspace_users(mindspace_id),
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
        catalog_corpus_ids: Optional[list[str]] = None,
    ) -> ContextPrepareResponse:
        """
        Retrieve multiple memory sources for a mindspace in a single call.

        Sources are queried in parallel on the server and bundled into one response.

        Args:
            mindspace_id: Mindspace ID
            participant_id: Participant ID (required)
            chat_history: Chat history params (limit)
            corpus: Corpus search params (query)
            pelican: Deprecated; accepted and ignored by the server. Use
                ``client.v1.episode.search`` / ``list_range`` instead.
            api_key: Optional API key (sent as x-api-key header)
            catalog_corpus_ids: Extra corpus ids to resolve into the response's
                ``corpora`` catalog beside the space's own (max 64)

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
        if catalog_corpus_ids:
            body["catalog_corpus_ids"] = catalog_corpus_ids

        headers = {}
        if api_key:
            headers["x-api-key"] = api_key

        response = await self._http.post(
            Routes.magickspace_context(mindspace_id),
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
            Routes.magickspace_livekit_token(mindspace_id),
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
            Routes.magickspace_livekit_join(mindspace_id),
            json={"participant_ids": participant_ids},
        )
        return LivekitJoinResponse.model_validate(response)
