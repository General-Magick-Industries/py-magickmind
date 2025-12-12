"""Realtime client implementation using centrifuge-python."""

import asyncio
import logging
from typing import Optional, List


from centrifuge import (
    Client,
    ClientEventHandler,
)
from centrifuge.exceptions import ReplyError

from ..auth.base import AuthProvider
from ..exceptions import MagickMindError


logger = logging.getLogger(__name__)


class RealtimeClient:
    """
    Async client for real-time features using WebSockets.
    Wraps centrifuge.Client to handle authentication and Bifrost-specific patterns.
    """

    def __init__(self, auth: AuthProvider, ws_url: str):
        """
        Initialize realtime client.

        Args:
            auth: Authentication provider (must support get_token)
            ws_url: WebSocket URL (e.g., "ws://localhost:8888/connection/websocket")
        """
        self.auth = auth
        self.ws_url = ws_url
        self._client: Optional[Client] = None
        self._events: Optional[ClientEventHandler] = None

    async def _get_token(self) -> str:
        """Get token wrapper for centrifuge client."""
        # AuthProvider.get_token() is synchronous currently.
        # We wrap it in a thread execution to be safe if it does IO blocking.
        # Ideally get_token should be async, but for MVP we run it in executor.
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.auth.get_token)

    async def connect(self, events: Optional[ClientEventHandler] = None) -> None:
        """
        Connect to the realtime service.

        Args:
            events: Optional ClientEventHandler for global events
        """
        if self._client:
            return

        self._events = events or ClientEventHandler()

        self._client = Client(
            self.ws_url,
            events=self._events,
            get_token=self._get_token,
            use_protobuf=False,
        )

        await self._client.connect()
        await self._client.ready()

    async def disconnect(self) -> None:
        """Disconnect from the realtime service."""
        if self._client:
            await self._client.disconnect()
            self._client = None

    async def subscribe(self, target_user_id: str) -> None:
        """
        Subscribe to a user's channel via RPC.

        This uses the Bifrost backend to manage the subscription:
        1. Derives service_user_id from the auth token
        2. Builds the correct channel name (personal channel)
        3. Subscribes this client to that channel

        The Centrifugo SDK automatically maintains server-side subscriptions
        across reconnections, so no manual tracking is needed.

        Args:
            target_user_id: ID of the user to subscribe to
        """
        if not self._client:
            raise MagickMindError("Realtime client not connected")

        data = {
            "target_user_id": target_user_id,
        }

        try:
            await self._client.rpc("subscribe", data)
        except ReplyError as e:
            raise MagickMindError(f"Subscribe failed: {e}")

    async def subscribe_many(self, target_user_ids: List[str]) -> None:
        """
        Subscribe to multiple users concurrently.

        Fires all RPC subscribe requests in parallel for better performance
        when subscribing to many users at once.

        Args:
            target_user_ids: List of user IDs to subscribe to

        Raises:
            MagickMindError: If any subscription fails
        """
        if not target_user_ids:
            return

        tasks = [self.subscribe(uid) for uid in target_user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for errors
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            # Raise the first error encountered
            raise errors[0]

    async def unsubscribe(self, target_user_id: str) -> None:
        """
        Unsubscribe from a user's channel via RPC.

        Args:
            target_user_id: ID of the user to unsubscribe from
        """
        if not self._client:
            raise MagickMindError("Realtime client not connected")

        data = {
            "target_user_id": target_user_id,
        }

        try:
            await self._client.rpc("unsubscribe", data)
        except ReplyError as e:
            raise MagickMindError(f"Unsubscribe failed: {e}")

    async def unsubscribe_many(self, target_user_ids: List[str]) -> None:
        """
        Unsubscribe from multiple users concurrently.

        Fires all RPC unsubscribe requests in parallel for better performance
        when unsubscribing from many users at once.

        Args:
            target_user_ids: List of user IDs to unsubscribe from

        Raises:
            MagickMindError: If any unsubscription fails
        """
        if not target_user_ids:
            return

        tasks = [self.unsubscribe(uid) for uid in target_user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for errors
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            # Raise the first error encountered
            raise errors[0]

    @property
    def client(self) -> Optional[Client]:
        """Get underlying centrifuge client."""
        return self._client
