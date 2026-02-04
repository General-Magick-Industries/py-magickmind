# Backend Integration Guide

This guide is for the **primary use case**: Backend services using the SDK to integrate with Bifrost.

> **Note**: The SDK also works for desktop applications and CLI tools. If you're building one of those, many patterns here still apply, just without the "relay to your frontend" step.

## Your Architecture (Backend as Middleware)

```
[Your Frontend/App] ←→ [Your Backend + SDK] ←→ [Bifrost API]
```

As a backend, you're **middleware** - receiving data from Bifrost and managing state for your own frontend/application.

## Key Challenges for Backend Users

### 1. Message Deduplication
Events might arrive multiple times (reconnects, retries). You need to track what you've processed.

### 2. Message Ordering
Messages might arrive out of order. You need a strategy to handle this.

### 3. Gap Handling
If your backend goes down or disconnects, you'll miss realtime events. You need to fill these gaps.

### 4. Consistency
Your database state needs to stay consistent with Bifrost's truth.

## Recommended Architecture Pattern

### The Hybrid Approach (Realtime + Periodic Sync)

This combines the **speed of realtime events** with the **reliability of HTTP polling**:

```python
from magick_mind import MagickMind, ChatPayload
import asyncio
from typing import Set, Optional

class ChatBackendService:
    """
    Production-ready backend service for handling chat.
    
    Features:
    - Realtime events for low latency
    - Deduplication to prevent double-processing
    - Periodic sync to catch missed events
    - History API for gap filling
    """
    
    def __init__(self, client: MagickMind):
        self.client = client
        
        # Track processed messages (use Redis in production)
        self.processed_messages: Set[str] = set()
        
        # Track last sync position for pagination
        self.last_sync_cursor: Optional[str] = None
    
    async def handle_realtime_event(self, channel: str, data: dict):
        """
        Handle incoming realtime event.
        
        Called when WebSocket receives a message publication.
        """
        # Parse the event payload
        try:
            payload = ChatPayload.model_validate(data)
        except Exception as e:
            logger.error(f"Invalid payload: {e}")
            return
        
        # Deduplicate - critical for backends!
        if payload.message_id in self.processed_messages:
            logger.debug(f"Skipping duplicate: {payload.message_id}")
            return
        
        # Process the message
        await self._process_message(payload)
        
        # Mark as processed
        self.processed_messages.add(payload.message_id)
    
    async def _process_message(self, payload: ChatPayload):
        """
        Your business logic for processing a message.
        
        This is where you:
        - Store in your database
        - Trigger webhooks
        - Notify your frontend
        - Update analytics
        - etc.
        """
        # Example: Store in your DB
        await your_db.messages.insert({
            "message_id": payload.message_id,
            "task_id": payload.task_id,
            "content": payload.content,
            "reply_to": payload.reply_to,
            "processed_at": datetime.utcnow(),
        })
        
        # Example: Notify your frontend via WebSocket
        await your_websocket_server.broadcast({
            "type": "new_message",
            "payload": payload.model_dump(),
        })
    
    async def sync_history(
        self, 
        mindspace_id: str,
        since_message_id: Optional[str] = None
    ):
        """
        Sync chat history from Bifrost.
        
        Use cases:
        - On startup: Get recent history
        - After reconnect: Fill gaps
        - Periodic: Verify consistency
        
        Note: Requires mindspaces.get_messages() to be implemented
              in the SDK (coming soon!)
        """
        # TODO: Once history endpoint is added to SDK
        # messages = await self.client.v1.mindspaces.get_messages(
        #     mindspace_id=mindspace_id,
        #     after_id=since_message_id,
        #     limit=100
        # )
        
        # For now, you'd call the HTTP endpoint directly:
        response = self.client.http.get(
            "/v1/mindspaces/messages",
            params={
                "mindspace_id": mindspace_id,
                "after_id": since_message_id or "",
                "limit": 100,
            }
        )
        
        messages = response.json().get("chat_histories", [])
        
        # Process each message
        for msg_data in messages:
            # Convert to ChatPayload (map field names)
            payload = ChatPayload(
                message_id=msg_data["id"],
                task_id="",  # May not be in history
                content=msg_data["content"],
                reply_to=msg_data.get("reply_to_message_id"),
            )
            
            # Check if already processed
            if payload.message_id not in self.processed_messages:
                await self._process_message(payload)
                self.processed_messages.add(payload.message_id)
        
        # Update cursor for next sync
        if messages:
            self.last_sync_cursor = messages[-1]["id"]
    
    async def periodic_sync(self, mindspace_id: str, interval: int = 300):
        """
        Run periodic sync to catch any missed events.
        
        Args:
            mindspace_id: Mindspace to sync
            interval: Seconds between syncs (default 5 minutes)
        """
        while True:
            try:
                await self.sync_history(
                    mindspace_id=mindspace_id,
                    since_message_id=self.last_sync_cursor
                )
            except Exception as e:
                logger.error(f"Sync failed: {e}")
            
            await asyncio.sleep(interval)
    
    async def start(self, mindspace_id: str, user_id: str):
        """
        Start the backend service.
        
        This is the main entry point that sets up everything.
        """
        # 1. Initial history sync on startup
        logger.info("Syncing initial history...")
        await self.sync_history(mindspace_id=mindspace_id)
        
        # 2. Connect to realtime
        logger.info("Connecting to realtime...")
        await self.client.realtime.connect()
        
        # 3. Subscribe to events
        await self.client.realtime.subscribe(
            target_user_id=user_id,
            on_publication=self.handle_realtime_event
        )
        
        # 4. Start periodic sync in background
        asyncio.create_task(self.periodic_sync(mindspace_id))
        
        logger.info("Backend service running!")
```

