#!/usr/bin/env python3
"""
Example demonstrating email/password authentication with automatic token refresh.

Usage:
    export MAGICKMIND_BASE_URL="http://localhost:8888"
    export MAGICKMIND_EMAIL="user@example.com"
    export MAGICKMIND_PASSWORD="your_password"
    python examples/authentication.py
"""

import asyncio
import os

from dotenv import load_dotenv

from magick_mind import MagickMind

load_dotenv()


async def main():
    # Get config from environment
    base_url = os.getenv("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")
    email = os.getenv("MAGICKMIND_EMAIL")
    password = os.getenv("MAGICKMIND_PASSWORD")

    if not email or not password:
        print(
            "Error: MAGICKMIND_EMAIL and MAGICKMIND_PASSWORD environment variables are required"
        )
        return

    print(f"Connecting to: {base_url}")
    print(f"Authenticating as: {email}")

    # Create client — auth is lazy (happens on first API call, not here)
    async with MagickMind(base_url=base_url, email=email, password=password) as client:
        print(f"Authenticated (before API call): {client.is_authenticated()}")  # False

        # Trigger lazy login by making any API call
        await client.v1.end_user.query()

        print(f"Authenticated (after API call): {client.is_authenticated()}")  # True
        print("\nToken refresh is automatic — no need to manually refresh!")


if __name__ == "__main__":
    asyncio.run(main())
