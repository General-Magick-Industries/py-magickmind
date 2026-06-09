"""Cortex v2 Reason example: MCTS with LLM candidates.

Set:
    export MAGICKMIND_API_KEY="sk-..."
    export MAGICKMIND_BASE_URL="https://api.magickmind.ai"  # optional
    export MAGICKMIND_REASON_MODEL_A="provider/model-a"
    export MAGICKMIND_REASON_MODEL_B="provider/model-b"
    export MAGICKMIND_RATING_MODEL="provider/rating-model"
    export MAGICKMIND_AGGREGATOR_MODEL="provider/aggregator-model"
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from magickmind import Client, LLM, MCTS


async def main() -> None:
    load_dotenv()

    api_key = os.environ["MAGICKMIND_API_KEY"]
    base_url = os.environ.get("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")
    model_a = os.environ["MAGICKMIND_REASON_MODEL_A"]
    model_b = os.environ["MAGICKMIND_REASON_MODEL_B"]
    rating_model = os.environ["MAGICKMIND_RATING_MODEL"]
    aggregator_model = os.environ["MAGICKMIND_AGGREGATOR_MODEL"]

    async with Client(api_key=api_key, base_url=base_url, timeout=180.0) as client:
        response = await client.reason(
            algorithm=MCTS(
                nodes=[LLM(model_a), LLM(model_b)],
                rating_model=rating_model,
                aggregator_model=aggregator_model,
            ),
            messages=[
                {
                    "role": "user",
                    "content": "Give the strongest argument for and against using MCTS.",
                }
            ],
        )
        print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
