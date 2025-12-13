"""
Simple example demonstrating history resource usage.

This example shows how to fetch chat history with pagination.
"""

import os
from magick_mind import MagickMind

# Initialize client with credentials
client = MagickMind(
    base_url=os.getenv("MAGICK_MIND_BASE_URL", "https://api.example.com"),
    email=os.getenv("MAGICK_MIND_EMAIL"),
    password=os.getenv("MAGICK_MIND_PASSWORD"),
)

# Your mindspace ID
mindspace_id = "your-mindspace-id"

print("=" * 60)
print("Chat History Example")
print("=" * 60)

# 1. Get latest messages
print("\n📜 Fetching latest 10 messages...")
history = client.v1.history.get_messages(mindspace_id=mindspace_id, limit=10)

print(f"\nFound {len(history.chat_histories)} messages:")
for msg in history.chat_histories:
    print(f"  • [{msg.id}] {msg.sent_by_user_id}: {msg.content[:50]}...")
    if msg.reply_to_message_id:
        print(f"    ↳ Reply to: {msg.reply_to_message_id}")

# 2. Forward pagination (get newer messages)
if history.last_id and input("\n\nFetch newer messages? (y/n): ").lower() == "y":
    print("\n⏩ Fetching messages after latest...")
    newer = client.v1.history.get_messages(
        mindspace_id=mindspace_id,
        after_id=history.last_id,
        limit=10,
    )

    if newer.chat_histories:
        print(f"Found {len(newer.chat_histories)} newer messages")
        print(f"Has more: {newer.has_more}")
    else:
        print("No newer messages found")

# 3. Backward pagination (get older messages)
if history.chat_histories and input("\nFetch older messages? (y/n): ").lower() == "y":
    print("\n⏪ Fetching messages before first...")
    oldest_id = history.chat_histories[0].id
    older = client.v1.history.get_messages(
        mindspace_id=mindspace_id,
        before_id=oldest_id,
        limit=10,
    )

    if older.chat_histories:
        print(f"Found {len(older.chat_histories)} older messages")
        print(f"Has older: {older.has_older}")
    else:
        print("No older messages found")

# 4. Pagination loop example
print("\n\n" + "=" * 60)
print("Full History Fetch Example (all messages)")
print("=" * 60)

if input("\nFetch ALL messages? (y/n): ").lower() == "y":
    all_messages = []
    cursor = None
    page = 1

    while True:
        print(f"\n📄 Fetching page {page}...")

        if cursor:
            batch = client.v1.history.get_messages(
                mindspace_id=mindspace_id,
                after_id=cursor,
                limit=50,
            )
        else:
            batch = client.v1.history.get_messages(
                mindspace_id=mindspace_id,
                limit=50,
            )

        all_messages.extend(batch.chat_histories)
        print(
            f"   Got {len(batch.chat_histories)} messages (total: {len(all_messages)})"
        )

        if not batch.has_more:
            break

        cursor = batch.next_after_id
        page += 1

    print(f"\n✅ Total messages fetched: {len(all_messages)}")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
