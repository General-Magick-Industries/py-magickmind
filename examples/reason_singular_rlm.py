"""Cortex v2 Reason example: Singular RLM.

Set:
    export MAGICKMIND_API_KEY="sk-..."
    export MAGICKMIND_BASE_URL="https://api.magickmind.ai"  # optional
    export MAGICKMIND_RLM_MAIN_MODEL="provider/main-model"
    export MAGICKMIND_RLM_SUB_MODEL="provider/sub-model"
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
    main_model = os.environ["MAGICKMIND_RLM_MAIN_MODEL"]
    sub_model = os.environ["MAGICKMIND_RLM_SUB_MODEL"]

    async with Client(api_key=api_key, base_url=base_url) as client:
        response = await client.reason(
            algorithm=Singular(
                RLM(
                    main_model_config=main_model,
                    sub_model_config=sub_model,
                    max_iterations=2,
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
