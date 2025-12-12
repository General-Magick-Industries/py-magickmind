# Realtime Integration Guide

This guide explains how to use the Realtime features of the Magick Mind SDK effectively, especially for high-scale scenarios (500+ users) and robust error handling.

## Architecture

The SDK uses a WebSocket connection (powered by Centrifugo) to receive real-time updates. Unlike traditional Pub/Sub where you subscribe to arbitrary channels, this SDK uses an **RPC-based subscription model**:

1.  **RPC `subscribe`**: You ask the Bifrost backend to subscribe your connection to a specific `target_user_id`.
2.  **Backend Logic**: The backend validates permissions and subscribes your connection's session to the correct internal channel (e.g., `user:123:updates`).
3.  **Events**: You receive messages via the standard client event handlers.

### Why Client-Side Tracking?

Because we use an **RPC call** to initate the subscription (to hide channel implementation details from the client), the standard Centrifugo client library is not aware of these server-side subscriptions. 

If the connection is lost:
1.  The server cleans up the session (eventually).
2.  The standard client reconnects but doesn't know it needs to re-subscribe to those users.

**Therefore, the SDK maintains a local set of active user IDs and automatically re-issues the RPC calls upon reconnection.**

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

## Connection Resilience & Auto-Resubscribe

The SDK automatically tracks your active subscriptions locally. 

**Behavior on Disconnect:**
- If the WebSocket connection drops, the client will attempt to reconnect automatically (controlled by `centrifuge-python`'s backoff).
- Upon successful reconnection (`connected` event), the SDK's internal handler triggers.
- It automatically re-issues `subscribe` RPC calls for all currently tracked users.

**Note**: This restoration happens asynchronously immediately after connection.

## Error Handling

### Connection Errors
Handle connection errors by listening to the `error` event in your `ClientEventHandler` or wrapping calls in try/except blocks.

### Subscription Errors
`subscribe` and `subscribe_many` will raise `MagickMindError` if the backend rejects the request (e.g., invalid permission, user not found).

## Best Practices

1.  **Batching**: If adding users incrementally, try to batch them into groups of 10-50 for `subscribe_many` rather than awaiting 50 individual calls.
2.  **Concurrency**: The SDK uses `asyncio.gather` for bulk ops. If you are subscribing to thousands of users, consider chunking your list to avoid overwhelming the event loop or hitting backend rate limits.
3.  **Cleanup**: Always unsubscribe when a user is no longer needed to reduce server load.
3.  **Cleanup**: Always unsubscribe when a user is no longer needed to reduce server load.

## Advanced: Relaying to End-Users

In a typical topology, this SDK runs on **your backend service** (the middleware), which sits between Bifrost and your End-Users.

```mermaid
graph LR
    B[Bifrost] -- WebSocket --> S[Your Service (SDK)]
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

*   **Multiplexing (Good)**: You connect **once** to Bifrost. Over this single connection, you tell Bifrost: "I want updates for User A, User B, and User C." Bifrost sends *only* those updates down that single wire. This is efficient network usage.
*   **Firehose (Bad)**: Subscribing to a wildcard channel like `root:*` receiving *everything* for the entire system. We are **not** doing this.
*   **One Connection per User (Bad)**: Opening 500 separate WebSocket connections from your backend for each user you monitor. This consumes unnecessary resources (file descriptors, memory).

The single `RelayHandler` is your **Central Dispatch**. It looks at the `channel` name of each incoming packet and routes it to the correct destination.

By acting as the gateway, you maintain control over what your end-users see.

### Implementation Logic

The SDK provides a high-level `RealtimeEventHandler` that handles the channel parsing for you. You only need to override `on_message` and `on_connected`.

*(Full runnable example available in `examples/fan_out_relay.py`)*

```python
from magick_mind.realtime.handler import RealtimeEventHandler

class RelayHandler(RealtimeEventHandler):
    async def on_connected(self, ctx):
        print(f"✅ Connected! Client ID: {ctx.client}")

    async def on_message(self, user_id: str, payload: Any) -> None:
        """
        Called when a message is received for a specific user.
        The SDK automatically parsed 'personal:user_123#svc' -> 'user_123'.
        """
        print(f"📨 Message for [{user_id}]: {payload}")
        
        # Forward to that user's frontend
        await self.relay_to_frontend(user_id, payload)
```
