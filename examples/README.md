# SDK Examples

Working examples for the Magick Mind Python SDK.

## Setup

### 1. Install dependencies

```bash
cd libs/sdk
uv sync --all-extras
```

### 2. Create `.env` in the `libs/sdk/` directory

```bash
# Required for all examples
MAGICKMIND_BASE_URL="https://api.magickmind.ai"
MAGICKMIND_EMAIL="your@email.com"
MAGICKMIND_PASSWORD="your_password"

# Required for corpus ingest & query examples
MAGICKMIND_API_KEY="sk-your-litellm-virtual-key"

# Optional — for Cortex v2 Reason examples
MAGICKMIND_REASON_MODEL="provider/model"
MAGICKMIND_REASON_MODEL_A="provider/model-a"
MAGICKMIND_REASON_MODEL_B="provider/model-b"
MAGICKMIND_RLM_MAIN_MODEL="provider/main-model"
MAGICKMIND_RLM_SUB_MODEL="provider/sub-model"
MAGICKMIND_LAMBDA_MAIN_MODEL="provider/main-model"
MAGICKMIND_LAMBDA_SUB_MODEL="provider/sub-model"
MAGICKMIND_RATING_MODEL="provider/rating-model"
MAGICKMIND_AGGREGATOR_MODEL="provider/aggregator-model"

# Required for realtime/chat examples
MAGICKMIND_WS_ENDPOINT="wss://centrifugo.magickmind.ai/connection/websocket"

# Optional — created by setup_resources.py if not set
USER_ID="user-test-456"
MINDSPACE_ID=""
PROJECT_ID=""

# Optional — for chat examples
OPENROUTER_API_KEY="sk-or-..."
```

All examples call `load_dotenv()` so the `.env` file is picked up automatically.

### 3. Create test resources (optional)

```bash
uv run python examples/setup_resources.py
```

This creates an End User, Project, and Mindspace, and writes their IDs back to `.env`.

### 4. Run an example

```bash
uv run python examples/authentication.py
```

## Environment Variables

| Variable | Used by | Description |
|----------|---------|-------------|
| `MAGICKMIND_BASE_URL` | All | API gateway URL |
| `MAGICKMIND_EMAIL` | All | Login email |
| `MAGICKMIND_PASSWORD` | All | Login password |
| `MAGICKMIND_API_KEY` | corpus_ingest, resource_management, Reason examples | LiteLLM virtual key for per-tenant LLM/embedding/reasoning usage |
| `MAGICKMIND_REASON_MODEL` | reason_basic, reason_singular_llm, reason_streaming, reason_mcts_mixed | Model ID for Singular LLM and mixed MCTS examples |
| `MAGICKMIND_REASON_MODEL_A` | reason_mcts | First MCTS LLM candidate model |
| `MAGICKMIND_REASON_MODEL_B` | reason_mcts | Second MCTS LLM candidate model |
| `MAGICKMIND_RLM_MAIN_MODEL` | reason_singular_rlm, reason_mcts_mixed | RLM main model |
| `MAGICKMIND_RLM_SUB_MODEL` | reason_singular_rlm, reason_mcts_mixed | RLM sub model |
| `MAGICKMIND_LAMBDA_MAIN_MODEL` | reason_singular_lambda | Lambda RLM main (reduce/compose) model |
| `MAGICKMIND_LAMBDA_SUB_MODEL` | reason_singular_lambda | Lambda RLM sub (leaf) model |
| `MAGICKMIND_RATING_MODEL` | reason_mcts, reason_mcts_mixed | MCTS rating model |
| `MAGICKMIND_AGGREGATOR_MODEL` | reason_mcts, reason_mcts_mixed | MCTS aggregator model |
| `MAGICKMIND_WS_ENDPOINT` | chat_workflow, bulk_subscribe, backend_service | Centrifugo WebSocket URL |
| `USER_ID` | chat_workflow, backend_service, setup_resources | End-user ID for subscriptions |
| `MINDSPACE_ID` | chat_workflow, backend_service, error_handling | Mindspace to send messages to |
| `PROJECT_ID` | setup_resources | Project ID (auto-created if missing) |
| `OPENROUTER_API_KEY` | chat_workflow, error_handling | LLM provider API key for chat |

