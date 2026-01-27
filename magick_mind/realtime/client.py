"""Realtime client implementation using centrifuge-python."""

import asyncio
import base64
import json
import logging
from typing import Optional, List

from centrifuge import (
    Client,
    ClientEventHandler,
    PublicationContext,
    SubscriptionEventHandler,
)

from ..auth.base import AuthProvider
from ..exceptions import MagickMindError


logger = logging.getLogger(__name__)


def _extract_jwt_sub(token: str) -> Optional[str]:
    """
    Decode JWT without verification to extract 'sub'.
    Returns None if parsing fails.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
        sub = payload.get("sub")
        return sub if isinstance(sub, str) else None
    except Exception:
        return None


class _DelegatingSubscriptionHandler(SubscriptionEventHandler):
    """Routes client-side subscription publications to ClientEventHandler.on_publication."""

    def __init__(self, client_handler: ClientEventHandler, channel: str):
        self._client_handler = client_handler
        self._channel = channel

    async def on_publication(self, ctx: PublicationContext) -> None:
        """Route client-side publication to the ClientEventHandler."""
        logger.debug(f"Publication on {self._channel}: {ctx.pub.data}")

        # Wrap in adapter for ClientEventHandler
        server_ctx = _PublicationAdapter(ctx, self._channel)
        try:
            await self._client_handler.on_publication(server_ctx)
        except Exception:
            logger.exception(f"Error in on_publication handler for {self._channel}")

    async def on_subscribed(self, ctx) -> None:
        logger.info(f"✅ Subscribed to channel: {self._channel}")

    async def on_unsubscribed(self, ctx) -> None:
        logger.info(f"Unsubscribed from channel: {self._channel}")

    async def on_error(self, ctx) -> None:
        logger.error(f"Subscription error on {self._channel}: {ctx}")


class _PublicationAdapter:
    """Adapts PublicationContext to look like ServerPublicationContext."""

    def __init__(self, client_ctx: PublicationContext, channel: str):
        self.pub = client_ctx.pub
        self.channel = channel


class RealtimeClient:
    """
    Async client for real-time features using WebSockets.
    Uses pure client-side subscriptions for reliability.
    """

    def __init__(self, auth: AuthProvider, ws_url: str):
        self.auth = auth
        self.ws_url = ws_url
        self._client: Optional[Client] = None
        self._events: Optional[ClientEventHandler] = None

    async def _get_token(self) -> str:
        """Get token wrapper for centrifuge client."""
        try:
            return await self.auth.get_token_async()
        except Exception:
            raise

    async def connect(self, events: Optional[ClientEventHandler] = None) -> None:
        """Connect to the realtime service."""
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
        Subscribe to a user's channel using client-side subscription.

        Args:
            target_user_id: ID of the user to subscribe to
        """
        if not self._client:
            raise MagickMindError("Realtime client not connected")

        # Build channel name
        token = await self._get_token()
        service_user_id = _extract_jwt_sub(token)
        if not service_user_id:
            raise MagickMindError("Failed to extract service_user_id from JWT")

        channel = f"personal:{target_user_id}#{service_user_id}"
        logger.debug(f"Subscribing to channel: {channel}")

        # Create client-side subscription with handler
        await self._ensure_subscription(channel)

    async def _ensure_subscription(self, channel: str) -> None:
        """Ensure client-side subscription exists with proper event handler."""
        if not self._client or not self._events:
            return

        sub_events = _DelegatingSubscriptionHandler(self._events, channel)

        try:
            existing_sub = self._client.get_subscription(channel)
            if existing_sub:
                state = getattr(existing_sub, "state", None)
                state_name = getattr(state, "name", "")
                if state_name == "UNSUBSCRIBED":
                    await existing_sub.subscribe()
                    logger.info(f"Resubscribed to {channel}")
            else:
                sub = self._client.new_subscription(channel, events=sub_events)
                await sub.subscribe()
                logger.info(f"Subscribed to {channel}")
        except Exception as e:
            logger.error(f"Subscription failed for {channel}: {e}")
            raise MagickMindError(f"Subscribe failed: {e}")

    async def subscribe_many(self, target_user_ids: List[str]) -> None:
        """Subscribe to multiple users concurrently."""
        if not target_user_ids:
            return

        tasks = [self.subscribe(uid) for uid in target_user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            raise errors[0]

    async def unsubscribe(self, target_user_id: str) -> None:
        """Unsubscribe from a user's channel."""
        if not self._client:
            raise MagickMindError("Realtime client not connected")

        token = await self._get_token()
        service_user_id = _extract_jwt_sub(token)
        if not service_user_id:
            return

        channel = f"personal:{target_user_id}#{service_user_id}"
        sub = self._client.get_subscription(channel)
        if sub:
            await sub.unsubscribe()

    async def unsubscribe_many(self, target_user_ids: List[str]) -> None:
        """Unsubscribe from multiple users concurrently."""
        if not target_user_ids:
            return

        tasks = [self.unsubscribe(uid) for uid in target_user_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

    @property
    def client(self) -> Optional[Client]:
        """Get underlying centrifuge client."""
        return self._client
