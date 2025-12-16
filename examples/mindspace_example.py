"""
Example: Using the Mindspace resource

This example demonstrates full CRUD operations for mindspaces
and fetching messages with pagination.
"""

import os

from magick_mind import MagickMind

# Initialize client with credentials
client = MagickMind(
    base_url=os.getenv("BIFROST_URL", "https://bifrost.example.com"),
    email=os.getenv("USER_EMAIL", "user@example.com"),
    password=os.getenv("USER_PASSWORD", "password"),
)

print("=== Mindspace Resource Examples ===\n")

# 1. Create a private mindspace
print("1. Creating a private mindspace...")
private_space = client.v1.mindspace.create(
    name="My Personal Workspace",
    type="private",
    description="Private workspace for personal projects",
    corpus_ids=["corp-123"],
)

if private_space.success:
    print(f"✓ Created mindspace: {private_space.mindspace.id}")
    print(f"  Name: {private_space.mindspace.name}")
    print(f"  Type: {private_space.mindspace.type}")
    print(f"  Corpora: {private_space.mindspace.corpus_ids}")
    mindspace_id = private_space.mindspace.id
else:
    print(f"✗ Failed: {private_space.message}")
    exit(1)

# 2. Create a group mindspace
print("\n2. Creating a group mindspace...")
group_space = client.mindspace.create(  # Using convenience alias
    name="Engineering Team",
    type="group",
    description="Team collaboration space",
    corpus_ids=["corp-1", "corp-2"],
    user_ids=["user-1", "user-2", "user-3"],
)

if group_space.success:
    print(f"✓ Created group mindspace: {group_space.mindspace.id}")
    print(f"  Members: {len(group_space.mindspace.user_ids)} users")
else:
    print(f"✗ Failed: {group_space.message}")

# 3. List all mindspaces
print("\n3. Listing all mindspaces...")
mindspaces = client.v1.mindspace.list()

if mindspaces.success:
    print(f"✓ Found {len(mindspaces.mindspaces)} mindspace(s):")
    for ms in mindspaces.mindspaces:
        print(f"  - {ms.name} ({ms.type}) - {ms.id}")
else:
    print(f"✗ Failed: {mindspaces.message}")

# 4. List mindspaces filtered by user
print("\n4. Listing mindspaces for specific user...")
user_mindspaces = client.v1.mindspace.list(user_id="user-1")

if user_mindspaces.success:
    print(f"✓ Found {len(user_mindspaces.mindspaces)} mindspace(s) for user-1")
else:
    print(f"✗ Failed: {user_mindspaces.message}")

# 5. Get a specific mindspace
print("\n5. Getting mindspace by ID...")
mindspace = client.v1.mindspace.get(mindspace_id)

if mindspace.success:
    print(f"✓ Retrieved mindspace: {mindspace.mindspace.name}")
    print(f"  Description: {mindspace.mindspace.description}")
    print(f"  Project ID: {mindspace.mindspace.project_id}")
else:
    print(f"✗ Failed: {mindspace.message}")

# 6. Update mindspace
print("\n6. Updating mindspace...")
updated = client.v1.mindspace.update(
    mindspace_id=mindspace_id,
    name="My Updated Workspace",
    description="Updated description with more details",
    corpus_ids=["corp-123", "corp-456"],  # Add another corpus
)

if updated.success:
    print(f"✓ Updated mindspace: {updated.mindspace.name}")
    print(f"  New corpora count: {len(updated.mindspace.corpus_ids)}")
    print(f"  Corpora: {updated.mindspace.corpus_ids}")
else:
    print(f"✗ Failed: {updated.message}")

# 7. Get messages from mindspace (latest)
print("\n7. Getting latest messages from mindspace...")
messages = client.v1.mindspace.get_messages(mindspace_id=mindspace_id, limit=10)

print(f"✓ Retrieved {len(messages.chat_histories)} message(s)")
if messages.chat_histories:
    for msg in messages.chat_histories[:3]:  # Show first 3
        print(f"  - [{msg.sent_by_user_id}]: {msg.content[:50]}...")
    print(f"  Has more: {messages.has_more}")
    print(f"  Has older: {messages.has_older}")

    # 8. Forward pagination (get newer messages)
    if messages.has_more and messages.next_after_id:
        print("\n8. Getting newer messages (forward pagination)...")
        newer = client.v1.mindspace.get_messages(
            mindspace_id=mindspace_id,
            after_id=messages.next_after_id,
            limit=10,
        )
        print(f"✓ Retrieved {len(newer.chat_histories)} newer message(s)")

    # 9. Backward pagination (get older messages)
    if messages.has_older and messages.next_before_id:
        print("\n9. Getting older messages (backward pagination)...")
        older = client.v1.mindspace.get_messages(
            mindspace_id=mindspace_id,
            before_id=messages.next_before_id,
            limit=10,
        )
        print(f"✓ Retrieved {len(older.chat_histories)} older message(s)")
else:
    print("  (No messages in this mindspace yet)")

# 10. Delete mindspace
print("\n10. Deleting mindspace...")
try:
    client.v1.mindspace.delete(mindspace_id)
    print(f"✓ Deleted mindspace: {mindspace_id}")
except Exception as e:
    print(f"✗ Failed to delete: {e}")

print("\n=== Example Complete ===")
