#!/usr/bin/env python3
"""
Example: Caching Pattern with Redis

Demonstrates caching individual messages (not paginated lists) to reduce
Bifrost API calls while keeping lists always fresh.

Pattern:
- List endpoints: Always fetch from Bifrost (pagination is hard to cache)
- Detail endpoints: Cache individual messages by ID
- Write endpoints: Invalidate specific messages

This balances freshness (lists) with performance (details).

Dependencies:
    pip install redis

Usage:
    # Start Redis locally
    docker run -d -p 6379:6379 redis

    # Run example
    export BIFROST_EMAIL="service@example.com"
    export BIFROST_PASSWORD="password"
    export BIFROST_BASE_URL="http://localhost:8888"
    python examples/caching_example.py
"""

import asyncio
import os
import json
import logging
from datetime import timedelta
from typing import Optional

import redis
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from magick_mind import MagickMind

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("caching_example")

# Initialize
app = FastAPI(title="Caching Example")

# SDK client (service credentials)
client = MagickMind(
    email=os.getenv("BIFROST_EMAIL"),
    password=os.getenv("BIFROST_PASSWORD"),
    base_url=os.getenv("BIFROST_BASE_URL", "http://localhost:8888"),
)

# Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True,  # Auto-decode bytes to strings
)

# Cache stats (for monitoring)
cache_stats = {"hits": 0, "misses": 0, "invalidations": 0}


# Request/Response models
class SendMessageRequest(BaseModel):
    mindspace_id: str
    message: str
    sender_id: str
    api_key: str


class UpdateMessageRequest(BaseModel):
    content: str


# === Endpoints ===


@app.get("/messages")
async def list_messages(
    mindspace_id: str,
    cursor: Optional[str] = None,
    limit: int = 50,
):
    """
    List messages (NEVER cached - pagination is complex).

    But we DO cache each individual message for detail views.
    """
    logger.info(f"Fetching messages for mindspace {mindspace_id}")

    # Always fetch from Bifrost
    result = client.v1.history.get_messages(
        mindspace_id=mindspace_id,
        after_id=cursor,
        limit=limit,
    )

    # Side effect: Cache each message individually
    for msg in result.chat_histories:
        cache_key = f"message:{msg.id}"
        redis_client.setex(
            cache_key,
            timedelta(hours=1),  # 1 hour TTL
            json.dumps(
                {
                    "id": msg.id,
                    "content": msg.content,
                    "sent_by_user_id": msg.sent_by_user_id,
                    "reply_to_message_id": msg.reply_to_message_id,
                    "created_at": str(msg.created_at),
                }
            ),
        )
        logger.debug(f"Cached message {msg.id}")

    return {
        "messages": [
            {
                "id": m.id,
                "content": m.content,
                "sent_by": m.sent_by_user_id,
                "created_at": str(m.created_at),
            }
            for m in result.chat_histories
        ],
        "next_cursor": result.next_after_id,
        "has_more": result.has_more,
    }


@app.get("/messages/{message_id}")
async def get_message(message_id: str):
    """
    Get single message (CACHED by message ID).

    This is where caching provides value - detail views are fast.
    """
    cache_key = f"message:{message_id}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        cache_stats["hits"] += 1
        logger.info(f"Cache HIT for message {message_id}")
        return json.loads(cached)

    # Cache miss
    cache_stats["misses"] += 1
    logger.info(f"Cache MISS for message {message_id}")

    # Fetch from Bifrost
    # Note: SDK doesn't have get_message_by_id yet, so we'd fetch full list
    # For demonstration, we'll return a simulated response

    # In real implementation:
    # msg = client.v1.messages.get(message_id=message_id)

    # Simulated for example
    msg_data = {
        "id": message_id,
        "content": "Message content from Bifrost",
        "sent_by_user_id": "user-123",
        "reply_to_message_id": None,
        "created_at": "2024-01-01T10:00:00Z",
    }

    # Cache it
    redis_client.setex(cache_key, timedelta(hours=1), json.dumps(msg_data))

    return msg_data


