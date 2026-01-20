"""
Example: Fan-Out Relay Service (Production Pattern)

This demonstrates building a relay/middleware service that:
1. Subscribes to multiple user channels
2. Receives messages from Bifrost
3. Processes and forwards them to your frontend (WebSocket, SSE, FCM, etc.)

Architecture:
    [End User Frontends] ← [Your Relay Service + SDK] ← [Bifrost]

Key Concepts:
- Per-user subscriptions (100 users = 100 subscriptions on 1 connection)
- Message deduplication (critical when users are in same group)
- Centralized handler routing messages to correct frontend connections

Use Cases:
- Telegram/Discord bots
- Mobile app backends (push notifications)
- Web app backends (WebSocket/SSE to browser)
- Admin dashboards

For a complete production example with Redis dedup and history sync,
see: examples/backend_service.py
"""

import asyncio
import logging
from typing import Dict, Set, Any

from magick_mind.realtime.handler import RealtimeEventHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RelayService")


class RelayService(RealtimeEventHandler):
    """
    Central handler for relaying messages to end-user frontends.

    In production, this would:
    - Maintain WebSocket connections to end-user frontends
    - Use Redis for deduplication
    - Handle reconnection and error recovery
    """

    def __init__(self):
        # Deduplication (use Redis in production!)
        self.processed_ids: Set[str] = set()

        # Mock: Your frontend connections (WebSocket, SSE, FCM tokens, etc.)
        self.frontend_connections: Dict[str, Any] = {}

        # Metrics
        self.metrics = {
            "received": 0,
            "duplicates": 0,
            "relayed": 0,
            "errors": 0,
        }

    async def on_connected(self, ctx) -> None:
        logger.info(f"✅ Connected to Bifrost! Client ID: {ctx.client}")

    async def on_message(self, user_id: str, payload: Dict[str, Any]) -> None:
        """
        High-level handler: User ID is already extracted!

        This is called for every message. The SDK has already:
        - Parsed the channel name
        - Extracted the user_id
        - Deserialized the payload
        """
        self.metrics["received"] += 1

        # Get message ID for deduplication
        message_id = payload.get("message_id") or payload.get("id")
        if not message_id:
            logger.warning(f"Message for {user_id} has no ID, processing anyway...")
            message_id = f"no-id-{self.metrics['received']}"

        # CRITICAL: Deduplicate
        if message_id in self.processed_ids:
            self.metrics["duplicates"] += 1
            logger.debug(f"⏭️  Skipping duplicate {message_id}")
            return

        logger.info(f"📨 Message for [{user_id}]: {payload.get('type', 'unknown')}")

        try:
            # Process and relay to frontend
            await self.relay_to_frontend(user_id, payload)

            # Mark as processed AFTER successful relay
            self.processed_ids.add(message_id)
            self.metrics["relayed"] += 1

        except Exception as e:
            logger.error(f"Failed to relay message {message_id}: {e}")
            self.metrics["errors"] += 1
            # Don't mark as processed if relay failed
            # Will retry on duplicate (or catch in history sync)

    async def relay_to_frontend(self, user_id: str, payload: Dict[str, Any]) -> None:
        """
        Relay message to end-user's frontend connection.

        In production, this would:
        - Look up user's WebSocket connection
        - Send message via SSE/WebSocket/FCM
        - Handle disconnected users gracefully
        """
        # Mock delay to simulate network I/O
        await asyncio.sleep(0.01)

        # Mock: Find user's frontend connection
        connection = self.frontend_connections.get(user_id)

        if connection:
            logger.info(f"   🚀 Relaying to frontend connection for user {user_id}")
            # In production:
            # await connection.send_json(payload)
        else:
            logger.warning(
                f"   ⚠️  No frontend connection for {user_id}, storing for later..."
            )
            # In production:
            # await redis.lpush(f"pending:{user_id}", json.dumps(payload))

    def register_frontend(self, user_id: str, connection: Any):
        """Register a frontend connection for a user."""
        self.frontend_connections[user_id] = connection
        logger.info(f"Registered frontend connection for {user_id}")

    def unregister_frontend(self, user_id: str):
        """Unregister a frontend connection."""
        if user_id in self.frontend_connections:
            del self.frontend_connections[user_id]
            logger.info(f"Unregistered frontend connection for {user_id}")


async def main():
    """
    Demo: Simulate relay service with mock data.

    In production, you would:
    1. Initialize MagickMind client
    2. Create RelayService handler
    3. Connect to realtime
    4. Subscribe to user IDs via subscribe_many()
    5. Handle frontend connections (WebSocket server, etc.)
    """
    print("=" * 60)
    print("Relay Service Demo (Mock)")
    print("=" * 60)

    # Create relay service
    relay = RelayService()

    # Simulate frontend connections
    relay.register_frontend("user_123", "mock_websocket_conn_1")
    relay.register_frontend("user_456", "mock_websocket_conn_2")

    print(f"\n✅ Registered {len(relay.frontend_connections)} frontend connections")

    # Simulate incoming messages
    print("\n--- Simulating Incoming Messages ---\n")

    # Message 1: First time
    await relay.on_message(
        "user_123",
        {
            "message_id": "msg_001",
            "type": "agent_response",
            "content": "Hello from AI!",
        },
    )

    # Message 2: Duplicate (will be skipped)
    await relay.on_message(
        "user_123",
        {
            "message_id": "msg_001",  # Same ID!
            "type": "agent_response",
            "content": "Hello from AI!",
        },
    )

    # Message 3: Different user, different message
    await relay.on_message(
        "user_456",
        {
            "message_id": "msg_002",
            "type": "agent_response",
            "content": "Different message",
        },
    )

    # Message 4: User without frontend connection
    await relay.on_message(
        "user_789",
        {
            "message_id": "msg_003",
            "type": "agent_response",
            "content": "No frontend for this user",
        },
    )

    # Show metrics
    print("\n--- Metrics ---")
    print(f"Received: {relay.metrics['received']}")
    print(f"Duplicates skipped: {relay.metrics['duplicates']}")
    print(f"Successfully relayed: {relay.metrics['relayed']}")
    print(f"Errors: {relay.metrics['errors']}")
    print(f"Unique messages processed: {len(relay.processed_ids)}")

    print("\n--- Done ---")


if __name__ == "__main__":
    """
    Production Setup:
    
    1. Use RealtimeClient with this handler:
        client = MagickMind(email="...", password="...", base_url="...")
        relay = RelayService()
        await client.realtime.connect(events=relay)
        await client.realtime.subscribe_many(user_ids)
    
    2. Add Redis for deduplication:
        self.redis = redis.Redis()
        if not self.redis.sadd("processed_msgs", message_id):
            return  # Duplicate
    
    3. Integrate with your WebSocket/SSE server:
        class RelayService(RealtimeEventHandler):
            def __init__(self, websocket_server):
                self.ws_server = websocket_server
            
            async def relay_to_frontend(self, user_id, payload):
                await self.ws_server.send_to_user(user_id, payload)
    
    4. See examples/backend_service.py for complete production pattern
    """
    asyncio.run(main())