## Usage Example

```python
# main.py - Your backend application
import asyncio
import os
from magick_mind import MagickMind

async def main():
    # Initialize SDK client
    client = MagickMind(
        base_url=os.getenv("BIFROST_URL"),
        email=os.getenv("BIFROST_EMAIL"),
        password=os.getenv("BIFROST_PASSWORD"),
    )
    
    # Create backend service
    service = ChatBackendService(client)
    
    # Start it
    await service.start(
        mindspace_id="mind-123",
        user_id="service-user-456"
    )
    
    # Keep running
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
```

## State Management Best Practices

### DO Track:

✅ **Message IDs you've processed**
```python
# In production, use Redis or your database
processed_messages = set()  # Or: redis.sadd("processed", msg_id)
```

✅ **Last sync cursor for pagination**
```python
last_sync_cursor = "msg-789"  # Last message ID you synced
```

✅ **Connection state for recovery**
```python
is_connected = True
last_disconnect_time = None
```

### DON'T Necessarily:

❌ **Store full message content long-term**
- Bifrost is the source of truth
- Only cache if you need offline capability or have specific business requirements

❌ **Implement complex ordering logic**
- Use `after_id` pagination from history endpoint
- Bifrost handles ordering

❌ **Trust realtime as only source**
- Always have HTTP fallback
- Periodically verify consistency

## Deduplication Strategies

### Strategy 1: In-Memory Set (Simple, Good for Development)

```python
processed = set()

if message_id not in processed:
    process(message)
    processed.add(message_id)
```

**Pros:** Simple, fast  
**Cons:** Lost on restart, memory limited

### Strategy 2: Redis Set (Recommended for Production)

```python
import redis
r = redis.Redis()

if not r.sismember("processed_messages", message_id):
    process(message)
    r.sadd("processed_messages", message_id)
    r.expire("processed_messages", 86400)  # 24h TTL
```

**Pros:** Survives restarts, scalable  
**Cons:** Network overhead

### Strategy 3: Database Check (Most Reliable)

```python
existing = await db.messages.find_one({"message_id": message_id})

if not existing:
    await process(message)
    await db.messages.insert({"message_id": message_id, ...})
```

**Pros:** Permanent record, no separate tracking  
**Cons:** Slower, DB load

## Recovery Patterns

### On Startup
```python
async def on_startup():
    # 1. Get last processed message from your DB
    last_msg = await db.messages.find_one(sort=[("created_at", -1)])
    
    # 2. Sync everything after that
    if last_msg:
        await sync_history(since_message_id=last_msg["message_id"])
    else:
        # First time - get recent history
        await sync_history()  # Gets latest 100
```

### On Reconnect
```python
async def on_reconnect():
    # Fill any gaps that occurred during downtime
    await sync_history(since_message_id=last_sync_cursor)
```

### Periodic Health Check
```python
async def health_check():
    """Verify your state matches Bifrost."""
    # Compare your message count with Bifrost's
    our_count = await db.messages.count()
    bifrost_history = await get_full_history()
    
    if our_count != len(bifrost_history):
        logger.warning(f"Count mismatch: {our_count} vs {len(bifrost_history)}")
        await full_resync()
```

## Error Handling

```python
async def handle_realtime_event(self, channel: str, data: dict):
    try:
        payload = ChatPayload.model_validate(data)
    except ValidationError as e:
        # Log and skip invalid events
        logger.error(f"Invalid event payload: {e}")
        return
    
    try:
        await self._process_message(payload)
    except Exception as e:
        # Log but don't crash - event will be caught in next sync
        logger.error(f"Failed to process {payload.message_id}: {e}")
        # Optionally: Add to retry queue
```

## Performance Considerations

### Connection Pooling
```python
# SDK already handles this, but if calling HTTP directly:
import httpx

http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=10)
)
```

### Batch Processing
```python
# If syncing large history:
async def sync_history_batched(mindspace_id: str):
    cursor = None
    while True:
        messages = await get_messages(after_id=cursor, limit=100)
        if not messages:
            break
        
        # Process batch
        await asyncio.gather(*[
            process_message(msg) for msg in messages
        ])
        
        cursor = messages[-1].message_id
```

### Rate Limiting
```python
from asyncio import Semaphore

# Limit concurrent processing
semaphore = Semaphore(10)

async def process_message(msg):
    async with semaphore:
        await _process_message(msg)
```

## Monitoring & Observability

```python
# Track metrics
class Metrics:
    messages_received = 0
    messages_processed = 0
    messages_duplicates = 0
    sync_count = 0
    errors = 0

# Log key events
logger.info(f"Received message: {payload.message_id}")
logger.info(f"Processed {Metrics.messages_processed} messages")
logger.warning(f"Duplicate rate: {Metrics.messages_duplicates / Metrics.messages_received}")
```

## Common Pitfall: Event Trust

❌ **Don't do this:**
```python
# Trusting realtime as only source
async def on_event(data):
    await process(data)  # What if you missed some events?
```

✅ **Do this:**
```python
# Hybrid with fallback
async def on_event(data):
    await process(data)  # Fast path

# And separately:
async def periodic_sync():
    await sync_history()  # Safety net
```

## Next Steps

1. **Implement your business logic** in `_process_message()`
2. **Choose deduplication strategy** (Redis recommended)
3. **Set up monitoring** for message counts and errors
4. **Test recovery** by simulating disconnects
5. **Consider implementing** message queues (SQS, RabbitMQ) for reliability

## Questions?

- Check [Architecture Patterns](../architecture/event_driven_patterns.md) for deeper explanation
- See [examples/backend_service.py](../../examples/backend_service.py) for complete code
- Open an issue if you need help with your specific use case
