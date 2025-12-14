"""
Example: Project Resource Usage

Demonstrates CRUD operations on projects using the Magick Mind SDK.
Projects organize corpora and resources for agentic SaaS backends.
"""

import os

from magick_mind import MagickMindClient


def main():
    """Demonstrate project resource operations."""
    # Initialize client
    base_url = os.getenv("MAGICK_MIND_BASE_URL", "http://localhost:8888")
    api_key = os.getenv("MAGICK_MIND_API_KEY", "your-api-key")

    client = MagickMindClient(base_url=base_url, api_key=api_key)

    print("=" * 60)
    print("Project Resource Example")
    print("=" * 60)

    # 1. Create a new project
    print("\n1. Creating a new project...")
    project = client.v1.project.create(
        name="My Agentic Assistant",
        description="An AI-powered customer support assistant",
        corpus_ids=["corpus-123", "corpus-456"],
    )
    print(f"✓ Created project: {project.id}")
    print(f"  Name: {project.name}")
    print(f"  Description: {project.description}")
    print(f"  Corpus IDs: {project.corpus_ids}")
    print(f"  Created by: {project.created_by}")
    print(f"  Created at: {project.created_at}")

    # 2. Get the project by ID
    print(f"\n2. Retrieving project {project.id}...")
    retrieved = client.v1.project.get(project_id=project.id)
    print(f"✓ Retrieved project: {retrieved.name}")

    # 3. List all projects
    print("\n3. Listing all projects...")
    all_projects = client.v1.project.list()
    print(f"✓ Found {len(all_projects)} project(s):")
    for p in all_projects:
        print(f"  - {p.name} (ID: {p.id})")

    # 4. List projects by creator
    print(f"\n4. Listing projects created by {project.created_by}...")
    user_projects = client.v1.project.list(created_by_user_id=project.created_by)
    print(f"✓ Found {len(user_projects)} project(s) by this user")

    # 5. Update the project
    print(f"\n5. Updating project {project.id}...")
    updated = client.v1.project.update(
        project_id=project.id,
        name="Updated Agentic Assistant",
        description="Now with enhanced capabilities!",
        corpus_ids=["corpus-123", "corpus-456", "corpus-789"],
    )
    print("✓ Updated project:")
    print(f"  Name: {updated.name}")
    print(f"  Description: {updated.description}")
    print(f"  Corpus IDs: {updated.corpus_ids}")
    print(f"  Updated at: {updated.updated_at}")

    # 6. Delete the project
    print(f"\n6. Deleting project {project.id}...")
    client.v1.project.delete(project_id=project.id)
    print("✓ Project deleted successfully")

    # Verify deletion
    print("\n7. Verifying deletion...")
    remaining_projects = client.v1.project.list()
    print(f"✓ Remaining projects: {len(remaining_projects)}")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
