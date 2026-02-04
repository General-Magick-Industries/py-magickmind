"""
History resource for Magick Mind SDK v1 API.

Provides methods to fetch chat history with pagination.
"""

from typing import Optional

from magick_mind.models.v1.history import HistoryResponse
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes


class HistoryResourceV1(BaseResource):
    """
    History resource for fetching chat messages.

    Supports three pagination modes:
    1. Latest: Get most recent N messages
    2. Forward: Get messages after a specific message_id
    3. Backward: Get messages before a specific message_id
    """

    def get_messages(
        self,
        mindspace_id: str,
        after_id: Optional[str] = None,
        before_id: Optional[str] = None,
        limit: int = 50,
    ) -> HistoryResponse:
        """
        Fetch chat history with keyset pagination.

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
            HistoryResponse with messages and pagination cursors

        Raises:
            ValueError: If both after_id and before_id are provided

        Example:
            # Get latest 50 messages
            history = client.v1.history.get_messages(mindspace_id="mind-123")

            # Forward pagination (newer messages)
            more = client.v1.history.get_messages(
                mindspace_id="mind-123",
                after_id=history.last_id,
                limit=50
            )

            # Backward pagination (older messages)
            older = client.v1.history.get_messages(
                mindspace_id="mind-123",
                before_id=history.chat_histories[0].id,
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
        response = self._http.get(Routes.HISTORY_MESSAGES, params=params)

        # Parse and return
        return HistoryResponse(**response.json())
