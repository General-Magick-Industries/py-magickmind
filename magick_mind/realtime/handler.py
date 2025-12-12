"""
High-level event handler for Magick Mind Realtime Client.
Abstracts away Centrifugo channel parsing details.
"""

import logging
from typing import Any, Optional

from centrifuge import ClientEventHandler, ServerPublicationContext, ConnectedContext

logger = logging.getLogger(__name__)


class RealtimeEventHandler(ClientEventHandler):
    """
    Abstract base class for handling Realtime SDK events.

    Subclass this and override `on_message` to handle incoming user updates.
    The SDK handles channel parsing and data extraction for you.
    """

    async def on_connected(self, ctx: ConnectedContext) -> None:
        """Called when connected to the Realtime Gateway."""
        logger.info(f"✅ Connected to Realtime Gateway (Client ID: {ctx.client})")

    async def on_message(self, user_id: str, payload: Any) -> None:
        """
        Called when a message is received for a specific user.

        Args:
            user_id: The ID of the end-user this message is for.
            payload: The message content (dict, string, etc).
        """
        pass

    async def on_raw_message(self, channel: str, payload: Any) -> None:
        """
        Called when a message is received but the user ID could not be parsed,
        or for non-standard channels.
        """
        pass

    async def on_publication(self, ctx: ServerPublicationContext) -> None:
        """
        Internal handler. Parses channel context and dispatches to on_message.
        """
        channel = self._extract_channel(ctx)
        data = self._extract_data(ctx)

        user_id = self._extract_user_id(channel)

        if user_id:
            await self.on_message(user_id, data)
        else:
            await self.on_raw_message(channel, data)

    def _extract_channel(self, ctx: ServerPublicationContext) -> str:
        """
        Extract channel from context in a version-resilient way.
        """
        # Try direct attribute
        ch = getattr(ctx, "channel", None)
        if ch:
            return ch

        # Try inside pub object
        pub = getattr(ctx, "pub", None)
        if pub:
            return getattr(pub, "channel", "")

        return ""

    def _extract_data(self, ctx: ServerPublicationContext) -> Any:
        """
        Extract data payload from context.
        """
        pub = getattr(ctx, "pub", None)
        return getattr(pub, "data", None) if pub else None

    def _extract_user_id(self, channel: str) -> Optional[str]:
        """
        Parse User ID from channel string.
        Format confirmed as: personal:<target_user_id>#<service_user_id>
        """
        if not channel:
            return None

        # 1. Remove namespace (personal:)
        if ":" in channel:
            without_ns = channel.split(":", 1)[1]
        else:
            without_ns = channel

        # 2. Extract first part before '#'
        # "user_123#service_456" -> "user_123"
        if "#" in without_ns:
            return without_ns.split("#")[0]

        return without_ns
