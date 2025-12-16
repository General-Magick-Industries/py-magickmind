# Corpus Resource Guide

A comprehensive guide to using the Corpus resource in the Magick Mind SDK for managing knowledge bases and document collections for RAG (Retrieval Augmented Generation) workflows.

## Overview

**Corpus** represents a collection of artifacts (documents, files, images) that provide contextual knowledge for AI-powered conversations. Corpus enable **Retrieval Augmented Generation (RAG)** - the AI can reference your documents to provide more accurate, context-aware responses.

**Key Uses:**
- **Knowledge bases** - Company docs, technical manuals, policies
- **Document collections** - Research papers, reports, specifications
- **Contextual AI** - AI agents that reference your specific data
- **Multi-tenant systems** - Isolated knowledge per customer/team

**Relationship to Mindspaces:**
- Corpus are **attached to mindspaces** to provide context
- Multiple mindspaces can share the same corpus
- Private mindspaces can access group corpus (asymmetric access)

## Quick Start

```python
from magick_mind import MagickMind

# Initialize client
client = MagickMind(
    base_url="https://bifrost.example.com",
    email="user@example.com",
    password="password"
)

# Create a knowledge base
kb = client.v1.corpus.create(
    name="Engineering Handbook",
    description="Technical documentation and best practices",
    artifact_ids=[]  # Add artifacts later
)

corpus_id = kb.corpus.id

# Attach to a mindspace for RAG
mindspace = client.v1.mindspace.create(
    name="Engineering Team Chat",
    type="group",
    corpus_ids=[corpus_id],  # AI can now reference this knowledge
    user_ids=["alice", "bob", "charlie"]
)
```

## Core Operations

### Creating Corpus

```python
# Create an empty corpus
corpus = client.v1.corpus.create(
    name="Product Documentation",
    description="User guides, API docs, and tutorials"
)

# Create with initial artifacts
corpus = client.v1.corpus.create(
    name="Research Papers",
    description="AI/ML research collection",
    artifact_ids=["art-001", "art-002", "art-003"]
)
```

### Listing & Retrieving

```python
# List all corpus
all_corpus = client.v1.corpus.list()
for corp in all_corpus.corpus:
    print(f"{corp.name}: {len(corp.artifact_ids)} files")

# Filter by user (only returns corpus created by that user)
my_corpus = client.v1.corpus.list(user_id="user-123")

# Get specific corpus
corpus = client.v1.corpus.get("corp-abc-123")
print(f"Name: {corpus.corpus.name}")
print(f"Artifacts: {corpus.corpus.artifact_ids}")
```

### Updating

Update corpus metadata and artifact associations:

```python
# Update corpus (replaces artifact list)
client.v1.corpus.update(
    corpus_id="corp-abc-123",
    name="Updated Name",
    description="Updated description",
    artifact_ids=["art-1", "art-2", "art-3", "art-4"]  # Complete list
)
```

> **Note**: `update()` replaces the entire artifact list. To add one file, include all existing IDs plus the new one.

### Deleting

```python
# Delete a corpus
response = client.v1.corpus.delete("corp-abc-123")
print(response.message)
```

## Working with Artifacts

Corpus contain **artifacts** (uploaded files). Here's the complete workflow:

### 1. Upload Files to Create Artifacts

```python
# Step 1: Get presigned upload URL
presign_resp = client.v1.artifact.presign(
    file_name="handbook.pdf",
    content_type="application/pdf",
    size_bytes=1024000
)

artifact_id = presign_resp.id
upload_url = presign_resp.upload_url
required_headers = presign_resp.required_headers

# Step 2: Upload file to S3
import httpx

with open("handbook.pdf", "rb") as f:
    upload_resp = httpx.put(
        upload_url,
        content=f.read(),
        headers=required_headers
    )
    upload_resp.raise_for_status()

# Step 3: (Optional) Finalize if webhook not available
client.v1.artifact.finalize(
    artifact_id=artifact_id,
    bucket=presign_resp.bucket,
    key=presign_resp.key
)

print(f"Uploaded artifact: {artifact_id}")
```

### 2. Add Artifacts to Corpus

```python
# Get current corpus state
corpus = client.v1.corpus.get("corp-123")

# Add new artifact while preserving existing ones
updated_artifacts = corpus.corpus.artifact_ids + [artifact_id]

# Update corpus
client.v1.corpus.update(
    corpus_id="corp-123",
    name=corpus.corpus.name,
    description=corpus.corpus.description,
    artifact_ids=updated_artifacts
)
```

### 3. Remove Artifacts from Corpus

