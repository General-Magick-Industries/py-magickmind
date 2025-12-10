# Resource Implementation Guide

A **practical guide** for SDK contributors showing how to add resources with versioned models.

## Purpose

This guide provides working code examples for adding new API resources to the SDK. If you're a contributor implementing chat, history, or other endpoints, use this as a reference.

**For SDK users:** See the main [README](../../../README.md) instead.

## Recommended Structure

When adding resources to the SDK, use **explicit versioned folders**:

```
magick_mind/
├── models/
│   ├── common.py        # Shared types
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── chat.py      # ChatSendRequest, ChatSendResponse  
│   │   └── history.py
│   └── v2/
│       ├── __init__.py
│       ├── chat.py      # V2 versions (different structure)
│       └── history.py
│
└── resources/
    ├── __init__.py      # V1Resources, V2Resources
    ├── base.py          # BaseResource
    ├── v1/
    │   ├── __init__.py
    │   ├── chat.py      # ChatResourceV1
    │   └── history.py   # HistoryResourceV1
    └── v2/
        ├── __init__.py  
        ├── chat.py      # ChatResourceV2
        └── history.py   # HistoryResourceV2
```

## Reference Files

This example provides:

- **`models_v1_chat.py`** - V1 Pydantic request/response models
- **`models_v2_chat.py`** - V2 Pydantic request/response models (hypothetical evolution)
- **`resource_chat.py`** - ChatResource implementation (hybrid approach for reference)

> **Note:** For production, split `resource_chat.py` into separate `v1/chat.py` and `v2/chat.py` files following the versioned folder structure above.

## How to Add Resources (Production Pattern)

### Step 1: Create V1 Models

```bash
mkdir -p magick_mind/models/v1
```

Create `magick_mind/models/v1/chat.py`:
```python
from pydantic import BaseModel, Field

class ChatSendRequest(BaseModel):
    api_key: str
    message: str
    chat_id: str
    sender_id: str

class ChatSendResponse(BaseModel):
    success: bool
    message_id: str
    text: str
```

### Step 2: Create V1 Resource

```bash
mkdir -p magick_mind/resources/v1
```

Create `magick_mind/resources/v1/chat.py`:
```python
from ...models.v1.chat import ChatSendRequest, ChatSendResponse
from ..base import BaseResource

class ChatResourceV1(BaseResource):
    def send(self, api_key: str, message: str, chat_id: str, sender_id: str):
        request = ChatSendRequest(...)
        response = self._http.post("/v1/magickmind/chat", json=request.model_dump())
        return ChatSendResponse.model_validate(response.json())
```

### Step 3: Create Resource Container

Update `magick_mind/resources/__init__.py`:
```python
class V1Resources:
    def __init__(self, http_client):
        from .v1.chat import ChatResourceV1
        self.chat = ChatResourceV1(http_client)
```

### Step 4: Wire to Main Client

Update `magick_mind/client.py`:
```python
from .resources import V1Resources

class MagickMind:
    def __init__(self, ...):
        # ...
        self.v1 = V1Resources(self.http)
        self.chat = self.v1.chat  # Default alias
```

### Step 5: Use It!

```python
from magick_mind import MagickMind

client = MagickMind(email="...", password="...", base_url="...")

# Explicit version
response = client.v1.chat.send(
    api_key="sk-...",
    message="Hello!",
    chat_id="chat-123",
    sender_id="user-456"
)

# Or default alias
response = client.chat.send(...)
```

## Architecture Patterns Demonstrated

- ✅ **Pydantic validation** - Type-safe request/response
- ✅ **Version namespaces** - `client.v1.chat`, `client.v2.chat`
- ✅ **Single resource, multiple versions** - Handles v1 and v2
- ✅ **Clean imports** - Type hints with TYPE_CHECKING
- ✅ **Self-documenting** - Examples show usage

