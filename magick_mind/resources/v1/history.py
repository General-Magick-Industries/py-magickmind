"""
History resource for Magick Mind SDK v1 API.

Provides methods to fetch chat history with pagination.

.. deprecated::
    Use :class:`MindspaceResourceV1.get_messages` instead.
"""

from __future__ import annotations

import warnings
from typing import Optional

from magick_mind.models.v1.history import HistoryResponse
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes


class HistoryResourceV1(BaseResource):
    """
    History resource for fetching chat messages.

    .. deprecated::
        Use ``client.v1.mindspace.get_messages()`` instead. This resource
        exists for backward compatibility and delegates to the correct
        ``/v1/mindspaces/{id}/messages`` endpoint.
    """

    async def get_messages(
        self,
        mindspace_id: str,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> HistoryResponse:
        """
        Fetch chat history with cursor-based pagination.

        .. deprecated::
            Use ``client.v1.mindspace.get_messages()`` instead.

        Args:
            mindspace_id: Mindspace to fetch messages from
            cursor: Pagination cursor
            limit: Maximum number of messages to return
            order: Sort order — ``"asc"`` or ``"desc"``

        Returns:
            HistoryResponse with messages and pagination cursors
        """
        warnings.warn(
            "HistoryResourceV1.get_messages() is deprecated. "
            "Use client.v1.mindspace.get_messages() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        params: dict[str, object] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order

        response_data = await self._http.get(
            Routes.mindspace_messages(mindspace_id),
            params=params if params else None,
        )

        return HistoryResponse(**response_data)
