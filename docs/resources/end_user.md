# End User Resource - Magick Mind SDK

The End User Resource provides a complete CRUD interface for managing end users in your agentic SaaS backend.

## Overview

End users represent the actual users of applications built on the Magick Mind platform in a multi-tenant architecture. Each end user belongs to a specific tenant and can be mapped to external systems via an optional external ID.

## Installation

The end user resource is included in the Magick Mind SDK:

```python
from magick_mind import MagickMind

client = MagickMind(
    base_url="https://api.example.com",
    email="user@example.com",
    password="your-password"
)

# Access the end user resource
end_users = client.v1.end_user
```

## API Reference

### `create(name, external_id=None)`

Create a new end user.

**Parameters:**
- `name` (str, required): End user name
- `external_id` (str, optional): External ID for mapping to external systems

> **Note:** `tenant_id` and `actor_id` are derived from your authenticated session automatically.

**Returns:** `EndUser` object

**Example:**
```python
end_user = client.v1.end_user.create(
    name="John Doe",
    external_id="ext-789"
)
print(f"Created end user: {end_user.id}")
```

---

### `get(end_user_id)`

Get an end user by ID.

**Parameters:**
- `end_user_id` (str, required): The end user ID to retrieve

**Returns:** `EndUser` object

**Example:**
```python
end_user = client.v1.end_user.get(end_user_id="user-123")
print(f"End user name: {end_user.name}")
print(f"Tenant ID: {end_user.tenant_id}")
print(f"External ID: {end_user.external_id}")
```

---

### `query(name=None, external_id=None, cursor=None, limit=None, order=None)`

Query end users with optional filters. All parameters are optional.

**Parameters:**
- `name` (str, optional): Filter by end user name
- `external_id` (str, optional): Filter by external ID
- `cursor` (str, optional): Pagination cursor
- `limit` (int, optional): Maximum number of results to return
- `order` (str, optional): Sort order (`"asc"` or `"desc"`)

**Returns:** List of `EndUser` objects

**Example:**
```python
# Get all end users (no filters)
all_users = client.v1.end_user.query()
for user in all_users:
    print(f"- {user.name} (ID: {user.id})")

# Find user by external ID
external_users = client.v1.end_user.query(external_id="ext-789")
if external_users:
    user = external_users[0]
    print(f"Found: {user.name}")

# Filter by name with pagination
filtered = client.v1.end_user.query(name="John Doe", limit=10)
```

---

### `update(end_user_id, name=None, external_id=None)`

Update an existing end user. All update fields are optional - only provided fields will be updated.

**Parameters:**
- `end_user_id` (str, required): The end user ID to update
- `name` (str, optional): New end user name
- `external_id` (str, optional): New external ID

**Returns:** Updated `EndUser` object

**Example:**
```python
# Update name only
updated = client.v1.end_user.update(
    end_user_id="user-123",
    name="Jane Doe"
)

# Update multiple fields
updated = client.v1.end_user.update(
    end_user_id="user-123",
    name="Jane Smith",
    external_id="new-ext-id"
)
print(f"Updated at: {updated.updated_at}")
```

---

### `delete(end_user_id)`

Delete an end user.

**Parameters:**
- `end_user_id` (str, required): The end user ID to delete

**Returns:** None

**Example:**
```python
client.v1.end_user.delete(end_user_id="user-123")
print("End user deleted successfully")
```

## Data Models

### EndUser

The main end user data model.

**Fields:**
- `id` (str): End user ID
- `name` (str): End user name
- `external_id` (str | None): Optional external ID for mapping to external systems
- `tenant_id` (str): Tenant ID this end user belongs to
- `created_by` (str | None): User ID of the creator
- `updated_by` (str | None): User ID of the last updater
- `created_at` (str): Creation timestamp (ISO8601)
- `updated_at` (str): Last update timestamp (ISO8601)

## Complete Example

```python
import os
from magick_mind import MagickMind

# Initialize client
client = MagickMind(
    base_url=os.getenv("MAGICK_MIND_BASE_URL"),
    email=os.getenv("MAGICK_MIND_EMAIL"),
    password=os.getenv("MAGICK_MIND_PASSWORD")
)

# Create a new end user
end_user = client.v1.end_user.create(
    name="John Doe",
    external_id="customer-ext-001"
)
print(f"Created: {end_user.id}")

# Get the end user
retrieved = client.v1.end_user.get(end_user_id=end_user.id)
print(f"Name: {retrieved.name}")

# Query end users
users = client.v1.end_user.query(name="John")
print(f"Found users: {len(users)}")

# Update the end user
updated = client.v1.end_user.update(
    end_user_id=end_user.id,
    name="Jane Doe",
    external_id="customer-ext-updated"
)
print(f"Updated: {updated.name}")

# Query by external ID to verify update
found_users = client.v1.end_user.query(external_id="customer-ext-updated")
if found_users:
    print(f"Found by external ID: {found_users[0].name}")

# List all end users
all_users = client.v1.end_user.query()
print(f"Total end users: {len(all_users)}")

# Delete the end user
client.v1.end_user.delete(end_user_id=end_user.id)
print("End user deleted successfully")
```

## Use Cases

### Managing End Users

```python
# Create end users with external IDs
alice = client.v1.end_user.create(
    name="Alice",
    external_id="alice@company-a.com"
)

bob = client.v1.end_user.create(
    name="Bob",
    external_id="bob@company-b.com"
)

# List all end users
all_users = client.v1.end_user.query()
print(f"Total users: {len(all_users)}")
```

### External System Integration

```python
# Map to external system (e.g., CRM)
end_user = client.v1.end_user.create(
    name="Customer Name",
    external_id="salesforce-contact-456"
)

# Later, look up by external ID
external_users = client.v1.end_user.query(
    external_id="salesforce-contact-456"
)
if external_users:
    api_user = external_users[0]
    print(f"API user ID: {api_user.id}")
```

## Error Handling

The end user resource follows the SDK's standard error handling:

```python
from requests.exceptions import HTTPError

try:
    end_user = client.v1.end_user.get(end_user_id="non-existent")
except HTTPError as e:
    if e.response.status_code == 404:
        print("End user not found")
    elif e.response.status_code == 403:
        print("Access denied")
    else:
        print(f"API error: {e}")
```

## Integration with the Magick Mind API

The end user resource maps directly to the Magick Mind API's `/v1/end-users` endpoints:

- **POST** `/v1/end-users` - Create end user
- **GET** `/v1/end-users/:id` - Get end user by ID
- **GET** `/v1/end-users` - Query end users (with optional filters)
- **PUT** `/v1/end-users/:id` - Update end user
- **DELETE** `/v1/end-users/:id` - Delete end user

All requests require authentication via the SDK's configured credentials.

## Testing

Run the end user resource tests:

```bash
# Test models
pytest tests/test_end_user_models.py -v

# Test resource
pytest tests/test_end_user_resource.py -v

# Test both
pytest tests/test_end_user_* -v
```

## See Also

- [Project Resource](project.md) - For managing projects
- [Backend Integration Guide](../guides/backend_integration.md) - For integrating with backends
- [API Documentation](../../../bifrost/api/v1/end_users.api) - Backend API spec
