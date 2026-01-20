# Event-Driven Architecture Patterns

This guide explains architectural patterns for using the Magick Mind SDK in event-driven systems.

## 🏗️ Where This SDK Fits

**Primary use case: Backend services** 

This Python SDK is designed primarily for **backend services** that integrate Bifrost into your application:

```
[Your Frontend]  ←→  [Your Backend + SDK]  ←→  [Bifrost SaaS]
  (You manage)         (SDK lives here)         (We provide)
```

**Also works well for:**
- ✅ Desktop applications (PyQt, Tkinter, wxPython)
- ✅ CLI tools and automation scripts
- ✅ Server-side scripts

**For browser/mobile frontends:**
- ❌ Browser-based web apps: Would need JavaScript/TypeScript SDK (not yet available)
- ❌ Native mobile apps: Would need Swift/Kotlin SDKs (not yet available)

**Most common architectures:**
- **Telegram Bot**: Telegram Chat ← Python Bot (SDK) ← Bifrost
- **Web App**: React Frontend ← FastAPI Backend (SDK) ← Bifrost
- **Mobile App**: Flutter App ← Django Backend (SDK) ← Bifrost
- **Desktop App**: PyQt GUI (SDK) ← Bifrost (direct connection)

**Your backend is middleware** - receiving data from Bifrost and managing state for YOUR frontend.

## Table of Contents

