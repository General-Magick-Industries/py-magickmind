# Episode Resource - Magick Mind SDK

The Episode Resource ingests conversation messages into an agent's episodic memory.

## Overview

Episodic memory is what lets an agent recall earlier conversations. Every message an agent takes part in — the messages it receives **and** the replies it sends — should be ingested, or the agent remembers only half of every exchange.

The resource is a thin client over one endpoint. Deciding *when* to call it, and what to do when it fails, is the caller's job; see [Operational guidance](#operational-guidance).

## Installation

```python
from magick_mind import MagickMind

client = MagickMind(
    base_url="https://api.example.com",
    email="user@example.com",
    password="your-password",
)

episodes = client.v1.episode
```

## Two routes, chosen by credential

Which method you call depends on which credential your process holds, not on what you want to do.

| Credential | Method | Route | Memory owner |
| --- | --- | --- | --- |
| Service-user (email/password) | `process()` | `POST /v1/episodes/process` | `agent_id` in the body |
| The agent's own end-user JWT | `process_own()` | `POST /v1/end-user/episodes/process` | the token subject |

The two are not interchangeable. Calling one with the other's credential fails with `401`, because the routes verify differently signed tokens. The SDK attaches a hint pointing at the correct method.

## API Reference

### `process(*, agent_id, magickspace_id, sender_id, message, message_id, display_name=None, is_group=False, skip_persona=False)`

Ingest a message into a named agent's episodic memory, using service-user credentials.

**Parameters:**
- `agent_id` (str, **required**): The agent whose memory this is written to. A write always needs an owner, and no credential on this route supplies one implicitly.
- `magickspace_id` (str, required): Magickspace the message belongs to
- `sender_id` (str, required): Who sent the message. Must be a participant of the magickspace and reference a readable end user.
- `message` (str, required): Message text
- `message_id` (str, required): Your own ID for this message
- `display_name` (str, optional): Sender display name. Omit and the server uses the end user's own name.
- `is_group` (bool, optional): Whether this came from a group conversation
- `skip_persona` (bool, optional): Skip persona resolution when building the episode. Set this when you do not need the agent's persona folded into the stored episode — it avoids the persona lookup.

All arguments are keyword-only: the call takes several same-typed string IDs, and a positional swap would be silent.

**Returns:** `ProcessEpisodeResponse` with `message_processed` (bool)

**Raises:** `MagickMindError` — `400` empty `agent_id`, `401` wrong credential kind, `403` sender is not a participant or the agent is not readable, `404` magickspace not found.

**Example:**

```python
result = await client.v1.episode.process(
    agent_id="agent-123",
    magickspace_id="ms-456",
    sender_id="eu-789",
    message="What's the status of my order?",
    message_id="msg-001",
)
print(result.message_processed)
```

---

### `process_own(*, magickspace_id, sender_id, message, message_id, display_name=None, is_group=False, skip_persona=False)`

Ingest a message into the **calling agent's** episodic memory, using that agent's end-user JWT. No `agent_id` is sent — the server resolves the owner from the token subject.

Mint the token with [`end_user.mint_token()`](end_user.md), then build the
agent's client from it:

```python
agent_client = MagickMind.from_token("https://api.example.com", minted.token)
```

**Parameters:** as `process()`, minus `agent_id`.

**Returns:** `ProcessEpisodeResponse`

**Raises:** `MagickMindError` — `401` service-user credentials or a revoked token, `403` sender is not a participant, `404` magickspace not found.

**Example:**

```python
result = await agent_client.v1.episode.process_own(
    magickspace_id="ms-456",
    sender_id="eu-789",
    message="Your order shipped this morning.",
    message_id="msg-002",
)
```

## Operational guidance

### Ingest both sides of the conversation

Capture the inbound message *and* the agent's reply. A hook that only fires on inbound messages stores questions without answers, and the resulting memory reads as a monologue.

```python
await client.v1.episode.process(
    agent_id=AGENT_ID, magickspace_id=space, sender_id=user_id,
    message=user_text, message_id=inbound_id,
)

reply = await generate_reply(user_text)

await client.v1.episode.process(
    agent_id=AGENT_ID, magickspace_id=space, sender_id=AGENT_ID,
    message=reply, message_id=outbound_id,
)
```

### Make ingest best-effort

A memory outage must never stop an agent from replying. Log and continue:

```python
try:
    await client.v1.episode.process(...)
except MagickMindError as exc:
    logger.warning("episode ingest failed: %s", exc)
```

Validate configuration at startup instead, so a bad base URL or credential fails fast rather than being swallowed once per message forever.
