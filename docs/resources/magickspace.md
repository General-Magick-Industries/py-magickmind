# MagickSpace Resource Guide

A comprehensive guide to using the MagickSpace resource in the Magick Mind SDK for managing organizational containers for chat conversations, knowledge bases, and user collaboration.

## Overview

**MagickSpace is central to the Magick Mind API** - it's where everything starts and ends. Conversations, knowledge, and users all come together in magickspaces.

**MagickSpaces** are organizational containers that group together:
- **Chat conversations** - Message history and interactions
- **Knowledge bases** - Attached corpus for contextual AI responses
- **Users** - Members with access to the space
- **Projects** - Optional organizational grouping

**Two types:**
- **`private`** - Single-user personal workspaces (individual context, personal AI)
- **`group`** - Multi-user collaborative spaces (team knowledge, shared context)

### Privacy Model

**Asymmetric access pattern** - designed for privacy while maximizing utility:

- ✅ **Private → Group**: Private magickspaces **can access** group knowledge
  - Personal AI benefits from team corpus, company docs, shared resources
  - Individual gets collective knowledge without exposing personal context
  
- ❌ **Group → Private**: Group magickspaces **cannot access** private conversations
  - Personal conversations stay personal
  - Clear privacy boundary: group is shared, private is isolated

**Example:**
```python
# Alice's private space can use team knowledge
alice_personal = client.magickspaces.create(
    name="Alice's Personal Assistant",
    type="private",
    corpus_ids=["team-handbook", "company-docs"]  # ✅ Can access group corpus
)

# Team space cannot see Alice's personal conversations
eng_team = client.magickspaces.create(
    name="Engineering Team",
    type="group",
    corpus_ids=["codebase", "specs"]
    # ❌ Cannot access Alice's private magickspace
)
```

This model follows **least privilege** principles - users get access to shared knowledge without sacrificing privacy.

## Quick Start

```python
from magick_mind import MagickMind

# Initialize client
client = MagickMind(
    base_url="https://api.magickmind.ai",
    email="user@example.com",
    password="password"
)

# Create a private magickspace
workspace = client.magickspaces.create(
    name="My Personal Workspace",
    type="private",
    description="Personal workspace for my projects"
)

# Create a group magickspace
team = client.magickspaces.create(
    name="Engineering Team",
    type="group",
    description="Team collaboration space",
    participant_ids=["user-1", "user-2", "user-3"],
    corpus_ids=["corp-handbook", "corp-docs"]
)
```

## Core Operations

### Creating MagickSpaces

```python
# Private: individual workspace with personal+team knowledge
private = client.magickspaces.create(
    name="My Research",
    type="private",
    corpus_ids=["team-docs", "personal-notes"]  # Can access both
)

# Group: collaborative team workspace
team = client.magickspaces.create(
    name="Product Team",
    type="group",
    participant_ids=["alice", "bob", "charlie"],
    corpus_ids=["specs", "designs"],
    project_id="proj-v2"  # Optional project link
)
```

### Listing & Retrieving

```python
# List all
all_spaces = client.magickspaces.list()

# Filter by participant
user_spaces = client.magickspaces.list(participant_id="alice")

# Get specific magickspace
space = client.magickspaces.get("mind-123")
```

### Updating & Deleting

```python
# Update (replaces entire lists, include all existing IDs)
client.magickspaces.update(
    magickspace_id="mind-123",
    name="Updated Name",
    corpus_ids=["corp-1", "corp-2", "corp-3"],  # All IDs
    participant_ids=["user-1", "user-2", "user-3", "user-4"]  # All IDs
)

# Delete
client.magickspaces.delete("mind-123")
```

> **Note**: `update()` replaces entire lists. To add one item, include all existing IDs plus the new one.

## Message History

MagickSpaces maintain chat message history. Use `get_messages()` with cursor-based pagination.

### Latest Messages

Get the most recent N messages:

```python
messages = await client.v1.magickspaces.get_messages("mind-123", limit=50)

print(f"Retrieved {len(messages.chat_histories)} messages")

# Display messages
for msg in messages.chat_histories:
    print(f"[{msg.sent_by_user_id}]: {msg.content}")
    
# Check for more data
print(f"Has more: {messages.has_more}")
print(f"Has older: {messages.has_older}")
```

### Cursor Pagination

Use cursors from the `paging` field to navigate:

```python
# Start with latest
initial = await client.v1.magickspaces.get_messages("mind-123", limit=20)

# Get next page if available
if initial.has_more and initial.next_after_id:
    page2 = await client.v1.magickspaces.get_messages(
        "mind-123",
        cursor=initial.next_after_id,
        limit=20,
    )
    print(f"Found {len(page2.chat_histories)} more messages")

# Get previous page
if initial.has_older and initial.next_before_id:
    older = await client.v1.magickspaces.get_messages(
        "mind-123",
        cursor=initial.next_before_id,
        limit=20,
    )
    print(f"Found {len(older.chat_histories)} older messages")
```

### Sending Messages

Send a message directly to a magickspace:

