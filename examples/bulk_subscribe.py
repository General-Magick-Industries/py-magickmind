#!/usr/bin/env python3
"""
Example: Bulk subscribe/unsubscribe for relay services.

This demonstrates subscribing to many users at once, useful for:
- Relay services that fan out messages to many end-users
- Admin dashboards monitoring multiple users
- Analytics services tracking user activity

Usage:
    export BIFROST_BASE_URL="http://localhost:8888"
    export BIFROST_EMAIL="service@example.com"
    export BIFROST_PASSWORD="your_password"
    export BIFROST_WS_ENDPOINT="ws://localhost:8888/connection/websocket"
    uv run --env-file .env python examples/bulk_subscribe.py
"""

import asyncio
import os
import logging
from magick_mind import MagickMind
from centrifuge import ClientEventHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bulk_subscribe_example")


async def main():
    # Get config from environment
    base_url = os.getenv("BIFROST_BASE_URL", "http://localhost:8888")
    ws_endpoint = os.getenv(
        "BIFROST_WS_ENDPOINT", "ws://localhost:8888/connection/websocket"
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

    # Event handler for server-side publications
    class MyHandler(ClientEventHandler):
        async def on_connected(self, ctx):
            logger.info(f"Connected: {ctx}")

        async def on_publication(self, ctx):
            logger.info(f"Message from {ctx.channel}: {ctx.pub.data}")

    rt = client.realtime

    try:
        # Connect to realtime
        logger.info("Connecting to realtime...")
        await rt.connect(events=MyHandler())
        logger.info("✅ Connected!")

        # Simulate subscribing to many users (e.g., relay service)
        user_ids = [f"user_{i}" for i in range(50)]

        logger.info(f"Subscribing to {len(user_ids)} users concurrently...")
        await rt.subscribe_many(user_ids)
        logger.info("✅ All subscriptions successful!")

        # Keep listening
        logger.info("Listening for 10 seconds...")
        await asyncio.sleep(10)

        # Bulk unsubscribe
        logger.info(f"Unsubscribing from {len(user_ids)} users...")
        await rt.unsubscribe_many(user_ids)
        logger.info("✅ All unsubscribed!")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await rt.disconnect()
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