## Examples

### corpus_ingest.py — Full Document Ingest & Query

The most complete example. Demonstrates the entire corpus lifecycle:

1. Create a corpus
2. Upload a document (presign → S3 PUT → finalize)
3. Add artifact to corpus (triggers ingestion)
4. Poll status: `NOT_FOUND` → `PENDING` → `PROCESSING` → `PROCESSED`
5. Query with LLM synthesis
6. Query context-only (raw retrieved chunks, no LLM)
7. Cleanup

```bash
# Use the built-in sample document
uv run python examples/corpus_ingest.py --sample

# Or provide your own file
uv run python examples/corpus_ingest.py path/to/document.pdf
```

**Requires:** `MAGICKMIND_BASE_URL`, `MAGICKMIND_EMAIL`, `MAGICKMIND_PASSWORD`, `MAGICKMIND_API_KEY`

---

### authentication.py — Lazy Auth & Token Refresh

Shows that authentication is lazy (happens on first API call, not on construction) and that token refresh is automatic.

```bash
uv run python examples/authentication.py
```

**Requires:** `MAGICKMIND_BASE_URL`, `MAGICKMIND_EMAIL`, `MAGICKMIND_PASSWORD`

---

### resource_management.py — CRUD for All Resources

End Users, Projects, Mindspaces, Corpus, and Artifacts — create, list, query, update, delete. Also includes corpus query examples (LLM and context-only).

```bash
uv run python examples/resource_management.py
```

**Requires:** `MAGICKMIND_BASE_URL`, `MAGICKMIND_EMAIL`, `MAGICKMIND_PASSWORD`, `MAGICKMIND_API_KEY`

---

### completions.py — OpenAI-Compatible Chat

Uses `client.openai_client()` for streaming and non-streaming completions via the MagickMind API's OpenAI-compatible endpoint.

```bash
uv run python examples/completions.py
```

**Requires:** `MAGICKMIND_BASE_URL`, `MAGICKMIND_EMAIL`, `MAGICKMIND_PASSWORD`, `MAGICKMIND_API_KEY`

---

### reason_basic.py — Minimal Cortex v2 Reason

Smallest direct Cortex v2 Reason API call. This is equivalent to the Singular
LLM example with less surrounding explanation.

```bash
uv run python examples/reason_basic.py
```

**Requires:** `MAGICKMIND_API_KEY`

---

### reason_singular_llm.py — Cortex v2 Singular LLM

Direct Cortex v2 Reason API call with a single LLM node.

```bash
uv run python examples/reason_singular_llm.py
```

**Requires:** `MAGICKMIND_API_KEY`

---

### reason_singular_rlm.py — Cortex v2 Singular RLM

Direct Cortex v2 Reason API call with an RLM node.

```bash
uv run python examples/reason_singular_rlm.py
```

**Requires:** `MAGICKMIND_API_KEY`

---

### reason_singular_lambda.py — Cortex v2 Singular Lambda RLM

Direct Cortex v2 Reason API call with a Lambda RLM node (map-reduce style
decomposition for long-document reasoning).

```bash
uv run python examples/reason_singular_lambda.py
```

**Requires:** `MAGICKMIND_API_KEY`

---

### reason_mcts.py — Cortex v2 MCTS

Direct Cortex v2 Reason API call with MCTS over LLM candidates.

```bash
uv run python examples/reason_mcts.py
```

**Requires:** `MAGICKMIND_API_KEY`

---

### reason_mcts_mixed.py — Cortex v2 Mixed MCTS

Direct Cortex v2 Reason API call with mixed LLM and RLM MCTS candidates.

```bash
uv run python examples/reason_mcts_mixed.py
```

**Requires:** `MAGICKMIND_API_KEY`

---

### reason_streaming.py — Cortex v2 Streaming + Thinking UI

Streams Cortex v2 Reason events and renders answer tokens separately from
`reason.*` thinking/progress events.

```bash
uv run python examples/reason_streaming.py
```

**Requires:** `MAGICKMIND_API_KEY`

---

### chat_workflow.py — Realtime Chat

Decorator-based event handling, subscribing to a user's channel, sending a chat message, and receiving AI responses in real-time via WebSocket.

```bash
uv run python examples/chat_workflow.py
```