- [Your Backend's Role](#your-backends-role)
- [Pattern 1: Events as Source of Truth](#pattern-1-events-as-source-of-truth)
- [Pattern 2: Events as Notifications](#pattern-2-events-as-notifications)
- [Pattern 3: Hybrid Approach (Recommended)](#pattern-3-hybrid-approach-recommended)
- [Choosing the Right Pattern](#choosing-the-right-pattern)
- [Real-World Implementations](#real-world-implementations)

## Your Backend's Role

As a backend using the SDK, your responsibilities are:

1. **Receive** events/data from Bifrost
2. **Process** business logic (validate, transform, enrich)
3. **Store** in your database
4. **Relay** to your frontend (via your own WebSocket/REST/GraphQL)

The pattern you choose affects **how** you do step #1 (receive from Bifrost).

### Important: Personal Channel Subscription Pattern

**Your backend subscribes to personal channels for each end user**, not to shared "rooms" or "mindspaces":

```python
# ✅ CORRECT: Subscribe to personal channel for specific end user
await client.realtime.subscribe(
    target_user_id="end-user-456",  # Specific end user
    on_publication=handle_event
)
# This subscribes to: personal:end-user-456#<your-service-id>
```

```python
# ❌ INCORRECT: Don't subscribe to mindspace/room directly
await client.realtime.subscribe(
    target_user_id="mindspace-123",  # This is a room, not a user!
    on_publication=handle_event
)
```

**Why personal channels?**
- **Isolation**: Each user only receives their own events
- **Security**: Users can't see each other's messages
- **Scalability**: Better performance for multi-user systems

**Pattern**: When you subscribe with `target_user_id="user-456"`, the SDK internally constructs the channel name as `personal:<user-456>#<service-user-id>` and subscribes to it.

**Note**: You might still use `mindspace_id` for **history fetching** via HTTP, but realtime subscriptions are per end user.

### Self-Service Pattern (Robotics/IoT)

**Edge Case:** When the service user and end user are the same entity (robot authenticates as itself):

```python
# Robot/Device as both service and end user
client = MagickMind(
    email="robot-001@company.com",  # Service credentials
    password="robot-password"
)

# Subscribe to own channel (service_user == end_user)
await client.realtime.subscribe("robot-001")  # Same identity!
# Channel: personal:robot-001#robot-001

# Send as itself
response = client.v1.chat.send(
    sender_id="robot-001",  # Same as service user
    message="Analyze my sensor data"
)

# Receive own AI responses
async def on_message(user_id, payload):
    # user_id == "robot-001" (self)
    print(f"AI response: {payload['content']}")
```

**Use Cases:**
- **Autonomous Robots**: Robot has AI conversations about its own state
- **IoT Devices**: Smart devices with on-board AI processing
- **Desktop Apps**: Single-user personal AI assistants
- **Edge Devices**: Industrial equipment with self-diagnostics AI

**Pattern Still Works:**
- ✅ Channel: `personal:robot-001#robot-001` (valid!)
- ✅ History: Fetch with `mindspace_id` and filter by `sender_id="robot-001"`
- ✅ Correlation: Use `reply_to_message_id` as normal


## Pattern 1: Events as Source of Truth

### How It Works

```
Bifrost --event(full message)--> Your Backend --relay--> Your Frontend
                                      ↓
                                 Store in DB
```

The event from Bifrost contains **complete data**. Your backend trusts it and relays it.

### Code Example

```python
"""
Pattern 1: Events as Source of Truth

Your backend receives complete data from Bifrost and relays to your frontend.
"""

from magick_mind import MagickMind, ChatPayload
from fastapi import FastAPI, WebSocket
import asyncio

# Your backend application
app = FastAPI()

class ChatBackend:
    def __init__(self, client: MagickMind):
        self.sdk_client = client
        self.your_db = YourDatabase()
        self.your_websocket_connections = set()  # Your frontend connections
    
    async def on_bifrost_event(self, channel: str, data: dict):
        """
        Receives event from Bifrost with complete message data.
        Backend processes and relays to YOUR frontend.
        """
        # Parse event from Bifrost
        message = ChatPayload.model_validate(data)
        
        print(f"📥 Received from Bifrost: {message.message_id}")
        
        # Business logic: Store in YOUR database
        await self.your_db.messages.insert_one({
            "id": message.message_id,
            "task_id": message.task_id,
            "content": message.content,
            "reply_to": message.reply_to,
            "received_at": datetime.now()
        })
        
        # Relay to YOUR frontend via YOUR WebSocket
        await self.broadcast_to_your_frontend({
            "type": "new_message",
            "data": {
                "id": message.message_id,
                "content": message.content,
                "task_id": message.task_id
            }
        })
        
        print(f"✓ Stored and relayed to frontend")
    
    async def broadcast_to_your_frontend(self, data: dict):
        """Send to YOUR frontend's WebSocket connections"""
        for websocket in self.your_websocket_connections:
            try:
                await websocket.send_json(data)
            except:
                self.your_websocket_connections.remove(websocket)
    
    async def start(self, end_user_id: str):
        """Connect to Bifrost and start listening for this end user"""
        # Connect SDK to Bifrost
        await self.sdk_client.realtime.connect()
        
        # Subscribe to personal channel for this specific end user
        # Pattern: personal:<target_user_id>#<service_user_id>
        await self.sdk_client.realtime.subscribe(
            target_user_id=end_user_id,
            on_publication=self.on_bifrost_event
        )
        print(f"✓ Backend listening for user {end_user_id}")

# Your frontend connects to YOUR WebSocket endpoint
@app.websocket("/ws")
async def your_frontend_websocket(websocket: WebSocket):
    """Your frontend connects here, NOT to Bifrost directly"""
    await websocket.accept()
    backend.your_websocket_connections.add(websocket)
    
    try:
        while True:
            # Handle messages from your frontend
            data = await websocket.receive_json()
            # Process frontend requests...
    finally:
        backend.your_websocket_connections.remove(websocket)
```

### Use Cases

**✅ Good For:**

**1. Activity/Status Dashboards**
```python
async def on_bifrost_event(self, channel, data):
    activity = parse_activity(data)
    
    # Store in Redis for dashboard queries
    await redis.lpush("activities", json.dumps(activity))
    
    # Push to your frontend Dashboard
    await self.broadcast_to_dashboard(activity)
```

**2. Notification Relays**
```python
async def on_bifrost_event(self, channel, data):
    notification = parse_notification(data)
    
    # Store notification
    await db.notifications.insert(notification)
    
    # Send push notification via FCM/APNS to your app
    await send_push_notification(notification.user_id, notification)
```

**3. Live Feed Aggregators**
```python
async def on_bifrost_event(self, channel, data):
    feed_item = parse_feed_item(data)
    
    # Add to feed cache
    await redis.zadd("feed", {feed_item.id: time.now()})
    
    # Relay to your frontend  
    await broadcast_to_feed_subscribers(feed_item)
```

**❌ Not Good For:**

- Critical financial data (can't risk missing events)
- Audit trails (need guaranteed completeness)
- Order-dependent processing (events might arrive out of order)

### Pros & Cons

**Pros:**
- ⚡ **Fast** - Single hop from Bifrost → Your Backend → Your Frontend
- 🎯 **Simple** - No extra fetching logic
- 💾 **Efficient** - Only process data when it changes

**Cons:**
- ⚠️ **Reliability** - Missed event from Bifrost = data never reaches your frontend
- 🔄 **No recovery** - If backend is down, you miss events
- 📊 **Ordering** - Events might arrive out of sequence

### Real Example: Telegram Bot

```python
"""Real-world: Telegram bot receiving AI responses"""

from telegram import Bot
from magick_mind import MagickMind, ChatPayload

class TelegramBotBackend:
    def __init__(self, sdk_client: MagickMind, bot: Bot):
        self.sdk = sdk_client
        self.telegram_bot = bot
        self.chat_mappings = {}  # Map Bifrost task_id → Telegram chat_id
    
    async def on_ai_response(self, channel: str, data: dict):
        """
        Bifrost sends AI response →
        Your bot backend relays to Telegram →
        User sees message in Telegram
        """
        message = ChatPayload.model_validate(data)
        
        # Get which Telegram chat this belongs to
        telegram_chat_id = self.chat_mappings.get(message.task_id)
        
        if telegram_chat_id:
            # Relay to YOUR frontend (Telegram)
            await self.telegram_bot.send_message(
                chat_id=telegram_chat_id,
                text=message.content
            )
            
            print(f"✓ Relayed to Telegram chat {telegram_chat_id}")
```

## Pattern 2: Events as Notifications

### How It Works

```
Bifrost --event("message 123 created")--> Your Backend
                                              ↓
                                    Fetch full data from Bifrost
                                              ↓
                                         Store in DB
                                              ↓
                                    Relay to Your Frontend
```

Event is minimal - just says something changed. Your backend fetches complete data.

### Code Example

```python
"""
Pattern 2: Events as Notifications

Event triggers your backend to fetch authoritative data.
"""

from magick_mind import MagickMind, ChatPayload

class ChatBackendWithFetch:
    def __init__(self, client: MagickMind):
        self.sdk_client = client
        self.your_db = YourDatabase()
    
    async def on_bifrost_notification(self, channel: str, data: dict):
        """
        Receives notification from Bifrost (minimal data).
        Backend fetches full data, then relays to frontend.
        """
        # Event: Just says "message created" with ID
        message_id = data.get("message_id")
        
        print(f"🔔 Notification from Bifrost: message {message_id} created")
        
        # Fetch complete, authoritative data from Bifrost
        # TODO: This endpoint doesn't exist yet in SDK
        response = self.sdk_client.http.get(f"/v1/messages/{message_id}")
        message = ChatPayload.model_validate(response.json())
        
        print(f"📥 Fetched from Bifrost: {message.content[:50]}...")
        
        # Verify data integrity before storing
        if not message.message_id or not message.content:
            print("⚠️ Invalid message data, skipping")
            return
        
        # Store in YOUR database (authoritative for your frontend)
        await self.your_db.messages.insert_one({
            "id": message.message_id,
            "task_id": message.task_id,
            "content": message.content,
            "verified": True,  # We fetched this, we trust it
            "stored_at": datetime.now()
        })
        
        # Relay to YOUR frontend via YOUR API
        await self.broadcast_to_your_frontend({
            "type": "new_message",
            "data": message.model_dump()
        })
        
        print(f"✓ Verified, stored, and relayed")
```

### Use Cases

**✅ Perfect For:**

**1. Financial/Payment Processing**
```python
async def on_payment_notification(self, channel, data):
    payment_id = data["payment_id"]
    
    # MUST fetch authoritative data - can't trust event for money!
    payment = await self.sdk_client.http.get(f"/v1/payments/{payment_id}")
    
    # Verify, store, process
    if payment.verified:
        await self.your_db.payments.insert(payment)
        await self.process_payment(payment)
        await self.notify_your_frontend(payment)
```

**2. Order Management (E-commerce)**
```python
async def on_order_notification(self, channel, data):
    order_id = data["order_id"]
    
    # Fetch complete order details
    order = await self.sdk_client.http.get(f"/v1/orders/{order_id}")
    
    # Store in your database
    await self.your_db.orders.insert(order)
    
    # Trigger fulfillment workflow
    await self.fulfillment_service.process(order)
    
    # Update your frontend
    await self.broadcast_to_admin_dashboard(order)
```

**3. Healthcare/Compliance Systems**
```python
async def on_patient_update_notification(self, channel, data):
    patient_id = data["patient_id"]
    
    # Fetch complete, verified patient record
    record = await self.sdk_client.http.get(f"/v1/patients/{patient_id}")
    
    # Store with audit trail
    await self.your_db.patient_records.insert({
        **record,
        "fetched_at": datetime.now(),
        "verified": True
    })
    
    # Update EHR system
    await self.ehr_system.update(record)
```

### Pros & Cons

**Pros:**
- ✅ **Reliable** - Can always re-fetch if needed
- 🔄 **Recoverable** - Missed notification? Periodic fetch catches it
- ✓ **Verifiable** - Data integrity guaranteed
- 📊 **Audit-ready** - Complete records of what was fetched when

**Cons:**
- 🐌 **Slower** - Extra network round-trip to Bifrost
- 📈 **More load** - More API calls to Bifrost
- ⚙️ **Complex** - Need fetch logic in your backend

## Pattern 3: Hybrid Approach (Recommended)

### How It Works

```
Bifrost --event(full data)--> Your Backend --quick relay--> Your Frontend
                                   ↓
                              Store in DB
                                   ↓
                         Periodic fetch (every 5min)
                                   ↓
                           Fill any gaps
```

Trust events for speed, verify with periodic fetching for reliability.

### Code Example

```python
"""
Pattern 3: Hybrid Approach (RECOMMENDED FOR PRODUCTION)

Fast path: Trust and relay events
Slow path: Periodic sync to catch gaps
"""

from magick_mind import MagickMind, ChatPayload
import asyncio
from typing import Set

class ProductionChatBackend:
    """
    Production-ready backend with hybrid pattern.
    
    Used in real systems like Telegram bots, web apps, mobile backends.
    """
    
    def __init__(self, client: MagickMind):
        self.sdk_client = client
        self.your_db = YourDatabase()
        self.your_frontend_websockets = set()
        
        # Track what we've seen
        self.processed_message_ids: Set[str] = set()
        self.last_sync_cursor = None
    
    async def on_bifrost_event(self, channel: str, data: dict):
        """
        FAST PATH: Receive event from Bifrost, process immediately.
        """
        message = ChatPayload.model_validate(data)
        
        # Deduplicate
        if message.message_id in self.processed_message_ids:
            return
        
        print(f"⚡ Quick path: {message.message_id}")
        
        # Store in YOUR database
        await self.your_db.messages.insert_one({
            "id": message.message_id,
            "content": message.content,
            "task_id": message.task_id,
            "source": "realtime_event",
            "received_at": datetime.now()
        })
        
        # Relay to YOUR frontend immediately
        await self.broadcast_to_frontend({
            "type": "new_message",
            "data": message.model_dump()
        })
        
        # Track it
        self.processed_message_ids.add(message.message_id)
        
        print(f"✓ Stored and relayed")
    
    async def periodic_sync(self, mindspace_id: str):
        """
        RELIABLE PATH: Periodic sync to catch any missed events.
        
        Runs every 5 minutes in background.
        """
        while True:
            await asyncio.sleep(300)  # 5 minutes
            
            print("🔄 Running periodic sync...")
            
            try:
                # Fetch history from Bifrost
                response = self.sdk_client.http.get(
                    "/v1/mindspaces/messages",
                    params={
                        "mindspace_id": mindspace_id,
                        "after_id": self.last_sync_cursor or "",
                        "limit": 100
                    }
                )
                
                messages = response.json().get("chat_histories", [])
                
                # Find any we missed
                gaps_found = 0
                for msg_data in messages:
                    msg_id = msg_data["id"]
                    
                    if msg_id not in self.processed_message_ids:
                        # We MISSED this event! Add it now
                        print(f"⚠️ GAP FOUND: {msg_id}")
                        gaps_found += 1
                        
                        message = ChatPayload(
                            message_id=msg_id,
                            task_id="",
                            content=msg_data["content"],
                            reply_to=msg_data.get("reply_to_message_id")
                        )
                        
                        # Store in YOUR database
                        await self.your_db.messages.insert_one({
                            "id": message.message_id,
                            "content": message.content,
                            "source": "sync_recovery",
                            "recovered_at": datetime.now()
                        })
                        
                        # Relay to YOUR frontend
                        await self.broadcast_to_frontend({
                            "type": "recovered_message",
                            "data": message.model_dump()
                        })
                        
                        self.processed_message_ids.add(msg_id)
                
                # Update cursor
                if messages:
                    self.last_sync_cursor = messages[-1]["id"]
                
                print(f"✓ Sync complete: {len(messages)} checked, {gaps_found} gaps filled")
                
            except Exception as e:
                print(f"✗ Sync failed: {e}")
    
    async def broadcast_to_frontend(self, data: dict):
        """Broadcast to YOUR frontend's WebSocket connections"""
        for ws in self.your_frontend_websockets:
            try:
                await ws.send_json(data)
            except:
                self.your_frontend_websockets.remove(ws)
    
    async def start(self, end_user_id: str, mindspace_id: str):
        """
        Start hybrid backend service for a specific end user.
        
        Args:
            end_user_id: End user to subscribe to (personal channel)
            mindspace_id: Mindspace context for history sync
        
        Sets up both fast (events) and reliable (sync) paths.
        """
        print("🚀 Starting hybrid backend...")
        
        # 1. Connect to Bifrost realtime (fast path)
        await self.sdk_client.realtime.connect()
        
        # Subscribe to personal channel for this specific end user
        # Pattern: personal:<end_user_id>#<service_user_id>
        await self.sdk_client.realtime.subscribe(
            target_user_id=end_user_id,
            on_publication=self.on_bifrost_event
        )
        print(f"  ✓ Realtime connected for user {end_user_id}")
        
        # 2. Start periodic sync (reliability)
        asyncio.create_task(self.periodic_sync(mindspace_id))
        print("  ✓ Periodic sync started (safety net)")
        
        print("✓ Hybrid backend running!")
        print("  - Events: Instant relay to your frontend")
        print("  - Sync: Every 5min to catch gaps")

# Usage in your backend application
async def main():
    # Initialize SDK client
    sdk_client = MagickMind(
        email="your-service@example.com",
        password="your-password",
        base_url="https://bifrost.example.com"
    )
    
    # Create your production backend
    backend = ProductionChatBackend(sdk_client)
    
    # Start it - subscribe to specific end user's personal channel
    await backend.start(
        end_user_id="end-user-456",  # The actual end user
        mindspace_id="mind-123"  # Mindspace context
    )
    
    # Keep running
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
```

### Use Cases

**✅ Perfect For (Most Production Systems):**

**1. Chat Applications (like your Telegram bot)**
```python
# Events: Show messages instantly
# Sync: Catch any gaps due to network issues
```

**2. Collaboration Tools**
```python
# Events: Show updates immediately
# Sync: Verify document state periodically
```

**3. Social Media Backends**
```python
# Events: Add posts to feed in real-time
# Sync: Refresh complete feed occasionally
```

**4. Mobile App Backends**
```python
# Events: Push notifications instantly
# Sync: Ensure app has complete data when it opens
```

### Pros & Cons

**Pros:**
- ⚡ **Fast** - Events provide instant updates to your frontend
- ✅ **Reliable** - Periodic sync fills gaps
- 🔄 **Recoverable** - Backend downtime doesn't lose data permanently
- 💪 **Production-ready** - Handles real-world conditions

**Cons:**
- ⚙️ **More complex** - Need both event handlers and sync logic
- 💾 **More code** - Deduplication, cursor tracking, gap detection
- 🧠 **State management** - Must track processed IDs

## Choosing the Right Pattern

### Decision Tree for Your Backend

```
Can you afford to lose data?
├─ YES → Need real-time speed for your frontend?
│         ├─ YES → Pattern 1: Events as Truth
│         └─ NO  → Pattern 2: Events as Notifications
│
└─ NO  → Is your frontend latency-sensitive?
          ├─ YES → Pattern 3: Hybrid ✅ (RECOMMENDED)
          └─ NO  → Pattern 2: Events as Notifications
```

### Quick Reference

| Your Backend Needs | Pattern 1 | Pattern 2 | Pattern 3 |
|-------------------|-----------|-----------|-----------|
| Instant frontend updates | ✅ Yes | ❌ Slow | ✅ Yes |
| Data reliability | ❌ Risky | ✅ Best | ✅ Good |
| Handle backend downtime | ❌ Poor | ✅ Excellent | ✅ Good |
| API load to Bifrost | ✅ Low | ❌ High | ⚠️ Medium |
| Implementation complexity | ✅ Simple | ⚠️ Medium | ❌ Complex |
| Audit/compliance ready | ❌ No | ✅ Yes | ✅ Yes |

## Real-World Implementations

### Your Telegram Bot (Pattern 3: Hybrid)

```python
"""
Real architecture of a Telegram bot using Bifrost
"""

# Architecture:
# Telegram Chat (Your Frontend)
#     ↕
# Python Bot Backend + SDK (This is your code)
#     ↕  
# Bifrost AI Service (SaaS)

class TelegramBotBackend:
    async def on_bifrost_ai_response(self, channel, data):
        """Bifrost sends AI response → Relay to Telegram"""
        message = ChatPayload.model_validate(data)
        
        # Get Telegram chat to send to
        telegram_chat_id = self.task_to_chat_mapping[message.task_id]
        
        # Relay to YOUR frontend (Telegram)
        await self.telegram_bot.send_message(
            chat_id=telegram_chat_id,
            text=message.content
        )
        
        # Store in your DB
        await self.db.messages.insert(message)
```

### Web App Backend (Pattern 3: Hybrid)

```python
"""
React frontend ← FastAPI backend + SDK ← Bifrost
"""

from fastapi import FastAPI, WebSocket

app = FastAPI()

class WebAppBackend:
    def __init__(self):
        self.frontend_connections = set()  # YOUR frontend's WebSockets
    
    async def on_bifrost_event(self, channel, data):
        """Bifrost → Your backend → Your React frontend"""
        message = ChatPayload.model_validate(data)
        
        # Store in your DB
        await db.messages.insert(message)
        
        # Relay to YOUR frontend
        await self.broadcast_to_react_app({
            "type": "ai_message",
            "data": message.model_dump()
        })

@app.websocket("/ws")
async def your_frontend_connects_here(websocket: WebSocket):
    """Your React app connects to YOUR backend, not to Bifrost"""
    await websocket.accept()
    backend.frontend_connections.add(websocket)
```

### Mobile App Backend (Pattern 3: Hybrid)

```
Flutter/React Native App (Your Frontend)
            ↕
     Django/FastAPI + SDK (Your Backend)
            ↕
        Bifrost SaaS
```

## Your Backend's Responsibilities

No matter which pattern you choose, your backend must:

### 1. Process Events from Bifrost
```python
async def on_event_from_bifrost(self, channel, data):
    # Parse Bifrost's event
    message = ChatPayload.model_validate(data)
    ...
```

### 2. Store in Your Database
```python
    # Store in YOUR database (PostgreSQL, MongoDB, etc.)
    await your_db.messages.insert({
        "id": message.message_id,
        "content": message.content,
        ...
    })
```

### 3. Relay to Your Frontend
```python
    # Send to YOUR frontend via YOUR communication channel
    # (WebSocket, REST API, GraphQL, Push Notifications, etc.)
    await your_websocket_server.broadcast(message)
    # or
    await your_rest_api.notify_clients(message)
    # or
    await send_push_notification(user_id, message)
```

### 4. Handle Your Business Logic
```python
    # Your custom logic
    if is_urgent(message):
        await trigger_alert()
    
    if contains_payment_info(message):
        await process_payment()
    
    await update_analytics(message)
```

## Summary

**Pattern 1** = Fast but risky → Good for non-critical feeds  
**Pattern 2** = Reliable but slow → Good for critical data with audit needs  
**Pattern 3** = Best of both → **Recommended for most production backends**

### Start Here (Recommended)

Most backend services should use **Pattern 3 (Hybrid)**:
- Relay events immediately to your frontend (fast)
- Periodic sync in background (reliable)
- Track processed IDs (deduplicate)

See [Backend Integration Guide](../guides/backend_integration.md) for complete implementation.

### Related Documentation

- [Backend Integration Guide](../guides/backend_integration.md) - Complete backend service template
- [examples/backend_service.py](../../examples/backend_service.py) - Production-ready code
- [Realtime Guide](../realtime_guide.md) - WebSocket client usage
