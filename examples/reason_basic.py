"""Minimal Cortex v2 Reason SDK example.

Set:
    export MAGICKMIND_API_KEY="sk-..."
    export MAGICKMIND_BASE_URL="https://api.magickmind.ai"  # optional
"""

from __future__ import annotations

import asyncio
import os

from magickmind import Client, LLM, Singular


async def main() -> None:
    api_key = os.environ["MAGICKMIND_API_KEY"]
    base_url = os.environ.get("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")

    async with Client(api_key=api_key, base_url=base_url) as client:
        response = await client.reason(
            algorithm=Singular(LLM("openrouter/openai/gpt-4o")),
            messages=[
                {"role": "user", "content": "Explain Cortex v2 in one sentence."}
            ],
        )
        print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
