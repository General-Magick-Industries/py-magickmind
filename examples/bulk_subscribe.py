#!/usr/bin/env python3
"""
Example: Bulk Subscriptions with Message Deduplication

This demonstrates:
- Subscribing to many users efficiently (50 users)
- Message deduplication (CRITICAL for production!)
- Why you need deduplication when users are in same group

Real-World Scenario:
- You subscribe to user_1, user_2, user_3
- All 3 users are in the same mindspace/group
- AI sends message to the group
- You receive the SAME message 3 times (once per user)
- Without deduplication, you process it 3 times!

Production Note:
- This example uses in-memory deduplication (simple but loses state on restart)
- For production, use Redis (see docs/realtime_guide.md)

Usage:
    export BIFROST_BASE_URL="http://localhost:8888"
    export BIFROST_EMAIL="service@example.com"
    export BIFROST_PASSWORD="your_password"
    export BIFROST_WS_ENDPOINT="ws://localhost:8888/connection/websocket"
    uv run python examples/bulk_subscribe.py
"""

import asyncio
import os
import logging
from typing import Set

from dotenv import load_dotenv

from magick_mind import MagickMind
from magick_mind.realtime.events import ChatMessageEvent

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bulk_subscribe")


class DeduplicatingProcessor:
    """
    Message processor with deduplication.

    CRITICAL: When subscribing to multiple users in the same group,
    you'll receive duplicate messages. Always deduplicate!
    """

    def __init__(self) -> None:
        self.processed_ids: Set[str] = set()  # In production: use Redis!
        self.metrics = {
            "total_received": 0,
            "duplicates_skipped": 0,
            "messages_processed": 0,
        }

    async def handle_chat(self, event: ChatMessageEvent) -> None:
        """Handle incoming chat_message event with deduplication."""
        self.metrics["total_received"] += 1
        payload = event.payload

        # Deduplicate - CRITICAL for production!
        if payload.message_id in self.processed_ids:
            self.metrics["duplicates_skipped"] += 1
            logger.debug(f"⏭️  Skipping duplicate {payload.message_id}")
            return

        # Process the message
        self.metrics["messages_processed"] += 1
        logger.info(f"📨 Message {payload.message_id}: {payload.message[:50]}")

        # Mark as processed
        self.processed_ids.add(payload.message_id)

        # Log metrics periodically
        if self.metrics["total_received"] % 10 == 0:
            self.log_metrics()

    def log_metrics(self) -> None:
        """Log deduplication metrics."""
        total = self.metrics["total_received"]
        dupes = self.metrics["duplicates_skipped"]
        processed = self.metrics["messages_processed"]

        if total > 0:
            dupe_rate = (dupes / total) * 100
            logger.info(
                f"📊 Metrics: {total} received, {processed} processed, "
                f"{dupes} duplicates ({dupe_rate:.1f}% duplicate rate)"
            )


async def main():
    # Get config from environment
    base_url = os.getenv("BIFROST_BASE_URL", "https://dev-bifrost.magickmind.ai")
    ws_endpoint = os.getenv(
        "BIFROST_WS_ENDPOINT", "wss://dev-centrifugo.magickmind.ai/connection/websocket"
    )
    email = os.getenv("BIFROST_EMAIL")
    password = os.getenv("BIFROST_PASSWORD")

    if not email or not password:
        logger.error("BIFROST_EMAIL and BIFROST_PASSWORD are required")
        return

    # Create client
    client = MagickMind(
        base_url=base_url, email=email, password=password, ws_endpoint=ws_endpoint
    )

    # Create deduplicating processor
    processor = DeduplicatingProcessor()

    # Register event handler using decorator API
    @client.realtime.on("chat_message")
    async def handle_chat(event: ChatMessageEvent) -> None:
        await processor.handle_chat(event)

    try:
        # Connect to realtime
        logger.info("Connecting to realtime...")
        await client.realtime.connect()
        logger.info("✅ Connected!")

        # Simulate subscribing to many users (e.g., relay service, admin dashboard)
        # Per-user subscription model: 50 users = 50 subscriptions (on 1 connection)
        user_ids = [f"user_{i}" for i in range(50)]

        logger.info(f"Subscribing to {len(user_ids)} users concurrently...")
        logger.info(
            "Note: If these users are in the same group/mindspace, "
            "we'll receive duplicate messages!"
        )
        await client.realtime.subscribe_many(user_ids)
        logger.info("✅ All subscriptions successful!")

        # Keep listening
        logger.info("Listening for 30 seconds...")
        logger.info("Watch for duplicate messages being skipped!")
        await asyncio.sleep(30)

        # Show final metrics
        processor.log_metrics()
        logger.info(
            f"Processed IDs count: {len(processor.processed_ids)} unique messages"
        )

        # Bulk unsubscribe
        logger.info(f"Unsubscribing from {len(user_ids)} users...")
        await client.realtime.unsubscribe_many(user_ids)
        logger.info("✅ All unsubscribed!")

    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
    finally:
        await client.realtime.disconnect()
        await client.close()


if __name__ == "__main__":
    """
    Production Recommendations:
    
    1. Use Redis for deduplication (not in-memory set):
       - Survives restarts
       - Can be shared across multiple backend instances
       - Built-in TTL for cleanup
       
    2. Monitor duplicate rates:
       - 0% = All users in separate groups (rare)
       - 67% = 3 users in same group (2/3 messages are dupes)
       - Higher % = More users sharing groups
       
    3. See docs/realtime_guide.md for production patterns
    """
    asyncio.run(main())
