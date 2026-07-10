# Reason Resource Guide (v2)

A guide to the **Cortex v2 Reason** resource in the Magick Mind SDK — a single
endpoint for advanced reasoning that supports multiple algorithms (single-model,
recursive decomposition, and Monte-Carlo Tree Search) with optional token streaming.

## Overview

**Reason is the v2 reasoning entry point.** You send chat messages plus an algorithm
configuration, and Cortex returns a synthesized answer — either as a single response or
as a stream of typed progress events.

**Two ways to specify what runs:**
- **`model`** — a shorthand for a single-model call.
- **`algorithm`** — an explicit reasoning strategy built from nodes (see below).

**Algorithms:**
- **Singular** — runs one reasoning node.
- **MCTS** — runs several candidate nodes, rates them, and aggregates a winner.

**Nodes** (the units an algorithm runs):
- **LLM** — a single language-model call.
- **RLM** — a recursive language model that decomposes a problem, solves the parts, and
  recombines them.
- **Lambda** — a map-reduce RLM variant for long inputs: detects the task type, plans a
  chunking strategy, solves chunks with a sub model, and composes the answer with a main
  model. Text output only.

**Two response modes:**
- **Non-streaming** (`stream=False`) — returns a single `ReasonResponse`.
- **Streaming** (`stream=True`) — returns an async iterator of typed `ReasonEvent`
  objects (answer tokens plus reasoning-progress milestones).

## Quick Start

```python
from magick_mind import MagickMind

client = MagickMind(
    base_url="https://api.magickmind.ai",
    email="user@example.com",
    password="password",
)

# Simplest call: a single message against a single model
response = await client.reason(
    model="openrouter/anthropic/claude-sonnet-4",
    message="What is the capital of France?",
)

print(response.text_answer)   # "Paris is the capital of France."
print(response.usage.output_tokens)
```

`client.reason` is a convenience alias for `client.v2.reason`. Both are the same
resource and accept the same arguments.

> Reason calls are **async** — `await` them inside an event loop.

### Multi-turn messages

Pass OpenAI-style `messages` instead of a single `message`:

```python
response = await client.reason(
    model="openrouter/anthropic/claude-sonnet-4",
    messages=[
        {"role": "system", "content": "You are a terse assistant."},
        {"role": "user", "content": "Why is the sky blue?"},
    ],
    temperature=0.7,
)
```

Each message is `{"role": ..., "content": ...}` where `role` is `"system"`, `"user"`,
or `"assistant"`. You can also use the typed `ChatMessage` model.

## Streaming

Set `stream=True` to receive a live stream of typed events. The return value is an async
iterator you consume with `async for`:

```python
stream = await client.reason(
    model="openrouter/anthropic/claude-sonnet-4",
    message="Tell me a short story.",
    stream=True,
)

answer = []
async for event in stream:
    if event.is_token():
        # Incremental chunk of the final answer
        print(event.content, end="", flush=True)
        answer.append(event.content)
    elif event.is_thinking():
        # Reasoning-progress milestone — useful for a "thinking" UI
        print(f"\n[progress] {event.type}")

print("\n\nFinal answer:", "".join(answer))
```

### Event types

Every event is a `ReasonEvent` with `type`, `trace_id`, `payload`, and `data` attributes.
Helper subclasses make the common cases easy:

| Class | When | Key accessors |
|---|---|---|
| `ReasonTokenEvent` | An answer chunk (`reason.answer.delta`) | `.content`, `.is_token() == True` |
| `ReasonThinkingEvent` | A reasoning-progress milestone | `.is_thinking() == True` |
| `ReasonCompleteEvent` | Terminal success (`reason.completed` / `reason.answer.complete`) | — |
| `ReasonFailedEvent` | Terminal failure (`reason.failed`) | `.error_code`, `.message` |

```python
from magick_mind import ReasonFailedEvent

async for event in stream:
    if isinstance(event, ReasonFailedEvent):
        raise RuntimeError(f"{event.error_code}: {event.message}")
```

