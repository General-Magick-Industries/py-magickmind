# SDK Examples

This directory contains working examples demonstrating key patterns for the Magick Mind SDK.

## Quick Start

1. **Set up your environment:**
   ```bash
   export MAGICKMIND_BASE_URL="http://localhost:8888"
   export MAGICKMIND_EMAIL="user@example.com"
   export MAGICKMIND_PASSWORD="your_password"
   export MAGICKMIND_WS_ENDPOINT="ws://localhost:8888/connection/websocket"
   ```

2. **Create required resources:**
   ```bash
   uv run python examples/setup_resources.py
   ```
   This creates test End User, Project, and Mindspace, and updates your `.env` file.

3. **Run an example:**
   ```bash
   uv run python examples/authentication.py
   ```

## Examples

### 1. authentication.py
**Basic email/password authentication with automatic token refresh.**

Demonstrates:
- Creating a client with email/password credentials
- Automatic login on first API call
- Automatic token refresh when tokens expire
- Context manager usage for cleanup

**Use this when:** You need to understand basic SDK authentication.

```bash
uv run python examples/authentication.py
```

---

### 2. resource_management.py
**CRUD operations for core resources: End Users, Projects, and Mindspaces.**

Demonstrates:
- End User management (create, query, update, delete)
- Project management (create, list, update, delete)
- Mindspace management (create, list, get messages, update, delete)
- Message pagination (forward and backward)
- Proper cleanup patterns

**Use this when:** You need to manage users, projects, or mindspaces programmatically.

```bash
uv run python examples/resource_management.py
```

---

### 3. chat_workflow.py
**Complete chat workflow with realtime streaming.**

Demonstrates:
- Using `RealtimeEventHandler` for clean message handling
- Subscribing to a single user's updates
- Sending chat messages with proper configuration
- Receiving AI responses in real-time via WebSocket
- Error handling with `ProblemDetailsException`
- Model verification and selection

**Use this when:** You're building a simple chat interface with realtime updates.

```bash
uv run python examples/chat_workflow.py
```

---

### 4. bulk_subscribe.py
**Bulk subscriptions with message deduplication.**

Demonstrates:
- Subscribing to many users efficiently (50 users in example)
- **Message deduplication** (CRITICAL for production!)
- Why deduplication is needed when users share groups/mindspaces
- Bulk subscribe/unsubscribe operations
- Metrics tracking for duplicate detection

**Use this when:** You're building a relay service, admin dashboard, or any backend that monitors multiple users.

**Production Note:** This example uses in-memory deduplication. For production, use Redis (see [Realtime Guide](../docs/realtime_guide.md)).

```bash
uv run python examples/bulk_subscribe.py
```

---

### 5. backend_service.py
**Production-ready backend service pattern.**

Demonstrates:
- Message deduplication for reliable processing
- Hybrid realtime + periodic sync pattern
- Recovery from WebSocket disconnects
- Initial history sync on startup
- Periodic background sync to catch missed events
- Production-ready error handling
- Metrics tracking

**Use this when:** You're building a production backend that needs reliable message processing.

**Architecture:**
```
[Your Frontend/App] ←→ [Your Backend + This SDK] ←→ [Magick Mind API]
```

```bash
uv run python examples/backend_service.py
```

---

### 6. error_handling_patterns.py
**Comprehensive error handling patterns.**

Demonstrates:
- All SDK exception types (`AuthenticationError`, `ValidationError`, `ProblemDetailsException`, `RateLimitError`)
- Field-level validation error extraction
- Request ID usage for support tickets
- Retry patterns with exponential backoff
- Production-ready error handling
- Logging integration (Sentry-ready)

**Use this when:** You need to implement robust error handling in production.

```bash
uv run python examples/error_handling_patterns.py
```

---

### 7. setup_resources.py
**Setup script for creating test resources.**

Demonstrates:
- Creating End User, Project, and Mindspace
- Updating `.env` file with resource IDs
- Error handling with `ProblemDetailsException` and `ValidationError`
- Checking for existing resources before creating new ones

**Use this when:** You're setting up a new development environment.

```bash
uv run python examples/setup_resources.py
```

---

## Common Patterns

### Authentication
All examples use email/password authentication:
```python
from magick_mind import MagickMind

client = MagickMind(
    email="user@example.com",
    password="your_password",
    base_url="https://api.example.com"
)
```

### Realtime Events
Use `RealtimeEventHandler` for clean event handling:
```python
from magick_mind.realtime.handler import RealtimeEventHandler

class MyHandler(RealtimeEventHandler):
    async def on_message(self, user_id: str, payload: dict):
        print(f"Message for {user_id}: {payload}")

await client.realtime.connect(events=MyHandler())
await client.realtime.subscribe(target_user_id="user-123")
```

### Error Handling
Always handle SDK exceptions:
```python
from magick_mind.exceptions import (
    AuthenticationError,
    ValidationError,
    ProblemDetailsException,
    RateLimitError,
)

try:
    response = client.v1.chat.send(...)
except ValidationError as e:
    # Handle field-level validation errors
    for field, messages in e.get_field_errors().items():
        print(f"{field}: {messages}")
except ProblemDetailsException as e:
    # Handle other API errors
    print(f"[{e.status}] {e.title}: {e.detail}")
    print(f"Request ID: {e.request_id}")  # Save for support
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MAGICKMIND_BASE_URL` | Yes | Magick Mind API URL (e.g., `http://localhost:8888`) |
| `MAGICKMIND_EMAIL` | Yes | Service account email |
| `MAGICKMIND_PASSWORD` | Yes | Service account password |
| `MAGICKMIND_WS_ENDPOINT` | For realtime | WebSocket endpoint (e.g., `ws://localhost:8888/connection/websocket`) |
| `USER_ID` | Optional | End user ID for testing (default: `user-test-456`) |
| `MINDSPACE_ID` | Optional | Mindspace ID for testing (default: `mind-test-123`) |
| `PROJECT_ID` | Optional | Project ID for testing |
| `OPENROUTER_API_KEY` | Optional | API key for LLM (for chat examples) |

## Next Steps

- **Production Integration:** See [Backend Integration Guide](../docs/guides/backend_integration.md)
- **Realtime Patterns:** See [Realtime Guide](../docs/realtime_guide.md)
- **Error Handling:** See [Error Handling Guide](../docs/guides/error_handling.md)
- **Architecture:** See [Backend Architecture](../docs/architecture/backend_architecture.md)

## Troubleshooting

### Import Errors
If you see "Import X could not be resolved":
```bash
# Make sure you're in the SDK directory
cd libs/sdk

# Sync dependencies
uv sync --all-extras

# Verify installation
uv run pyright --version
```

### Authentication Errors
If authentication fails:
1. Verify `MAGICKMIND_EMAIL` and `MAGICKMIND_PASSWORD` are correct
2. Check that the API is running at `MAGICKMIND_BASE_URL`
3. Ensure your service account has proper permissions

### WebSocket Connection Errors
If realtime examples fail:
1. Verify `MAGICKMIND_WS_ENDPOINT` is set correctly
2. Check that WebSocket endpoint is accessible
3. Ensure firewall allows WebSocket connections

## Contributing

Found a bug or have a suggestion? See [Contributing Guide](../docs/contributing/README.md).
