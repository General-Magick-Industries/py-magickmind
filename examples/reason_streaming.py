"""Minimal Cortex v2 Reason streaming example.

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


def render_thinking_event(event_type: str, payload: dict) -> None:
    """Render reason.* progress events for a simple terminal thinking UI."""
    if event_type == "reason.started":
        print(
            f"\nthinking: started {payload.get('algorithm', 'reasoning')}", flush=True
        )
        return
    if event_type.startswith("reason.mcts."):
        print(f"\nthinking: mcts {event_type.removeprefix('reason.mcts.')}", flush=True)
        return
    if event_type.startswith("reason.rlm."):
        print(f"\nthinking: rlm {event_type.removeprefix('reason.rlm.')}", flush=True)
        return
    print(f"\nthinking: {event_type}", flush=True)


async def main() -> None:
    load_dotenv()

    api_key = os.environ["MAGICKMIND_API_KEY"]
    base_url = os.environ.get("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")
    model = os.environ["MAGICKMIND_REASON_MODEL"]

    async with Client(api_key=api_key, base_url=base_url) as client:
        stream = await client.reason(
            algorithm=Singular(LLM(model)),
            messages=[{"role": "user", "content": "Think through a simple tradeoff."}],
            stream=True,
        )

        answer_started = False
        async for event in stream:
            if event.is_token():
                if not answer_started:
                    print("answer: ", end="", flush=True)
                    answer_started = True
                print(event.content, end="", flush=True)
            elif event.is_thinking():
                if answer_started:
                    print()
                    answer_started = False
                render_thinking_event(event.type, event.payload)
        if answer_started:
            print()


if __name__ == "__main__":
    asyncio.run(main())
