# Mindspace Resource Guide

A comprehensive guide to using the Mindspace resource in the Magick Mind SDK for managing organizational containers for chat conversations, knowledge bases, and user collaboration.

## Overview

**Mindspace is central to Bifrost** - it's where everything starts and ends. Conversations, knowledge, and users all come together in mindspaces.

**Mindspaces** are organizational containers that group together:
- **Chat conversations** - Message history and interactions
- **Knowledge bases** - Attached corpus for contextual AI responses
- **Users** - Members with access to the space
- **Projects** - Optional organizational grouping

**Two types:**
- **`private`** - Single-user personal workspaces (individual context, personal AI)
- **`group`** - Multi-user collaborative spaces (team knowledge, shared context)

### Privacy Model

**Asymmetric access pattern** - designed for privacy while maximizing utility:

- ✅ **Private → Group**: Private mindspaces **can access** group knowledge
  - Personal AI benefits from team corpus, company docs, shared resources
  - Individual gets collective knowledge without exposing personal context
  
- ❌ **Group → Private**: Group mindspaces **cannot access** private conversations
  - Personal conversations stay personal
  - Clear privacy boundary: group is shared, private is isolated

**Example:**
```python
# Alice's private space can use team knowledge
alice_personal = client.mindspace.create(
    name="Alice's Personal Assistant",
    type="private",
    corpus_ids=["team-handbook", "company-docs"]  # ✅ Can access group corpus
)

# Team space cannot see Alice's personal conversations
eng_team = client.mindspace.create(
    name="Engineering Team",
    type="group",
    corpus_ids=["codebase", "specs"]
    # ❌ Cannot access Alice's private mindspace
)
```

This model follows **least privilege** principles - users get access to shared knowledge without sacrificing privacy.

## Quick Start

```python
from magick_mind import MagickMind

# Initialize client
client = MagickMind(
    base_url="https://bifrost.example.com",
    email="user@example.com",
    password="password"
)

# Create a private mindspace
workspace = client.mindspace.create(
    name="My Personal Workspace",
    type="private",
    description="Personal workspace for my projects"
)

# Create a group mindspace
team = client.mindspace.create(
    name="Engineering Team",
    type="group",
    description="Team collaboration space",
    user_ids=["user-1", "user-2", "user-3"],
    corpus_ids=["corp-handbook", "corp-docs"]
)
```

## Core Operations

### Creating Mindspaces

```python
# Private: individual workspace with personal+team knowledge
private = client.mindspace.create(
    name="My Research",
    type="private",
    corpus_ids=["team-docs", "personal-notes"]  # Can access both
)

# Group: collaborative team workspace
team = client.mindspace.create(
    name="Product Team",
    type="group",
    user_ids=["alice", "bob", "charlie"],
    corpus_ids=["specs", "designs"],
    project_id="proj-v2"  # Optional project link
)
```

### Listing & Retrieving

```python
# List all
all_spaces = client.mindspace.list()

# Filter by user
user_spaces = client.mindspace.list(user_id="alice")

# Get specific mindspace
space = client.mindspace.get("mind-123")
```

### Updating & Deleting

```python
# Update (replaces entire lists, include all existing IDs)
client.mindspace.update(
    mindspace_id="mind-123",
    name="Updated Name",
    corpus_ids=["corp-1", "corp-2", "corp-3"],  # All IDs
    user_ids=["user-1", "user-2", "user-3", "user-4"]  # All IDs
)

# Delete
client.mindspace.delete("mind-123")
```

> **Note**: `update()` replaces entire lists. To add one item, include all existing IDs plus the new one.

## Message History

Mindspaces maintain chat message history. Use `get_messages()` with three pagination modes.

### Latest Messages

Get the most recent N messages:

```python
messages = client.mindspace.get_messages(
    mindspace_id="mind-123",
    limit=50
)

print(f"Retrieved {len(messages.chat_histories)} messages")

# Display messages
for msg in messages.chat_histories:
    print(f"[{msg.sent_by_user_id}]: {msg.content}")
    
# Check for more data
print(f"Has more recent: {messages.has_more}")
print(f"Has older: {messages.has_older}")
```

### Forward Pagination (Newer Messages)

Get messages after a specific point (useful for incremental updates):

```python
# Start with latest
initial = client.mindspace.get_messages(
    mindspace_id="mind-123",
    limit=20
)

# Get newer messages if available
if initial.has_more and initial.next_after_id:
    newer = client.mindspace.get_messages(
        mindspace_id="mind-123",
        after_id=initial.next_after_id,
        limit=20
    )
    print(f"Found {len(newer.chat_histories)} newer messages")
```

### Backward Pagination (Older Messages)

