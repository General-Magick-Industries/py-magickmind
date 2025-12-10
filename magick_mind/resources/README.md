# Extending the SDK with Resource Clients

This directory contains the **base structure** for API resource clients.

## Recommended Pattern: Versioned Folders

When implementing resources, use **explicit versioned folders** that mirror bifrost's API structure:

```
magick_mind/resources/
├── __init__.py          # BaseResource, V1Resources, V2Resources
├── base.py              # BaseResource class (or in __init__.py)
├── v1/
│   ├── __init__.py
│   ├── chat.py          # ChatResourceV1
│   └── history.py       # HistoryResourceV1
└── v2/
    ├── __init__.py
    ├── chat.py          # ChatResourceV2
    └── history.py       # HistoryResourceV2
```

**Why versioned folders?** They mirror bifrost's API structure and keep versions isolated.

## Beta and Experimental Features

Beta features can be organized in two ways depending on how bifrost implements them:

### Pattern A: Beta as Separate Container

Use when beta is a **full API version** with breaking changes (preparation for v2):

```
resources/
├── v1/
│   └── chat.py          # ChatResourceV1 → /v1/magickmind/chat
└── beta/
    └── chat.py          # ChatResourceBeta → /beta/magickmind/chat
```

```python
class V1Resources:
    def __init__(self, http_client):
        self.chat = ChatResourceV1(http_client)

class BetaResources:
    def __init__(self, http_client):
        self.chat = ChatResourceBeta(http_client)  # Breaking changes

# Usage
client.v1.chat.send(message="...")      # Stable
client.beta.chat.send(content={...})    # Different API (breaking)
```

**When to use:**
- Beta has different request/response structure
- Testing major breaking changes
- Beta will become v2

### Pattern B: Beta as Attribute Within Version

Use when beta is a **feature flag** within the same version:

```
resources/
└── v1/
    ├── chat.py          # ChatResourceV1 → /v1/magickmind/chat
    └── chat_beta.py     # ChatBetaResourceV1 → /v1/magickmind/chatbeta
```

```python
class V1Resources:
    def __init__(self, http_client):
        self.chat = ChatResourceV1(http_client)
        self.chat_beta = ChatBetaResourceV1(http_client)  # Feature flag

# Usage
client.v1.chat.send(message="...")           # Stable
client.v1.chat_beta.send(                    # Same structure, new features
    message="...",
    experimental_param=True  # New parameter being tested
)
```

**When to use:**
- Beta has same basic structure as stable
- Testing new parameters/features
- A/B testing
- Beta is not a breaking change

### Pattern C: Both (Flexible)

You can use both patterns if bifrost has both types of beta features:

```python
class V1Resources:
    def __init__(self, http_client):
        self.chat = ChatResourceV1(http_client)
        self.chat_beta = ChatBetaResourceV1(http_client)  # Feature flag

class BetaResources:
    def __init__(self, http_client):
        self.chat = ChatResourceBeta(http_client)  # Breaking version

# Usage
client.v1.chat.send(...)        # Stable v1
client.v1.chat_beta.send(...)   # Beta feature in v1 (non-breaking)
client.beta.chat.send(...)      # Beta API version (breaking)
```

**Guideline:** Match the pattern to how bifrost actually implements the endpoint. Check the API path structure first.

## Example: V1 Chat Resource

```python
# resources/v1/chat.py
from ...models.v1.chat import ChatSendRequest, ChatSendResponse
from ..base import BaseResource

class ChatResourceV1(BaseResource):
    """Client for /v1/magickmind/chat endpoints."""
    
    def send(
        self,
        api_key: str,
        message: str,
        chat_id: str,
        sender_id: str,
    ) -> ChatSendResponse:
        """Send a chat message."""
        request = ChatSendRequest(
            api_key=api_key,
            message=message,
            chat_id=chat_id,
            sender_id=sender_id,
        )
        response = self._http.post(
            "/v1/magickmind/chat",
            json=request.model_dump()
        )
        return ChatSendResponse.model_validate(response.json())
```

## Resource Containers

Create version containers in `resources/__init__.py`:

```python
from .v1.chat import ChatResourceV1
from .v1.history import HistoryResourceV1

class V1Resources:
    """Container for all v1 API resources."""
    def __init__(self, http_client):
        self.chat = ChatResourceV1(http_client)
        self.history = HistoryResourceV1(http_client)

class V2Resources:
    """Container for all v2 API resources."""
    def __init__(self, http_client):
        from .v2.chat import ChatResourceV2
        self.chat = ChatResourceV2(http_client)
```

## Wire to Main Client

Update `client.py`:

```python
from .resources import V1Resources, V2Resources

class MagickMind:
    def __init__(self, ...):
        # ... existing init ...
        
        # Version namespaces
        self.v1 = V1Resources(self.http)
        self.v2 = V2Resources(self.http)
        
        # Default alias
        self.chat = self.v1.chat
```

## Usage

```python
from magick_mind import MagickMind

client = MagickMind(email="...", password="...", base_url="...")

# Explicit version (recommended)
response = client.v1.chat.send(
    api_key="sk-...",
    message="Hello!",
    chat_id="123",
    sender_id="user-456"
)

# Or default alias
response = client.chat.send(...)
```

## Complete Example

See **[docs/examples/chat_implementation/](../../../docs/examples/chat_implementation/)** for a complete working reference implementation.

## Benefits

1. **Explicit versioning** - `client.v1.chat` vs `client.v2.chat`
2. **Type safety** - Pydantic models validate requests/responses
3. **Mirrors Bifrost** - SDK structure matches API structure
4. **Safe evolution** - Breaking changes require explicit opt-in

