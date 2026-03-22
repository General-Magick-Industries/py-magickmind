# Artifact Resource

The Artifact resource provides file upload capabilities using presigned S3 URLs and webhook-based completion confirmation.

## Overview

The artifact upload flow follows modern best practices:

1. **Request presigned URL** from the backend
2. **Upload file directly to S3** using the presigned URL
3. **Webhook confirmation** (automatic via S3 Lambda trigger)
4. **Query artifact metadata** after upload completes

## Architecture

```
Client → Magick Mind API (presign) → S3 (upload) → Lambda → Webhook → Artifact Service
```

- **Presigned URLs**: Secure, time-limited upload URLs that keep file data off application servers
- **Direct S3 Upload**: Files stream directly to S3, making it scalable for large files
- **Webhook Completion**: S3 triggers Lambda which calls webhook to confirm upload
- **Client Finalize**: Fallback method for local development when webhooks aren't available

## Quick Start

### Simple Upload

```python
from magick_mind import MagickMind

client = MagickMind(
    email="user@example.com",
    password="password",
    base_url="https://api.example.com"
)

# Upload a file (all-in-one convenience method)
presign_resp, upload_resp = client.v1.artifact.upload_file(
    file_path="./document.pdf",
    content_type="application/pdf",
    corpus_id="corpus-123"
)

print(f"Uploaded! Artifact ID: {presign_resp.id}")
```

### Manual Upload Flow

```python
# Step 1: Get presigned URL
presign_resp = client.v1.artifact.presign_upload(
    file_name="document.pdf",
    content_type="application/pdf",
    size_bytes=1024000,
    corpus_id="corpus-123"
)

# Step 2: Upload to S3
with open("document.pdf", "rb") as f:
    requests.put(
        presign_resp.upload_url,
        data=f,
        headers=presign_resp.required_headers
    )

# Step 3: Webhook handles completion automatically
# Or use finalize() in local dev:
client.v1.artifact.finalize(
    artifact_id=presign_resp.id,
    bucket=presign_resp.bucket,
    key=presign_resp.key,
    corpus_id="corpus-123"
)
```

## API Reference

### `presign_upload()`

Get a presigned S3 URL for uploading a file.

**Parameters:**
- `file_name` (str, required): Name of the file to upload
- `content_type` (str, required): MIME type (e.g., `"application/pdf"`)
- `size_bytes` (int, required): File size in bytes
- `end_user_id` (str, optional): End user identifier
- `corpus_id` (str, optional): Corpus to associate artifact with

**Returns:** `PresignArtifactResponse`

**Example:**
```python
response = client.v1.artifact.presign_upload(
    file_name="report.pdf",
    content_type="application/pdf",
    size_bytes=2048000
)
```

### `upload_file()`

Convenience method that combines presign and upload.

**Parameters:**
- `file_path` (str, required): Path to file to upload
- `content_type` (str, required): MIME type
- `end_user_id` (str, optional): End user identifier
- `corpus_id` (str, optional): Corpus to associate artifact with

**Returns:** `tuple[PresignArtifactResponse, requests.Response]`

**Example:**
```python
presign_resp, upload_resp = client.v1.artifact.upload_file(
    file_path="./data.json",
    content_type="application/json",
    corpus_id="corpus-456"
)
```

### `get()`

Retrieve artifact metadata by ID.

**Parameters:**
- `artifact_id` (str, required): Artifact ID to retrieve

**Returns:** `Artifact`

**Example:**
```python
artifact = client.v1.artifact.get(artifact_id="art-123")
print(f"Status: {artifact.status}")
print(f"S3 URL: {artifact.s3_url}")
```

### `list()`

Query artifacts with optional filters.

**Parameters:**
- `corpus_id` (str, optional): Filter by corpus
- `end_user_id` (str, optional): Filter by end user
- `status` (str, optional): Filter by status (`uploaded`, `processing`, `ready`, `failed`)

**Returns:** `list[Artifact]`

**Example:**
```python
# All artifacts for a corpus
artifacts = client.v1.artifact.list(corpus_id="corpus-123")

# Ready artifacts only
ready = client.v1.artifact.list(status="ready")
```

### `delete()`

Delete an artifact.

**Parameters:**
- `artifact_id` (str, required): Artifact ID to delete

**Returns:** None

**Example:**
```python
client.v1.artifact.delete(artifact_id="art-123")
```

### `finalize()`

Client-driven finalize (fallback for local development).

**Parameters:**
- `artifact_id` (str, required): Artifact ID from presign response
- `bucket` (str, required): S3 bucket name
- `key` (str, required): S3 object key
- `version_id` (str, optional): S3 version ID
- `size_bytes` (int, optional): Uploaded file size
- `content_type` (str, optional): Content type
- `etag` (str, optional): S3 ETag
- `checksum_sha256` (str, optional): SHA256 checksum
- `corpus_id` (str, optional): Corpus ID

**Returns:** `FinalizeArtifactResponse`

**Example:**
```python
response = client.v1.artifact.finalize(
    artifact_id=presign_resp.id,
    bucket=presign_resp.bucket,
    key=presign_resp.key,
    corpus_id="corpus-123"
)
```

