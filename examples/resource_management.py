"""
Example: Resource Management

Demonstrates CRUD operations for core resources using the Magick Mind SDK:
- End Users: User identity management in multi-tenant architecture
- Projects: Organize corpus and resources for agentic SaaS backends
- Mindspaces: Central organizing concept for conversations and collaboration

This example consolidates patterns from end_user_example.py, project_example.py,
and mindspace_example.py into a single comprehensive resource management guide.
"""

import os

from magick_mind import MagickMind


def main():
    """Demonstrate resource management operations."""
    # Initialize client
    base_url = os.getenv("MAGICK_MIND_BASE_URL", "http://localhost:8888")
    email = os.getenv("MAGICK_MIND_EMAIL", "user@example.com")
    password = os.getenv("MAGICK_MIND_PASSWORD", "your-password")

    client = MagickMind(base_url=base_url, email=email, password=password)

    print("=" * 60)
    print("Resource Management Example")
    print("=" * 60)

    # ========================================================================
    # PART 1: END USER MANAGEMENT
    # ========================================================================
    print("\n" + "=" * 60)
    print("PART 1: End User Management")
    print("=" * 60)

    # 1. Create a new end user
    print("\n1. Creating a new end user...")
    end_user = client.v1.end_user.create(
        name="John Doe",
        tenant_id="tenant-123",
        actor_id="admin-456",
        external_id="ext-john-doe-789",
    )
    print(f"✓ Created end user: {end_user.id}")
    print(f"  Name: {end_user.name}")
    print(f"  External ID: {end_user.external_id}")
    print(f"  Tenant ID: {end_user.tenant_id}")
    print(f"  Created by: {end_user.created_by}")
    print(f"  Created at: {end_user.created_at}")

    # 2. Get the end user by ID
    print(f"\n2. Retrieving end user {end_user.id}...")
    retrieved_user = client.v1.end_user.get(end_user_id=end_user.id)
    print(f"✓ Retrieved end user: {retrieved_user.name}")

    # 3. Query all end users
    print("\n3. Querying all end users...")
    all_end_users = client.v1.end_user.query()
    print(f"✓ Found {len(all_end_users)} end user(s):")
    for user in all_end_users[:3]:  # Show first 3
        print(f"  - {user.name} (ID: {user.id})")

    # 4. Query end users by tenant
    print(f"\n4. Querying end users for tenant {end_user.tenant_id}...")
    tenant_users = client.v1.end_user.query(tenant_id=end_user.tenant_id)
    print(f"✓ Found {len(tenant_users)} end user(s) in this tenant")

    # 5. Query end users by external ID
    if end_user.external_id:
        print(f"\n5. Querying end user by external ID {end_user.external_id}...")
        external_users = client.v1.end_user.query(external_id=end_user.external_id)
        if external_users:
            print(f"✓ Found end user: {external_users[0].name}")

    # 6. Update the end user
    print(f"\n6. Updating end user {end_user.id}...")
    updated_user = client.v1.end_user.update(
        end_user_id=end_user.id,
        name="Jane Doe",
        external_id="ext-jane-doe-updated",
    )
    print("✓ Updated end user:")
    print(f"  Name: {updated_user.name}")
    print(f"  External ID: {updated_user.external_id}")
    print(f"  Updated by: {updated_user.updated_by}")
    print(f"  Updated at: {updated_user.updated_at}")

    # ========================================================================
    # PART 2: PROJECT MANAGEMENT
    # ========================================================================
    print("\n" + "=" * 60)
    print("PART 2: Project Management")
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
    retrieved_project = client.v1.project.get(project_id=project.id)
    print(f"✓ Retrieved project: {retrieved_project.name}")

    # 3. List all projects
    print("\n3. Listing all projects...")
    all_projects = client.v1.project.list()
    print(f"✓ Found {len(all_projects)} project(s):")
    for p in all_projects[:3]:  # Show first 3
        print(f"  - {p.name} (ID: {p.id})")

    # 4. List projects by creator
    print(f"\n4. Listing projects created by {project.created_by}...")
    user_projects = client.v1.project.list(created_by_user_id=project.created_by)
    print(f"✓ Found {len(user_projects)} project(s) by this user")

    # 5. Update the project
    print(f"\n5. Updating project {project.id}...")
    updated_project = client.v1.project.update(
        project_id=project.id,
        name="Updated Agentic Assistant",
        description="Now with enhanced capabilities!",
        corpus_ids=["corpus-123", "corpus-456", "corpus-789"],
    )
    print("✓ Updated project:")
    print(f"  Name: {updated_project.name}")
    print(f"  Description: {updated_project.description}")
    print(f"  Corpus IDs: {updated_project.corpus_ids}")
    print(f"  Updated at: {updated_project.updated_at}")

    # ========================================================================
    # PART 3: MINDSPACE MANAGEMENT
    # ========================================================================
    print("\n" + "=" * 60)
    print("PART 3: Mindspace Management")
    print("=" * 60)

    # 1. Create a private mindspace
    print("\n1. Creating a private mindspace...")
    private_space = client.v1.mindspace.create(
        name="My Personal Workspace",
        type="PRIVATE",
        description="Private workspace for personal projects",
        corpus_ids=["corpus-123"],
    )
    print(f"✓ Created mindspace: {private_space.id}")
    print(f"  Name: {private_space.name}")
    print(f"  Type: {private_space.type}")
    print(f"  Corpus: {private_space.corpus_ids}")
    mindspace_id = private_space.id

    # 2. Create a group mindspace
    print("\n2. Creating a group mindspace...")
    group_space = client.v1.mindspace.create(
        name="Engineering Team",
        type="GROUP",
        description="Team collaboration space",
        corpus_ids=["corpus-1", "corpus-2"],
        user_ids=["user-1", "user-2", "user-3"],
    )
    print(f"✓ Created group mindspace: {group_space.id}")
    print(f"  Members: {len(group_space.user_ids)} users")

    # 3. List all mindspaces
    print("\n3. Listing all mindspaces...")
    mindspaces = client.v1.mindspace.list()
    print(f"✓ Found {len(mindspaces.mindspaces)} mindspace(s):")
    for ms in mindspaces.mindspaces[:3]:  # Show first 3
        print(f"  - {ms.name} ({ms.type}) - {ms.id}")

    # 4. List mindspaces filtered by user
    print("\n4. Listing mindspaces for specific user...")
    user_mindspaces = client.v1.mindspace.list(user_id="user-1")
    print(f"✓ Found {len(user_mindspaces.mindspaces)} mindspace(s) for user-1")

    # 5. Get a specific mindspace
    print(f"\n5. Getting mindspace by ID {mindspace_id}...")
    mindspace = client.v1.mindspace.get(mindspace_id)
    print(f"✓ Retrieved mindspace: {mindspace.name}")
    print(f"  Description: {mindspace.description}")
    print(f"  Project ID: {mindspace.project_id}")

    # 6. Update mindspace
    print(f"\n6. Updating mindspace {mindspace_id}...")
    updated_mindspace = client.v1.mindspace.update(
        mindspace_id=mindspace_id,
        name="My Updated Workspace",
        description="Updated description with more details",
        corpus_ids=["corpus-123", "corpus-456"],  # Add another corpus
    )
    print(f"✓ Updated mindspace: {updated_mindspace.name}")
    print(f"  New corpus count: {len(updated_mindspace.corpus_ids)}")
    print(f"  Corpus: {updated_mindspace.corpus_ids}")

    # 7. Get messages from mindspace (latest)
    print(f"\n7. Getting latest messages from mindspace {mindspace_id}...")
    messages = client.v1.mindspace.get_messages(mindspace_id=mindspace_id, limit=10)

    print(f"✓ Retrieved {len(messages.chat_histories)} message(s)")
    if messages.chat_histories:
        for msg in messages.chat_histories[:3]:  # Show first 3
            content_preview = msg.content[:50] if msg.content else ""
            print(f"  - [{msg.sent_by_user_id}]: {content_preview}...")
        print(f"  Has more: {messages.has_more}")
        print(f"  Has older: {messages.has_older}")

        # 8. Forward pagination (get newer messages)
        if messages.has_more and messages.next_after_id:
            print("\n8. Getting newer messages (forward pagination)...")
            newer = client.v1.mindspace.get_messages(
                mindspace_id=mindspace_id,
                after_id=messages.next_after_id,
                limit=10,
            )
            print(f"✓ Retrieved {len(newer.chat_histories)} newer message(s)")

        # 9. Backward pagination (get older messages)
        if messages.has_older and messages.next_before_id:
            print("\n9. Getting older messages (backward pagination)...")
            older = client.v1.mindspace.get_messages(
                mindspace_id=mindspace_id,
                before_id=messages.next_before_id,
                limit=10,
            )
            print(f"✓ Retrieved {len(older.chat_histories)} older message(s)")
    else:
        print("  (No messages in this mindspace yet)")

    # ========================================================================
    # CLEANUP
    # ========================================================================
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    # Delete mindspace
    print(f"\n1. Deleting mindspace {mindspace_id}...")
    try:
        client.v1.mindspace.delete(mindspace_id)
        print(f"✓ Deleted mindspace: {mindspace_id}")
    except Exception as e:
        print(f"✗ Failed to delete mindspace: {e}")

    # Delete project
    print(f"\n2. Deleting project {project.id}...")
    try:
        client.v1.project.delete(project_id=project.id)
        print("✓ Project deleted successfully")
    except Exception as e:
        print(f"✗ Failed to delete project: {e}")

    # Verify project deletion
    print("\n3. Verifying project deletion...")
    remaining_projects = client.v1.project.list()
    print(f"✓ Remaining projects: {len(remaining_projects)}")

    # Delete end user
    print(f"\n4. Deleting end user {end_user.id}...")
    try:
        client.v1.end_user.delete(end_user_id=end_user.id)
        print("✓ End user deleted successfully")
    except Exception as e:
        print(f"✗ Failed to delete end user: {e}")

    # Verify end user deletion
    print("\n5. Verifying end user deletion...")
    remaining_users = client.v1.end_user.query()
    print(f"✓ Remaining end users: {len(remaining_users)}")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
