"""
Example: Basic Realtime Chat Integration

This demonstrates:
- Using RealtimeEventHandler for clean message handling
- Subscribing to a single user's updates
- Receiving AI responses in real-time
- Proper error handling with ProblemDetailsException
- Proper error handling with ProblemDetailsException

For production backend services with multiple users, see:
- examples/bulk_subscribe.py - Handling many users
- examples/backend_service.py - Full production pattern with deduplication
"""

import asyncio
import os
import logging
from typing import List
from dotenv import load_dotenv

from magick_mind import MagickMind
from magick_mind.models.v1.chat import ConfigSchema
from magick_mind.models.v1.model import Model
from magick_mind.realtime.handler import RealtimeEventHandler
from magick_mind.exceptions import (
    AuthenticationError,
    ProblemDetailsException,
    ValidationError,
    RateLimitError,
)
from magick_mind.exceptions import (
    AuthenticationError,
    ProblemDetailsException,
    ValidationError,
    RateLimitError,
)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")
# Enable debug logs for centrifuge to see disconnect reason
logging.getLogger("centrifuge").setLevel(logging.DEBUG)
logger = logging.getLogger("realtime_chat")


class MyRealtimeHandler(RealtimeEventHandler):
    """
    High-level event handler with automatic user ID parsing.
    """

    async def on_connected(self, ctx):
        logger.info(f"Connected to realtime! Client ID: {ctx.client}")
        logger.info(f"Connected to realtime! Client ID: {ctx.client}")

    async def on_disconnected(self, ctx):
        logger.info(f"Disconnected: {ctx}")
        logger.info(f"Disconnected: {ctx}")

    async def on_message(self, user_id: str, payload: dict):
        """
        Called when a message is received.

        The SDK automatically extracts the user_id from the channel.
        You just get clean user_id + payload.
        """
        logger.info(f"Message for user [{user_id}]:")
        logger.info(f"Message for user [{user_id}]:")
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

    # Initialize SDK with error handling
    try:
        client = MagickMind(
            email=email,  # type: ignore (validated above)
            password=password,  # type: ignore (validated above)
            base_url=base_url,
            ws_endpoint=ws_endpoint,
        )
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        return
    # Initialize SDK with error handling
    try:
        client = MagickMind(
            email=email,  # type: ignore (validated above)
            password=password,  # type: ignore (validated above)
            base_url=base_url,
            ws_endpoint=ws_endpoint,
        )
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        return

    # Create handler
    handler = MyRealtimeHandler()

    try:
        # Connect to realtime with our handler
        logger.info("Connecting to realtime...")
        await client.realtime.connect(events=handler)
        logger.info("Realtime client ready!")

        # Verify Models (Client-Side)
        logger.info("Fetching available models...")
        try:
            # Note: client.models.list() is a sync call
            available_models: List[Model] = await asyncio.to_thread(client.models.list)
            available_ids = [m.id for m in available_models]
            model_id = "openrouter/openrouter/meta-llama/llama-4-maverick"

            if model_id not in available_ids:
                logger.info(
                    f"Model '{model_id}' not in declared list, but using it as default."
                )
        except ProblemDetailsException as e:
            logger.warning(f"Could not fetch models: [{e.status}] {e.detail}")
            model_id = "openrouter/openrouter/meta-llama/llama-4-maverick"
            if model_id not in available_ids:
                logger.info(
                    f"Model '{model_id}' not in declared list, but using it as default."
                )
        except ProblemDetailsException as e:
            logger.warning(f"Could not fetch models: [{e.status}] {e.detail}")
            model_id = "openrouter/openrouter/meta-llama/llama-4-maverick"

        # Subscribe to a user's updates
        # Pattern: Service account monitors updates for end users
        target_user = os.environ.get("USER_ID", "user-test-456")
        mindspace_id = os.environ.get("MINDSPACE_ID", "mind-test-123")
        target_user = os.environ.get("USER_ID", "user-test-456")
        mindspace_id = os.environ.get("MINDSPACE_ID", "mind-test-123")

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
        logger.info(f"Subscribed to {target_user}")
        logger.info(f"Subscribed to {target_user}")

        # Send a trigger message with proper error handling
        logger.info(f"Sending chat message with model={model_id}...")
        # Send a trigger message with proper error handling
        logger.info(f"Sending chat message with model={model_id}...")

        try:
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
                logger.info(f"Message sent! ID: {response.content.message_id}")
                logger.info(f"Sync Response Content: {response.content.content}")
            else:
                logger.info("Message sent (no content in response)!")

        except ValidationError as e:
            # Handle field-level validation errors (400 Bad Request)
            logger.error(f"Validation error: {e.title}")
            for field, messages in e.get_field_errors().items():
                logger.error(f"  - {field}: {', '.join(messages)}")
            return

        except ProblemDetailsException as e:
            # Handle other API errors with rich details
            logger.error(f"Chat API error: [{e.status}] {e.title}")
            logger.error(f"  Detail: {e.detail}")
            if e.request_id:
                logger.error(f"  Request ID: {e.request_id} (save this for support)")
            if e.instance:
                logger.error(f"  Instance: {e.instance}")
            return

        except RateLimitError as e:
            logger.error(f"Rate limited: {e}")
            logger.error("Please wait before retrying.")
            return

        # Keep listening for realtime events
        try:
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
                logger.info(f"Message sent! ID: {response.content.message_id}")
                logger.info(f"Sync Response Content: {response.content.content}")
            else:
                logger.info("Message sent (no content in response)!")

        except ValidationError as e:
            # Handle field-level validation errors (400 Bad Request)
            logger.error(f"Validation error: {e.title}")
            for field, messages in e.get_field_errors().items():
                logger.error(f"  - {field}: {', '.join(messages)}")
            return

        except ProblemDetailsException as e:
            # Handle other API errors with rich details
            logger.error(f"Chat API error: [{e.status}] {e.title}")
            logger.error(f"  Detail: {e.detail}")
            if e.request_id:
                logger.error(f"  Request ID: {e.request_id} (save this for support)")
            if e.instance:
                logger.error(f"  Instance: {e.instance}")
            return

        except RateLimitError as e:
            logger.error(f"Rate limited: {e}")
            logger.error("Please wait before retrying.")
            return

        # Keep listening for realtime events
        logger.info("Waiting for realtime events...")
        logger.info("Listening for events... (Press Ctrl+C to stop)")
        await asyncio.sleep(60)
        await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        logger.error(f"Unexpected error: {e}", exc_info=True)
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
        BIFROST_WS_ENDPOINT - WebSocket endpoint (required)
        USER_ID             - End user ID (optional, default: user-test-456)
        MINDSPACE_ID        - Mindspace ID (optional, default: mind-test-123)
        OPENROUTER_API_KEY  - API key for LLM (optional)
        BIFROST_WS_ENDPOINT - WebSocket endpoint (required)
        USER_ID             - End user ID (optional, default: user-test-456)
        MINDSPACE_ID        - Mindspace ID (optional, default: mind-test-123)
        OPENROUTER_API_KEY  - API key for LLM (optional)
    
    Example:
        export BIFROST_EMAIL="service@example.com"
        export BIFROST_PASSWORD="your-password"
        export BIFROST_WS_ENDPOINT="wss://dev-bifrost.magickmind.ai/connection/websocket"
        export BIFROST_WS_ENDPOINT="wss://dev-bifrost.magickmind.ai/connection/websocket"
        python examples/realtime_chat.py
    """
    asyncio.run(main())
