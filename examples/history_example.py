"""
Example: Chat History with Pagination

Demonstrates the history resource using the new standardized pagination format.

Run setup_resources.py first to configure your .env file.
"""

import os
from dotenv import load_dotenv

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException

# Load .env file
load_dotenv()

# Get credentials from environment
email = os.getenv("BIFROST_EMAIL")
password = os.getenv("BIFROST_PASSWORD")
base_url = os.getenv("BIFROST_BASE_URL", "https://dev-bifrost.magickmind.ai")
mindspace_id = os.getenv("MINDSPACE_ID")

if not email or not password:
    print("ERROR: Missing BIFROST_EMAIL or BIFROST_PASSWORD in .env")
    print("Run: python setup_resources.py first")
    exit(1)

if not mindspace_id:
    print("ERROR: Missing MINDSPACE_ID in .env")
    print("Run: python setup_resources.py first")
    exit(1)

# Initialize client
client = MagickMind(email=email, password=password, base_url=base_url)

print("=" * 60)
print("Chat History Example")
print("=" * 60)
print(f"Mindspace: {mindspace_id}")

try:
    # 1. Get latest messages using new pagination format
    print("\n📜 Fetching latest 10 messages...")
    history = client.v1.history.get_messages(mindspace_id=mindspace_id, limit=10)

    # Access via new standardized format: data + paging
    print(f"\nFound {len(history.data)} messages:")
    for msg in history.data:
        content = msg.content[:50] if msg.content else "(no content)"
        print(f"  • [{msg.id}] {msg.sent_by_user_id}: {content}...")
        if msg.reply_to_message_id:
            print(f"    ↳ Reply to: {msg.reply_to_message_id}")

    # Show pagination info
    print(f"\n📊 Pagination info:")
    print(f"  has_more: {history.paging.has_more}")
    print(f"  has_previous: {history.paging.has_previous}")
    print(f"  cursors.after: {history.paging.cursors.after}")
    print(f"  cursors.before: {history.paging.cursors.before}")

    # Demo backward-compat properties still work
    print(f"\n🔄 Backward-compat check:")
    print(f"  chat_histories length: {len(history.chat_histories)}")
    print(f"  has_older: {history.has_older}")
    print(f"  next_after_id: {history.next_after_id}")

    # 2. Forward pagination (get newer messages)
    if history.paging.cursors.after:
        print("\n⏩ Testing forward pagination...")
        newer = client.v1.history.get_messages(
            mindspace_id=mindspace_id,
            after_id=history.paging.cursors.after,
            limit=5,
        )
        print(f"  Got {len(newer.data)} newer messages")
        print(f"  has_more: {newer.paging.has_more}")

    # 3. Backward pagination (get older messages)
    if history.data and history.paging.cursors.before:
        print("\n⏪ Testing backward pagination...")
        older = client.v1.history.get_messages(
            mindspace_id=mindspace_id,
            before_id=history.paging.cursors.before,
            limit=5,
        )
        print(f"  Got {len(older.data)} older messages")
        print(f"  has_previous: {older.paging.has_previous}")

except ProblemDetailsException as e:
    print(f"\n❌ API Error: [{e.status}] {e.title}")
    print(f"   Detail: {e.detail}")
    if e.request_id:
        print(f"   Request ID: {e.request_id}")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
