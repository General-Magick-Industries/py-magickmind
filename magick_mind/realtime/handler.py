"""
Decorator-based event router for Centrifugo realtime publications.

Usage:
    router = EventRouter()

    @router.on("chat_message")
    async def handle_chat(event: ChatMessageEvent):
        print(event.payload.message)

    @router.on("image_generation")
    async def handle_image(event: ImageGenerationEvent):
        print(event.payload.data)

    # Catch-all for unregistered event types
    @router.on_unknown
    async def handle_unknown(event: UnknownEvent):
        logger.warning(f"Unhandled event type: {event.type}")
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from centrifuge import ClientEventHandler, ServerPublicationContext

from magick_mind.realtime.events import UnknownEvent, parse_ws_event

logger = logging.getLogger(__name__)


# Type alias for event handler callbacks
EventCallback = Callable[..., Awaitable[None]]


class EventRouter(ClientEventHandler):
    """
    Routes Centrifugo publications to registered async callbacks by event type.

    Integrates with centrifuge-python's ClientEventHandler so it can be passed
    directly to RealtimeClient.connect().
    """

    def __init__(self) -> None:
        self._handlers: dict[str, EventCallback] = {}
        self._unknown_handler: EventCallback | None = None

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
        """

        def decorator(fn: EventCallback) -> EventCallback:
            self._unknown_handler = fn
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

        event = parse_ws_event(data)
        handler = self._handlers.get(event.type)

        if handler:
            try:
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
                await self._unknown_handler(unknown)
            except Exception:
                logger.exception(
                    f"Error in unknown event handler for type '{event.type}'"
                )
        else:
            logger.debug(f"No handler registered for event type: {event.type}")
