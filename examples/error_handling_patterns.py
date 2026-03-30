"""
Example: Comprehensive Error Handling Patterns

Demonstrates:
- All SDK exception types and when they're raised
- Field-level validation error handling
- Request ID usage for support tickets
- Retry patterns with exponential backoff
- Logging integration for production
- Error monitoring patterns (Sentry-ready)

Run this example to see proper error handling in action:
    export MAGICKMIND_EMAIL="your@email.com"
    export MAGICKMIND_PASSWORD="your_password"
    export MAGICKMIND_BASE_URL="https://api.magickmind.ai"
    python examples/error_handling_patterns.py
"""

import asyncio
import logging
import os
import time
from typing import Optional

from dotenv import load_dotenv

from magick_mind import MagickMind
from magick_mind.exceptions import (
    AuthenticationError,
    MagickMindError,
    ProblemDetailsException,
    RateLimitError,
    ValidationError,
)
from magick_mind.models.v1.chat import ChatSendResponse

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions for Production Patterns
# ============================================================================


def handle_validation_error(e: ValidationError) -> dict:
    """
    Extract and log field-level validation errors.

    This pattern is useful for displaying errors to users in a UI.
    """
    logger.error(f"Validation failed: {e.title}")
    logger.error(f"Request ID: {e.request_id} (save for support)")

    # Group errors by field for UI display
    field_errors = e.get_field_errors()
    for field, messages in field_errors.items():
        logger.error(f"  {field}:")
        for msg in messages:
            logger.error(f"    - {msg}")

    # Example: Return this structure for JSON API responses
    return {
        "error": "validation_failed",
        "message": e.title,
        "fields": field_errors,
        "request_id": e.request_id,
    }


def exponential_backoff(attempt: int, base_delay: float = 1.0) -> float:
    """
    Calculate exponential backoff delay with maximum cap.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds

    Returns:
        Delay in seconds (capped at 60s)
    """
    return min(base_delay * (2**attempt), 60.0)


