"""
Example: Basic Realtime Chat Integration

This demonstrates:
- Using the decorator-based EventRouter for clean message handling
- Subscribing to a single user's updates
- Receiving AI responses in real-time
- Proper error handling with ProblemDetailsException

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
from magick_mind.realtime.events import (
    ChatMessageEvent,
    ImageGenerationEvent,
    UnknownEvent,
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


async def main():
    # Load credentials from environment
    email = os.environ.get("MAGICKMIND_EMAIL")
    password = os.environ.get("MAGICKMIND_PASSWORD")
    base_url = os.environ.get("MAGICKMIND_BASE_URL", "https://dev-api.magickmind.ai")
    ws_endpoint = os.environ.get("MAGICKMIND_WS_ENDPOINT")

    # Required vars
    if not all([email, password, ws_endpoint]):
        logger.error(
            "Missing required environment variables (MAGICKMIND_EMAIL, MAGICKMIND_PASSWORD, MAGICKMIND_WS_ENDPOINT)"
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

    try:
        # Register event handlers using decorator API
        @client.realtime.on("chat_message")
        async def handle_chat(event: ChatMessageEvent) -> None:
            logger.info(f"Chat message received: {event.payload.message_id}")
            logger.info(f"   Content: {event.payload.message[:80]}")

        @client.realtime.on("image_generation")
        async def handle_image(event: ImageGenerationEvent) -> None:
            logger.info(f"Image generated: {event.payload.message_id}")
            if event.payload.data:
                logger.info(f"   Artifact: {event.payload.data.id}")

        @client.realtime.on_unknown
        async def handle_unknown(event: UnknownEvent) -> None:
            logger.warning(f"Unknown event type: {event.type}")

        # Connect to realtime
        logger.info("Connecting to realtime...")
        await client.realtime.connect()
        logger.info("Realtime client ready!")

        # Default model for chat
        model_id = "openrouter/openrouter/meta-llama/llama-4-maverick"

        # Subscribe to a user's updates
        # Pattern: Service account monitors updates for end users
        target_user = os.environ.get("USER_ID", "user-test-456")
        mindspace_id = os.environ.get("MINDSPACE_ID", "mind-test-123")

        # Show which service account we're connecting as
        service_user_id = await client.get_user_id()

        logger.info(f"Service account JWT sub: {service_user_id}")
        logger.info(f"Subscribing to end user: {target_user}")
        logger.info(f"Expected channel: personal:{target_user}#{service_user_id}")

        await client.realtime.subscribe(target_user_id=target_user)
        logger.info(f"Subscribed to {target_user}")

        # Send a trigger message with proper error handling
        logger.info(f"Sending chat message with model={model_id}...")

        try:
            response = await client.v1.chat.send(
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

    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        await client.realtime.disconnect()
        await client.close()
        logger.info("Disconnected")


if __name__ == "__main__":
    """
    Run this example:
    
    Environment variables:
        MAGICKMIND_EMAIL       - Your service account email
        MAGICKMIND_PASSWORD    - Your service account password
        MAGICKMIND_BASE_URL    - Magick Mind API URL (optional)
        MAGICKMIND_WS_ENDPOINT - WebSocket endpoint (required)
        USER_ID                - End user ID (optional, default: user-test-456)
        MINDSPACE_ID           - Mindspace ID (optional, default: mind-test-123)
        OPENROUTER_API_KEY     - API key for LLM (optional)
    
    Example:
        export MAGICKMIND_EMAIL="service@example.com"
        export MAGICKMIND_PASSWORD="your-password"
        export MAGICKMIND_WS_ENDPOINT="wss://dev-centrifugo.magickmind.ai/connection/websocket"
        python examples/chat_workflow.py
    """
    asyncio.run(main())