- `event.is_token()` → append `event.content` to build the final answer.
- `event.is_thinking()` → MCTS/RLM progress milestones; render or ignore.
- Streams stop on a terminal event (success or failure).

## Algorithms

Build algorithms from the typed helpers exported by `magick_mind`. Pass the result as
`algorithm=`.

### Singular

```python
from magick_mind import Singular, LLM

response = await client.reason(
    algorithm=Singular(node=LLM(model="openrouter/anthropic/claude-sonnet-4")),
    message="Explain entropy simply.",
)
```

### MCTS

Runs multiple candidates, rates them, and aggregates the winner. Requires **at least two
nodes** plus a rating model and an aggregator model:

```python
from magick_mind import MCTS, LLM

response = await client.reason(
    algorithm=MCTS(
        nodes=[
            LLM(model="openrouter/anthropic/claude-sonnet-4"),
            LLM(model="openrouter/openai/gpt-4o"),
        ],
        rating_model="openrouter/anthropic/claude-sonnet-4",
        aggregator_model="openrouter/anthropic/claude-sonnet-4",
        iterations=4,
    ),
    message="What's the most robust sorting algorithm for nearly-sorted data?",
)
```

### RLM node

A recursive language model decomposes a problem and solves the parts. Use it anywhere a
node is accepted (as a Singular node, or as an MCTS candidate):

```python
from magick_mind import Singular, RLM

response = await client.reason(
    algorithm=Singular(
        node=RLM(
            main_model_config="openrouter/anthropic/claude-sonnet-4",
            sub_model_config="openrouter/openai/gpt-4o-mini",
            max_iterations=2,
        )
    ),
    message="Plan a three-day itinerary for Kyoto with a food focus.",
)
```

Each model slot accepts a model-id string or a `ModelConfig`. `sub_model_config`,
`image_model_config`, and `max_iterations` are optional; set `image_model_config` to
use the image-generation RLM path. `max_iterations` is clamped server-side to `[1, 50]`.

### Lambda node

A map-reduce RLM variant for long inputs (the wire key is `lambda`; the SDK class is
named `Lambda` because `lambda` is a Python keyword). Cortex detects the task type,
plans a chunking strategy against the configured context window, solves chunks with the
sub model, and composes the final answer with the main model. Use it anywhere a node is
accepted:

```python
from magick_mind import Singular, Lambda

response = await client.reason(
    algorithm=Singular(
        node=Lambda(
            main_model_config="openrouter/anthropic/claude-sonnet-4",
            sub_model_config="openrouter/openai/gpt-4o-mini",
        )
    ),
    message="Summarize the key obligations in this contract: ...",
)
```

- `main_model_config` (required) — reduce/compose calls that need cross-chunk reasoning.
- `sub_model_config` (optional) — leaf calls over individual chunks; falls back to
  `main_model_config` when unset.
- `context_window_chars` (optional, default 100000) — the model context window in
  characters, used for chunk planning; must be positive.
- `accuracy_target` (optional, default 0.80) — minimum accuracy target for planning;
  must be in `(0, 1]`.

Lambda nodes produce text output only.

> **Availability:** lambda nodes are not yet accepted by the API edge — requests using
> them currently fail validation there. The shapes below document the contract for when
> edge support lands.

### Per-model tuning with `ModelConfig`

Any model slot accepts a plain model-id string or a `ModelConfig` for fine control:

```python
from magick_mind import Singular, LLM, ModelConfig

node = LLM(model=ModelConfig(
    model="openrouter/anthropic/claude-sonnet-4",
    temperature=0.3,
    max_tokens=1024,
    top_p=0.95,
    reasoning_effort="medium",
))
response = await client.reason(algorithm=Singular(node=node), message="...")
```

For image-generation models, set the output size with `image_size`. It is ignored unless
the model is an image-generation model:

```python
from magick_mind import ModelConfig, ImageSize

ModelConfig(model="openrouter/openai/gpt-image-1", image_size=ImageSize.SIZE_1024)
# ImageSize options: SIZE_1024, SIZE_1536, SIZE_2048
```

## Response

A non-streaming call returns a `ReasonResponse`:

