#!/usr/bin/env python3
"""
Example: Complete Chat Workflow (HTTP Send + Realtime Receive)

This demonstrates the full chat loop:
1. Send message via HTTP (client.v1.chat.send)
2. Receive AI responses via Realtime (WebSocket)
3. Correlate responses via reply_to_message_id
4. Handle multiple responses (quick reply + slow reply)

Real-World Pattern:
- User sends question via HTTP API (gets message_id back)
- AI sends quick acknowledgment: reply_to_message_id = your message_id
- AI sends full answer later: reply_to_message_id = your message_id
- Your app correlates responses to original message

Key Concepts:
- HTTP for sending (reliable, get message_id)
- Realtime for receiving (low latency, all responses)
- Correlation via reply_to_message_id (match responses to requests)
- Deduplication (group subscriptions cause duplicates)

Production Pattern:
- Use notification pattern: notification → fetch from history API
- Store messages with reply_to_message_id for correlation
- See examples/notification_pattern_example.py for recommended approach
- See examples/backend_service.py for full production implementation

Usage:
    export BIFROST_BASE_URL="http://localhost:8888"
    export BIFROST_EMAIL="user@example.com"
    export BIFROST_PASSWORD="password"
    export BIFROST_WS_ENDPOINT="ws://localhost:8888/connection/websocket"
    uv run python examples/complete_chat_workflow.py
"""

import asyncio
import os
import logging
from typing import Set

from magick_mind import MagickMind
from magick_mind.realtime.handler import RealtimeEventHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("chat_workflow")


class ChatWorkflowHandler(RealtimeEventHandler):
    """
    Handler that displays AI responses as they arrive.

    Features:
    - Deduplication (critical for production)
    - Multi-response handling (quick + slow replies)
    - Simple display as messages arrive
    """

    def __init__(self):
        # Deduplication (use Redis in production!)
        self.processed_ids: Set[str] = set()

        # Simple counter
        self.response_count = 0

    async def on_connected(self, ctx):
        logger.info(f"✅ Connected to realtime! Client: {ctx.client}")

    async def on_message(self, user_id: str, payload: dict):
        """Handle incoming AI response."""
        # Extract message ID
        message_id = payload.get("message_id") or payload.get("id")

        if not message_id:
            logger.warning("Message has no ID, skipping...")
            return

        # Deduplicate - CRITICAL!
        if message_id in self.processed_ids:
            logger.debug(f"⏭️  Skipping duplicate {message_id}")
            return

        self.processed_ids.add(message_id)
        self.response_count += 1

        # Extract correlation info
        content = payload.get("content", "")
        msg_type = payload.get("type", "unknown")
        reply_to = payload.get("reply_to_message_id")  # This correlates responses!

        logger.info("=" * 60)
        logger.info(f"📨 AI Response #{self.response_count}")
        logger.info(f"   Message ID: {message_id}")
        logger.info(f"   Reply To: {reply_to or 'N/A'}")  # Shows correlation
        logger.info(f"   From User: {user_id}")
        logger.info(f"   Type: {msg_type}")
        logger.info(f"   Content: {content[:100]}{'...' if len(content) > 100 else ''}")
        logger.info("=" * 60)

        # Production pattern: Store in database
        # await db.messages.insert({
        #     "message_id": message_id,
        #     "reply_to_message_id": reply_to,  # Correlation!
        #     "user_id": user_id,
        #     "type": msg_type,
        #     "content": content,
        #     "received_at": datetime.utcnow()
        # })


