# Magick Mind SDK

Python SDK for backend services integrating with the Magick Mind platform. Provides type-safe, validated access to chat, mindspace, and realtime features.

## Installation

Using `uv` (recommended):

```bash
uv add magickmind
```

Using pip:

```bash
pip install magickmind
```

For development:

```bash
git clone https://github.com/General-Magick-Industries/py-magickmind
cd py-magickmind
uv sync --all-extras
```

## Quick Start

### Authentication

```python
import asyncio
from magick_mind import MagickMind

async def main():
    async with MagickMind(
        email="user@example.com",
        password="your_password",
        base_url="https://api.magickmind.ai",
    ) as client:
        # Authentication happens automatically on first API call.
        # Tokens are automatically refreshed when needed.
        user_id = await client.get_user_id()
        print(f"Authenticated as: {user_id}")

asyncio.run(main())
```

> **Note**: The `api_key` you might see in chat requests is **not for SDK authentication**.
> It's a parameter you pass when calling LLM endpoints (for tracking/billing).
> The SDK itself authenticates with JWT tokens from `/v1/auth/login`.

### Basic Chat

```python
import asyncio
from magick_mind import MagickMind

async def main():
    async with MagickMind(
        email="user@example.com",
        password="your_password",
        base_url="https://api.magickmind.ai",
    ) as client:
        response = await client.v1.chat.send(
            api_key="sk-your-llm-key",
            mindspace_id="mind-789",
            message="Hello!",
            enduser_id="user-456",
        )
        print(response.content.content)  # AI response text

asyncio.run(main())
```

### Realtime (Decorator API)

```python
import asyncio
from magick_mind import MagickMind
from magick_mind.realtime.events import ChatMessageEvent, EventContext

async def main():
    client = MagickMind(
        email="user@example.com",
        password="password", 
        base_url="https://api.magickmind.ai",
        ws_endpoint="wss://api.magickmind.ai/connection/websocket"
    )

    # Register handler — optional EventContext identifies the end user
    @client.realtime.on("chat_message")
    async def handle_chat(event: ChatMessageEvent, ctx: EventContext):
        print(f"Message for {ctx.target_user_id}: {event.payload.message}")

    # Connect and subscribe
    await client.realtime.connect()
    await client.realtime.subscribe_many(["user-1", "user-2"])

    # Keep listening...
    await asyncio.sleep(60)

asyncio.run(main())
```

## Key Concepts

### Mindspaces

**Mindspace is the central organizing concept in the Magick Mind API** - it's where conversations, knowledge, and collaboration converge:

- All chat conversations happen within a mindspace
- Knowledge (corpus) attaches to mindspaces to provide context for AI responses  
- Users collaborate through mindspaces (private for individuals, group for teams)
- Most operations reference a `mindspace_id`

📖 **Learn more:** [Mindspace Resource Guide](docs/resources/mindspace.md)

### Service Users

This SDK is designed for **service-level authentication** (email/password). Your backend authenticates as a service user and acts on behalf of end users.

**Common architecture:**
```
[Your Frontend/App] ←→ [Your Backend + This SDK] ←→ [Magick Mind API]
```

For direct device-to-API patterns (robotics/IoT), see [Event-Driven Patterns](docs/architecture/event_driven_patterns.md#self-service-pattern-roboticsiot).

## Documentation

### Architecture

- [Backend Architecture](docs/architecture/backend_architecture.md) - Service-level integration patterns
- [Event-Driven Patterns](docs/architecture/event_driven_patterns.md) - Events as source of truth vs. notifications
- [Realtime Patterns](docs/architecture/realtime_patterns.md) - WebSocket subscription patterns

### Guides

- [Backend Integration](docs/guides/backend_integration.md) - Production patterns for message deduplication, hybrid sync, recovery
- [Error Handling](docs/guides/error_handling.md) - Exception types, retry patterns, production examples
- [Advanced Usage](docs/guides/advanced_usage.md) - Direct HTTP client access for power users
- [Persona & Prepare](docs/guides/persona.md) - AI persona creation, versioning, and system prompt generation
- [Realtime Guide](docs/realtime_guide.md) - Complete WebSocket guide with bulk operations and relay architecture

### Resources

- [Mindspace](docs/resources/mindspace.md) - Central organizing concept
- [Corpus](docs/resources/corpus.md) - Knowledge base management
- [Artifact](docs/resources/artifact.md) - Document/blob storage
- [End User](docs/resources/end_user.md) - User identity management
- [Project](docs/resources/project.md) - Project organization

### Contributing

- [Contributing Guide](docs/contributing/README.md) - How to extend the SDK
- [Resource Implementation Guide](docs/contributing/resource_implementation_guide/README.md) - Template for adding typed resources

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/General-Magick-Industries/py-magickmind
cd py-magickmind

# Install dependencies
uv sync --all-extras
```

### Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_auth.py -v

# Run with coverage
uv run pytest tests/ --cov=magick_mind --cov-report=html
```

### Type Checking

```bash
uv run pyright
```

### Formatting

```bash
uv run ruff format .
```

## Examples

The `examples/` directory contains working examples demonstrating key SDK patterns:

| Example | Description |
|---------|-------------|
| **authentication.py** | Email/password authentication with auto-refresh |
| **resource_management.py** | CRUD operations for End Users, Projects, and Mindspaces |
| **persona_workflow.py** | Persona creation, versioning, and prepare (system prompt generation) |
| **chat_workflow.py** | Complete chat workflow with realtime streaming |
| **bulk_subscribe.py** | Bulk subscriptions with message deduplication |
| **backend_service.py** | Production-ready backend service pattern |
| **error_handling_patterns.py** | Comprehensive error handling patterns |
| **setup_resources.py** | Setup script for creating test resources |

📖 **See [examples/README.md](examples/README.md) for detailed descriptions and usage.**

Quick start:

```bash
# 1. Set environment variables
export MAGICKMIND_BASE_URL="http://localhost:8888"
export MAGICKMIND_EMAIL="user@example.com"
export MAGICKMIND_PASSWORD="your_password"

# 2. Create test resources
uv run python examples/setup_resources.py

# 3. Run an example
uv run python examples/authentication.py
```

## License

MIT License - see LICENSE file for details.

## Authors

- Adrian (adrian@magickmind.ai)
- Minnie (minnie@magickmind.ai)
- Turtle (turtle@magickmind.ai)