```python
response = await client.reason(model="...", message="...")

response.text_answer    # str | None — the text answer
response.content        # convenience alias for text_answer
response.image          # ImageResult | None — for image-generation algorithms
response.usage          # UsageStats | None — tokens, calls, cost
response.trace          # dict | None — structured reasoning trace
response.trace_id       # str | None — correlation id
response.success        # bool | None
response.error          # str | None
response.degradations   # list[str] — soft-failure log
```

`UsageStats` fields: `input_tokens`, `output_tokens`, `llm_calls`, `litellm_cost_usd`,
`model_used` (empty for multi-model algorithms), `model_provider`.

`ImageResult` fields: `b64_json` (inline base64), `url` (provider URL), `mime_type`.

## Best Practices

### 1. Use `model` for simple calls, `algorithm` for control

A bare `model="..."` is the fastest path for single-model answers. Reach for
`Singular` / `MCTS` only when you need recursion or multi-candidate aggregation.

### 2. Stream long answers

For anything user-facing, pass `stream=True` and render `is_token()` chunks as they
arrive. Use `is_thinking()` events to show reasoning progress.

### 3. Pass a `trace_id` for correlation

Supply your own `trace_id` to tie SDK calls to your own logs; it is echoed back on the
response and on every stream event.

### 4. Right-size MCTS

`iterations` must be at least the number of nodes and is capped server-side. More
iterations means more cost — start small and increase only if quality demands it.

### 5. Check `degradations`

A successful response can still carry `degradations`. Inspect it when answer quality
matters.

## Error Handling

Failed requests raise `MagickMindError`, which carries a `status_code`:

```python
from magick_mind import MagickMindError

try:
    response = await client.reason(model="...", message="...")
except MagickMindError as e:
    print(f"Reason failed ({e.status_code}): {e}")
```

The SDK automatically retries transient failures (network errors, timeouts, and status
codes `408, 409, 425, 429, 500, 502, 503, 504`) with exponential backoff. For streaming,
a retry only occurs if no events have been emitted yet; once the stream has started, an
interruption surfaces as an error rather than restarting.

Validation errors are raised before any request is sent — `model` or `algorithm` is
required, and `messages` or `message` is required (and `messages` must be non-empty).

## API Reference

### `client.reason(...)` / `client.v2.reason(...)`

Call Cortex v2 Reason. Returns a `ReasonResponse` when `stream=False`, or an async
iterator of `ReasonEvent` when `stream=True`.

**Parameters:**
- `model` (str, optional): Single-model shorthand. Required if `algorithm` is absent.
- `algorithm` (Singular | MCTS | mapping, optional): Reasoning strategy. Required if
  `model` is absent.
- `message` (str, optional): Single user message. Required if `messages` is absent.
- `messages` (list, optional): OpenAI-style messages. Required if `message` is absent;
  must be non-empty.
- `stream` (bool, optional): Stream typed events. Default `False`.
- `temperature` (float, optional)
- `max_tokens` (int, optional)
- `top_p` (float, optional)
- `response_format` (str, optional): JSON schema for structured output.
- `trace_id` (str, optional): Opaque correlation id, echoed back.
- `verified` (bool, optional): Request verified-answer behavior.
- `message_id` (str, optional): Caller-supplied message identifier.
- `user_id` (str, optional): End-user identifier for attribution.

**Returns:** `ReasonResponse` | `HTTPReasonStream` (async iterator of `ReasonEvent`).

`client.reason.create(...)` is an explicit alias for the same call.

---

## Wire Format Reference

This section documents the raw HTTP/SSE contract for callers integrating **without** the
SDK (e.g. a client in another language). All shapes match what the SDK sends and parses.

### Endpoint

| | |
|---|---|
| **Method / Path** | `POST /v2/chat/completions` |
| **Base URL** | `https://api.magickmind.ai` |

### Headers

| Header | Non-streaming | Streaming |
|---|---|---|
| `Authorization` | `Bearer <api_key>` | `Bearer <api_key>` |
| `Content-Type` | `application/json` | `application/json` |
| `Accept` | `application/json` | `text/event-stream` |

