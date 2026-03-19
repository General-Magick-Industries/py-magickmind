"""
Example: Resource Management

Demonstrates CRUD operations for core resources using the Magick Mind SDK:
- End Users: User identity management in multi-tenant architecture
- Projects: Organize corpus and resources for agentic SaaS backends
- Mindspaces: Central organizing concept for conversations and collaboration
- Corpus: Knowledge base and artifact management for RAG workflows

This example consolidates patterns from end_user_example.py, project_example.py,
and mindspace_example.py into a single comprehensive resource management guide.
"""

import asyncio
import os

from dotenv import load_dotenv

from magick_mind import MagickMind

load_dotenv()


async def main():
    """Demonstrate resource management operations."""
    # Initialize client
    base_url = os.getenv("MAGICKMIND_BASE_URL", "https://dev-api.magickmind.ai")
    email = os.getenv("MAGICKMIND_EMAIL", "user@example.com")
    password = os.getenv("MAGICKMIND_PASSWORD", "your-password")

    async with MagickMind(base_url=base_url, email=email, password=password) as client:
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
        end_user = await client.v1.end_user.create(
            name="John Doe",
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
        retrieved_user = await client.v1.end_user.get(end_user_id=end_user.id)
        print(f"✓ Retrieved end user: {retrieved_user.name}")

        # 3. Query all end users
        print("\n3. Querying all end users...")
        all_end_users = await client.v1.end_user.query()
        print(f"✓ Found {len(all_end_users)} end user(s):")
        for user in all_end_users[:3]:  # Show first 3
            print(f"  - {user.name} (ID: {user.id})")

        # 4. Query end users by tenant
        print(f"\n4. Querying end users for tenant {end_user.tenant_id}...")
        tenant_users = await client.v1.end_user.query()
        print(f"✓ Found {len(tenant_users)} end user(s) in this tenant")

        # 5. Query end users by external ID
        if end_user.external_id:
            print(f"\n5. Querying end user by external ID {end_user.external_id}...")
            external_users = await client.v1.end_user.query(
                external_id=end_user.external_id
            )
            if external_users:
                print(f"✓ Found end user: {external_users[0].name}")

        # 6. Update the end user
        print(f"\n6. Updating end user {end_user.id}...")
        updated_user = await client.v1.end_user.update(
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
        project = await client.v1.project.create(
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
        retrieved_project = await client.v1.project.get(project_id=project.id)
        print(f"✓ Retrieved project: {retrieved_project.name}")

        # 3. List all projects
        print("\n3. Listing all projects...")
        all_projects = await client.v1.project.list()
        print(f"✓ Found {len(all_projects)} project(s):")
        for p in all_projects[:3]:  # Show first 3
            print(f"  - {p.name} (ID: {p.id})")

        # 4. List projects by creator
        print(f"\n4. Listing projects created by {project.created_by}...")
        user_projects = await client.v1.project.list(
            created_by_user_id=project.created_by
        )
        print(f"✓ Found {len(user_projects)} project(s) by this user")

        # 5. Update the project
        print(f"\n5. Updating project {project.id}...")
        updated_project = await client.v1.project.update(
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
        private_space = await client.v1.mindspace.create(
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
        group_space = await client.v1.mindspace.create(
            name="Engineering Team",
            type="GROUP",
            description="Team collaboration space",
            corpus_ids=["corpus-1", "corpus-2"],
            participant_ids=["user-1", "user-2", "user-3"],
        )
        print(f"✓ Created group mindspace: {group_space.id}")
        print(f"  Members: {len(group_space.participant_ids)} users")

        # 3. List all mindspaces
        print("\n3. Listing all mindspaces...")
        mindspaces = await client.v1.mindspace.list()
        print(f"✓ Found {len(mindspaces.data)} mindspace(s):")
        for ms in mindspaces.data[:3]:  # Show first 3
            print(f"  - {ms.name} ({ms.type}) - {ms.id}")

        # 4. List mindspaces filtered by user
        print("\n4. Listing mindspaces for specific user...")
        user_mindspaces = await client.v1.mindspace.list(participant_id="user-1")
        print(f"✓ Found {len(user_mindspaces.data)} mindspace(s) for user-1")

        # 5. Get a specific mindspace
        print(f"\n5. Getting mindspace by ID {mindspace_id}...")
        mindspace = await client.v1.mindspace.get(mindspace_id)
        print(f"✓ Retrieved mindspace: {mindspace.name}")
        print(f"  Description: {mindspace.description}")
        print(f"  Project ID: {mindspace.project_id}")

        # 6. Update mindspace
        print(f"\n6. Updating mindspace {mindspace_id}...")
        updated_mindspace = await client.v1.mindspace.update(
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
        messages = await client.v1.mindspace.get_messages(
            mindspace_id=mindspace_id, limit=10
        )

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
                newer = await client.v1.mindspace.get_messages(
                    mindspace_id=mindspace_id,
                    after_id=messages.next_after_id,
                    limit=10,
                )
                print(f"✓ Retrieved {len(newer.chat_histories)} newer message(s)")

            # 9. Backward pagination (get older messages)
            if messages.has_older and messages.next_before_id:
                print("\n9. Getting older messages (backward pagination)...")
                older = await client.v1.mindspace.get_messages(
                    mindspace_id=mindspace_id,
                    before_id=messages.next_before_id,
                    limit=10,
                )
                print(f"✓ Retrieved {len(older.chat_histories)} older message(s)")
        else:
            print("  (No messages in this mindspace yet)")

        # ========================================================================
        # PART 4: CORPUS & ARTIFACT MANAGEMENT
        # ========================================================================
        print("\n" + "=" * 60)
        print("PART 4: Corpus & Artifact Management")
        print("=" * 60)

        # 1. Create a corpus
        print("\n1. Creating a corpus...")
        corpus = await client.v1.corpus.create(
            name="SDK Example Knowledge Base",
            description="Documents for testing artifact management",
        )
        corpus_id = corpus.id
        print(f"✓ Created corpus: {corpus_id}")
        print(f"  Name: {corpus.name}")

        # 2. Add artifacts to corpus (triggers ingestion)
        # Note: These artifact IDs would come from prior uploads via artifact.presign()
        print("\n2. Adding artifacts to corpus...")
        try:
            result = await client.v1.corpus.add_artifacts(
                corpus_id, ["artifact-001", "artifact-002"]
            )
            print(f"✓ Added {result.added_count} artifact(s)")
            if result.failed_artifact_ids:
                print(f"  Failed: {result.failed_artifact_ids}")
        except Exception as e:
            print(f"  Skipped (no real artifacts): {e}")

        # 3. Add a single artifact
        print("\n3. Adding a single artifact...")
        try:
            result = await client.v1.corpus.add_artifact(corpus_id, "artifact-003")
            print(f"✓ Added {result.added_count} artifact(s)")
        except Exception as e:
            print(f"  Skipped (no real artifact): {e}")

        # 4. List artifact statuses
        print("\n4. Listing artifact statuses...")
        try:
            statuses = await client.v1.corpus.list_artifact_statuses(corpus_id)
            print(f"✓ Found {len(statuses)} artifact status(es):")
            for s in statuses[:5]:
                print(f"  - {s.artifact_id}: {s.status}")
                if s.error:
                    print(f"    Error: {s.error}")
        except Exception as e:
            print(f"  Skipped: {e}")

        # 5. Get single artifact status
        print("\n5. Getting single artifact status...")
        try:
            status = await client.v1.corpus.get_artifact_status(
                corpus_id, "artifact-001"
            )
            print(f"✓ Status: {status.status}")
            print(f"  Content length: {status.content_length}")
            print(f"  Updated at: {status.updated_at}")
        except Exception as e:
            print(f"  Skipped: {e}")

        # 6. Remove artifact from corpus
        print("\n6. Removing artifact from corpus...")
        try:
            await client.v1.corpus.remove_artifact(corpus_id, "artifact-001")
            print("✓ Artifact removed")
        except Exception as e:
            print(f"  Skipped: {e}")

        # ========================================================================
        # CLEANUP
        # ========================================================================
        print("\n" + "=" * 60)
        print("CLEANUP")
        print("=" * 60)

        # Delete corpus
        print(f"\n0. Deleting corpus {corpus_id}...")
        try:
            await client.v1.corpus.delete(corpus_id)
            print(f"✓ Deleted corpus: {corpus_id}")
        except Exception as e:
            print(f"✗ Failed to delete corpus: {e}")

        # Delete mindspace
        print(f"\n1. Deleting mindspace {mindspace_id}...")
        try:
            await client.v1.mindspace.delete(mindspace_id)
            print(f"✓ Deleted mindspace: {mindspace_id}")
        except Exception as e:
            print(f"✗ Failed to delete mindspace: {e}")

        # Delete project
        print(f"\n2. Deleting project {project.id}...")
        try:
            await client.v1.project.delete(project_id=project.id)
            print("✓ Project deleted successfully")
        except Exception as e:
            print(f"✗ Failed to delete project: {e}")

        # Verify project deletion
        print("\n3. Verifying project deletion...")
        remaining_projects = await client.v1.project.list()
        print(f"✓ Remaining projects: {len(remaining_projects)}")

        # Delete end user
        print(f"\n4. Deleting end user {end_user.id}...")
        try:
            await client.v1.end_user.delete(end_user_id=end_user.id)
            print("✓ End user deleted successfully")
        except Exception as e:
            print(f"✗ Failed to delete end user: {e}")

        # Verify end user deletion
        print("\n5. Verifying end user deletion...")
        remaining_users = await client.v1.end_user.query()
        print(f"✓ Remaining end users: {len(remaining_users)}")

        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
