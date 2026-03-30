# Backend Architecture Guide

## Overview

The Magick Mind SDK is designed for server-side integration with the Magick Mind API using service-level authentication.

> [!NOTE]
> This SDK is intended for backend applications. For browser or mobile app integration, your backend acts as an intermediary between end users and the Magick Mind API.

---

## Architecture Pattern

### Standard Three-Tier Architecture

```
┌─────────────────┐
│   End Users     │  (Browser, Mobile App, Desktop)
│  (Your Auth)    │
└────────┬────────┘
         │ Your authentication (JWT, session, etc.)
         ↓
┌─────────────────┐
│  Your Backend   │  (Node.js, Python, Go, etc.)
│  + Magick SDK   │  ← Service credentials
└────────┬────────┘
         │ SDK calls (authenticated with service account)
         ↓
┌─────────────────┐
│   Magick Mind API   │  (Magick Mind Platform)
└─────────────────┘
```

**Key Points:**
- ✅ End users authenticate with **your** auth system
- ✅ Your backend verifies end-user credentials
- ✅ Your backend uses SDK with **service credentials**
- ✅ Your backend controls permissions and access
- ✅ the Magick Mind API never sees end users directly

---

## Backend Integration Patterns

Your backend sits between end users and the Magick Mind API. Here are the common patterns for structuring this integration:

### Pattern 1: Pure Proxy (No Storage)

**When to use:** Simple apps, low traffic, the Magick Mind API as single source of truth

**Definition:** Backend routes requests to the Magick Mind API without storing data. Still needs to handle pagination, auth, and response formatting.

```python
from magick_mind import MagickMind
from fastapi import FastAPI, Depends

app = FastAPI()
client = MagickMind(email="...", password="...")

# Authentication helper
def verify_user(token: str):
    # Your auth logic
    return decode_jwt(token)

# Send chat message
@app.post("/chat/send")
async def send(request: ChatRequest, user = Depends(verify_user)):
    # Proxy to the Magick Mind API
    response = client.v1.chat.send(
        api_key=request.api_key,
        mindspace_id=request.mindspace_id,
        message=request.message,
        sender_id=user.id
    )
    return response

# Get message history with pagination
@app.get("/messages")
async def get_messages(
    mindspace_id: str,
    cursor: str = None,      # Cursor for pagination
    limit: int = 50,
    user = Depends(verify_user)
):
    # Verify user has access to mindspace
    if not user.can_access(mindspace_id):
        raise Forbidden()
    
    # Proxy to the Magick Mind API with pagination
    result = await client.v1.mindspace.get_messages(
        mindspace_id,
        cursor=cursor,
        limit=limit,
    )
    
    # Return the Magick Mind API's response (optionally transform format)
    return {
        "messages": result.chat_histories,
        "next_cursor": result.next_after_id,  # For next page
        "has_more": result.has_more
    }
```

**Frontend usage:**
```javascript
// First page
let resp = await fetch('/messages?mindspace_id=mind-123&limit=50');

// Next page
resp = await fetch(`/messages?mindspace_id=mind-123&cursor=${resp.next_cursor}&limit=50`);
```

**Pros:**
- ✅ Simple implementation
- ✅ No storage complexity
- ✅ the Magick Mind API is single source of truth
- ✅ No data sync issues

**Cons:**
- ⚠️ Every request hits the Magick Mind API (latency + cost)
- ⚠️ No caching
- ⚠️ Depends on the Magick Mind API availability
- ⚠️ Can't query locally (full-text search, etc.)

---

### Pattern 2: Caching Layer

**When to use:** High traffic, need fast responses, want to reduce the Magick Mind API load

**Challenge:** Pagination makes caching complex. You need to choose: cache pages, or cache individual items?

#### Recommended: Cache Individual Messages

**Strategy:** Don't cache paginated lists. Cache individual messages by ID and always fetch lists from the Magick Mind API.