```python
# Get current state
corpus = client.v1.corpus.get("corp-123")

# Remove specific artifact
artifact_to_remove = "art-old-001"
updated_artifacts = [
    aid for aid in corpus.corpus.artifact_ids 
    if aid != artifact_to_remove
]

# Update
client.v1.corpus.update(
    corpus_id="corp-123",
    name=corpus.corpus.name,
    description=corpus.corpus.description,
    artifact_ids=updated_artifacts
)
```

## Common Patterns

### Building a Knowledge Base from Scratch

Complete workflow for creating a corpus with documents:

```python
def build_knowledge_base(name: str, description: str, file_paths: list[str]):
    """Create a corpus from local files."""
    
    # 1. Create empty corpus
    corpus_resp = client.v1.corpus.create(
        name=name,
        description=description,
        artifact_ids=[]
    )
    corpus_id = corpus_resp.corpus.id
    print(f"Created corpus: {corpus_id}")
    
    # 2. Upload all files
    artifact_ids = []
    for file_path in file_paths:
        # Get file info
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        content_type = guess_content_type(file_name)
        
        # Presign
        presign = client.v1.artifact.presign(
            file_name=file_name,
            content_type=content_type,
            size_bytes=file_size
        )
        
        # Upload to S3
        with open(file_path, "rb") as f:
            httpx.put(
                presign.upload_url,
                content=f.read(),
                headers=presign.required_headers
            ).raise_for_status()
        
        artifact_ids.append(presign.id)
        print(f"  Uploaded: {file_name}")
    
    # 3. Associate artifacts with corpus
    client.v1.corpus.update(
        corpus_id=corpus_id,
        name=name,
        description=description,
        artifact_ids=artifact_ids
    )
    
    print(f"✓ Knowledge base ready with {len(artifact_ids)} files")
    return corpus_id

# Usage
corpus_id = build_knowledge_base(
    name="Engineering Docs",
    description="Technical documentation",
    file_paths=["manual.pdf", "specs.md", "api-guide.pdf"]
)
```

### Sharing Knowledge Across Mindspaces

One corpus can serve multiple mindspaces:

```python
# Create shared knowledge base
shared_kb = client.v1.corpus.create(
    name="Company Handbook",
    description="Policies, benefits, and guidelines",
    artifact_ids=handbook_artifacts
)
kb_id = shared_kb.corpus.id

# Share with engineering team
eng_space = client.v1.mindspace.create(
    name="Engineering Team",
    type="group",
    corpus_ids=[kb_id],  # Has access to handbook
    user_ids=eng_team_members
)

# Share with sales team
sales_space = client.v1.mindspace.create(
    name="Sales Team",
    type="group",
    corpus_ids=[kb_id],  # Also has access to handbook
    user_ids=sales_team_members
)
```

### Multi-Corpus Strategy

Attach multiple specialized corpus to a mindspace:

```python
# Create domain-specific corpus
general_kb = client.v1.corpus.create(
    name="General Knowledge",
    description="Company-wide information",
    artifact_ids=general_docs
)

tech_kb = client.v1.corpus.create(
    name="Technical Specs",
    description="Architecture and design docs",
    artifact_ids=tech_docs
)

product_kb = client.v1.corpus.create(
    name="Product Info",
    description="Features and roadmap",
    artifact_ids=product_docs
)

# Combine in a mindspace
mindspace = client.v1.mindspace.create(
    name="Product Engineering Team",
    type="group",
    corpus_ids=[
        general_kb.corpus.id,   # Company info
        tech_kb.corpus.id,      # Technical context
        product_kb.corpus.id    # Product context
    ],
    user_ids=team_members
)
```

### Incremental Updates

Add documents to a corpus over time:

```python
def add_document_to_corpus(corpus_id: str, file_path: str):
    """Add a single document to existing corpus."""
    
    # Upload artifact
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    presign = client.v1.artifact.presign(
        file_name=file_name,
        content_type=guess_content_type(file_name),
        size_bytes=file_size
    )
    
    with open(file_path, "rb") as f:
        httpx.put(
            presign.upload_url,
            content=f.read(),
            headers=presign.required_headers
        ).raise_for_status()
    
    # Get current corpus
    corpus = client.v1.corpus.get(corpus_id)
    
    # Add to artifact list
    updated_artifacts = corpus.corpus.artifact_ids + [presign.id]
    
    # Update corpus
    client.v1.corpus.update(
        corpus_id=corpus_id,
        name=corpus.corpus.name,
        description=corpus.corpus.description,
        artifact_ids=updated_artifacts
    )
    
    print(f"Added {file_name} to corpus {corpus_id}")

# Usage
add_document_to_corpus("corp-123", "new-policy.pdf")
```

## Design Guidance

### When to Use Corpus

**Use corpus when:**
- ✅ AI needs to reference specific documents
- ✅ Building domain-specific assistants
- ✅ Implementing RAG workflows
- ✅ Creating knowledge-based chat agents

