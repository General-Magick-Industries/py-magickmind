"""
Decorator-based event router for Centrifugo realtime publications.

Usage:
    router = EventRouter()

    # Event-only handler (backward compatible)
    @router.on("chat_message")
    async def handle_chat(event: ChatMessageEvent):
        print(event.payload.message)

    # Magickspace fan-out (what an agent connected as an end user receives)
    @router.on(MAGICKSPACE_MESSAGE)
    async def handle_turn(event: MagickspaceMessageEvent):
        if event.payload.is_signal or event.payload.is_control:
            return
        print(f"{event.payload.sent_by_user_name}: {event.payload.content}")

    # Handler with EventContext — identifies which end-user the event is for
    @router.on("chat_message")
    async def handle_chat(event: ChatMessageEvent, ctx: EventContext):
        print(f"Message for {ctx.target_user_id}: {event.payload.message}")

    @router.on("image_generation")
    async def handle_image(event: ImageGenerationEvent, ctx: EventContext):
        print(f"Image for {ctx.target_user_id}: {event.payload.data}")

    # Catch-all for unregistered event types
    @router.on_unknown
    async def handle_unknown(event: UnknownEvent, ctx: EventContext):
        logger.warning(f"Unhandled event type: {event.type} on {ctx.channel}")
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable

from centrifuge import (
    ClientEventHandler,
    DisconnectedContext,
    ServerPublicationContext,
)

from magick_mind.realtime.events import (
    EventContext,
    UnknownEvent,
    dispatch_key,
    parse_ws_event,
)

logger: logging.Logger = logging.getLogger(__name__)


# Type alias for event handler callbacks
EventCallback = Callable[..., Awaitable[None]]


def _wants_context(fn: EventCallback) -> bool:
    """Return True if *fn* accepts a second positional parameter (EventContext)."""
    try:
        params = list(inspect.signature(fn).parameters.values())
    except (ValueError, TypeError):
        return False
    positional_kinds = {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    }
    positional = [p for p in params if p.kind in positional_kinds]
    return len(positional) >= 2


class EventRouter(ClientEventHandler):
    """
    Routes Centrifugo publications to registered async callbacks by event type.

    Integrates with centrifuge-python's ClientEventHandler so it can be passed
    directly to RealtimeClient.connect().

    Handlers may accept one or two positional arguments::

        @router.on("chat_message")
        async def handle(event: ChatMessageEvent): ...          # event only

        @router.on("chat_message")
        async def handle(event: ChatMessageEvent, ctx: EventContext): ...  # with context
    """

    def __init__(self) -> None:
        self._handlers: dict[str, EventCallback] = {}
        self._handler_wants_ctx: dict[str, bool] = {}
        self._unknown_handler: EventCallback | None = None
        self._unknown_wants_ctx: bool = False
        self.on_disconnected_hook: (
            Callable[[DisconnectedContext], Awaitable[None]] | None
        ) = None

    async def on_disconnected(self, ctx: DisconnectedContext) -> None:
        if self.on_disconnected_hook is not None:
            await self.on_disconnected_hook(ctx)

    def on(self, event_type: str) -> Callable[[EventCallback], EventCallback]:
        """
        Register a handler for a specific event type.

        Args:
            event_type: The WsEvent type string (e.g. "chat_message", "image_generation")

        Returns:
            Decorator that registers the handler function.
        """

        def decorator(fn: EventCallback) -> EventCallback:
            self._handlers[event_type] = fn
            self._handler_wants_ctx[event_type] = _wants_context(fn)
            return fn

        return decorator

    @property
    def on_unknown(self) -> Callable[[EventCallback], EventCallback]:
        """
        Register a catch-all handler for unknown/unregistered event types.

        Usage:
            @router.on_unknown
            async def handle_unknown(event: UnknownEvent):
                ...

            @router.on_unknown
            async def handle_unknown(event: UnknownEvent, ctx: EventContext):
                ...
        """

        def decorator(fn: EventCallback) -> EventCallback:
            self._unknown_handler = fn
            self._unknown_wants_ctx = _wants_context(fn)
            return fn

        return decorator

    async def on_publication(self, ctx: ServerPublicationContext) -> None:
        """
        Internal: called by centrifuge-python on each publication.
        Parses raw data into typed event, dispatches to registered handler.
        """
        data = getattr(ctx.pub, "data", None)
        channel: str = getattr(ctx, "channel", "") or ""
        if not isinstance(data, dict):
            logger.warning("Dropping non-object publication on %s", channel)
            return

        info = getattr(ctx.pub, "info", None)
        publisher = getattr(info, "user", "") or ""
        event_ctx = EventContext.from_channel(channel, publisher_user_id=publisher)

        # A server-side subscription hands publications straight to this method
        # from centrifuge's message loop, which has no guard of its own: one
        # exception there stops every later publication while the socket stays
        # open. Nothing may escape from here.
        try:
            event = parse_ws_event(data)
        except Exception:
            logger.exception("Dropping unparseable publication on %s", channel)
            return
        key = dispatch_key(event)
        handler = self._handlers.get(key)

        if handler:
            try:
                if self._handler_wants_ctx.get(key, False):
                    await handler(event, event_ctx)
                else:
                    await handler(event)
            except Exception:
                logger.exception(f"Error in handler for event type '{key}'")
        elif self._unknown_handler:
            try:
                unknown = (
                    event
                    if isinstance(event, UnknownEvent)
                    else UnknownEvent(type=event.type, payload=data.get("payload", {}))
                )
                if self._unknown_wants_ctx:
                    await self._unknown_handler(unknown, event_ctx)
                else:
                    await self._unknown_handler(unknown)
            except Exception:
                logger.exception(
                    f"Error in unknown event handler for type '{event.type}'"
                )
        else:
            logger.debug(f"No handler registered for event type: {event.type}")