```python
import redis
import json

redis_client = redis.Redis()

# List endpoint: ALWAYS fetch from the Magick Mind API (don't cache pagination)
@app.get("/messages")
async def get_messages(
    mindspace_id: str,
    cursor: str = None,
    limit: int = 50,
    user = Depends(verify_user)
):
    # No caching here - pagination is complex to cache
    result = await client.v1.mindspace.get_messages(
        mindspace_id,
        cursor=cursor,
        limit=limit,
    )
    
    # BUT cache each individual message (for detail views)
    for msg in result.chat_histories:
        redis_client.setex(
            f"message:{msg.id}",
            3600,  # 1 hour
            json.dumps(msg)
        )
    
    return result

# Detail endpoint: Use cache
@app.get("/messages/{message_id}")
async def get_message(message_id: str, user = Depends(verify_user)):
    # Try cache
    cached = redis_client.get(f"message:{message_id}")
    if cached:
        return json.loads(cached)
    
    # Miss: Fetch from the Magick Mind API
    msg = client.v1.messages.get(message_id=message_id)
    
    # Cache it
    redis_client.setex(f"message:{msg.id}", 3600, json.dumps(msg))
    return msg

# Send: Invalidate is easy (just delete individual message)
@app.post("/messages/send")
async def send_message(request: SendRequest, user = Depends(verify_user)):
    response = client.v1.chat.send(
        mindspace_id=request.mindspace_id,
        message=request.message,
        sender_id=user.id
    )
    
    # No cache to invalidate (lists aren't cached)
    # The new message will be in cache when list is fetched
    return response

# Update: Invalidate single message
@app.patch("/messages/{message_id}")
async def update_message(message_id: str, update: UpdateRequest):
    # Update the Magick Mind API
    response = client.v1.messages.update(message_id, update.content)
    
    # Invalidate JUST this message
    redis_client.delete(f"message:{message_id}")
    
    return response
```

**Why this works:**
- ✅ Pagination always fresh (from the Magick Mind API)
- ✅ Detail views cached (faster)
- ✅ Simple invalidation (one key per message)
- ✅ No stale list issues

#### Alternative: Cache First Page Only

If you want to cache lists, only cache the first page (most commonly accessed):

```python
@app.get("/messages")
async def get_messages(mindspace_id: str, cursor: str = None, limit: int = 50):
    # Only cache first page
    if cursor is None:
        cache_key = f"messages:{mindspace_id}:first_page"
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    
    # Fetch from the Magick Mind API
    result = await client.v1.mindspace.get_messages(
        mindspace_id,
        cursor=cursor,
        limit=limit,
    )
    
    # Cache ONLY first page (short TTL)
    if cursor is None:
        redis_client.setex(cache_key, 60, json.dumps(result.model_dump()))
    
    return result

# Invalidation: Delete first page cache
@app.post("/messages/send")
async def send_message(request: SendRequest):
    response = client.v1.chat.send(...)
    
    # Invalidate first page
    redis_client.delete(f"messages:{request.mindspace_id}:first_page")
    
    return response
```

**Pros:**
- ✅ Fast first page (80% of traffic)
- ✅ Simple invalidation
- ✅ Other pages always fresh

**Cons:**
- ⚠️ Only first page cached
- ⚠️ Still need to handle invalidation

#### Don't Do: Cache All Pages

**❌ Problem:** Each page needs unique cache key. Invalidation becomes complex.

```python
# ❌ Don't do this
cache_key = f"messages:{mindspace_id}:cursor:{cursor}:limit:{limit}"
# Too many cache keys, hard to invalidate all pages
```

**Pros:**
- ✅ Individual messages cached (fast detail views)
- ✅ Lists always fresh (from the Magick Mind API)
- ✅ Simple invalidation
- ✅ No stale data issues

**Cons:**
- ⚠️ List requests always hit the Magick Mind API
- ⚠️ Not ideal for very high traffic

---

### Pattern 3: Full Database Storage

**When to use:** Need rich queries, analytics, offline mode, custom IDs

```python
from magick_mind.realtime.events import ChatMessageEvent, EventContext

@client.realtime.on("chat_message")
async def handle(event: ChatMessageEvent, ctx: EventContext):
    payload = event.payload
    # Store in your database
    await db.messages.insert({
        "id": generate_id(),  # Your ID
        "api_message_id": payload.message_id,
        "reply_to_message_id": payload.reply_to,
        "user_id": ctx.target_user_id,
        "content": payload.message,
        "created_at": datetime.utcnow(),
    })

# Periodic sync to catch missed messages
async def sync_with_api():
    last_cursor = await db.get_last_cursor()
    
    history = await client.v1.mindspace.get_messages(
        mindspace_id,
        cursor=last_cursor,
        limit=100,
    )
    
    for msg in history.data:
        await db.messages.upsert({
            "api_message_id": msg.id,
            "content": msg.content,
            "api_version": msg.version
        })
```

**Pros:**
- ✅ Full control over data
- ✅ Rich querying (full-text search, etc.)
- ✅ Use your own IDs
- ✅ Analytics and reporting

**Cons:**
- ⚠️ Need to sync with the Magick Mind API
- ⚠️ Handle updates/deletes
- ⚠️ Two sources of truth
- ⚠️ More storage

---

## Realtime Integration Patterns

### Pattern A: Realtime as Notification

**Realtime triggers history fetch (source of truth)**

