"""Cortex v2 Reason example: MCTS with mixed LLM and RLM candidates.

Set:
    export MAGICKMIND_API_KEY="sk-..."
    export MAGICKMIND_BASE_URL="https://api.magickmind.ai"  # optional
    export MAGICKMIND_REASON_MODEL="provider/model"
    export MAGICKMIND_RLM_MAIN_MODEL="provider/main-model"
    export MAGICKMIND_RLM_SUB_MODEL="provider/sub-model"
    export MAGICKMIND_RATING_MODEL="provider/rating-model"
    export MAGICKMIND_AGGREGATOR_MODEL="provider/aggregator-model"
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from magickmind import Client, LLM, MCTS, RLM


async def main() -> None:
    load_dotenv()

    api_key = os.environ["MAGICKMIND_API_KEY"]
    base_url = os.environ.get("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")
    llm_model = os.environ["MAGICKMIND_REASON_MODEL"]
    main_model = os.environ["MAGICKMIND_RLM_MAIN_MODEL"]
    sub_model = os.environ["MAGICKMIND_RLM_SUB_MODEL"]
    rating_model = os.environ["MAGICKMIND_RATING_MODEL"]
    aggregator_model = os.environ["MAGICKMIND_AGGREGATOR_MODEL"]

    async with Client(api_key=api_key, base_url=base_url, timeout=180.0) as client:
        response = await client.reason(
            algorithm=MCTS(
                nodes=[
                    LLM(llm_model),
                    RLM(
                        main_model_config=main_model,
                        sub_model_config=sub_model,
                        max_iterations=2,
                    ),
                ],
                rating_model=rating_model,
                aggregator_model=aggregator_model,
            ),
            messages=[
                {
                    "role": "user",
                    "content": "Compare direct answering with decomposed reasoning.",
                }
            ],
        )
        print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
