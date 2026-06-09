"""Cortex v2 Reason example: Singular LLM.

Set:
    export MAGICKMIND_API_KEY="sk-..."
    export MAGICKMIND_BASE_URL="https://api.magickmind.ai"  # optional
    export MAGICKMIND_REASON_MODEL="provider/model"
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from magickmind import Client, LLM, Singular


async def main() -> None:
    load_dotenv()

    api_key = os.environ["MAGICKMIND_API_KEY"]
    base_url = os.environ.get("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")
    model = os.environ["MAGICKMIND_REASON_MODEL"]

    async with Client(api_key=api_key, base_url=base_url) as client:
        response = await client.reason(
            algorithm=Singular(LLM(model)),
            messages=[
                {
                    "role": "user",
                    "content": "Explain Cortex v2 Reason in one sentence.",
                }
            ],
        )
        print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
