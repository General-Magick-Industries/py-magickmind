"""
Example: End User Resource Usage

Demonstrates CRUD operations on end users using the Magick Mind SDK.
End users represent the actual users of applications built on the bifrost
platform in a multi-tenant architecture.
"""

import os

from magick_mind import MagickMind


def main():
    """Demonstrate end user resource operations."""
    # Initialize client
    base_url = os.getenv("MAGICK_MIND_BASE_URL", "http://localhost:8888")
    email = os.getenv("MAGICK_MIND_EMAIL", "user@example.com")
    password = os.getenv("MAGICK_MIND_PASSWORD", "your-password")

    client = MagickMind(base_url=base_url, email=email, password=password)

    print("=" * 60)
    print("End User Resource Example")
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
    retrieved = client.v1.end_user.get(end_user_id=end_user.id)
    print(f"✓ Retrieved end user: {retrieved.name}")

    # 3. Query all end users (no filters)
    print("\n3. Querying all end users...")
    all_end_users = client.v1.end_user.query()
    print(f"✓ Found {len(all_end_users)} end user(s):")
    for user in all_end_users:
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
    updated = client.v1.end_user.update(
        end_user_id=end_user.id,
        name="Jane Doe",
        external_id="ext-jane-doe-updated",
    )
    print("✓ Updated end user:")
    print(f"  Name: {updated.name}")
    print(f"  External ID: {updated.external_id}")
    print(f"  Updated by: {updated.updated_by}")
    print(f"  Updated at: {updated.updated_at}")

    # 7. Delete the end user
    print(f"\n7. Deleting end user {end_user.id}...")
    client.v1.end_user.delete(end_user_id=end_user.id)
    print("✓ End user deleted successfully")

    # Verify deletion
    print("\n8. Verifying deletion...")
    remaining_users = client.v1.end_user.query()
    print(f"✓ Remaining end users: {len(remaining_users)}")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
