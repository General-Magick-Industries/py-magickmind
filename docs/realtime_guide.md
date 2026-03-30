# Realtime Integration Guide

This guide explains how to use the Realtime features of the Magick Mind SDK effectively, especially for high-scale scenarios (500+ users) and robust error handling.

> [!CAUTION]
> **Message Deduplication is Essential!**  
> If you subscribe to multiple users in the same group/mindspace, you will receive duplicate messages. You MUST implement deduplication to avoid processing the same message multiple times. See [Message Deduplication](#message-deduplication--critical) for details.

## Architecture

The SDK uses a WebSocket connection to receive real-time updates. Unlike traditional Pub/Sub where you subscribe to arbitrary channels, this SDK uses an **RPC-based subscription model**:

1.  **RPC `subscribe`**: You ask the Magick Mind API backend to subscribe your connection to a specific `target_user_id`.
2.  **Backend Logic**: The backend validates permissions and subscribes your connection's session to the correct internal channel (e.g., `user:123:updates`).
3.  **Events**: You receive messages via the standard client event handlers.

## Subscription Management

The SDK automatically manages your subscriptions across connection lifecycles.

**How it works:**
1. Call `client.realtime.subscribe("user-123")` 
2. SDK establishes a server-side subscription to that user's updates
3. Your handler receives messages for subscribed users

**Connection Recovery:**
- ✅ Automatic reconnection on disconnect
- ✅ Subscriptions are restored automatically
- ✅ No manual tracking or state management needed

**Developer Impact:** Subscribe once and forget. The SDK handles connection recovery and subscription restoration transparently.

## Subscription Patterns: Per-User Model

### The Correct Pattern: One Subscription Per User ✅

**When you have 500 users, you create 500 subscriptions.**

Each user gets their own isolated subscription. You interact purely with user IDs:

```python
# Subscribe to all 500 users
await client.realtime.subscribe_many([
    "user_1", "user_2", "user_3", ..., "user_500"
])
```

**Why This is the Right Approach:**

1. **🔒 Security & Privacy** - Each user can ONLY see their own messages, no data leakage
2. **📊 Efficiency** - Server sends data only to users who need it
3. **📈 Scalability** - The realtime infrastructure is designed to handle millions of channels efficiently
4. **🎯 Isolation** - Easy to debug per-user issues, clean separation of concerns

**Performance Reality:** 500 subscriptions use approximately 500KB of metadata. The realtime server can handle 1M+ active subscriptions per instance.

---

### ❌ Anti-Pattern: Room/Group Channels

**Don't do this for personal user messages:**

```python
# ❌ BAD: One channel for all users  
await client.realtime.subscribe("room_mindspace_123")
# Problem: ALL 500 users receive ALL messages
# Then you must filter client-side → security nightmare
```

**Why This is Wrong:**
- 🔓 **Privacy Violation**: All users see all data
- 📡 **Bandwidth Waste**: Send everything to everyone, then filter
- 🐛 **Complexity**: Manual client-side filtering required
- 🔒 **Security Risk**: Can't enforce access control

**When to Use Room Channels:** Only for true broadcast scenarios where EVERYONE needs the same data (e.g., system-wide announcements, global events).

---

### ❌ Anti-Pattern: Firehose

**Don't subscribe to wildcard channels:**

```python
# ❌ TERRIBLE: Subscribe to everything
await client.realtime.subscribe("root:*")  
# Backend receives EVERYTHING from entire system
```

**Why This is Wrong:**
- 🔥 **Overwhelming**: Cannot scale, will crash under load
- 🔒 **Security**: Backend shouldn't have access to all system data
- 💸 **Cost**: Massive bandwidth waste

**When to Use:** Only for system-level analytics or logging services that genuinely need all events.

---

### FAQ: Subscription Patterns

**Q: "Isn't creating 500 subscriptions inefficient?"**

A: No! The realtime infrastructure is designed for this exact use case. Each subscription is lightweight metadata (~1KB). The server can handle **millions** of concurrent subscriptions. The SDK's `subscribe_many()` makes this fast via parallel RPCs.

**Q: "Why not put everyone in one 'mindspace' channel?"**

A: **Privacy and security.** Room channels mean ALL users receive ALL messages, then you'd need client-side filtering. This is:
- Insecure (users can inspect network traffic)
- Inefficient (wasted bandwidth)  
- Complex (manual filtering logic)

Per-user channels = server-side filtering (secure, fast, simple).

**Q: "Does this mean 500 WebSocket connections?"**

A: No! This is **ONE connection** with **500 subscriptions**. Multiplexing multiple subscriptions over a single WebSocket is the core benefit of this architecture.

**Q: "What if I genuinely need room-based collaboration?"**

A: Use room channels when:
- Real-time collaboration (everyone edits same document)
- Live dashboards (everyone sees same metrics)
- Chat rooms (everyone participates in conversation)

For **personal notifications/messages**, always use per-user channels.

---

## Scalability & Bulk Operations

When managing many users (e.g., a dashboard monitoring 500 agents), use the bulk operations to ensure efficiency and avoid head-of-line blocking.

### `subscribe_many`

Use `subscribe_many` to subscribe to a list of users in parallel.

```python
users_to_monitor = [f"user-{i}" for i in range(500)]

await realtime.subscribe_many(users_to_monitor)
```

The SDK handles:
- Parallel execution (using `asyncio.gather`)
- Error aggregation (raises the first error encountered, logs others)
- Internal state tracking

### `unsubscribe_many`

Similarly, use `unsubscribe_many` to clean up:

```python
await realtime.unsubscribe_many(users_to_monitor)
```

## Connection Resilience

The realtime server automatically handles connection recovery and subscription restoration.

**Behavior on Disconnect:**
- If the WebSocket connection drops, the client will attempt to reconnect automatically (controlled by `centrifuge-python`'s exponential backoff).
- Upon successful reconnection, the server automatically restores all subscriptions.
- No manual re-subscription needed - this happens transparently.

**What This Means for You:**
- ✅ Just call `subscribe()` or `subscribe_many()` once
- ✅ Reconnection is automatic
- ✅ Subscriptions persist across reconnects
- ✅ No state tracking required in your code

## Error Handling

### Connection Errors
Handle connection errors by listening to the `error` event in your `ClientEventHandler` or wrapping calls in try/except blocks.

### Subscription Errors
`subscribe` and `subscribe_many` will raise `MagickMindError` if the backend rejects the request (e.g., invalid permission, user not found).

---

## Message Deduplication ⚠️ CRITICAL

**Problem:** When subscribing to multiple users who are in the same group/mindspace, your backend will receive **duplicate messages**.

### Why Duplicates Happen

Scenario:
- You subscribe to `user_A`, `user_B`, and `user_C`
- All three users are in `mindspace_123`
- AI generates a response for `mindspace_123`
- The message is sent to ALL users in that mindspace
- **Your backend receives the same message 3 times** (once per subscription)

```python
# Backend subscribes to 3 users
await client.realtime.subscribe_many(["user_A", "user_B", "user_C"])

# AI sends message to mindspace_123
# → Message delivered to user_A's channel
# → Message delivered to user_B's channel  
# → Message delivered to user_C's channel

# Your handler is called 3 times with THE SAME message!
@client.realtime.on("chat_message")
async def handle(event: ChatMessageEvent, ctx: EventContext):
    # Called 3x: ctx.target_user_id="user_A", then "user_B", then "user_C"
    # But event.payload.message_id is IDENTICAL
    print(f"Received for {ctx.target_user_id}: {event.payload.message_id}")
```

### The Solution: Deduplication

**Always track processed message IDs** and skip duplicates:

```python
from magick_mind.realtime.events import ChatMessageEvent, EventContext

processed_ids: set[str] = set()  # In production: use Redis/database

@client.realtime.on("chat_message")
async def handle(event: ChatMessageEvent, ctx: EventContext):
    message_id = event.payload.message_id

    # Deduplicate - CRITICAL for multi-user subscriptions!
    if message_id in processed_ids:
        logger.debug(f"Skipping duplicate {message_id} (via {ctx.target_user_id})")
        return

    # Process message — ctx.target_user_id tells you who it's for
    await process_message(event.payload)

    # Mark as processed
    processed_ids.add(message_id)
```

### Production Deduplication Strategies

**Option 1: Redis Set (Recommended)**
```python
import redis

r = redis.Redis()

@client.realtime.on("chat_message")
async def handle(event: ChatMessageEvent, ctx: EventContext):
    message_id = event.payload.message_id

    # Atomic check-and-set
    if not r.sadd("processed_messages", message_id):
        return  # Already processed

    await process_message(event.payload)

    # Optional: Set TTL to clean up old IDs
    r.expire("processed_messages", 86400)  # 24 hours
```

**Option 2: Database Flag**
```python
@client.realtime.on("chat_message")
async def handle(event: ChatMessageEvent, ctx: EventContext):
    message_id = event.payload.message_id

    # Atomic insert (or use ON CONFLICT DO NOTHING)
    result = await db.execute(
        "INSERT INTO processed_messages (id) VALUES ($1) ON CONFLICT DO NOTHING RETURNING id",
        message_id,
    )

    if not result:
        return  # Duplicate

    await process_message(event.payload)
```

**Option 3: In-Memory (Development Only)**
```python
# Simple but loses state on restart!
processed_ids: set[str] = set()

@client.realtime.on("chat_message")
async def handle(event: ChatMessageEvent):
    if event.payload.message_id in processed_ids:
        return
    processed_ids.add(event.payload.message_id)
    await process_message(event.payload)
```

### When Deduplication is Essential

✅ **You MUST deduplicate in production:**
- Building relay services (Telegram bot, Discord bot, backend middleware)
- Storing messages in a database
- Triggering webhooks or external APIs
- Any scenario where duplicate processing would be harmful

**Why always deduplicate?** You don't control whether end-users are in groups. Even if you subscribe to "one user" today, they might join a group tomorrow, and you'll start receiving duplicates without warning.

❌ **Only skip deduplication if:**
- **Development/testing only** - You're debugging and want to see all events
- **Truly idempotent** - Your processing is mathematically idempotent (same message 3x = same result, no side effects)
- **Pure logging** - You're just logging/monitoring and duplicates don't matter

> [!WARNING]
> Don't assume "single user = no duplicates." End-users can join groups at any time. Always implement deduplication for production systems.

### Real-World Example: Telegram Bot

```python
r = redis.Redis()

@client.realtime.on("chat_message")
async def handle_telegram(event: ChatMessageEvent, ctx: EventContext):
    message_id = event.payload.message_id

    # Deduplicate - prevent sending same message 3x to Telegram!
    if not r.sadd(f"sent:{message_id}", "1", ex=3600):
        logger.info(f"Already sent {message_id} to Telegram, skipping")
        return

    # Send to Telegram group
    await bot.send_message(
        chat_id=TELEGRAM_GROUP_ID,
        text=event.payload.message,
    )

    logger.info(f"Sent {message_id} to Telegram (via {ctx.target_user_id})")

# Subscribe to all group members
await client.realtime.subscribe_many([
    "user_alice", "user_bob", "user_charlie"
])
```

### Metrics and Monitoring

Track duplicate rates to understand your traffic:

```python
processed_ids: set[str] = set()
metrics = {"total_received": 0, "duplicates": 0, "processed": 0}

@client.realtime.on("chat_message")
async def handle(event: ChatMessageEvent, ctx: EventContext):
    metrics["total_received"] += 1

    if event.payload.message_id in processed_ids:
        metrics["duplicates"] += 1
        return

    processed_ids.add(event.payload.message_id)
    metrics["processed"] += 1

    await process_message(event.payload)

def get_duplicate_rate():
    if metrics["total_received"] == 0:
        return 0.0
    return metrics["duplicates"] / metrics["total_received"]

# Log periodically
# Duplicate rate: 0.67 (67% duplicates = 3 subscriptions to same mindspace)
```

---

## Best Practices

1.  **Batching**: If adding users incrementally, try to batch them into groups of 10-50 for `subscribe_many` rather than awaiting 50 individual calls.
2.  **Concurrency**: The SDK uses `asyncio.gather` for bulk ops. If you are subscribing to thousands of users, consider chunking your list to avoid overwhelming the event loop or hitting backend rate limits.
3.  **Cleanup**: Always unsubscribe when a user is no longer needed to reduce server load.
3.  **Cleanup**: Always unsubscribe when a user is no longer needed to reduce server load.

## Advanced: Relaying to End-Users

In a typical topology, this SDK runs on **your backend service** (the middleware), which sits between the Magick Mind API and your End-Users.

```mermaid
graph LR
    B[Magick Mind API] -- WebSocket --> S[Your Service (SDK)]
    S -- "WS / SSE / FC" --> U1[End User 1]
    S -- "WS / SSE / FC" --> U2[End User 2]
    S -- "..." --> Un[End User N]
```

### The Fan-Out Pattern

1.  **Receive**: Your service receives a message for `user-123` via the SDK `on_publication` event.
2.  **Process**: You validate/transform the data if needed.
3.  **Relay**: You push the update to `user-123`'s frontend using your own direct channel (e.g., your own WebSocket server, Server-Sent Events, or Firebase Cloud Messaging).

### Multiplexing vs. Firehose

You might wonder: *"Why is there only one handler? Is this a firehose?"*

*   **Multiplexing (Good)**: You connect **once** to the Magick Mind API. Over this single connection, you tell the API: "I want updates for User A, User B, and User C." The API sends *only* those updates down that single wire. This is efficient network usage.
*   **Firehose (Bad)**: Subscribing to a wildcard channel like `root:*` receiving *everything* for the entire system. We are **not** doing this.
*   **One Connection per User (Bad)**: Opening 500 separate WebSocket connections from your backend for each user you monitor. This consumes unnecessary resources (file descriptors, memory).

The single `RelayHandler` is your **Central Dispatch**. It looks at the `channel` name of each incoming packet and routes it to the correct destination.

By acting as the gateway, you maintain control over what your end-users see.

### Implementation Logic

The SDK's `EventContext` gives you the parsed `target_user_id` directly — no manual channel parsing required.

```python
from magick_mind.realtime.events import ChatMessageEvent, EventContext

@client.realtime.on("chat_message")
async def relay_handler(event: ChatMessageEvent, ctx: EventContext):
    """
    Called when a message is received for a specific user.
    ctx.target_user_id is parsed from the channel automatically.
    """
    print(f"📨 Message for [{ctx.target_user_id}]: {event.payload.message}")

    # Forward to that user's frontend
    await relay_to_frontend(ctx.target_user_id, event.payload)
```

---

## Next Steps

### For Production Backends

If you're building a **backend service** (relay, Telegram bot, etc.), you'll need more than just realtime:

📖 **[Backend Integration Guide](../guides/backend_integration.md)**
- Hybrid realtime + HTTP sync patterns
- Gap filling after disconnects  
- Reliable message processing
- Periodic consistency checks

📖 **[Event-Driven Architecture Patterns](../architecture/event_driven_patterns.md)**
- Event sourcing vs event notifications
- When to use realtime vs HTTP
- Migration strategies

### Working Examples

💻 **[examples/backend_service.py](../../examples/backend_service.py)**
- Complete production-ready backend
- Deduplication, sync, recovery
- Copy-paste starting point

💻 **[examples/bulk_subscribe.py](../../examples/bulk_subscribe.py)**
- Bulk operations demo
- Handling 500+ users

💻 **[examples/fan_out_relay.py](../../examples/fan_out_relay.py)**
- RealtimeEventHandler usage
- Message routing patterns

### Architecture Guides

📐 **[Realtime Subscription Patterns](../architecture/realtime_patterns.md)**
- Deep dive: Per-user vs room vs firehose
- Decision matrix and migration guides
- Performance benchmarks
