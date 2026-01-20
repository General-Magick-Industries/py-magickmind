"""
Example: Using the typed chat resource

This example demonstrates how to use the new V1 chat resource
with type safety and Pydantic validation.
"""

import os
from dotenv import load_dotenv

from magick_mind import MagickMind
from magick_mind.models.v1.chat import ConfigSchema

# Load environment variables from .env file
load_dotenv()

# Initialize client with credentials
client = MagickMind(
    base_url=os.getenv("BIFROST_BASE_URL", "https://dev-bifrost.magickmind.ai"),
    email=os.getenv("BIFROST_EMAIL"),
    password=os.getenv("BIFROST_PASSWORD"),
)

print("✅ Client initialized and authenticated")

# Create config for chat (new OpenAPI 3.1 structure)
config = ConfigSchema(
    fast_model_id="openrouter/meta-llama/llama-3.1-8b-instruct:free",
    smart_model_ids=["openrouter/meta-llama/llama-3.1-8b-instruct:free"],
    compute_power=50,
)

# Send a chat message using typed resource
response = client.v1.chat.send(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    mindspace_id=os.getenv("MINDSPACE_ID", "mind-test-123"),
    message="Hello! Can you help me understand quantum computing?",
    enduser_id=os.getenv("USER_ID", "user-test-456"),
    config=config,
)

# Access response with type safety
if response.success:
    print("✅ Chat sent successfully")
    print(f"Message ID: {response.content.message_id}")
    print(f"Task ID: {response.content.task_id}")
    print(f"\n📝 AI Response:\n{response.content.content}")
else:
    print(f"❌ Failed: {response.message}")