def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an error should be retried.

    Retry policy:
    - Rate limits (429) - always retry
    - Server errors (500+) - always retry
    - Client errors (4xx except 429) - never retry
    """
    if isinstance(exception, RateLimitError):
        return True
    if isinstance(exception, ProblemDetailsException):
        return exception.status >= 500
    return False


async def send_with_retry(
    client: MagickMind, mindspace_id: str, message: str, max_retries: int = 3
) -> Optional[ChatSendResponse]:
    """
    Send chat message with retry logic for transient errors.

    Implements exponential backoff for rate limits and server errors.
    """
    for attempt in range(max_retries):
        try:
            response = await client.v1.chat.send(
                api_key=os.getenv("OPENROUTER_API_KEY", "sk-test"),
                mindspace_id=mindspace_id,
                message=message,
                enduser_id=os.getenv("USER_ID", "user-test"),
                fast_model_id="openrouter/openrouter/meta-llama/llama-4-maverick",
                smart_model_ids=["openrouter/openrouter/meta-llama/llama-4-maverick"],
                compute_power=50,
            )
            logger.info(
                f"✓ Message sent successfully: {response.content and response.content.message_id}"
            )
            return response

        except RateLimitError as e:
            if attempt == max_retries - 1:
                logger.error("Max retries reached for rate limit")
                raise

            delay = exponential_backoff(attempt)
            logger.warning(
                f"Rate limited (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s..."
            )
            await asyncio.sleep(delay)

        except ProblemDetailsException as e:
            # Don't retry client errors (4xx except 429)
            if not is_retryable_error(e):
                logger.error(f"Client error [{e.status}]: {e.title}")
                logger.error(f"Detail: {e.detail}")
                logger.error(f"Request ID: {e.request_id}")
                raise

            # Retry server errors (5xx)
            if attempt == max_retries - 1:
                logger.error("Max retries reached for server error")
                logger.error(
                    f"Request ID: {e.request_id} ← Contact support with this ID"
                )
                raise

            delay = exponential_backoff(attempt)
            logger.warning(
                f"Server error {e.status} (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s..."
            )
            await asyncio.sleep(delay)


# ============================================================================
# Example Scenarios
# ============================================================================


async def example_1_authentication_errors():
    """Example 1: Handling authentication failures."""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 1: Authentication Errors")
    logger.info("=" * 70)

    # Auth is lazy — constructor never raises AuthenticationError.
    # The error surfaces on the first API call that triggers login.
    client = MagickMind(
        email="wrong@example.com",
        password="wrongpassword",
        base_url=os.getenv("MAGICKMIND_BASE_URL", "https://api.magickmind.ai"),
    )

    try:
        await client.http.get("/v1/mindspaces")
    except AuthenticationError as e:
        logger.error(f"❌ Authentication failed: {e.message}")
        logger.info("ℹ️  Action: Check your email and password")
        logger.info("✓ Caught AuthenticationError correctly")
    finally:
        await client.close()


async def example_2_validation_errors(client: MagickMind):
    """Example 2: Handling field validation errors."""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 2: Validation Errors (Field-Level)")
    logger.info("=" * 70)

    try:
        # Send invalid request - empty required fields
        response = await client.v1.chat.send(
            api_key="",  # Invalid: empty
            mindspace_id="",  # Invalid: empty
            message="",  # Invalid: empty
            enduser_id="user-123",
            fast_model_id="gpt-4",
            smart_model_ids=["gpt-4"],
        )
    except ValidationError as e:
        logger.error(f"❌ Validation failed: {e.title}")
        logger.error(f"Request ID: {e.request_id}")

        # Extract field errors
        field_errors = e.get_field_errors()
        logger.error("Field errors:")
        for field, messages in field_errors.items():
            for msg in messages:
                logger.error(f"  • {field}: {msg}")

        logger.info("ℹ️  Action: Fix the invalid fields shown above")
        logger.info("✓ Caught ValidationError and extracted field details")


async def example_3_problem_details_with_request_id(client: MagickMind):
    """Example 3: ProblemDetailsException with request_id."""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 3: Problem Details (404 Not Found)")
    logger.info("=" * 70)

    try:
        # Try to access non-existent mindspace
        response = await client.v1.chat.send(
            api_key="sk-test",
            mindspace_id="nonexistent-mindspace-id",
            message="Hello",
            enduser_id="user-123",
            fast_model_id="gpt-4",
            smart_model_ids=["gpt-4"],
        )
    except ProblemDetailsException as e:
        logger.error(f"❌ API Error: [{e.status}] {e.title}")
        logger.error(f"Detail: {e.detail}")
        logger.error(f"Type URI: {e.type_uri}")

        # IMPORTANT: Log request_id for support
        if e.request_id:
            logger.error(f"Request ID: {e.request_id} ← SAVE THIS FOR SUPPORT!")

        logger.info("ℹ️  Action: Verify the mindspace ID exists")
        logger.info("✓ Caught ProblemDetailsException with request_id")


async def example_4_retry_pattern(client: MagickMind):
    """Example 4: Retry pattern with exponential backoff."""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 4: Retry Pattern (Exponential Backoff)")
    logger.info("=" * 70)

    mindspace_id = os.getenv("MINDSPACE_ID", "mind-test-123")

    try:
        # This will retry on rate limits and server errors
        response = await send_with_retry(
            client, mindspace_id=mindspace_id, message="Test with retry pattern"
        )

        if response:
            logger.info(
                f"✓ Message sent: {response.content and response.content.message_id}"
            )

    except Exception as e:
        logger.error(f"❌ Failed after retries: {type(e).__name__}: {e}")
        logger.info("ℹ️  Action: Check logs for retry attempts and delays")


async def example_5_production_error_handling(client: MagickMind):
    """Example 5: Production-ready error handling pattern."""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 5: Production Error Handling (Comprehensive)")
    logger.info("=" * 70)

    mindspace_id = os.getenv("MINDSPACE_ID", "mind-test-123")

    try:
        response = await client.v1.chat.send(
            api_key=os.getenv("OPENROUTER_API_KEY", "sk-test"),
            mindspace_id=mindspace_id,
            message="Production example message",
            enduser_id=os.getenv("USER_ID", "user-test"),
            fast_model_id="openrouter/openrouter/meta-llama/llama-4-maverick",
            smart_model_ids=["openrouter/openrouter/meta-llama/llama-4-maverick"],
            compute_power=50,
        )

        logger.info(f"✓ Success: {response.content and response.content.message_id}")

    except ValidationError as e:
        # Handle field errors - show to user
        logger.error("Validation error - display to user:")
        error_response = handle_validation_error(e)
        logger.info(f"API response: {error_response}")

    except RateLimitError as e:
        # Handle rate limiting - implement backoff
        logger.warning("Rate limited - implement backoff strategy")
        logger.error(f"Status: {e.status_code}")
        # In production: trigger circuit breaker or backoff mechanism

    except ProblemDetailsException as e:
        # Handle other API errors - log for monitoring
        logger.error(
            "API error",
            extra={
                "error_type": e.__class__.__name__,
                "status": e.status,
                "title": e.title,
                "detail": e.detail,
                "request_id": e.request_id,
                "type_uri": e.type_uri,
            },
        )

        # Decide action based on status
        if e.status >= 500:
            logger.info("ℹ️  Server error - schedule retry or alert ops team")
        elif e.status == 404:
            logger.info("ℹ️  Resource not found - check IDs")
        elif e.status == 403:
            logger.info("ℹ️  Forbidden - check permissions")

    except MagickMindError as e:
        # Catch-all for SDK errors
        logger.error(f"SDK error: {e.message}")
        if e.status_code:
            logger.error(f"Status: {e.status_code}")

    except Exception as e:
        # Unexpected errors
        logger.exception("Unexpected error occurred")

    finally:
        logger.info("✓ Demonstrated production error handling pattern")


# ============================================================================
# Main
# ============================================================================


async def main():
    """Run all error handling examples."""
    logger.info("=" * 70)
    logger.info("SDK Error Handling Patterns - Comprehensive Examples")
    logger.info("=" * 70)

    # Example 1: Authentication (uses wrong credentials intentionally)
    await example_1_authentication_errors()

    # Get valid credentials for remaining examples
    email = os.getenv("MAGICKMIND_EMAIL")
    password = os.getenv("MAGICKMIND_PASSWORD")
    base_url = os.getenv("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")

    if not email or not password:
        logger.warning(
            "\n⚠️  Set MAGICKMIND_EMAIL and MAGICKMIND_PASSWORD to run remaining examples"
        )
        logger.info("\nExample commands:")
        logger.info('  export MAGICKMIND_EMAIL="your@email.com"')
        logger.info('  export MAGICKMIND_PASSWORD="your_password"')
        logger.info('  export MAGICKMIND_BASE_URL="https://api.magickmind.ai"')
        return

    # Initialize client — auth is lazy (happens on first API call)
    client = MagickMind(email=email, password=password, base_url=base_url)
    logger.info(f"\nClient initialized for: {email}")

    try:
        # Example 2: Validation errors
        await example_2_validation_errors(client)

        # Example 3: Problem details with request_id
        await example_3_problem_details_with_request_id(client)

        # Example 4: Retry pattern
        # Uncomment to test retry logic (may take time with backoff)
        # await example_4_retry_pattern(client)

        # Example 5: Production pattern
        await example_5_production_error_handling(client)

    finally:
        await client.close()
        logger.info("\n" + "=" * 70)
        logger.info("All examples completed!")
        logger.info("=" * 70)


if __name__ == "__main__":
    """
    Run error handling examples.

    Environment variables:
        MAGICKMIND_EMAIL    - Your service account email
        MAGICKMIND_PASSWORD - Your service account password
        MAGICKMIND_BASE_URL - Magick Mind API URL (default: https://api.magickmind.ai)
        MINDSPACE_ID        - Mindspace ID for testing (optional)
        USER_ID             - End user ID for testing (optional)
        OPENROUTER_API_KEY  - API key for LLM (optional)

    Example:
        export MAGICKMIND_EMAIL="service@example.com"
        export MAGICKMIND_PASSWORD="your-password"
        python examples/error_handling_patterns.py
    """
    asyncio.run(main())
