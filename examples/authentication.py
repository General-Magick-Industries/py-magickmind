#!/usr/bin/env python3
"""
Example demonstrating email/password authentication with automatic token refresh.

Usage:
    export MAGICKMIND_BASE_URL="http://localhost:8888"
    export MAGICKMIND_EMAIL="user@example.com"
    export MAGICKMIND_PASSWORD="your_password"
    python examples/email_password_auth.py
"""

import asyncio
import os

from dotenv import load_dotenv

from magick_mind import MagickMind

load_dotenv()


async def main():
    # Get config from environment
    base_url = os.getenv("MAGICKMIND_BASE_URL", "https://dev-api.magickmind.ai")
    email = os.getenv("MAGICKMIND_EMAIL")
    password = os.getenv("MAGICKMIND_PASSWORD")

    if not email or not password:
        print(
            "Error: MAGICKMIND_EMAIL and MAGICKMIND_PASSWORD environment variables are required"
        )
        return

    print(f"Connecting to: {base_url}")
    print(f"Authenticating as: {email}")

    # Create client with email/password
    # Login happens automatically on first API call
    async with MagickMind(base_url=base_url, email=email, password=password) as client:
        print(f"\nClient: {client}")

        # Check authentication status
        print(f"Authenticated: {client.is_authenticated()}")

        # The client will automatically refresh tokens when they expire
        # You can now use the client to make API calls
        # Example: await client.http.get("/v1/some-endpoint")

        print("\n✅ Authentication successful!")
        print("✅ Token refresh is automatic - no need to manually refresh!")


if __name__ == "__main__":
    asyncio.run(main())
