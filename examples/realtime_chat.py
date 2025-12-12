"""
Example of using Realtime features (WebSocket/Centrifugo) with MagickMind SDK.
"""

import asyncio
import os
import logging
from magick_mind import MagickMind
from centrifuge import ClientEventHandler, SubscriptionEventHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("realtime_example")


async def main():
    # Load credentials
    email = os.getenv("BIFROST_EMAIL", "test@example.com")
    password = os.getenv("BIFROST_PASSWORD", "password")
    base_url = os.getenv("BIFROST_BASE_URL", "https://bifrost.example.com")

    # Initialize SDK
    client = MagickMind(email=email, password=password, base_url=base_url)

    logger.info("Connecting to realtime...")

    # Custom event handlers
    class MyClientHandler(ClientEventHandler):
        async def on_connected(self, ctx):
            logger.info(f"Connected: {ctx}")

        async def on_disconnected(self, ctx):
            logger.info(f"Disconnected: {ctx}")

        async def on_publication(self, ctx):
            # Handle server-side publications here
            logger.info(f"Received message via server-side sub: {ctx.pub.data}")

    # Use realtime (async context)
    rt = client.realtime

    try:
        # Connect with handler for server-side events
        await rt.connect(events=MyClientHandler())
        logger.info("Realtime client ready!")

        # Subscribe via RPC (Backend manages the channel)
        sender_id = "user-456"
        logger.info(f"Subscribing to updates from {sender_id}...")

        try:
            await rt.subscribe(target_user_id=sender_id)
            logger.info("Subscribe command sent successfully")
        except Exception as e:
            logger.error(f"Subscribe failed: {e}")

        # Keep alive for a bit
        logger.info("Listening for events... (Press Ctrl+C to stop)")
        await asyncio.sleep(10)

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await rt.disconnect()
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
