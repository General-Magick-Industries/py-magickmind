"""
Artifact resource example for Magick Mind SDK.

Demonstrates the complete file upload flow using presigned S3 URLs:
1. Obtain presigned URL
2. Upload file to S3
3. Monitor artifact status
4. Query and manage artifacts
"""

import os
import time

from magick_mind import MagickMind


def main():
    """Run artifact resource examples."""
    # Initialize the client
    client = MagickMind(
        email=os.getenv("MAGICK_MIND_EMAIL", "user@example.com"),
        password=os.getenv("MAGICK_MIND_PASSWORD", "your_password"),
        base_url=os.getenv("MAGICK_MIND_BASE_URL", "http://localhost:8080"),
    )

    print("=" * 60)
    print("Magick Mind SDK - Artifact Resource Examples")
    print("=" * 60)

    # Example 1: Presign Upload (Manual)
    print("\n1. Presign Upload (Manual Flow)")
    print("-" * 60)

    presign_resp = client.v1.artifact.presign_upload(
        file_name="example-document.pdf",
        content_type="application/pdf",
        size_bytes=1024000,  # 1MB
        corpus_id="corpus-123",
        end_user_id="user-456",
    )

    print("✅ Presign URL obtained")
    print(f"   Artifact ID: {presign_resp.id}")
    print(f"   S3 Bucket: {presign_resp.bucket}")
    print(f"   S3 Key: {presign_resp.key}")
    print(f"   Upload URL: {presign_resp.upload_url[:60]}...")
    print(f"   Expires at: {presign_resp.expires_at}")
    print(f"   Required Headers: {presign_resp.required_headers}")

    # Simulate file upload to S3 (you would use real file data)
    print("\n📤 Uploading to S3...")
    # fake_file_data = b"PDF content here..." * 1000
    # upload_response = requests.put(
    #     presign_resp.upload_url,
    #     data=fake_file_data,
    #     headers=presign_resp.required_headers
    # )
    # print(f"   Upload status: {upload_response.status_code}")

    # Example 2: Upload File (Convenience Method)
    print("\n2. Upload File (Convenience Method)")
    print("-" * 60)

    # Create a temporary test file
    test_file_path = "/tmp/test-upload.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file for artifact upload.\n" * 100)

    try:
        presign_resp, upload_resp = client.v1.artifact.upload_file(
            file_path=test_file_path,
            content_type="text/plain",
            corpus_id="corpus-123",
            end_user_id="user-456",
        )

        print("✅ File uploaded successfully")
        print(f"   Artifact ID: {presign_resp.id}")
        print(f"   Upload Status: {upload_resp.status_code}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

    # Example 3: Get Artifact
    print("\n3. Get Artifact by ID")
    print("-" * 60)

    try:
        artifact = client.v1.artifact.get(artifact_id=presign_resp.id)
        print(f"✅ Retrieved artifact: {artifact.id}")
        print(f"   Status: {artifact.status}")
        print(f"   S3 URL: {artifact.s3_url}")
        print(f"   Content Type: {artifact.content_type}")
        print(f"   Size: {artifact.size_bytes} bytes")
    except Exception as e:
        print(f"❌ Get failed: {e}")

    # Example 4: List Artifacts
    print("\n4. List Artifacts")
    print("-" * 60)

    try:
        # List all artifacts for a corpus
        artifacts = client.v1.artifact.list(corpus_id="corpus-123")
        print(f"✅ Found {len(artifacts)} artifacts for corpus-123")
        for artifact in artifacts[:5]:  # Show first 5
            print(f"   - {artifact.id}: {artifact.status} ({artifact.content_type})")

        # List by status
        ready_artifacts = client.v1.artifact.list(status="ready")
        print(f"\n✅ Found {len(ready_artifacts)} ready artifacts")

        # List by end user
        user_artifacts = client.v1.artifact.list(end_user_id="user-456")
        print(f"✅ Found {len(user_artifacts)} artifacts for user-456")
    except Exception as e:
        print(f"❌ List failed: {e}")

    # Example 5: Client Finalize (Fallback)
    print("\n5. Client Finalize (Fallback)")
    print("-" * 60)

    try:
        finalize_resp = client.v1.artifact.finalize(
            artifact_id=presign_resp.id,
            bucket=presign_resp.bucket,
            key=presign_resp.key,
            corpus_id="corpus-123",
            size_bytes=1024000,
            content_type="application/pdf",
            etag="mock-etag-12345",
        )
        print("✅ Finalized artifact")
        print(f"   Success: {finalize_resp.success}")
        print(f"   Message: {finalize_resp.message}")
    except Exception as e:
        print(f"❌ Finalize failed: {e}")

    # Example 6: Delete Artifact
    print("\n6. Delete Artifact")
    print("-" * 60)

    try:
        client.v1.artifact.delete(artifact_id=presign_resp.id)
        print(f"✅ Deleted artifact: {presign_resp.id}")
    except Exception as e:
        print(f"❌ Delete failed: {e}")

    # Example 7: Complete Upload Flow
    print("\n7. Complete Upload Flow")
    print("-" * 60)

    # Create a real file
    upload_file_path = "/tmp/complete-flow-test.json"
    with open(upload_file_path, "w") as f:
        f.write('{"message": "Complete upload flow test"}')

    try:
        # Step 1: Upload file
        presign_resp, upload_resp = client.v1.artifact.upload_file(
            file_path=upload_file_path,
            content_type="application/json",
            corpus_id="corpus-456",
        )
        print(f"✅ Step 1: File uploaded (Artifact ID: {presign_resp.id})")

        # Step 2: Wait for webhook processing (in real use)
        # In local dev, you might need to finalize manually
        print("⏳ Step 2: Waiting for webhook processing...")
        time.sleep(2)  # Simulate wait

        # Step 3: Check status
        artifact = client.v1.artifact.get(artifact_id=presign_resp.id)
        print(f"✅ Step 3: Artifact status: {artifact.status}")

        # Step 4: Use in application
        if artifact.status == "ready":
            print("✅ Step 4: Artifact ready for use!")
            print(f"   Access via: {artifact.s3_url}")
        else:
            print(f"⚠️  Artifact not ready yet (status: {artifact.status})")

        # Cleanup
        client.v1.artifact.delete(artifact_id=presign_resp.id)
        print("✅ Cleaned up artifact")

    except Exception as e:
        print(f"❌ Complete flow failed: {e}")
    finally:
        if os.path.exists(upload_file_path):
            os.remove(upload_file_path)

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