### Request body

A single JSON object. **Fields whose value is `null` are omitted.** At least one of
`algorithm` / `model` and one of `messages` / `message` must be present.

```json
{
  "model": "openrouter/anthropic/claude-sonnet-4",
  "messages": [{ "role": "user", "content": "Why is the sky blue?" }],
  "algorithm": null,
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 1024,
  "top_p": 0.95,
  "response_format": null,
  "trace_id": "abc-123",
  "verified": null,
  "message_id": null,
  "user_id": null
}
```

If only `message` is sent, it is expanded to
`"messages": [{"role": "user", "content": "<message>"}]`.

### Algorithm wire shapes

`algorithm` is a tagged union — exactly one of `singular` or `mcts`:

```json
{ "singular": { "node": <NODE> } }
```

```json
{
  "mcts": {
    "nodes": [ <NODE>, <NODE> ],
    "iterations": 4,
    "rating_model_config": { "model": "<id>" },
    "aggregator_model_config": { "model": "<id>" }
  }
}
```

A `<NODE>` is one of:

```json
{ "llm": { "model_config": { "model": "<id>" } } }
```

```json
{
  "rlm": {
    "main_model_config":  { "model": "<id>" },
    "sub_model_config":   { "model": "<id>" },
    "image_model_config": { "model": "<id>" },
    "max_iterations": 2
  }
}
```

```json
{
  "lambda": {
    "main_model_config": { "model": "<id>" },
    "sub_model_config":  { "model": "<id>" },
    "context_window_chars": 100000,
    "accuracy_target": 0.8
  }
}
```

Only `main_model_config` is required on an RLM node; `sub_model_config`,
`image_model_config`, and `max_iterations` are optional. Set `image_model_config` for the
image-generation RLM path.

Only `main_model_config` is required on a lambda node; `sub_model_config` (leaf calls,
falls back to the main config), `context_window_chars` (default 100000), and
`accuracy_target` (default 0.8) are optional. Lambda nodes are text-only and are **not
yet accepted by the API edge** (see the validation table below for the rules that apply
once they are).

A `model_config` requires `model` and optionally carries `temperature`, `max_tokens`,
`top_p`, `reasoning_effort`, and `image_config` (omitted when null). `image_config` is
`{ "size": "IMAGE_SIZE_1024X1024" | "IMAGE_SIZE_1536X1536" | "IMAGE_SIZE_2048X2048" }`
and is ignored unless the model is an image-generation model.

### Non-streaming response

```json
{
  "text_answer": "Paris is the capital of France.",
  "image": null,
  "usage": {
    "input_tokens": 12, "output_tokens": 8, "llm_calls": 1,
    "litellm_cost_usd": 0.00004,
    "model_used": "openrouter/anthropic/claude-sonnet-4",
    "model_provider": "anthropic"
  },
  "trace": { },
  "trace_id": "abc-123",
  "success": true,
  "error": null,
  "degradations": []
}
```

Clients should tolerate additional unknown fields.

### Streaming (SSE)

Each event is an SSE frame:

```
event: reason.<event_name>
data: {<JSON object>}

```

- Frames are separated by a blank line; lines starting with `:` are comments.
- A `data:` value of `[DONE]` ends the stream.
- The JSON object carries a top-level `trace_id` plus a payload object nested under a key
  named after the event.

```
event: reason.answer.delta
data: {"trace_id":"abc","answer_chunk":{"content":"Paris "}}

event: reason.completed
data: {"trace_id":"abc","completed":{"final_answer":"...","usage":{},"trace":{}}}

data: [DONE]

```

**Event types and their payload keys** (the key holding the payload inside `data`):

