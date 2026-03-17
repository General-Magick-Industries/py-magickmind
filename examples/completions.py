"""
OpenAI-compatible completions via Bifrost.

Bifrost exposes POST /v1/chat/completions — a full OpenAI-compatible
endpoint backed by Brain/Cortex. Use client.openai_client() to get a
pre-configured AsyncOpenAI pointed at it. No Centrifugo, no mindspace
context, no ChatHistory service needed — stateless LLM calls only.

Install the optional dep first:
    pip install magick-mind[openai]

Set BIFROST_API_KEY in your .env (your platform api key).
"""

import asyncio
import os

from dotenv import load_dotenv

from magick_mind import MagickMind

load_dotenv()


async def main() -> None:
    api_key = os.getenv("BIFROST_API_KEY", "")
    if not api_key:
        print(
            "Set BIFROST_API_KEY in .env — your platform api key (Bearer token for /v1/chat/completions)"
        )
        return

    client = MagickMind(
        email=os.getenv("BIFROST_EMAIL", ""),
        password=os.getenv("BIFROST_PASSWORD", ""),
        base_url=os.getenv("BIFROST_BASE_URL", "https://dev-bifrost.magickmind.ai"),
    )

    oai = client.openai_client(api_key=api_key)

    # --- Non-streaming ---
    print("=== Non-streaming ===")
    resp = await oai.chat.completions.create(
        model="openrouter/meta-llama/llama-4-maverick",
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
    )
    print(resp.choices[0].message.content)

    # --- Streaming ---
    print("\n=== Streaming ===")
    stream = await oai.chat.completions.create(
        model="openrouter/meta-llama/llama-4-maverick",
        messages=[{"role": "user", "content": "Count to 5, one number per line."}],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()

    # Tip: override compute_power per-request via extra_headers
    # resp = await oai.chat.completions.create(
    #     model="...", messages=[...],
    #     extra_headers={"X-Compute-Power": "3"},
    # )


if __name__ == "__main__":
    asyncio.run(main())