Get messages before a specific point (useful for scrolling back in history):

```python
# Start with latest
current = client.mindspace.get_messages(
    mindspace_id="mind-123",
    limit=20
)

# Load older messages
if current.has_older and current.next_before_id:
    older = client.mindspace.get_messages(
        mindspace_id="mind-123",
        before_id=current.next_before_id,
        limit=20
    )
    print(f"Found {len(older.chat_histories)} older messages")
```

### Message Data Structure

Each message in `chat_histories` contains:

```python
message = messages.chat_histories[0]

print(f"ID: {message.id}")
print(f"Mindspace: {message.mindspace_id}")
print(f"Sender: {message.sent_by_user_id}")
print(f"Content: {message.content}")
print(f"Status: {message.status}")
print(f"Artifacts: {message.artifact_ids}")
print(f"Reply to: {message.reply_to_message_id}")
print(f"Created: {message.created_at}")
```

## Common Patterns

### Creating a Project Workspace

Set up a complete workspace for a project:

```python
# 1. Create the mindspace
workspace = client.mindspace.create(
    name=f"Project: {project_name}",
    type="group",
    description=f"Workspace for {project_name}",
    project_id=project_id,
    user_ids=team_members,
    corpus_ids=knowledge_bases
)

mindspace_id = workspace.mindspace.id

# 2. Verify setup
space = client.mindspace.get(mindspace_id)
print(f"✓ Created workspace for {len(space.mindspace.user_ids)} members")
print(f"✓ Attached {len(space.mindspace.corpus_ids)} knowledge bases")
```

### Adding Knowledge to Existing Workspace

```python
# Get current state
current = client.mindspace.get("mind-123")

# Add new corpus while preserving existing ones
updated_corpus_ids = current.mindspace.corpus_ids + ["new-corpus-id"]

# Update
client.mindspace.update(
    mindspace_id="mind-123",
    name=current.mindspace.name,
    corpus_ids=updated_corpus_ids,
    user_ids=current.mindspace.user_ids
)
```

### Loading Full Message History

Efficiently load all messages using pagination:

```python
def load_all_messages(mindspace_id: str, batch_size: int = 100):
    """Load all messages from a mindspace using pagination."""
    all_messages = []
    
    # Start with latest
    response = client.mindspace.get_messages(
        mindspace_id=mindspace_id,
        limit=batch_size
    )
    all_messages.extend(response.chat_histories)
    
    # Keep loading older messages
    while response.has_older and response.next_before_id:
        response = client.mindspace.get_messages(
            mindspace_id=mindspace_id,
            before_id=response.next_before_id,
            limit=batch_size
        )
        all_messages.extend(response.chat_histories)
    
    return all_messages

# Usage
all_msgs = load_all_messages("mind-123")
print(f"Loaded {len(all_msgs)} total messages")
```

### Monitoring New Messages

Poll for new messages in real-time:

```python
def poll_new_messages(mindspace_id: str, last_message_id: str = None):
    """Check for new messages since last poll."""
    if last_message_id:
        # Get messages after the last known ID
        response = client.mindspace.get_messages(
            mindspace_id=mindspace_id,
            after_id=last_message_id,
            limit=50
        )
    else:
        # First poll - get latest
        response = client.mindspace.get_messages(
            mindspace_id=mindspace_id,
            limit=50
        )
    
    return response.chat_histories

# Usage in a loop
last_id = None
while True:
    new_messages = poll_new_messages("mind-123", last_id)
    
    if new_messages:
        print(f"Received {len(new_messages)} new messages")
        last_id = new_messages[-1].id  # Update to latest
        
        # Process messages...
    
    time.sleep(5)  # Poll every 5 seconds
```

## Design Guidance

### Thinking Mindspace-First

When architecting your Bifrost application, **start with mindspaces**:

#### 1. **Define Your Conversation Contexts**

What are the different contexts where users will interact with AI?

```python
# Example: Customer support application
support_mindspace = client.mindspace.create(
    name="Customer Support - Acme Corp",
    type="private",  # Each customer gets their own space
    corpus_ids=["help-docs", "product-specs", "faq"]
)

# Example: Team collaboration
team_mindspace = client.mindspace.create(
    name="Engineering Team",
    type="group",  # Shared team space
    user_ids=team_members,
    corpus_ids=["codebase-docs", "technical-specs"]
)
```

#### 2. **Map Knowledge to Contexts**

Which knowledge should be available in each mindspace?

- **Customer Support** → Help docs, product manuals, policies
- **Engineering Team** → Codebase, technical specs, architecture docs
- **Sales Team** → Product sheets, pricing, case studies

#### 3. **Consider Access Patterns**