**Requires:** `MAGICKMIND_BASE_URL`, `MAGICKMIND_EMAIL`, `MAGICKMIND_PASSWORD`, `MAGICKMIND_WS_ENDPOINT`

---

### bulk_subscribe.py — Multi-User Subscriptions

Subscribing to 50 users on a single connection with message deduplication. Critical for production backends where users share groups.

```bash
uv run python examples/bulk_subscribe.py
```

**Requires:** `MAGICKMIND_BASE_URL`, `MAGICKMIND_EMAIL`, `MAGICKMIND_PASSWORD`, `MAGICKMIND_WS_ENDPOINT`

---

### backend_service.py — Production Backend Pattern

Combines realtime events with periodic history sync for reliable message processing. Includes deduplication, reconnect recovery, and metrics.

```bash
uv run python examples/backend_service.py
```

**Requires:** `MAGICKMIND_BASE_URL`, `MAGICKMIND_EMAIL`, `MAGICKMIND_PASSWORD`, `MAGICKMIND_WS_ENDPOINT`, `MINDSPACE_ID`, `USER_ID`

---

### persona_workflow.py — Persona & Prepare Workflow

Complete persona lifecycle: create a persona with traits and tones, prepare system prompts
(global and per-user), manage versions with trait constraints, and demonstrate chat integration.

```bash
uv run python examples/persona_workflow.py
```

**Requires:** `MAGICKMIND_BASE_URL`, `MAGICKMIND_EMAIL`, `MAGICKMIND_PASSWORD`

---

### error_handling_patterns.py — Exception Handling

All SDK exception types, field-level validation errors, request IDs for support, retry with exponential backoff.

```bash
uv run python examples/error_handling_patterns.py
```

**Requires:** `MAGICKMIND_BASE_URL`, `MAGICKMIND_EMAIL`, `MAGICKMIND_PASSWORD`

---

### setup_resources.py — Bootstrap Dev Environment

Creates End User, Project, and Mindspace if they don't exist. Writes IDs to `.env` for other examples to use.

```bash
uv run python examples/setup_resources.py
```

**Requires:** `MAGICKMIND_BASE_URL`, `MAGICKMIND_EMAIL`, `MAGICKMIND_PASSWORD`

## Common Patterns

### Authentication (all examples)

```python
async with MagickMind(
    base_url="https://api.magickmind.ai",
    email="user@example.com",
    password="password",
) as client:
    # Auth happens automatically on first API call
    await client.v1.corpus.list()
```

### Realtime Events (decorator API)

```python
from magick_mind.realtime.events import ChatMessageEvent, EventContext

# Handler with EventContext — identifies which end-user the event is for
@client.realtime.on("chat_message")
async def handle_chat(event: ChatMessageEvent, ctx: EventContext) -> None:
    print(f"Message for {ctx.target_user_id}: {event.payload.message}")

# Handler without context still works (backward compatible)
@client.realtime.on("chat_message")
async def handle_chat(event: ChatMessageEvent) -> None:
    print(event.payload.message)

await client.realtime.connect()
await client.realtime.subscribe(target_user_id="user-123")
```

### Error Handling

```python
from magick_mind.exceptions import (
    AuthenticationError,
    ValidationError,
    ProblemDetailsException,
    RateLimitError,
)

try:
    response = await client.v1.chat.send(...)
except ValidationError as e:
    for field, messages in e.get_field_errors().items():
        print(f"{field}: {messages}")
except ProblemDetailsException as e:
    print(f"[{e.status}] {e.title}: {e.detail}")
    print(f"Request ID: {e.request_id}")  # save for support
```

## Troubleshooting

### DNS / Connection errors
If you see `nodename nor servname provided`, verify `MAGICKMIND_BASE_URL` resolves:
```bash
nslookup api.magickmind.ai
```

### Authentication errors
- Verify email/password in `.env`
- Auth errors happen on the first API call, not on client construction

### Corpus query returns empty
- Ensure `MAGICKMIND_API_KEY` is set (LiteLLM virtual key)
- Check artifact status is `PROCESSED` before querying

### WebSocket connection errors
- Verify `MAGICKMIND_WS_ENDPOINT` is set and accessible
- Check firewall allows WebSocket connections
