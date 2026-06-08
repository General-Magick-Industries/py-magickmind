"""Cortex v2 Reason example: Singular RLM.

Set:
    export MAGICKMIND_API_KEY="sk-..."
    export MAGICKMIND_BASE_URL="https://api.magickmind.ai"  # optional
    export MAGICKMIND_RLM_DECOMPOSER_MODEL="provider/decomposer-model"
    export MAGICKMIND_RLM_LEAF_MODEL="provider/leaf-model"
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from magickmind import Client, RLM, Singular


async def main() -> None:
    load_dotenv()

    api_key = os.environ["MAGICKMIND_API_KEY"]
    base_url = os.environ.get("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")
    decomposer_model = os.environ["MAGICKMIND_RLM_DECOMPOSER_MODEL"]
    leaf_model = os.environ["MAGICKMIND_RLM_LEAF_MODEL"]

    async with Client(api_key=api_key, base_url=base_url) as client:
        response = await client.reason(
            algorithm=Singular(
                RLM(
                    decomposer_model=decomposer_model,
                    leaf_model=leaf_model,
                    max_depth=2,
                )
            ),
            messages=[
                {
                    "role": "user",
                    "content": "Break down whether a small team should automate reports.",
                }
            ],
        )
        print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
