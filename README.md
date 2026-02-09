# Magick Mind SDK

Python SDK for the Magick Mind platform (Bifrost). Type-safe access to chat, mindspace, and realtime features.

> **Backend-Only SDK** — Designed for server-side applications with service-level authentication.  
> Architecture: `End Users → Your Backend (+ SDK) → Bifrost`

## Installation

```bash
# Using uv (recommended)
uv add magick-mind

# Using pip
pip install magick-mind

# For development
git clone <repository-url> && cd magick-mind-sdk
uv sync --all-extras
```

## Quick Start

### Authentication

```python
from magick_mind import MagickMind

client = MagickMind(
    email="user@example.com",
    password="your_password",
    base_url="https://bifrost.example.com"
)
# Tokens refresh automatically
```

### Send a Chat Message

```python
response = client.http.post(
    "/v1/magickmind/chat",
    json={
        "api_key": "sk-your-llm-key",
        "message": "Hello!",
        "mindspace_id": "mind-123",
        "sender_id": "user-456"
    }
)
# Response streams via Centrifugo WebSocket
```

### Realtime Listener

```python
import asyncio
from magick_mind import MagickMind
from magick_mind.realtime.handler import RealtimeEventHandler

class MyHandler(RealtimeEventHandler):
    async def on_message(self, user_id: str, payload):
        print(f"Message for {user_id}: {payload}")

async def main():
    client = MagickMind(
        email="user@example.com",
        password="password",
        base_url="https://bifrost.example.com",
        ws_endpoint="wss://bifrost.example.com/connection/websocket"
    )
    await client.realtime.connect(events=MyHandler())
    await client.realtime.subscribe_many(["user-1", "user-2"])
    await asyncio.sleep(60)

asyncio.run(main())
```

## Key Concepts

**Mindspaces** — Central organizing concept. All conversations happen within a mindspace. Knowledge (corpus) attaches to mindspaces to provide AI context.

**Service Users** — This SDK authenticates as a service user (your backend). Your backend acts on behalf of end users via `sender_id`.

## Documentation

| Category | Guides |
|----------|--------|
| **Architecture** | [Backend Architecture](docs/architecture/backend_architecture.md) · [Event-Driven Patterns](docs/architecture/event_driven_patterns.md) · [Realtime Patterns](docs/architecture/realtime_patterns.md) |
| **Guides** | [Backend Integration](docs/guides/backend_integration.md) · [Error Handling](docs/guides/error_handling.md) · [Advanced Usage](docs/guides/advanced_usage.md) · [Realtime Guide](docs/realtime_guide.md) |
| **Resources** | [Mindspace](docs/resources/mindspace.md) · [Corpus](docs/resources/corpus.md) · [Artifact](docs/resources/artifact.md) · [End User](docs/resources/end_user.md) · [Project](docs/resources/project.md) |
| **Contributing** | [Contributing Guide](docs/contributing/README.md) · [Resource Implementation](docs/contributing/resource_implementation_guide/README.md) |

## Examples

```bash
export BIFROST_BASE_URL="http://localhost:8888"
export BIFROST_EMAIL="user@example.com"
export BIFROST_PASSWORD="your_password"

uv run python examples/email_password_auth.py
uv run python examples/chat_example.py
uv run python examples/realtime_chat.py
```

## Development

```bash
uv sync --all-extras      # Install dependencies
uv run pytest tests/ -v   # Run tests
uv run pyright            # Type check
uv run ruff format .      # Format
```

## License

MIT License — see LICENSE file.