async def main():
    # Get config from environment
    base_url = os.getenv("BIFROST_BASE_URL", "http://localhost:8888")
    ws_endpoint = os.getenv("BIFROST_WS_ENDPOINT")
    email = os.getenv("BIFROST_EMAIL")
    password = os.getenv("BIFROST_PASSWORD")

    if not email or not password:
        logger.error("BIFROST_EMAIL and BIFROST_PASSWORD are required")
        return

    # Initialize client
    logger.info("Initializing Magick Mind SDK...")
    client = MagickMind(
        base_url=base_url, email=email, password=password, ws_endpoint=ws_endpoint
    )

    # Create handler
    handler = ChatWorkflowHandler()

    try:
        # Step 1: Connect to Realtime FIRST
        logger.info("\n--- Step 1: Connect to Realtime ---")
        await client.realtime.connect(events=handler)
        logger.info("✅ Realtime connected")

        # Step 2: Subscribe to your user's updates
        sender_id = "user-123"  # Your user ID
        logger.info(f"\n--- Step 2: Subscribe to {sender_id} ---")
        await client.realtime.subscribe(sender_id)
        logger.info(f"✅ Subscribed to {sender_id}")

        # Give realtime connection a moment to stabilize
        await asyncio.sleep(1)

        # Step 3: Send chat message via HTTP
        logger.info("\n--- Step 3: Send Chat Message via HTTP ---")

        # You need valid API key and mindspace
        api_key = os.getenv("OPENROUTER_API_KEY") or "sk-test-key"
        mindspace_id = os.getenv("MINDSPACE_ID") or "mind-test-123"

        logger.info(f"Sending message to mindspace: {mindspace_id}")

        response = client.v1.chat.send(
            api_key=api_key,
            mindspace_id=mindspace_id,
            message="What is the meaning of life? Please think carefully.",
            sender_id=sender_id,
            fast_brain_model_id="openrouter/meta-llama/llama-3.1-8b-instruct:free",
        )

        if response.success:
            original_message_id = response.content.message_id
            logger.info("✅ Message sent successfully!")
            logger.info(f"   Message ID: {original_message_id}")
            logger.info(
                f"   AI responses will have reply_to_message_id = {original_message_id}"
            )
        else:
            logger.error(f"❌ Failed to send message: {response.message}")
            return

        # Step 4: Wait for AI responses via Realtime
        logger.info("\n--- Step 4: Waiting for AI Responses via Realtime ---")
        logger.info("AI may send multiple responses:")
        logger.info("  1. Quick reply (within 30s): Acknowledgment")
        logger.info("  2. Slow reply (2-5 mins): Full answer")
        logger.info("\nListening for 60 seconds...\n")

        # Listen for responses
        await asyncio.sleep(60)

        # Step 5: Show summary
        logger.info("\n--- Step 5: Summary ---")
        logger.info(f"Received {handler.response_count} response(s)")
        logger.info(f"Unique messages processed: {len(handler.processed_ids)}")

        if handler.response_count == 0:
            logger.warning("No responses received. This could mean:")
            logger.info("  - Invalid API key or mindspace")
            logger.info("  - AI is taking longer than 60s")
            logger.info("  - Bifrost configuration issue")

    except KeyboardInterrupt:
        logger.info("\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("\n--- Cleanup ---")
        await client.realtime.disconnect()
        client.close()
        logger.info("Disconnected")


if __name__ == "__main__":
    """
    This example demonstrates the complete workflow:
    
    1. HTTP for sending:
       - Reliable delivery
       - Get message_id back
       - Use typed resources (client.v1.chat.send)
    
    2. Realtime for receiving:
       - Low latency
       - Handle multiple responses per request
       - Correlate via reply_to_message_id
       - Deduplicate automatically
    
    3. Message correlation:
       - User sends: gets message_id "msg_123"
       - AI responds: reply_to_message_id = "msg_123"
       - Build conversation threads in your DB
    
    4. Multi-response pattern:
       - Quick acknowledgment: reply_to = msg_123
       - Slow thoughtful reply: reply_to = msg_123
       - Both correlated to original message
    
    Production Pattern (Notification + History Fetch):
    
    Recommended: Use notification pattern instead of storing realtime payload directly.
    
    ```python
    class ProductionHandler(RealtimeEventHandler):
        def __init__(self, client, db, redis):
            self.client = client
            self.db = db
            self.redis = redis
        
        async def on_message(self, user_id, payload):
            message_id = payload["message_id"]
            
            # 1. Deduplicate with Redis
            if not self.redis.sadd("processed", message_id):
                return
            
            # 2. Don't store payload! Fetch from history (source of truth)
            mindspace_id = payload.get("mindspace_id")
            history = self.client.v1.history.get_messages(
                mindspace_id=mindspace_id,
                limit=10  # Get recent messages
            )
            
            # 3. Store messages from history API
            for msg in history.chat_histories:
                await self.db.messages.insert({
                    "message_id": msg.id,
                    "reply_to_message_id": msg.reply_to_message_id,
                    "user_id": user_id,
                    "mindspace_id": mindspace_id,
                    "content": msg.content,
                    "type": msg.type,
                    "created_at": msg.created_at
                })
            
            # 4. Notify frontend (WebSocket, push, etc.)
            await self.notify_frontend(user_id, message_id)
    ```
    
    This ensures:
    - History API as source of truth (not realtime payload)
    - Correlation via reply_to_message_id
    - No data consistency issues
    - Redis deduplication prevents duplicate processing
    
    See also:
    - examples/notification_pattern_example.py - Recommended pattern
    - examples/backend_service.py - Full production pattern
    - examples/bulk_subscribe.py - Multi-user deduplication
    - docs/realtime_guide.md - Complete documentation
    - docs/guides/backend_integration.md - Production patterns
    """
    asyncio.run(main())