```python
msg = await client.v1.magickspaces.send_message(
    "mind-123",
    content="Hello, team!",
    sender_id="user-456",
)
print(f"Sent message {msg.id}")

# With optional fields
msg = await client.v1.magickspaces.send_message(
    "mind-123",
    content="Check this file",
    sender_id="user-456",
    artifact_ids=["art-789"],
    reply_to_message_id="msg-prev",
)
```

### Message Data Structure

Each message in `chat_histories` contains:

```python
message = messages.chat_histories[0]

print(f"ID: {message.id}")
print(f"MagickSpace: {message.magickspace_id}")
print(f"Sender: {message.sent_by_user_id}")
print(f"Content: {message.content}")
print(f"Status: {message.status}")
print(f"Type: {message.message_type}")
print(f"Reply to: {message.reply_to_message_id}")
print(f"Created: {message.create_at}")
```

## Common Patterns

### Creating a Project Workspace

Set up a complete workspace for a project:

```python
# 1. Create the magickspace
workspace = client.magickspaces.create(
    name=f"Project: {project_name}",
    type="group",
    description=f"Workspace for {project_name}",
    project_id=project_id,
    participant_ids=team_members,
    corpus_ids=knowledge_bases
)

magickspace_id = workspace.id

# 2. Verify setup
space = client.magickspaces.get(magickspace_id)
print(f"✓ Created workspace for {len(space.participant_ids)} members")
print(f"✓ Attached {len(space.corpus_ids)} knowledge bases")
```

### Adding Knowledge to Existing Workspace

```python
# Get current state
current = client.magickspaces.get("mind-123")

# Add new corpus while preserving existing ones
updated_corpus_ids = current.corpus_ids + ["new-corpus-id"]

# Update
client.magickspaces.update(
    magickspace_id="mind-123",
    name=current.name,
    corpus_ids=updated_corpus_ids,
    participant_ids=current.participant_ids
)
```

### Loading Full Message History

Efficiently load all messages using cursor pagination:

```python
async def load_all_messages(magickspace_id: str, batch_size: int = 100):
    """Load all messages from a magickspace using cursor pagination."""
    all_messages = []
    
    # Start with latest
    response = await client.v1.magickspaces.get_messages(magickspace_id, limit=batch_size)
    all_messages.extend(response.chat_histories)
    
    # Keep loading older messages
    while response.has_older and response.next_before_id:
        response = await client.v1.magickspaces.get_messages(
            magickspace_id,
            cursor=response.next_before_id,
            limit=batch_size,
        )
        all_messages.extend(response.chat_histories)
    
    return all_messages

# Usage
all_msgs = await load_all_messages("mind-123")
print(f"Loaded {len(all_msgs)} total messages")
```

### Monitoring New Messages

Poll for new messages (prefer Centrifugo realtime for production):

```python
async def poll_new_messages(magickspace_id: str, cursor: str = None):
    """Check for new messages since last cursor."""
    response = await client.v1.magickspaces.get_messages(
        magickspace_id,
        cursor=cursor,
        limit=50,
    )
    return response

# Usage in a loop
cursor = None
while True:
    response = await poll_new_messages("mind-123", cursor)
    
    if response.chat_histories:
        print(f"Received {len(response.chat_histories)} new messages")
        cursor = response.next_after_id  # Update cursor for next poll
        
        # Process messages...
    
    await asyncio.sleep(5)  # Poll every 5 seconds
```

## Design Guidance

### Thinking MagickSpace-First

When architecting your Magick Mind application, **start with magickspaces**:

#### 1. **Define Your Conversation Contexts**

What are the different contexts where users will interact with AI?

```python
# Example: Customer support application
support_magickspace = client.magickspaces.create(
    name="Customer Support - Acme Corp",
    type="private",  # Each customer gets their own space
    corpus_ids=["help-docs", "product-specs", "faq"]
)

# Example: Team collaboration
team_magickspace = client.magickspaces.create(
    name="Engineering Team",
    type="group",  # Shared team space
    participant_ids=team_members,
    corpus_ids=["codebase-docs", "technical-specs"]
)
```

#### 2. **Map Knowledge to Contexts**

Which knowledge should be available in each magickspace?

- **Customer Support** → Help docs, product manuals, policies
- **Engineering Team** → Codebase, technical specs, architecture docs
- **Sales Team** → Product sheets, pricing, case studies

#### 3. **Consider Access Patterns**

- **Private magickspaces** for individual user contexts (personal assistants, customer support tickets)
- **Group magickspaces** for team collaboration (shared projects, team knowledge bases)
- **Project-scoped magickspaces** for temporary initiatives

#### 4. **Design Your Message Flow**

```python
# All chat interactions reference a magickspace
response = client.chat.send(
    api_key="sk-...",
    magickspace_id="mind-123",  # The context for this conversation
    message="How do I deploy to production?",
    enduser_id="user-456"
)

# Messages are stored in the magickspace
history = await client.v1.magickspaces.get_messages("mind-123")
```

### Common Architecture Patterns