@app.post("/messages/send")
async def send_message(request: SendMessageRequest):
    """
    Send message (NO cache invalidation needed).

    Why? Lists aren't cached, and the new message will be cached
    when the list endpoint is called next.
    """
    logger.info(f"Sending message to mindspace {request.mindspace_id}")

    # Send via SDK
    response = client.v1.chat.send(
        api_key=request.api_key,
        mindspace_id=request.mindspace_id,
        message=request.message,
        sender_id=request.sender_id,
    )

    if not response.success:
        raise HTTPException(status_code=500, detail=response.message)

    # No cache to invalidate!
    # The new message will be in the cache when list is fetched next

    return {
        "success": True,
        "message_id": response.content.message_id,
    }


@app.patch("/messages/{message_id}")
async def update_message(message_id: str, request: UpdateMessageRequest):
    """
    Update message (INVALIDATE specific message cache).

    Simple invalidation: just delete the cache key.
    Next read will fetch fresh from Bifrost.
    """
    logger.info(f"Updating message {message_id}")

    # Update in Bifrost
    # Note: SDK doesn't have update endpoint yet
    # In real implementation:
    # response = client.v1.messages.update(message_id, request.content)

    # Invalidate cache
    cache_key = f"message:{message_id}"
    deleted = redis_client.delete(cache_key)

    if deleted:
        cache_stats["invalidations"] += 1
        logger.info(f"Invalidated cache for message {message_id}")

    return {
        "success": True,
        "message_id": message_id,
        "cache_invalidated": bool(deleted),
    }


@app.delete("/messages/{message_id}")
async def delete_message(message_id: str):
    """
    Delete message (INVALIDATE specific message cache).
    """
    logger.info(f"Deleting message {message_id}")

    # Delete from Bifrost
    # In real implementation:
    # client.v1.messages.delete(message_id=message_id)

    # Invalidate cache
    cache_key = f"message:{message_id}"
    deleted = redis_client.delete(cache_key)

    if deleted:
        cache_stats["invalidations"] += 1
        logger.info(f"Invalidated cache for message {message_id}")

    return {
        "success": True,
        "message_id": message_id,
        "cache_invalidated": bool(deleted),
    }


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache performance metrics.

    Use this to monitor cache effectiveness.
    """
    total_requests = cache_stats["hits"] + cache_stats["misses"]
    hit_rate = (cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

    return {
        "hits": cache_stats["hits"],
        "misses": cache_stats["misses"],
        "invalidations": cache_stats["invalidations"],
        "total_requests": total_requests,
        "hit_rate_percent": round(hit_rate, 2),
        "redis_info": {
            "keys": redis_client.dbsize(),
            "memory": redis_client.info("memory").get("used_memory_human"),
        },
    }


@app.post("/cache/clear")
async def clear_cache():
    """
    Clear all message caches (for testing/debugging).
    """
    pattern = "message:*"
    keys = redis_client.keys(pattern)
    deleted = 0

    for key in keys:
        redis_client.delete(key)
        deleted += 1

    logger.info(f"Cleared {deleted} cache entries")

    return {"cleared": deleted}


if __name__ == "__main__":
    """
    Run this example with:
    
    1. Start Redis:
        docker run -d -p 6379:6379 redis
    
    2. Set environment variables:
        export BIFROST_EMAIL="service@example.com"
        export BIFROST_PASSWORD="password"
        export BIFROST_BASE_URL="http://localhost:8888"
    
    3. Install dependencies:
        pip install fastapi uvicorn redis
    
    4. Run server:
        uvicorn caching_example:app --reload
    
    5. Test endpoints:
        # List (always fresh)
        curl http://localhost:8000/messages?mindspace_id=mind-123
        
        # Detail (cached)
        curl http://localhost:8000/messages/msg-456
        
        # Stats
        curl http://localhost:8000/cache/stats
    
    Expected behavior:
    - First detail request: MISS (fetches from Bifrost)
    - Second detail request: HIT (from Redis)
    - After update: Cache invalidated
    - Next detail request: MISS (fetches fresh)
    
    Cache hit rate should be >70% for detail endpoints in production.
    """
    import uvicorn

    logger.info("Starting caching example server...")
    logger.info("Make sure Redis is running on localhost:6379")

    uvicorn.run(app, host="0.0.0.0", port=8000)