**Don't use corpus for:**
- ❌ Real-time data that changes rapidly
- ❌ Transactional data (use APIs instead)
- ❌ User-generated content in conversations (stored in mindspace automatically)

### Corpus Organization Strategies

#### Strategy 1: One Corpus per Domain

```python
# Separate corpus for different knowledge domains
hr_corpus = client.v1.corpus.create(
    name="HR Policies",
    description="Benefits, leave, conduct"
)

eng_corpus = client.v1.corpus.create(
    name="Engineering Docs",
    description="Architecture, APIs, guides"
)

sales_corpus = client.v1.corpus.create(
    name="Sales Materials",
    description="Decks, case studies, pricing"
)
```

#### Strategy 2: One Corpus per Customer (Multi-tenant)

```python
def setup_customer_knowledge(customer_id: str, customer_name: str):
    """Create isolated corpus for each customer."""
    corpus = client.v1.corpus.create(
        name=f"{customer_name} Knowledge Base",
        description=f"Custom docs for {customer_name}",
        artifact_ids=get_customer_documents(customer_id)
    )
    return corpus.corpus.id
```

#### Strategy 3: Hierarchical (General + Specific)

```python
# General company knowledge (all teams)
company_corpus = client.v1.corpus.create(
    name="Company Knowledge",
    description="Shared across all teams"
)

# Team-specific knowledge
team_corpus = client.v1.corpus.create(
    name="Engineering Team Docs",
    description="Technical content"
)

# Combine in mindspace
mindspace = client.v1.mindspace.create(
    name="Engineering Chat",
    type="group",
    corpus_ids=[company_corpus.corpus.id, team_corpus.corpus.id]
)
```

## Best Practices

### 1. Keep Corpus Focused

Each corpus should have a clear purpose:

```python
# Good: Focused corpus
client.v1.corpus.create(
    name="API Documentation",
    description="REST API reference and guides"
)

# Avoid: Overly broad corpus
# Don't mix unrelated docs in one corpus
```

### 2. Use Descriptive Names

Make it clear what knowledge the corpus contains:

```python
# Good naming
"Customer Support Knowledge Base"
"Product Engineering Specs"
"Sales Training Materials"

# Avoid vague names
"Documents"
"Files"
"KB1"
```

### 3. Manage Artifact Lifecycles

Clean up outdated documents:

```python
# Regularly review and remove outdated artifacts
corpus = client.v1.corpus.get("corp-123")

# Filter out expired/deprecated artifacts
updated_artifacts = [
    aid for aid in corpus.corpus.artifact_ids
    if not is_deprecated(aid)
]

client.v1.corpus.update(
    corpus_id="corp-123",
    name=corpus.corpus.name,
    description=corpus.corpus.description,
    artifact_ids=updated_artifacts
)
```

### 4. Consider Access Patterns

- **Public knowledge** - Same corpus for all mindspaces
- **Team knowledge** - One corpus per team, shared in team mindspaces
- **Customer knowledge** - One corpus per customer (multi-tenant isolation)

### 5. Error Handling

```python
try:
    corpus = client.v1.corpus.create(
        name="Knowledge Base",
        description="Documentation"
    )
except Exception as e:
    print(f"Failed to create corpus: {e}")
```

## API Reference

### `create()`

Create a new corpus.

**Parameters:**
- `name` (str, required): Corpus name
- `description` (str, required): Corpus description
- `artifact_ids` (list[str], optional): Initial artifact IDs (default: [])

**Returns:** `CreateCorpusResponse`

---

### `get()`

Get corpus by ID.

**Parameters:**
- `corpus_id` (str, required): Corpus ID

**Returns:** `GetCorpusResponse`

---

### `list()`

List corpus, optionally filtered by user.

**Parameters:**
- `user_id` (str, optional): Filter by creator user ID

**Returns:** `ListCorpusResponse`

---

### `update()`

Update an existing corpus.

**Parameters:**
- `corpus_id` (str, required): Corpus ID to update
- `name` (str, required): Updated name
- `description` (str, required): Updated description
- `artifact_ids` (list[str], required): Updated artifact list (replaces existing)

**Returns:** `UpdateCorpusResponse`

---

### `delete()`

Delete a corpus.

**Parameters:**
- `corpus_id` (str, required): Corpus ID to delete

**Returns:** `DeleteCorpusResponse`

## Related Resources

- [Artifact Resource Guide](file:///Users/berry/centrifugo/AGD_Magick_Mind_SDK/docs/resources/artifact.md) - Uploading and managing files
- [Mindspace Resource Guide](file:///Users/berry/centrifugo/AGD_Magick_Mind_SDK/docs/resources/mindspace.md) - Attaching corpus to conversations
- [Corpus Example](file:///Users/berry/centrifugo/AGD_Magick_Mind_SDK/examples/corpus_example.py) - Complete usage examples
