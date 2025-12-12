"""
Example: Fan-Out / Relay Service

This script demonstrates how to Build a "Relay Service" using the Magick Mind SDK.
It uses the high-level `RealtimeEventHandler` to automatically parse channel names.
"""

import asyncio
import logging
import json
from typing import Dict, Any

from centrifuge import ConnectedContext
from magick_mind.realtime.handler import RealtimeEventHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RelayService")


class RelayHandler(RealtimeEventHandler):
    """
    Central handler for all realtime events.
    """

    async def on_connected(self, ctx: ConnectedContext) -> None:
        logger.info(f"✅ Connected to Bifrost! Client ID: {ctx.client}")

    async def on_message(self, user_id: str, payload: Any) -> None:
        """
        High-level handler: User ID is already extracted!
        """
        logger.info(f"📨 Message for [{user_id}]: {json.dumps(payload)}")

        # Relay to frontend
        await self.relay_to_frontend(user_id, payload)

    async def relay_to_frontend(self, user_id: str, payload: Dict[str, Any]) -> None:
        """
        Mock function to push data to your actual frontend.
        """
        await asyncio.sleep(0.01)
        print(f"   🚀 [RELAY] Pushing to Frontend Connection for User {user_id}...")


async def main():
    print("--- Starting Relay Service (High-Level) ---")

    handler = RelayHandler()

    # Simulate an incoming event loop (MockCtx)

    # Mock context structure to simulate "personal:user_123#svc_456"
    # We use a simple class to avoid instantiating the actual library class which might require more args
    class MockPub:
        data = {"type": "agent_response", "content": "Hello world!"}
        channel = "personal:user_123#svc_456"

    class MockCtx:
        channel = "personal:user_123#svc_456"
        pub = MockPub()

    print("\n--- Simulating Incoming Message ---")

    # The handler internal logic should extract "user_123"
    await handler.on_publication(MockCtx())

    print("\n--- Done ---")


if __name__ == "__main__":
    asyncio.run(main())