| `event:` | Payload key | Category |
|---|---|---|
| `reason.started` | `started` | progress |
| `reason.completed` | `completed` | terminal (success) |
| `reason.failed` | `failed` | terminal (failure) |
| `reason.answer.delta` | `answer_chunk` | answer token |
| `reason.answer.complete` | `answer_complete` | terminal (success) |
| `reason.degradation` | `degradation` | progress |
| `reason.trace.emitted` | `trace_emitted` | progress |
| `reason.mcts.started` | `mcts_started` | progress |
| `reason.mcts.candidate_started` | `mcts_candidate_started` | progress |
| `reason.mcts.candidate_completed` | `mcts_candidate_completed` | progress |
| `reason.mcts.rating_started` | `mcts_rating_started` | progress |
| `reason.mcts.rating_completed` | `mcts_rating_completed` | progress |
| `reason.mcts.aggregate_started` | `mcts_aggregate_started` | progress |
| `reason.mcts.iteration.started` | `mcts_iteration_started` | progress |
| `reason.mcts.iteration.completed` | `mcts_iteration_completed` | progress |
| `reason.mcts.final.ranking.completed` | `mcts_final_ranking_completed` | progress |
| `reason.rlm.sub_started` | `rlm_sub_started` | progress |
| `reason.rlm.sub_completed` | `rlm_sub_completed` | progress |
| `reason.rlm.repl_step` | `rlm_repl_step` | progress |

Lambda nodes additionally emit six progress events (payload keys
`lambda_task_detected`, `lambda_plan`, `lambda_sub_started`, `lambda_sub_completed`,
`lambda_reduce_started`, `lambda_reduce_completed`). Their `event:` names are not final
until the edge accepts lambda nodes; clients should treat unknown `reason.*` event names
as progress events and ignore them rather than fail.

Key payloads:

```jsonc
// reason.answer.delta  → answer_chunk
{ "content": "Paris " }

// reason.completed     → completed
{ "final_answer": "...", "usage": { }, "trace": { } }

// reason.failed        → failed
{ "error_code": "upstream_timeout", "message": "Model provider timed out." }
```

### Errors

On HTTP status `>= 400` the body is one of:

```json
{ "error": { "detail": "Human-readable detail", "title": "short_code" } }
```

```json
{ "message": "Human-readable error message" }
```

Surface `error.detail` (falling back to `error.title`) or `message`, with the HTTP
status. Status codes `408, 409, 425, 429, 500, 502, 503, 504` are retryable.

### Validation rules (server-enforced)

| Rule | Behavior |
|---|---|
| Neither `algorithm` nor `model` set | Hard fail |
| Neither `messages` nor `message` set | Hard fail |
| `messages` present but empty | Hard fail |
| `singular.node` empty | Hard fail |
| `mcts.nodes` length < 2 | Hard fail (use `singular`) |
| `mcts.iterations` < node count | Hard fail |
| `mcts.iterations` > 10 | Hard fail (cost cap) |
| MCTS mixed output types | Hard fail (all text or all image) |
| LLM node `model` empty | Hard fail |
| RLM `main_model_config` model empty | Hard fail |
| RLM `sub_model_config` / `image_model_config` model empty (when provided) | Hard fail |
| RLM `max_iterations` outside [1, 50] | Clamped silently |
| Lambda `main_model_config` model empty | Hard fail |
| Lambda `context_window_chars` ≤ 0 (when provided) | Hard fail |
| Lambda `accuracy_target` outside (0, 1] (when provided) | Hard fail |

### Direct HTTP examples (no SDK)

```bash
# Non-streaming
curl -sS https://api.magickmind.ai/v2/chat/completions \
  -H "Authorization: Bearer $MAGICKMIND_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"model":"openrouter/anthropic/claude-sonnet-4","message":"Capital of France?","stream":false}'

# Streaming
curl -N https://api.magickmind.ai/v2/chat/completions \
  -H "Authorization: Bearer $MAGICKMIND_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"model":"openrouter/anthropic/claude-sonnet-4","message":"Tell me a story.","stream":true}'
```

## Related Resources

- Reference implementation: [`magick_mind/resources/v2/reason.py`](../../magick_mind/resources/v2/reason.py)
- SSE event types: [`magick_mind/resources/v2/events.py`](../../magick_mind/resources/v2/events.py)
- Request/response models: [`magick_mind/models/v2/reason.py`](../../magick_mind/models/v2/reason.py)
