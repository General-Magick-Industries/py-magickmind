"""
Example: Using the typed chat resource

This example demonstrates how to use the new V1 chat resource
with type safety and Pydantic validation.
"""

import os
from magick_mind import MagickMind

# Initialize client with credentials
client = MagickMind(
    base_url=os.getenv("BIFROST_URL", "https://bifrost.example.com"),
    email=os.getenv("USER_EMAIL", "user@example.com"),
    password=os.getenv("USER_PASSWORD", "password"),
)

# Send a chat message using typed resource
# IDE will provide autocomplete for all parameters
response = client.v1.chat.send(
    api_key="sk-your-api-key",
    mindspace_id="mind-123",
    message="Hello! Can you help me understand quantum computing?",
    sender_id="user-456",
    fast_brain_model_id="openrouter/meta-llama/llama-4-maverick",
)

# Access response with type safety - IDE knows the structure
if response.success:
    print("✓ Chat sent successfully")
    print(f"Message ID: {response.content.message_id}")
    print(f"Task ID: {response.content.task_id}")
    print(f"\nAI Response:\n{response.content.content}")
else:
    print(f"✗ Failed: {response.message}")

# Send a follow-up message (reply)
follow_up = client.chat.send(  # Using convenience alias
    api_key="sk-your-api-key",
    mindspace_id="mind-123",
    message="Can you explain that in simpler terms?",
    sender_id="user-456",
    reply_to_message_id=response.content.message_id,  # Reference previous message
)

print(f"\n✓ Follow-up sent: {follow_up.content.content[:100]}...")
