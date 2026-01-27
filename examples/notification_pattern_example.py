#!/usr/bin/env python3
"""
Example: Realtime as Notification Pattern

Demonstrates using realtime events as notifications only, with Bifrost
history API as the source of truth.

Pattern:
- Realtime: Trigger/notification that something happened
- History API: Fetch actual data (source of truth)
- No storing realtime payload directly

This is the most conservative and correct approach - realtime for speed,
history for accuracy.

Use cases:
- Apps requiring perfect data consistency
- When you don't trust realtime payload format
- When you need full pagination/versioning from history API

Usage:
    export BIFROST_EMAIL="service@example.com"
    export BIFROST_PASSWORD="password"
    export BIFROST_BASE_URL="http://localhost:8888"
    python examples/notification_pattern_example.py
"""

import asyncio
import os
import logging
from typing import Set

from magick_mind import MagickMind
from magick_mind.realtime.handler import RealtimeEventHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification_pattern")


class NotificationOnlyHandler(RealtimeEventHandler):
    """
    Handle realtime events as notifications ONLY.

    Don't store the payload - just trigger a fetch from history API.
    """

    def __init__(self, client: MagickMind):
        self.client = client
        self.processed_notifications: Set[str] = set()
        self.stats = {
            "notifications_received": 0,
            "history_fetches_triggered": 0,
            "duplicates_skipped": 0,
        }

    async def on_connected(self, ctx):
        logger.info(f"✅ Connected to realtime: {ctx.client}")

    async def on_disconnected(self, ctx):
        logger.warning(f"⚠️  Disconnected: {ctx}")

    async def on_message(self, user_id: str, payload: dict):
        """
        Treat this as a notification only.

        Don't store the payload! Just trigger a history fetch.
        """
        self.stats["notifications_received"] += 1

        # Extract message ID for deduplication
        message_id = payload.get("message_id") or payload.get("id")
        if not message_id:
            logger.warning("Notification has no ID, skipping")
            return

        # Deduplicate notifications
        if message_id in self.processed_notifications:
            self.stats["duplicates_skipped"] += 1
            logger.debug(f"⏭️  Skipping duplicate notification {message_id}")
            return

        self.processed_notifications.add(message_id)

        logger.info(f"📬 Notification received for user [{user_id}]")
        logger.info(f"   Message ID: {message_id}")
        logger.info(f"   Type: {payload.get('type', 'unknown')}")

        # Don't use payload data! Just trigger  history fetch
        mindspace_id = payload.get("mindspace_id")
        if mindspace_id:
            logger.info(
                f"   ⏳ Triggering history fetch for mindspace {mindspace_id}..."
            )
            asyncio.create_task(self.fetch_from_history(mindspace_id, user_id))
            self.stats["history_fetches_triggered"] += 1
        else:
            logger.warning("   No mindspace_id in notification, can't fetch history")

    async def fetch_from_history(self, mindspace_id: str, user_id: str):
        """
        Fetch latest messages from Bifrost history API.

        This is the source of truth - not the realtime payload.
        """
        try:
            logger.info(f"📖 Fetching history for mindspace {mindspace_id}")

            # Fetch from history API (source of truth)
            result = self.client.v1.history.get_messages(
                mindspace_id=mindspace_id,
                limit=10,  # Get latest 10 messages
            )

            logger.info(
                f"✅ Fetched {len(result.chat_histories)} messages from history"
            )

            # Process messages from history (not from realtime!)
            for msg in result.chat_histories:
                await self.process_message_from_history(msg)

        except Exception as e:
            logger.error(f"❌ History fetch failed: {e}", exc_info=True)

    async def process_message_from_history(self, message):
        """
        Process message fetched from history API.

        This is where you'd store to database, send to frontend, etc.
        """
        logger.info("   📝 Processing message from history:")
        logger.info(f"      ID: {message.id}")
        logger.info(f"      Content: {message.content[:50]}...")
        logger.info(f"      Created: {message.created_at}")

        # In production, you'd:
        # - Store in your database
        # - Send to frontend via WebSocket
        # - Trigger webhooks
        # etc.

        # Simulated processing
        await asyncio.sleep(0.1)


async def main():
    """
    Demonstrate notification-only pattern.
    """
    # Initialize SDK
    client = MagickMind(
        email=os.getenv("BIFROST_EMAIL"),
        password=os.getenv("BIFROST_PASSWORD"),
        base_url=os.getenv("BIFROST_BASE_URL", "http://localhost:8888"),
    )

    user_id = os.getenv("USER_ID", "user-test-456")

    # Create notification handler
    handler = NotificationOnlyHandler(client)

    logger.info("=" * 60)
    logger.info("Notification Pattern Demo")
    logger.info("=" * 60)
    logger.info("\nPattern: Realtime → Notification → History Fetch\n")

    try:
        # Connect to realtime
        logger.info("--- Step 1: Connect to Realtime ---")
        await client.realtime.connect(events=handler)
        logger.info("Connected\n")

        # Subscribe to user
        logger.info(f"--- Step 2: Subscribe to {user_id} ---")
        await client.realtime.subscribe(user_id)
        logger.info("Subscribed\n")

        # Listen for notifications
        logger.info("--- Step 3: Listening for Notifications ---")
        logger.info("When a message arrives:")
        logger.info("  1. Receive notification via realtime")
        logger.info("  2. Don't use notification payload")
        logger.info("  3. Fetch from history API (source of truth)")
        logger.info("  4. Process data from history\n")

        logger.info("Listening for 60 seconds...\n")
        await asyncio.sleep(60)

        # Show stats
        logger.info("\n--- Stats ---")
        logger.info(
            f"Notifications received: {handler.stats['notifications_received']}"
        )
        logger.info(
            f"History fetches triggered: {handler.stats['history_fetches_triggered']}"
        )
        logger.info(f"Duplicates skipped: {handler.stats['duplicates_skipped']}")
        logger.info(f"Unique notifications: {len(handler.processed_notifications)}")

    except KeyboardInterrupt:
        logger.info("\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
    finally:
        await client.realtime.disconnect()
        client.close()
        logger.info("Disconnected")


if __name__ == "__main__":
    """
    This pattern is recommended when:
    
    1. **Data consistency is critical**
       - You need 100% accurate data
       - Realtime format might change
       - You want versioning from history API
    
    2. **You need full history features**
       - Pagination
       - Filtering
       - Cursor-based navigation
    
    3. **Conservative approach**
       - Realtime for notification speed
       - History API for data accuracy
       - Best of both worlds
    
    Trade-offs:
    - ✅ Always correct (history is source of truth)
    - ✅ Proper pagination support
    - ✅ Immune to realtime format changes
    - ⚠️ Extra API call per notification (history fetch)
    - ⚠️ Slightly higher latency
    
    Compare with:
    - examples/backend_service.py - Stores realtime payload directly
    - examples/database_storage_example.py - Hybrid approach
    
    This is the safest pattern for production with strict data requirements.
    """
    asyncio.run(main())
