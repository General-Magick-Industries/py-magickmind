# Realtime Subscription Patterns

This document explains the architectural patterns for realtime subscriptions in the Magick Mind SDK, with a focus on why the per-user model is the correct choice for most applications.

## Overview

The SDK uses WebSocket connections for realtime communication. The fundamental question when designing your architecture is:

**How do you subscribe to user updates?**

There are three common patterns, but only one is correct for personal user data.

---

## Pattern 1: Per-User Subscriptions ✅ (Recommended)

### Architecture

```
Backend Service (Your SDK Instance)
    │
    └─ Single WebSocket Connection to the Magick Mind API
        ├─ subscribe("user_1")  
        ├─ subscribe("user_2")  
        ├─ subscribe("user_3")  
        └─ ... (500 users = 500 subscriptions)

Each subscription is multiplexed over the same connection.
```

### Implementation

```python
# Subscribe to multiple users
await client.realtime.subscribe_many([
    "user_1", "user_2", "user_3", ..., "user_500"
])

# Handler receives per-user messages
class Handler(RealtimeEventHandler):
    async def on_message(self, user_id: str, payload):
        # user_id is already parsed
        # Only receives messages for subscribed users
        print(f"Message for {user_id}: {payload}")
```

### Why This is Correct

| Aspect | Benefit |
|--------|---------|
| **Security** | Each user can only see their own data. No cross-user leakage. |
| **Privacy** | GDPR/compliance friendly. Users isolated by design. |
| **Efficiency** | Server only sends relevant data. No client-side filtering. |
| **Scalability** | Realtime server handles millions of channels. 500 = ~500KB metadata. |
| **Debugging** | Easy to trace per-user issues. Clean logs. |

### Performance Reality

- **Metadata**: ~1KB per subscription
- **500 subscriptions**: ~500KB total memory
- **Centrifugo capacity**: 1M+ subscriptions per instance
- **Network**: Single WebSocket connection (multiplexed)

**Verdict**: Scales effortlessly to thousands of users.

---

## Pattern 2: Room/Group Channels ❌ (Anti-Pattern for Personal Data)

### Architecture

```
Backend Service
    │
    └─ subscribe("room_mindspace_123")
        ↓
    ALL users in mindspace receive ALL messages
        ↓
    user_1: [msg_a, msg_b, msg_c, msg_d, msg_e]
    user_2: [msg_a, msg_b, msg_c, msg_d, msg_e]  # Same messages!
    user_3: [msg_a, msg_b, msg_c, msg_d, msg_e]  # Same messages!
        ↓
    Manual client-side filtering: "Is this message for me?"
```

### Implementation

```python
# ❌ DON'T DO THIS for personal messages
await client.realtime.subscribe("room_mindspace_123")

class Handler(RealtimeEventHandler):
    async def on_raw_message(self, channel, payload):
        # Receive EVERYTHING
        # Must manually check: is this for the current user?
        if payload.get("user_id") == current_user_id:
            # Process it
            pass
        else:
            # Discard (but you still received it over network!)
            pass
```

### Why This is Wrong

| Problem | Impact |
|---------|--------|
| **Privacy Violation** | All users see all data in network traffic |
| **Security Risk** | Can't prevent users from inspecting traffic |
| **Bandwidth Waste** | Send 100% of data to all users, use 1% |
| **CPU Waste** | Client-side filtering on every message |
| **Complexity** | Manual filtering logic in every client |

### When to Use (Rarely)

Room channels are ONLY appropriate when:
- ✅ Real-time collaboration (shared document editing)
- ✅ Live dashboards (everyone sees same metrics)
- ✅ Chat rooms (everyone participates)
- ✅ System-wide announcements

For **personal user messages**, NEVER use room channels.

---

## Pattern 3: Firehose ❌ (Anti-Pattern)

### Architecture

```
Backend Service
    │
    └─ subscribe("root:*")  # Wildcard subscription
        ↓
    Receives EVERY EVENT from ENTIRE SYSTEM
        ↓
    - user_1 messages
    - user_2 messages
    - admin actions
    - system logs
    - ALL events from ALL users
```

### Why This is Wrong

| Problem | Impact |
|---------|--------|
| **Overwhelming** | Can't scale. Will crash under load. |
| **Security** | Shouldn't have access to all system data |
| **Cost** | Massive bandwidth usage |
| **Unusable** | Must filter 99.9% of irrelevant data |

### When to Use (Almost Never)

Only appropriate for:
- System-level analytics services
- Central logging/monitoring
- Audit trail collectors

For application logic, NEVER use firehose pattern.

---

## Decision Matrix

| Use Case | Pattern | Rationale |
|----------|---------|-----------|
| Personal notifications (SMS, email triggers) | Per-User ✅ | Privacy required |
| AI chat responses to users | Per-User ✅ | Each user gets own conversation |
| Admin dashboard monitoring 500 agents | Per-User ✅ | Need per-agent isolation |
| Backend relay to user frontends | Per-User ✅ | Security + efficiency |
| Shared whiteboard (everyone edits) | Room ✅ | True collaboration |
| Live sports scores (same for all) | Room ✅ | Genuine broadcast |
| System-wide announcement | Room ✅ | Everyone needs same message |
| Analytics pipeline | Firehose ⚠️ | Only if system-level access needed |

---

## Common Misconceptions

### "500 subscriptions will be slow"

**False.** The realtime infrastructure is designed for exactly this pattern. Each subscription is lightweight metadata. The bottleneck is network bandwidth, not subscription count.

### "One room channel is more efficient"

**False.** You save on subscription metadata but waste on:
- Bandwidth (send 100%, use 1%)
- CPU (client-side filtering)
- Security (everyone sees everything)

### "This means 500 WebSocket connections"

**False.** This is **ONE connection** with **500 multiplexed subscriptions**. That's the whole point of the architecture.

### "I need room channels to group users"

**Depends.** If each user sees different data within the "room," use per-user. If everyone truly sees the same data, use room.

---

## Migration Guide

If you currently use room channels for personal data:

### Before (Anti-Pattern)

```python
# ❌ One room for all users
await client.realtime.subscribe("room_project_123")

# Receive all messages, filter manually
class Handler(RealtimeEventHandler):
    async def on_raw_message(self, channel, payload):
        if payload["user_id"] in my_users:
            process(payload)
```

### After (Correct Pattern)

```python
# ✅ Subscribe to each user
await client.realtime.subscribe_many(my_users)

# Receive only relevant messages  
class Handler(RealtimeEventHandler):
    async def on_message(self, user_id, payload):
        # Already filtered server-side
        process(user_id, payload)
```

### Benefits After Migration

- ✅ Reduced bandwidth (10x-100x reduction typical)
- ✅ Better security (users isolated)
- ✅ Simpler code (no manual filtering)
- ✅ Better performance (server-side filtering)

---

## Summary

**For personal user data: Always use per-user subscriptions.**

- 500 users = 500 subscriptions ✅
- Scales to millions of users
- Secure, private, efficient
- What the SDK is designed for

**Room channels:** Only when users genuinely share the same data.

**Firehose:** Almost never. Only for system-level services.