```python
@client.realtime.on("chat_message")
async def handle_notification(event: ChatMessageEvent, ctx: EventContext):
    # Deduplicate
    if not redis.sadd("processed", event.payload.message_id):
        return

    # Just notify frontend — ctx.target_user_id identifies who
    await websocket.send_notification(ctx.target_user_id, {
        "type": "new_message",
        "message_id": event.payload.message_id,
    })

    # Optionally: Trigger background history fetch
    asyncio.create_task(fetch_from_history(ctx.target_user_id))

async def fetch_from_history(user_id):
    """Fetch latest from the Magick Mind API history API."""
    messages = await client.v1.mindspace.get_messages(
        get_mindspace(user_id),
        cursor=get_last_cursor(user_id),
    )
    # Store and/or send to frontend
```

**Benefits:**
- ✅ the Magick Mind API history is source of truth
- ✅ Proper pagination/versioning
- ✅ Realtime for speed, history for correctness

---

### Pattern B: Realtime Direct Storage

**Store realtime payload immediately (fast path)**

```python
@client.realtime.on("chat_message")
async def handle_direct(event: ChatMessageEvent, ctx: EventContext):
    # Deduplicate
    if not redis.sadd("processed", event.payload.message_id):
        return

    # Store immediately
    await db.messages.insert(event.payload.model_dump())

    # Send to frontend
    await websocket.send(ctx.target_user_id, event.payload.model_dump())
```

**Benefits:**
- ✅ Ultra-low latency
- ✅ Immediate frontend updates

**Trade-offs:**
- ⚠️ Must handle updates/deletes separately
- ⚠️ Need periodic reconciliation with history

---

### Pattern C: Hybrid (Recommended)

**Combine realtime speed + history correctness**

```python
@client.realtime.on("chat_message")
async def handle_hybrid(event: ChatMessageEvent, ctx: EventContext):
    payload = event.payload
    # 1. Deduplicate
    if not redis.sadd("processed", payload.message_id):
        return

    # 2. Send to frontend immediately (fast UX)
    await websocket.send(ctx.target_user_id, payload.model_dump())

    # 3. Store reference
    await db.message_refs.insert({
        "message_id": payload.message_id,
        "user_id": ctx.target_user_id,
        "received_at": datetime.utcnow(),
    })

    # 4. Background: Fetch from history and cache
    asyncio.create_task(cache_from_history(payload.message_id))

async def cache_from_history(message_id):
    """Fetch full message from source of truth."""
    msg = client.v1.history.get_message_by_id(message_id)
    await db.messages.upsert(msg)  # Cache it
```

**Benefits:**
- ✅ Fast frontend delivery
- ✅ History as source of truth
- ✅ Rich local caching for queries
- ✅ Best of both worlds

---

## Security Best Practices

### 1. Never Expose Service Credentials
```bash
# ✅ Good: Environment variables
export MAGICKMIND_EMAIL="service@company.com"
export MAGICKMIND_PASSWORD="secure_password"

# ❌ Bad: Hardcoded in code
client = MagickMind(email="service@company.com", password="abc123")
```

### 2. Verify End-User Tokens
```python
# Always verify before making SDK calls
@app.post("/api/chat")
async def chat(request: Request):
    # Verify token
    user = verify_jwt(request.headers['Authorization'])
    if not user:
        raise Unauthorized()
    
    # Then use SDK
    return client.v1.chat.send(sender_id=user.id, ...)
```

### 3. Implement Rate Limiting
```python
from slowapi import Limiter

limiter = Limiter(key_func=lambda: get_user_id())

@app.post("/api/chat")
@limiter.limit("10/minute")  # Per user
async def chat(request):
    ...
```

### 4. Log SDK Calls
```python
# Track SDK usage per user
logger.info(f"User {user.id} sent chat message", extra={
    "user_id": user.id,
    "mindspace_id": mindspace_id,
    "timestamp": datetime.utcnow()
})
```

---

## Next Steps

- See [Backend Integration Guide](../guides/backend_integration.md) for complete examples
- See [Realtime Guide](../realtime_guide.md) for WebSocket patterns
- See `examples/backend_service.py` for production-ready code

---

## FAQ

**Q: Can end users use the SDK directly in browsers?**  
A: No. This requires service credentials that should never be exposed. Use your backend as a proxy.

**Q: How do I authenticate end users?**  
A: Use your own auth system (JWT, sessions, Firebase Auth, etc.). The SDK authenticates your **backend** to the Magick Mind API.

**Q: What if I want end users to call the Magick Mind API directly?**  
A: This would require the API to support end-user authentication with scoped tokens. Contact the Magick Mind team for this feature.

**Q: How does this compare to Supabase?**  
A: Supabase offers both patterns (service role + anon key with RLS). This SDK is service-role only (like Firebase Admin).

**Q: Can I use this in a serverless function?**  
A: Yes! Perfect for serverless (AWS Lambda, Vercel, Cloudflare Workers). Just store credentials in environment variables.
