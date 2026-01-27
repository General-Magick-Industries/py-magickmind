"""
Example demonstrating API Keys resource operations.

This example shows how to create, list, update, and delete API keys
for authenticating requests using the Magick Mind SDK.
"""

from magick_mind import MagickMind

# Initialize client
client = MagickMind(
    email="your-email@example.com",
    password="your-password",
    base_url="https://api.example.com",
)

# User and project info
user_id = "user-123"
project_id = "proj-456"

# 1. Create a new API key
print("Creating a new API key...")
create_resp = client.v1.api_keys.create(
    user_id=user_id,
    project_id=project_id,
    models=["gpt-4", "gpt-3.5-turbo", "claude-3"],
    key_alias="Production Key",
    duration="90d",  # Valid for 90 days
    max_budget=100.0,  # $100 spending limit
)

# IMPORTANT: Save this key securely - it's only shown once!
api_key = create_resp.key.key
key_id = create_resp.key.key_id
print(f"API Key created: {api_key}")
print(f"  Key ID: {key_id}")
print(f"  Alias: {create_resp.key.key_alias}")
print(f"  Expires: {create_resp.key.expires}")
print()

# 2. List all API keys for the user
print(f"Listing API keys for user {user_id}...")
list_resp = client.v1.api_keys.list(user_id=user_id)
print(f"Found {len(list_resp.keys)} key(s):")
for key_meta in list_resp.keys:
    print(f"  - {key_meta.key_alias}")
    print(f"    ID: {key_meta.key_id}")
    print(f"    Project: {key_meta.project_id}")
    print(f"    Created: {key_meta.create_at}")
print()

# 3. Update the API key
print("Updating API key...")
update_resp = client.v1.api_keys.update(
    key=api_key,  # Use the actual key value
    models=["gpt-4", "gpt-3.5-turbo", "claude-3", "gemini-pro"],  # Added model
    key_alias="Updated Production Key",
    max_budget=200.0,  # Increased budget
)
print(f"Updated key: {update_resp.key.key_alias}")
print("  New budget: $200")
print()

# 4. Use the API key to make requests
print("Using the API key to send a chat message...")
# Note: This demonstrates how the API key is used in practice
chat_response = client.v1.chat.send(
    api_key=api_key,  # Authentication using the created key
    mindspace_id="mind-789",
    message="Hello, how are you?",
    enduser_id="enduser-001",
)
print(f"Chat response: {chat_response.message[:100]}...")
print()

# 5. Create a team key (shared key for team members)
print("Creating a team API key...")
team_key_resp = client.v1.api_keys.create(
    user_id=user_id,
    project_id=project_id,
    models=["gpt-4", "gpt-3.5-turbo"],
    key_alias="Engineering Team Key",
    duration="90d",
    team_id="team-eng-001",  # Associate with team
    max_budget=500.0,  # Higher budget for team
)
team_key = team_key_resp.key.key
team_key_id = team_key_resp.key.key_id
print(f"Team key created: {team_key_id}")
print("  For team: team-eng-001")
print("  Budget: $500 (shared across team)")
print()

# 6. Delete the API keys
print(f"Deleting API key {key_id}...")
delete_resp = client.v1.api_keys.delete(key_id=key_id)
print(f"Delete result: {delete_resp.message}")

print(f"Deleting team key {team_key_id}...")
delete_team = client.v1.api_keys.delete(key_id=team_key_id)
print(f"Delete result: {delete_team.message}")
print()

# Complete workflow example: Key rotation
print("=" * 70)
print("Complete workflow: API Key Rotation")
print("=" * 70)

print("\n1. Creating new API key (rotation)...")
new_key_resp = client.v1.api_keys.create(
    user_id=user_id,
    project_id=project_id,
    models=["gpt-4", "gpt-3.5-turbo"],
    key_alias="Production Key v2",
    duration="30d",
    max_budget=150.0,
)
new_key = new_key_resp.key.key
new_key_id = new_key_resp.key.key_id
print(f"  New key created: {new_key_id}")

print("\n2. Test the new key...")
# In production, you'd test the new key thoroughly before rotating
test_response = client.v1.chat.send(
    api_key=new_key,
    mindspace_id="mind-789",
    message="Test message with new key",
    enduser_id="enduser-001",
)
print(f"  Test successful: {test_response.success}")

print("\n3. List all active keys...")
all_keys = client.v1.api_keys.list(user_id=user_id)
print(f"  Active keys: {len(all_keys.keys)}")
for k in all_keys.keys:
    print(f"    - {k.key_alias} (created {k.create_at})")

print("\n4. Revoke old keys...")
# In practice, you'd keep the new key and delete the old one
# For this example, we'll clean up the new key
delete_new = client.v1.api_keys.delete(key_id=new_key_id)
print(f"  {delete_new.message}")

# Best Practices Summary
print("\n" + "=" * 70)
print("API Key Management Best Practices")
print("=" * 70)
print("""
1. **Secure Storage**: Store API keys in environment variables or secrets manager
2. **Key Rotation**: Regularly rotate keys (e.g., every 30-90 days)
3. **Least Privilege**: Only grant access to models actually needed
4. **Budget Limits**: Set max_budget to prevent unexpected costs
5. **Monitoring**: Track key usage and set up alerts
6. **Revocation**: Immediately delete compromised keys
7. **Team Keys**: Use team_id to associate keys with specific teams for tracking and organization
   - Useful for multi-tenant scenarios where each team needs separate keys
   - Allows tracking API usage per team
   - Example: `team_id="team-eng-001"` for engineering team's shared key
""")

print("\n✅ API Keys example completed!")
