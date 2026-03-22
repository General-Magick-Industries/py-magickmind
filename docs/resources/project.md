# Project Resource - Magick Mind SDK

The Project Resource provides a complete CRUD interface for managing projects in your agentic SaaS backend.

## Overview

Projects organize corpus and other resources for multi-tenant backends. Each project can be associated with multiple corpus IDs and is owned by a specific user.

## Installation

The project resource is included in the Magick Mind SDK:

```python
from magick_mind import MagickMindClient

client = MagickMindClient(
    base_url="https://api.example.com",
    api_key="your-api-key"
)

# Access the project resource
projects = client.v1.project
```

## API Reference

### `create(name, description="", corpus_ids=None)`

Create a new project.

**Parameters:**
- `name` (str, required): Project name
- `description` (str, optional): Project description (max 256 chars)
- `corpus_ids` (list[str], optional): List of corpus IDs to associate

**Returns:** `Project` object

**Example:**
```python
project = client.v1.project.create(
    name="My Agentic Assistant",
    description="An AI-powered customer support assistant",
    corpus_ids=["corpus-123", "corpus-456"]
)
print(f"Created project: {project.id}")
```

---

### `get(project_id)`

Get a project by ID.

**Parameters:**
- `project_id` (str, required): The project ID to retrieve

**Returns:** `Project` object

**Example:**
```python
project = client.v1.project.get(project_id="proj-123")
print(f"Project name: {project.name}")
print(f"Corpus IDs: {project.corpus_ids}")
```

---

### `list(created_by_user_id=None)`

List projects, optionally filtered by creator user ID.

**Parameters:**
- `created_by_user_id` (str, optional): Filter projects created by this user

**Returns:** List of `Project` objects

**Example:**
```python
# List all accessible projects
all_projects = client.v1.project.list()
for project in all_projects:
    print(f"- {project.name} (ID: {project.id})")

# List projects created by specific user
user_projects = client.v1.project.list(created_by_user_id="user-123")
```

---

### `update(project_id, name, description="", corpus_ids=None)`

Update an existing project.

**Parameters:**
- `project_id` (str, required): The project ID to update
- `name` (str, required): New project name
- `description` (str, optional): New project description (max 256 chars)
- `corpus_ids` (list[str], optional): New list of corpus IDs

**Returns:** Updated `Project` object

**Example:**
```python
updated = client.v1.project.update(
    project_id="proj-123",
    name="Updated Assistant",
    description="Now with enhanced capabilities!",
    corpus_ids=["corpus-123", "corpus-456", "corpus-789"]
)
print(f"Updated at: {updated.updated_at}")
```

---

### `delete(project_id)`

Delete a project.

**Parameters:**
- `project_id` (str, required): The project ID to delete

**Returns:** None

**Example:**
```python
client.v1.project.delete(project_id="proj-123")
print("Project deleted successfully")
```

## Data Models

### Project

The main project data model.

**Fields:**
- `id` (str): Project ID
- `name` (str): Project name
- `description` (str): Project description
- `corpus_ids` (list[str]): List of associated corpus IDs
- `created_by` (str): User ID of the creator
- `created_at` (str): Creation timestamp (ISO8601)
- `updated_at` (str): Last update timestamp (ISO8601)

## Complete Example

```python
import os
from magick_mind import MagickMindClient

# Initialize client
client = MagickMindClient(
    base_url=os.getenv("MAGICK_MIND_BASE_URL"),
    api_key=os.getenv("MAGICK_MIND_API_KEY")
)

# Create a new project
project = client.v1.project.create(
    name="Customer Support Bot",
    description="AI assistant for customer support",
    corpus_ids=["kb-corpus-1", "faq-corpus-2"]
)
print(f"Created: {project.id}")

# Get the project
retrieved = client.v1.project.get(project_id=project.id)
print(f"Name: {retrieved.name}")

# Update the project
updated = client.v1.project.update(
    project_id=project.id,
    name="Enhanced Support Bot",
    description="Now with multi-language support",
    corpus_ids=["kb-corpus-1", "faq-corpus-2", "ml-corpus-3"]
)

# List all projects
all_projects = client.v1.project.list()
print(f"Total projects: {len(all_projects)}")

# Delete the project
client.v1.project.delete(project_id=project.id)
```

## Error Handling

The project resource follows the SDK's standard error handling:

```python
from requests.exceptions import HTTPError

try:
    project = client.v1.project.get(project_id="non-existent")
except HTTPError as e:
    if e.response.status_code == 404:
        print("Project not found")
    else:
        print(f"API error: {e}")
```

## Integration with the Magick Mind API

The project resource maps directly to the Magick Mind API's `/v1/projects` endpoints:

- **POST** `/v1/projects` - Create project
- **GET** `/v1/projects/:id` - Get project by ID
- **GET** `/v1/projects` - List projects (with optional `user_id` filter)
- **PUT** `/v1/projects/:id` - Update project
- **DELETE** `/v1/projects/:id` - Delete project

All requests require authentication via the SDK's configured API key or credentials.

## Testing

Run the project resource tests:

```bash
# Test models
pytest tests/test_project_models.py -v

# Test resource
pytest tests/test_project_resource.py -v

# Test both
pytest tests/test_project_* -v
```

## See Also

- [History Resource](../history.py) - For fetching chat history
- [Chat Resource](../chat.py) - For sending chat messages
- [API Documentation](../../../bifrost/api/v1/project.api) - Backend API spec
