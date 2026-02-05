"""
Example demonstrating Corpus resource operations.

This example shows how to create, read, update, and delete corpus
(knowledge bases) using the Magick Mind SDK.
"""

from magick_mind import MagickMind

# Initialize client
client = MagickMind(
    email="your-email@example.com",
    password="your-password",
    base_url="https://api.example.com",
)

# 1. Create a new corpus
print("Creating a new corpus...")
create_resp = client.v1.corpus.create(
    name="Research Papers",
    description="Collection of AI research papers for RAG",
    artifact_ids=[],  # Empty initially
)
print(f"Created corpus: {create_resp.id}")
print(f"  Name: {create_resp.name}")
print(f"  Description: {create_resp.description}")
print()

corpus_id = create_resp.id

# 2. Get corpus by ID
print(f"Retrieving corpus {corpus_id}...")
get_resp = client.v1.corpus.get(corpus_id)
print(f"Retrieved corpus: {get_resp.name}")
print(f"  Created at: {get_resp.created_at}")
print()

# 3. Update corpus (e.g., add artifacts)
print(f"Updating corpus {corpus_id}...")
# Note: In real usage, you'd get artifact_ids from uploading files
# via client.v1.artifact.presign() and uploading to S3
update_resp = client.v1.corpus.update(
    corpus_id=corpus_id,
    name="AI Research Papers",
    description="Curated collection of AI and ML research papers",
    artifact_ids=["artifact-123", "artifact-456"],  # Example artifact IDs
)
print(f"Updated corpus: {update_resp.name}")
print(f"  Artifacts: {len(update_resp.artifact_ids)} files")
print()

# 4. List all corpus
print("Listing all corpus...")
list_resp = client.v1.corpus.list()
print(f"Found {len(list_resp.data)} corpus(es):")
for corpus in list_resp.data:
    print(f"  - {corpus.name} ({corpus.id})")
    print(f"    Description: {corpus.description}")
    print(f"    Artifacts: {len(corpus.artifact_ids)}")
    print(
        f"    Paging: next={list_resp.paging.cursors.after}, has_more={list_resp.paging.has_more}"
    )
print()

# 5. Delete corpus
print(f"Deleting corpus {corpus_id}...")
client.v1.corpus.delete(corpus_id)
print("Corpus deleted successfully (returns None)")
print()

# Complete workflow example: Create corpus with artifacts
print("=" * 70)
print("Complete workflow: Creating a corpus with uploaded artifacts")
print("=" * 70)

# Step 1: Upload some files and get artifact IDs
print("\n1. Uploading artifacts...")
# Example: presign and upload two files

artifact_ids = []

# In a real scenario, you'd upload actual files here
# For demonstration, we'll show the flow:
example_files = [
    {"name": "paper1.pdf", "content_type": "application/pdf", "size": 1024000},
    {"name": "paper2.pdf", "content_type": "application/pdf", "size": 2048000},
]

for file_info in example_files:
    print(f"  - Would upload: {file_info['name']}")
    # presign_resp = client.v1.artifact.presign(
    #     file_name=file_info['name'],
    #     content_type=file_info['content_type'],
    #     size_bytes=file_info['size'],
    # )
    # Upload to presign_resp.upload_url using requests/httpx
    # artifact_ids.append(presign_resp.id)

# Mock artifact IDs for this example
artifact_ids = ["art-demo-001", "art-demo-002"]
print(f"  Uploaded {len(artifact_ids)} artifacts")

# Step 2: Create corpus with uploaded artifacts
print("\n2. Creating corpus with artifacts...")
workflow_corpus = client.v1.corpus.create(
    name="ML Papers Collection",
    description="Machine learning research papers for semantic search",
    artifact_ids=artifact_ids,
)
print(f"  Created: {workflow_corpus.name}")
print(f"  Corpus ID: {workflow_corpus.id}")
print(f"  Contains {len(workflow_corpus.artifact_ids)} artifacts")

# Step 3: Use corpus for RAG queries
print("\n3. Corpus is now ready for RAG queries!")
print(f"  You can reference corpus_id '{workflow_corpus.id}' in chat messages")
print("  for retrieval-augmented generation.")

print("\n✅ Corpus example completed!")
