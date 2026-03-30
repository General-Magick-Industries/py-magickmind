"""
Decorator-based event router for Centrifugo realtime publications.

Usage:
    router = EventRouter()

    # Event-only handler (backward compatible)
    @router.on("chat_message")
    async def handle_chat(event: ChatMessageEvent):
        print(event.payload.message)

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

from centrifuge import ClientEventHandler, ServerPublicationContext

from magick_mind.realtime.events import EventContext, UnknownEvent, parse_ws_event

logger = logging.getLogger(__name__)


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
        if data is None:
            return

        channel: str = getattr(ctx, "channel", "") or ""
        event_ctx = EventContext.from_channel(channel)

        event = parse_ws_event(data)
        handler = self._handlers.get(event.type)

        if handler:
            try:
                if self._handler_wants_ctx.get(event.type, False):
                    await handler(event, event_ctx)
                else:
                    await handler(event)
            except Exception:
                logger.exception(f"Error in handler for event type '{event.type}'")
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