- **Private mindspaces** for individual user contexts (personal assistants, customer support tickets)
- **Group mindspaces** for team collaboration (shared projects, team knowledge bases)
- **Project-scoped mindspaces** for temporary initiatives

#### 4. **Design Your Message Flow**

```python
# All chat interactions reference a mindspace
response = client.chat.send(
    api_key="sk-...",
    mindspace_id="mind-123",  # The context for this conversation
    message="How do I deploy to production?",
    enduser_id="user-456"
)

# Messages are stored in the mindspace
history = client.mindspace.get_messages(mindspace_id="mind-123")
```

### Common Architecture Patterns

#### Pattern 1: One Mindspace per User Session

```python
# Each user gets their own private workspace
def onboard_user(user_id: str):
    mindspace = client.mindspace.create(
        name=f"{user_id}'s Workspace",
        type="private",
        corpus_ids=get_user_relevant_knowledge(user_id)
    )
    return mindspace.mindspace.id
```

#### Pattern 2: One Mindspace per Team/Organization

```python
# Teams share a collaborative space
def setup_team_workspace(team_name: str, members: list[str]):
    mindspace = client.mindspace.create(
        name=f"{team_name} Team Space",
        type="group",
        user_ids=members,
        corpus_ids=get_team_knowledge_bases(team_name)
    )
    return mindspace.mindspace.id
```

#### Pattern 3: Dynamic Mindspace per Conversation Topic

```python
# Create temporary mindspaces for specific tasks
def create_project_workspace(project: Project):
    mindspace = client.mindspace.create(
        name=f"Project: {project.name}",
        type="group",
        project_id=project.id,
        user_ids=project.team_members,
        corpus_ids=project.required_knowledge
    )
    return mindspace.mindspace.id
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

Link related mindspaces to projects for better organization:

```python
client.mindspace.create(
    name="Backend Team",
    type="group",
    project_id="proj-backend-v2",  # Link to project
    user_ids=backend_team
)
```

### 3. Manage Corpus Attachments Carefully

Corpus provide context to LLM conversations. Keep them relevant:

```python
# Good: Focused corpus for specific domain
client.mindspace.create(
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
    space = client.mindspace.create(
        name="Test Space",
        type="private"
    )
except Exception as e:
    print(f"Failed to create mindspace: {e}")
```

## API Reference

### `create()`

Create a new mindspace.

**Parameters:**
- `name` (str, required): Mindspace name (max 100 chars)
- `type` (Literal["private", "group"], required): Mindspace type
- `description` (str, optional): Description (max 256 chars)
- `project_id` (str, optional): Associated project ID
- `corpus_ids` (list[str], optional): Corpus IDs to attach
- `user_ids` (list[str], optional): User IDs to grant access

**Returns:** `CreateMindSpaceResponse`

---

### `get()`

Get mindspace by ID.

**Parameters:**
- `mindspace_id` (str, required): Mindspace ID

**Returns:** `GetMindSpaceResponse`

---

### `list()`

List mindspaces, optionally filtered by user.

**Parameters:**
- `user_id` (str, optional): Filter by user ID

**Returns:** `GetMindSpaceListResponse`

---

### `update()`

Update an existing mindspace.

**Parameters:**
- `mindspace_id` (str, required): Mindspace ID to update
- `name` (str, required): Updated name
- `description` (str, optional): Updated description
- `project_id` (str, optional): Updated project ID
- `corpus_ids` (list[str], optional): Updated corpus list
- `user_ids` (list[str], optional): Updated user list

**Returns:** `UpdateMindSpaceResponse`

---

### `delete()`

Delete a mindspace.

**Parameters:**
- `mindspace_id` (str, required): Mindspace ID to delete

**Returns:** None

---

### `get_messages()`

Fetch chat messages with pagination.

**Parameters:**
- `mindspace_id` (str, required): Mindspace to fetch from
- `after_id` (str, optional): Get messages after this ID (forward)
- `before_id` (str, optional): Get messages before this ID (backward)
- `limit` (int, optional): Max messages to return (default: 50)

**Returns:** `MindspaceMessagesResponse`

**Raises:** `ValueError` if both `after_id` and `before_id` are provided

## Related Resources

- [Chat Resource Example](file:///Users/berry/centrifugo/AGD_Magick_Mind_SDK/examples/chat_example.py) - Sending messages to mindspaces
- [History Resource](file:///Users/berry/centrifugo/AGD_Magick_Mind_SDK/magick_mind/resources/v1/history.py) - Alternative history access
- [Mindspace Example](file:///Users/berry/centrifugo/AGD_Magick_Mind_SDK/examples/mindspace_example.py) - Complete usage examples
