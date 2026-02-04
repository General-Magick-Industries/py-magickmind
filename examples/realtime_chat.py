"""
Example: Basic Realtime Chat Integration

This demonstrates:
- Using RealtimeEventHandler for clean message handling
- Subscribing to a single user's updates
- Receiving AI responses in real-time

For production backend services with multiple users, see:
- examples/bulk_subscribe.py - Handling many users
- examples/backend_service.py - Full production pattern with deduplication
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

from magick_mind import MagickMind
from magick_mind.models.v1.chat import ConfigSchema
from magick_mind.realtime.handler import RealtimeEventHandler

# Load environment variables
load_dotenv()

# Setup logging
# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")
# Enable debug logs for centrifuge to see disconnect reason
logging.getLogger("centrifuge").setLevel(logging.DEBUG)
logger = logging.getLogger("realtime_chat")


class MyRealtimeHandler(RealtimeEventHandler):
    """
    High-level event handler with automatic user ID parsing.
    """

    async def on_connected(self, ctx):
        logger.info(f"✅ Connected to realtime! Client ID: {ctx.client}")

    async def on_disconnected(self, ctx):
        logger.info(f"⚠️  Disconnected: {ctx}")

    async def on_message(self, user_id: str, payload: dict):
        """
        Called when a message is received.

        The SDK automatically extracts the user_id from the channel.
        You just get clean user_id + payload.
        """
        logger.info(f"📨 Message for user [{user_id}]:")
        logger.info(f"   Content: {payload.get('content', payload)}")
        logger.info(f"   Type: {payload.get('type', 'unknown')}")


async def main():
    # Load credentials from environment
    email = os.environ.get("BIFROST_EMAIL")
    password = os.environ.get("BIFROST_PASSWORD")
    base_url = os.environ.get("BIFROST_BASE_URL", "https://dev-bifrost.magickmind.ai")
    ws_endpoint = os.environ.get("BIFROST_WS_ENDPOINT")

    # Required vars
    if not all([email, password, ws_endpoint]):
        logger.error(
            "Missing required environment variables (BIFROST_EMAIL, BIFROST_PASSWORD, BIFROST_WS_ENDPOINT)"
        )
        return

    # Initialize SDK
    client = MagickMind(
        email=email, password=password, base_url=base_url, ws_endpoint=ws_endpoint
    )

    # Create handler
    handler = MyRealtimeHandler()

    try:
        # Connect to realtime with our handler
        logger.info("Connecting to realtime...")
        await client.realtime.connect(events=handler)
        logger.info("Realtime client ready!")

        # Verify Models (Client-Side)
        logger.info("Fetching available models...")
        # Note: client.models.list() is a sync call
        models_resp = await asyncio.to_thread(client.models.list)
        available_models = models_resp.data
        available_ids = [m.id for m in available_models]
        model_id = "openrouter/openrouter/meta-llama/llama-4-maverick"

        # Check if the server explicitly advertises this model or a suitable alternative
        # But prioritize the user's requested default if valid.

        # (Optional) If we wanted to fallback to 'magickmind' if available:
        # if "magickmind" in available_ids and model_id not in available_ids:
        #    ...

        # For now, we trust 'openai/gpt-4o-mini' works via pass-through even if not listed.
        if model_id not in available_ids:
            logger.info(
                f"Model '{model_id}' not in declared list, but using it as default."
            )
        # elif available_ids:
        #     # Use the first available one, attaching provider if present
        #     m = available_models[0]
        #     if m.provider:
        #         model_id = f"{m.provider}/{m.id}"
        #     else:
        #         model_id = m.id
        #     logger.info(f"Default 'magickmind' not found. Using fallback: {model_id}")
        # else:
        #     logger.warning("No models found! Using default 'magickmind' anyway.")

        # Subscribe to a user's updates
        # Pattern: Service account monitors updates for end users
        target_user = "user-test-456"  # The end user we're monitoring
        mindspace_id = "mind-test-123"

        # Debug: Show what JWT subject we're using
        import base64
        import json

        token = client.auth.get_token()
        payload = token.split(".")[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        service_user_id = decoded["sub"]

        logger.info(f"Service account JWT sub: {service_user_id}")
        logger.info(f"Subscribing to end user: {target_user}")
        logger.info(f"Expected channel: personal:{target_user}#{service_user_id}")

        await client.realtime.subscribe(target_user_id=target_user)
        logger.info(f"✅ Subscribed to {target_user}")

        # Send a trigger message
        logger.info(f"🚀 Sending chat message with model={model_id}...")

        # CRITICAL: The JWT subject from the WebSocket connection MUST match
        # the account making the chat request. Otherwise channels won't match!
        # Using the same authenticated client for both ensures this.

        # Run sync HTTP request in thread to avoid blocking async loop
        response = await asyncio.to_thread(
            client.v1.chat.send,
            api_key=os.getenv("OPENROUTER_API_KEY", "sk-test"),
            mindspace_id=mindspace_id,
            message="Hello from Realtime Example! Tell me a one-liner joke.",
            enduser_id=target_user,
            config=ConfigSchema(
                fast_model_id=model_id,
                smart_model_ids=[model_id],
                compute_power=50,
            ),
        )
        if response.content:
            logger.info(f"✅ Message sent! ID: {response.content.message_id}")
            logger.info(f"ℹ️  Sync Response Content: {response.content.content}")
        else:
            logger.info("✅ Message sent (no content in response)!")
        logger.info("Waiting for realtime events...")

        # Keep listening for a bit longer to receive the response
        logger.info("Listening for events... (Press Ctrl+C to stop)")
        await asyncio.sleep(
            60
        )  # Increased to 60 seconds to ensure we receive the response

    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
    finally:
        await client.realtime.disconnect()
        client.close()
        logger.info("Disconnected")


if __name__ == "__main__":
    """
    Run this example:
    
    Environment variables:
        BIFROST_EMAIL       - Your service account email
        BIFROST_PASSWORD    - Your service account password
        BIFROST_BASE_URL    - Bifrost API URL (optional)
        BIFROST_WS_ENDPOINT - WebSocket endpoint (optional)
    
    Example:
        export BIFROST_EMAIL="service@example.com"
        export BIFROST_PASSWORD="your-password"
        python examples/realtime_chat.py
    """
    asyncio.run(main())
