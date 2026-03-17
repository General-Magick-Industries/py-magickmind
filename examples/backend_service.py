"""
Backend Service Example

Demonstrates production-ready pattern for backend services using the SDK.

This example shows:
- Message deduplication
- Hybrid realtime + periodic sync
- Recovery from disconnects
- Reliable message processing

Use this as a template for your own backend integration.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional, Set

from magick_mind import MagickMind
from magick_mind.realtime.events import ChatMessageEvent, ChatMessagePayload

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ChatBackendService:
    """
    Production-ready backend service for handling chat messages.

    Features:
    - Deduplication to prevent double-processing
    - Realtime events for low latency
    - Periodic sync for reliability
    - Recovery from disconnects

    Architecture:
        [Your Frontend] <-> [This Service + SDK] <-> [Bifrost]
    """

    def __init__(self, client: MagickMind):
        self.client = client

        # Message tracking (use Redis or DB in production!)
        self.processed_messages: Set[str] = set()

        # Sync cursor for pagination
        self.last_sync_cursor: Optional[str] = None

        # Metrics
        self.metrics = {
            "received": 0,
            "processed": 0,
            "duplicates": 0,
            "errors": 0,
        }

    async def handle_chat_event(self, event: ChatMessageEvent) -> None:
        """
        Handle incoming chat_message realtime event.

        This is the fast path - processes events as they arrive.
        """
        self.metrics["received"] += 1
        payload = event.payload

        try:
            logger.info(f"Received event: {payload.message_id}")

            # Deduplicate - critical for backends!
            if payload.message_id in self.processed_messages:
                logger.debug(f"Skipping duplicate: {payload.message_id}")
                self.metrics["duplicates"] += 1
                return

            # Process the message
            await self._process_message(payload)

            # Mark as processed
            self.processed_messages.add(payload.message_id)
            self.metrics["processed"] += 1

        except Exception as e:
            logger.error(f"Failed to handle event: {e}", exc_info=True)
            self.metrics["errors"] += 1

    async def _process_message(self, payload: ChatMessagePayload) -> None:
        """
        Core business logic for processing a chat message.

        This is where you implement your specific requirements:
        - Store in your database
        - Trigger webhooks
        - Notify your frontend
        - Update analytics
        - etc.
        """
        content_preview = payload.message[:50]
        logger.info(f"Processing message {payload.message_id}: {content_preview}...")

        # Example: Store in your database
        message_data = {
            "message_id": payload.message_id,
            "task_id": payload.task_id,
            "content": payload.message,
            "reply_to": payload.reply_to,
            "processed_at": datetime.utcnow().isoformat(),
        }

        # TODO: Replace with your actual database
        # await your_db.messages.insert_one(message_data)
        logger.info(f"Would store: {message_data}")

        # Example: Notify your frontend via WebSocket
        # TODO: Replace with your actual WebSocket server
        # await your_websocket_server.broadcast({
        #     "type": "new_message",
        #     "payload": payload.model_dump(),
        # })
        logger.info("Would broadcast to frontend")

        # Example: Trigger webhook
        # TODO: Replace with your actual webhook
        # await httpx.post("https://your-app.com/webhook", json=message_data)
        logger.info("Would trigger webhook")

    async def sync_history(
        self, mindspace_id: str, since_message_id: Optional[str] = None
    ) -> None:
        """
        Sync chat history from Bifrost.

        This is the reliable fallback that catches any missed events.

        Use cases:
        - On startup: Get recent history
        - After reconnect: Fill gaps
        - Periodic: Verify consistency
        """
        logger.info(f"Syncing history (since={since_message_id or 'beginning'})...")

        try:
            # TEMP: Direct HTTP call until history resource is added to SDK
            # In future: messages = await self.client.v1.mindspaces.get_messages(...)

            response = await self.client.http.get(
                "/v1/mindspaces/messages",
                params={
                    "mindspace_id": mindspace_id,
                    "after_id": since_message_id or "",
                    "limit": 100,
                },
            )

            messages = response.get("chat_histories", [])

            logger.info(f"Fetched {len(messages)} messages from history")

            # Process each message
            for msg_data in messages:
                # Map history format to ChatMessagePayload
                # Note: History might have different field names than realtime events
                payload = ChatMessagePayload(
                    mindspace_id=msg_data.get("mindspace_id", ""),
                    message_id=msg_data["id"],
                    task_id=msg_data.get("task_id", ""),
                    message=msg_data["content"],
                    reply_to=msg_data.get("reply_to_message_id"),
                )

                # Check if already processed
                if payload.message_id not in self.processed_messages:
                    await self._process_message(payload)
                    self.processed_messages.add(payload.message_id)

            # Update cursor for next sync
            if messages:
                self.last_sync_cursor = messages[-1]["id"]
                logger.info(f"Updated sync cursor to {self.last_sync_cursor}")

        except Exception as e:
            logger.error(f"History sync failed: {e}", exc_info=True)
            self.metrics["errors"] += 1

    async def periodic_sync(self, mindspace_id: str, interval: int = 300) -> None:
        """
        Run periodic sync in background to catch missed events.

        Args:
            mindspace_id: Mindspace to sync
            interval: Seconds between syncs (default: 5 minutes)
        """
        logger.info(f"Starting periodic sync (every {interval}s)")

        while True:
            await asyncio.sleep(interval)

            try:
                logger.info("Running periodic sync...")
                await self.sync_history(
                    mindspace_id=mindspace_id, since_message_id=self.last_sync_cursor
                )
                logger.info(f"Metrics: {self.metrics}")

            except Exception as e:
                logger.error(f"Periodic sync failed: {e}", exc_info=True)

    async def start(self, mindspace_id: str, user_id: str) -> None:
        """
        Start the backend service.

        This is the main entry point that sets everything up.

        Args:
            mindspace_id: Mindspace to monitor
            user_id: Service user ID for authentication
        """
        logger.info("=" * 60)
        logger.info("Starting Chat Backend Service")
        logger.info("=" * 60)

        # 1. Register event handlers using decorator API
        @self.client.realtime.on("chat_message")
        async def handle_chat(event: ChatMessageEvent) -> None:
            await self.handle_chat_event(event)

        # 2. Initial history sync
        logger.info("Step 1: Syncing initial history...")
        await self.sync_history(mindspace_id=mindspace_id)

        # 3. Connect to realtime WebSocket
        logger.info("Step 2: Connecting to realtime...")
        await self.client.realtime.connect()

        # 4. Subscribe to chat events
        logger.info("Step 3: Subscribing to events...")
        await self.client.realtime.subscribe(target_user_id=user_id)

        # 5. Start periodic sync in background
        logger.info("Step 4: Starting periodic sync...")
        asyncio.create_task(self.periodic_sync(mindspace_id))

        logger.info("=" * 60)
        logger.info("✓ Backend service is running!")
        logger.info("  - Listening for realtime events")
        logger.info("  - Periodic sync active")
        logger.info("=" * 60)


async def main() -> None:
    """Main entry point for the backend service."""

    # Load configuration from environment
    bifrost_url = os.getenv("BIFROST_URL", "https://bifrost.example.com")
    bifrost_email = os.getenv("BIFROST_EMAIL")
    bifrost_password = os.getenv("BIFROST_PASSWORD")
    mindspace_id = os.getenv("MINDSPACE_ID", "mind-123")
    user_id = os.getenv("USER_ID", "service-user")

    if not bifrost_email or not bifrost_password:
        logger.error("BIFROST_EMAIL and BIFROST_PASSWORD must be set!")
        return

    # Initialize SDK client
    logger.info(f"Initializing client (URL: {bifrost_url})...")
    client = MagickMind(
        base_url=bifrost_url,
        email=bifrost_email,
        password=bifrost_password,
    )

    # Create and start backend service
    service = ChatBackendService(client)

    try:
        await service.start(mindspace_id=mindspace_id, user_id=user_id)

        # Keep running indefinitely
        await asyncio.Future()

    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Cleanup
        await client.close()
        logger.info(f"Final metrics: {service.metrics}")


if __name__ == "__main__":
    """
    Run the backend service.

    Environment variables:
        BIFROST_URL         - Bifrost API URL
        BIFROST_EMAIL       - Service account email
        BIFROST_PASSWORD    - Service account password
        MINDSPACE_ID        - Mindspace to monitor
        USER_ID             - Service user ID

    Example:
        export BIFROST_URL="https://bifrost.yourcompany.com"
        export BIFROST_EMAIL="service@yourcompany.com"
        export BIFROST_PASSWORD="your-password"
        export MINDSPACE_ID="mind-123"
        export USER_ID="service-user-456"

        python examples/backend_service.py
    """
    asyncio.run(main())
