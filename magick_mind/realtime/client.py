"""Realtime client implementation using centrifuge-python."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, Optional, List, cast

from centrifuge import (
    Client,
    DisconnectedContext,
    PublicationContext,
    ServerPublicationContext,
    SubscriptionEventHandler,
)

from ..auth.base import AuthProvider
from ..auth.end_user_token import EndUserTokenAuth
from ..auth.jwt import jwt_subject
from ..exceptions import MagickMindError
from .handler import EventCallback, EventRouter


logger: logging.Logger = logging.getLogger(__name__)

# Bifrost's connect proxy rejects a bad, expired, or revoked end-user token with
# this code. It is in Centrifugo's no-reconnect range (4500-4999), which
# centrifuge-python honours on the websocket-close path Bifrost uses.
DISCONNECT_UNAUTHORIZED = 4501


def _extract_jwt_sub(token: str) -> Optional[str]:
    """
    Decode JWT without verification to extract 'sub'.
    Returns None if parsing fails.
    """
    return jwt_subject(token)


class _DelegatingSubscriptionHandler(SubscriptionEventHandler):
    """Routes client-side subscription publications to EventRouter.on_publication."""

    def __init__(self, router: EventRouter, channel: str):
        self._router = router
        self._channel = channel

    async def on_publication(self, ctx: PublicationContext) -> None:
        """Route client-side publication to the EventRouter."""
        logger.debug(f"Publication on {self._channel}: {ctx.pub.data}")

        # Wrap in adapter for EventRouter.
        # _PublicationAdapter is structurally compatible with ServerPublicationContext.
        server_ctx = cast(
            ServerPublicationContext,
            _PublicationAdapter(ctx, self._channel),  # type: ignore[arg-type]
        )
        try:
            await self._router.on_publication(server_ctx)
        except Exception:
            logger.exception(f"Error in publication handler for {self._channel}")

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

    Two connection modes, chosen at construction:

    - **Service user** (default): the tenant JWT goes in the connect frame's
      ``token`` and the client subscribes to ``personal:{target}#{self}``
      channels with :meth:`subscribe`.
    - **End user** (``end_user=True``): the minted end-user JWT goes in the
      connect frame's ``data.token`` for Bifrost's connect proxy, which
      grants the connection exactly ``user:{sub}#{sub}`` server-side. Nothing
      to subscribe to -- magickspace fan-out arrives as soon as
      :meth:`connect` returns. A rotated token is swapped into the connect
      frame automatically, since the rotated-out one is revoked and could not
      reconnect.
    """

    def __init__(
        self, auth: AuthProvider, ws_url: Optional[str], *, end_user: bool = False
    ):
        self.auth = auth
        self.ws_url = ws_url
        self.end_user = end_user
        self._client: Optional[Client] = None
        self._router = EventRouter()
        self._connect_data: dict[str, Any] = {}
        self._router.on_disconnected_hook = self._on_disconnected
        self.last_disconnect: Optional[DisconnectedContext] = None
        if isinstance(auth, EndUserTokenAuth):
            auth.on_rotate(self._set_connect_token)

    def on(self, event_type: str) -> Callable[[EventCallback], EventCallback]:
        """Register a handler for a realtime event type."""
        return self._router.on(event_type)

    @property
    def on_unknown(self) -> Callable[[EventCallback], EventCallback]:
        """Register a catch-all for unknown event types."""
        return self._router.on_unknown

    @property
    def terminally_disconnected(self) -> bool:
        """True after the server refused the credential (code 4501).

        The underlying client will not reconnect; a new token is needed.
        """
        return (
            self.last_disconnect is not None
            and self.last_disconnect.code == DISCONNECT_UNAUTHORIZED
        )

    async def _get_token(self) -> str:
        """Get token wrapper for centrifuge client."""
        try:
            return await self.auth.get_token_async()  # type: ignore[attr-defined]
        except Exception:
            raise

    def _set_connect_token(self, token: str) -> None:
        self._connect_data["token"] = token

    async def _on_disconnected(self, ctx: DisconnectedContext) -> None:
        self.last_disconnect = ctx
        if ctx.code == DISCONNECT_UNAUTHORIZED:
            logger.error(
                "Realtime connection refused: end-user token rejected (code %s, %s)",
                ctx.code,
                ctx.reason,
            )

    async def connect(self) -> None:
        """Connect to the realtime service."""
        if self._client:
            return

        ws_url = self.ws_url
        if not ws_url:
            raise MagickMindError(
                "WebSocket URL is required for realtime connections. "
                "Pass ws_endpoint= when creating MagickMind client."
            )

        if self.end_user:
            self._set_connect_token(await self._get_token())
            client = Client(
                ws_url,
                events=self._router,
                data=self._connect_data,
                use_protobuf=False,
            )
        else:
            client = Client(
                ws_url,
                events=self._router,
                get_token=self._get_token,
                use_protobuf=False,
            )

        self.last_disconnect = None
        try:
            await client.connect()
            await client.ready()
        except Exception as e:
            # Leave the slot empty so a later connect() (after replace_token)
            # is a real attempt rather than the "already connected" no-op.
            await client.disconnect()
            reason = (
                f"end-user token rejected ({self.last_disconnect.reason})"
                if self.terminally_disconnected and self.last_disconnect
                else str(e)
            )
            raise MagickMindError(f"Realtime connect failed: {reason}") from e
        self._client = client

    async def disconnect(self) -> None:
        """Disconnect from the realtime service."""
        if self._client:
            await self._client.disconnect()
            self._client = None
        self._connect_data.clear()

    async def subscribe(self, target_user_id: str) -> None:
        """
        Subscribe to a user's channel using client-side subscription.

        Service-user mode only: an end-user connection is subscribed to its
        own ``user:`` channel by the server and has nothing to subscribe to.

        Args:
            target_user_id: ID of the user to subscribe to
        """
        if not self._client:
            raise MagickMindError("Realtime client not connected")
        if self.end_user:
            raise MagickMindError(
                "An end-user connection receives its own user: channel from the "
                "server; there is nothing to subscribe to"
            )

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
        if not self._client:
            return

        sub_events = _DelegatingSubscriptionHandler(self._router, channel)

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