## Models

### `Artifact`

Canonical artifact model representing an uploaded file.

**Fields:**
- `id` (str): Unique artifact identifier
- `bucket` (str): S3 bucket name
- `key` (str): S3 object key
- `s3_url` (str): S3 URL (`s3://bucket/key`)
- `content_type` (str): MIME type
- `size_bytes` (int): File size in bytes
- `status` (str): Artifact status
- `corpus_id` (str, optional): Associated corpus
- `end_user_id` (str, optional): Uploader's end user ID
- `created_at` (int, optional): Creation timestamp
- `updated_at` (int, optional): Last update timestamp

## Best Practices

### 1. Use `upload_file()` for Simplicity

The convenience method handles presigning and upload in one call:

```python
presign_resp, upload_resp = client.v1.artifact.upload_file(
    file_path="./file.pdf",
    content_type="application/pdf"
)
```

### 2. Check Upload Status

Always verify the S3 upload succeeded:

```python
if upload_resp.status_code == 200:
    print("Upload successful!")
else:
    print(f"Upload failed: {upload_resp.status_code}")
```

### 3. Use Webhooks in Production

In production, S3 Lambda webhooks handle completion automatically. Only use `finalize()` in local development.

### 4. Monitor Artifact Status

After upload, artifacts may be in different states:

```python
artifact = client.v1.artifact.get(artifact_id=id)

if artifact.status == "ready":
    # Artifact is ready for use
    process_artifact(artifact.s3_url)
elif artifact.status == "processing":
    # Still being processed (e.g., RAG ingestion)
    print("Please wait...")
elif artifact.status == "failed":
    # Upload or processing failed
    print(f"Error: {artifact.error_code}")
```

### 5. Associate with Corpus

Always associate artifacts with a corpus for organization:

```python
presign_resp = client.v1.artifact.presign_upload(
    file_name="doc.pdf",
    content_type="application/pdf",
    size_bytes=1000000,
    corpus_id="corpus-123"  # Associate with corpus
)
```

## Local Development

When running locally without S3 Lambda webhooks, use the finalize method:

```python
# Upload file
presign_resp, _ = client.v1.artifact.upload_file(...)

# Manually finalize
client.v1.artifact.finalize(
    artifact_id=presign_resp.id,
    bucket=presign_resp.bucket,
    key=presign_resp.key,
    corpus_id="corpus-123"
)
```

## Error Handling

```python
from requests.exceptions import HTTPError

try:
    presign_resp, upload_resp = client.v1.artifact.upload_file(
        file_path="./file.pdf",
        content_type="application/pdf"
    )
    upload_resp.raise_for_status()
    print(f"Success! Artifact ID: {presign_resp.id}")
    
except HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed")
    elif e.response.status_code == 413:
        print("File too large")
    else:
        print(f"Upload failed: {e}")
except FileNotFoundError:
    print("File not found")
```

## Chat Attachments

Artifacts can be attached to chat messages for document analysis, image understanding, and more.

### Basic Flow

```python
# Step 1: Upload artifact
presign_resp, upload_resp = client.v1.artifact.upload_file(
    file_path="./financial_report.pdf",
    content_type="application/pdf"
)

# Step 2: Send chat with artifact attached
chat_response = client.v1.chat.send(
    api_key="sk-...",
    mindspace_id="mind-123",
    message="Summarize the key findings from this report",
    enduser_id="user-456",
    artifact_ids=[presign_resp.id]  # Attach the artifact
)

print(chat_response.content.content)  # AI summary
```

### Multiple Attachments

```python
# Upload multiple files
doc1_resp, _ = client.v1.artifact.upload_file(
    file_path="./report1.pdf",
    content_type="application/pdf"
)

doc2_resp, _ = client.v1.artifact.upload_file(
    file_path="./report2.pdf",
    content_type="application/pdf"
)

# Send chat with both attached
response = client.v1.chat.send(
    api_key="sk-...",
    mindspace_id="mind-123",
    message="Compare these two reports and highlight differences",
    enduser_id="user-456",
    artifact_ids=[doc1_resp.id, doc2_resp.id]
)
```

### Reusing Artifacts

Artifacts are first-class resources that can be reused across multiple chats:

```python
# Upload once
artifact_resp, _ = client.v1.artifact.upload_file(
    file_path="./company_handbook.pdf",
    content_type="application/pdf"
)

# Use in multiple chat messages
response1 = client.v1.chat.send(
    message="What's the vacation policy?",
    artifact_ids=[artifact_resp.id],
    # ... other params
)

response2 = client.v1.chat.send(
    message="What about remote work policies?",
    artifact_ids=[artifact_resp.id],  # Same artifact
    # ... other params
)
```

### Benefits

- ✅ **Efficient**: Upload once, reference many times
- ✅ **Scalable**: Large files don't bloat message payloads
- ✅ **Manageable**: Artifacts have independent lifecycle (list, delete, etc.)
- ✅ **Flexible**: Mix different file types in one message

## See Also


- [ADR-004: Upload and Notifications](../../bifrost/docs/adr/ADR-004-upload-and-notifications.md)
- [Example Code](../examples/artifact_example.py)