#### Pattern 1: One MagickSpace per User Session

```python
# Each user gets their own private workspace
def onboard_user(user_id: str):
    magickspace = client.magickspaces.create(
        name=f"{user_id}'s Workspace",
        type="private",
        corpus_ids=get_user_relevant_knowledge(user_id)
    )
    return magickspace.magickspace.id
```

#### Pattern 2: One MagickSpace per Team/Organization

```python
# Teams share a collaborative space
def setup_team_workspace(team_name: str, members: list[str]):
    magickspace = client.magickspaces.create(
        name=f"{team_name} Team Space",
        type="group",
        participant_ids=members,
        corpus_ids=get_team_knowledge_bases(team_name)
    )
    return magickspace.magickspace.id
```

#### Pattern 3: Dynamic MagickSpace per Conversation Topic

```python
# Create temporary magickspaces for specific tasks
def create_project_workspace(project: Project):
    magickspace = client.magickspaces.create(
        name=f"Project: {project.name}",
        type="group",
        project_id=project.id,
        participant_ids=project.team_members,
        corpus_ids=project.required_knowledge
    )
    return magickspace.magickspace.id
```

## Best Practices

### 1. Choose the Right Type

- Use **`private`** for:
  - Personal workspaces
  - User-specific contexts
  - Individual research or projects

- Use **`group`** for:
  - Team collaboration
  - Shared knowledge bases
  - Multi-user projects

### 2. Organize with Projects

Link related magickspaces to projects for better organization:

```python
client.magickspaces.create(
    name="Backend Team",
    type="group",
    project_id="proj-backend-v2",  # Link to project
    participant_ids=backend_team
)
```

### 3. Manage Corpus Attachments Carefully

Corpus provide context to LLM conversations. Keep them relevant:

```python
# Good: Focused corpus for specific domain
client.magickspaces.create(
    name="Customer Support",
    type="group",
    corpus_ids=["corp-help-docs", "corp-faq", "corp-policies"]
)

# Avoid: Too many unrelated corpus
```

### 4. Pagination Strategy

- **Latest mode**: Initial page load
- **Backward mode**: User scrolling up (load history)
- **Forward mode**: Polling for new messages

### 5. Error Handling

```python
try:
    space = client.magickspaces.create(
        name="Test Space",
        type="private"
    )
except Exception as e:
    print(f"Failed to create magickspace: {e}")
```

## API Reference

### `create()`

Create a new magickspace.

**Parameters:**
- `name` (str, required): MagickSpace name (max 100 chars)
- `type` (Literal["private", "group"], required): MagickSpace type
- `description` (str, optional): Description (max 256 chars)
- `project_id` (str, optional): Associated project ID
- `corpus_ids` (list[str], optional): Corpus IDs to attach
- `participant_ids` (list[str], optional): User IDs to grant access

**Returns:** `CreateMagickSpaceResponse`

---

### `get()`

Get magickspace by ID.

**Parameters:**
- `magickspace_id` (str, required): MagickSpace ID

**Returns:** `GetMagickSpaceResponse`

---

### `list()`

List magickspaces, optionally filtered by user.

**Parameters:**
- `user_id` (str, optional): Filter by user ID

**Returns:** `GetMagickSpaceListResponse`

---

### `update()`

Update an existing magickspace.

**Parameters:**
- `magickspace_id` (str, required): MagickSpace ID to update
- `name` (str, required): Updated name
- `description` (str, optional): Updated description
- `project_id` (str, optional): Updated project ID
- `corpus_ids` (list[str], optional): Updated corpus list
- `participant_ids` (list[str], optional): Updated user list

**Returns:** `UpdateMagickSpaceResponse`

---

### `delete()`

Delete a magickspace.

**Parameters:**
- `magickspace_id` (str, required): MagickSpace ID to delete

**Returns:** None

---

### `get_messages()`

Fetch chat messages with cursor-based pagination.

**Parameters:**
- `magickspace_id` (str, required): MagickSpace to fetch from
- `cursor` (str, optional): Pagination cursor from `paging.cursors.after` or `.before`
- `limit` (int, optional): Max messages to return
- `order` (str, optional): Sort order — `"asc"` or `"desc"` (default: asc)

**Returns:** `MagickSpaceMessagesResponse`

---

### `send_message()`

Send a message to a magickspace.

**Parameters:**
- `magickspace_id` (str, required): MagickSpace to send to
- `content` (str, required): Message content text
- `sender_id` (str, required): ID of the user sending the message
- `reply_to_message_id` (str, optional): ID of message being replied to
- `artifact_ids` (list[str], optional): Artifact IDs to attach
- `message_type` (str, optional): Message type (default: `"TEXT"`)
- `broadcast` (bool, optional): Whether to broadcast via Centrifugo (default: True)

**Returns:** `ChatHistoryItem`

## Related Resources

- [Corpus Resource Guide](./corpus.md) - Attaching knowledge bases to magickspaces
- [Backend Integration Guide](../guides/backend_integration.md) - Server-side patterns
