"""Tests for artifact models."""

import pytest
from pydantic import ValidationError

from magick_mind.models.v1.artifact import (
    Artifact,
    ArtifactWebhookPayload,
    FinalizeArtifactRequest,
    GetArtifactResponse,
    ListArtifactsResponse,
    PresignArtifactRequest,
    PresignArtifactResponse,
)


class TestPresignArtifactRequest:
    """Test PresignArtifactRequest model."""

    def test_valid_request(self):
        """Test creating a valid presign request."""
        request = PresignArtifactRequest(
            file_name="document.pdf",
            content_type="application/pdf",
            size_bytes=1024000,
            end_user_id="user-123",
            corpus_id="corpus-456",
        )

        assert request.file_name == "document.pdf"
        assert request.content_type == "application/pdf"
        assert request.size_bytes == 1024000
        assert request.end_user_id == "user-123"
        assert request.corpus_id == "corpus-456"

    def test_minimal_request(self):
        """Test creating a minimal presign request."""
        request = PresignArtifactRequest(
            file_name="test.txt", content_type="text/plain", size_bytes=100
        )

        assert request.file_name == "test.txt"
        assert request.content_type == "text/plain"
        assert request.size_bytes == 100
        assert request.end_user_id is None
        assert request.corpus_id is None

    def test_invalid_size_bytes(self):
        """Test that size_bytes must be greater than 0."""
        with pytest.raises(ValidationError):
            PresignArtifactRequest(
                file_name="test.txt", content_type="text/plain", size_bytes=0
            )

        with pytest.raises(ValidationError):
            PresignArtifactRequest(
                file_name="test.txt", content_type="text/plain", size_bytes=-100
            )

    def test_missing_required_fields(self):
        """Test that required fields must be provided."""
        with pytest.raises(ValidationError):
            PresignArtifactRequest(content_type="text/plain", size_bytes=100)

        with pytest.raises(ValidationError):
            PresignArtifactRequest(file_name="test.txt", size_bytes=100)

        with pytest.raises(ValidationError):
            PresignArtifactRequest(file_name="test.txt", content_type="text/plain")


class TestPresignArtifactResponse:
    """Test PresignArtifactResponse model."""

    def test_valid_response(self):
        """Test creating a valid presign response."""
        response = PresignArtifactResponse(
            success=True,
            message="ok",
            id="art-123",
            bucket="test-bucket",
            key="artifacts/test.pdf",
            s3_url="s3://test-bucket/artifacts/test.pdf",
            upload_url="https://s3.amazonaws.com/test-bucket/artifacts/test.pdf?signature=...",
            expires_at=1700000000,
            required_headers={"Content-Type": "application/pdf"},
        )

        assert response.success is True
        assert response.id == "art-123"
        assert response.bucket == "test-bucket"
        assert response.key == "artifacts/test.pdf"
        assert "s3://" in response.s3_url
        assert "https://" in response.upload_url
        assert response.expires_at == 1700000000
        assert response.required_headers["Content-Type"] == "application/pdf"


class TestArtifact:
    """Test Artifact model."""

    def test_valid_artifact(self):
        """Test creating a valid artifact."""
        artifact = Artifact(
            id="art-123",
            bucket="test-bucket",
            key="artifacts/doc.pdf",
            s3_url="s3://test-bucket/artifacts/doc.pdf",
            content_type="application/pdf",
            size_bytes=2048000,
            status="ready",
            corpus_id="corpus-456",
            end_user_id="user-789",
            created_by="account-123",
            created_at=1700000000,
            updated_at=1700000100,
        )

        assert artifact.id == "art-123"
        assert artifact.bucket == "test-bucket"
        assert artifact.status == "ready"
        assert artifact.size_bytes == 2048000

    def test_minimal_artifact(self):
        """Test creating a minimal artifact."""
        artifact = Artifact(
            id="art-123",
            bucket="bucket",
            key="key",
            s3_url="s3://bucket/key",
            content_type="text/plain",
            size_bytes=100,
            status="uploaded",
        )

        assert artifact.id == "art-123"
        assert artifact.corpus_id is None
        assert artifact.etag is None
        assert artifact.version_id is None

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        artifact = Artifact(
            id="art-123",
            bucket="bucket",
            key="key",
            s3_url="s3://bucket/key",
            content_type="text/plain",
            size_bytes=100,
            status="ready",
            custom_field="custom_value",  # Extra field
        )

        # Should not raise error
        assert artifact.id == "art-123"


class TestGetArtifactResponse:
    """Test GetArtifactResponse model."""

    def test_valid_response(self):
        """Test creating a valid get response."""
        response = GetArtifactResponse(
            success=True,
            message="ok",
            artifact=Artifact(
                id="art-123",
                bucket="bucket",
                key="key",
                s3_url="s3://bucket/key",
                content_type="text/plain",
                size_bytes=100,
                status="ready",
            ),
        )

        assert response.success is True
        assert response.artifact.id == "art-123"


class TestListArtifactsResponse:
    """Test ListArtifactsResponse model."""

    def test_valid_response(self):
        """Test creating a valid list response."""
        response = ListArtifactsResponse(
            success=True,
            message="ok",
            artifacts=[
                Artifact(
                    id="art-1",
                    bucket="bucket",
                    key="key1",
                    s3_url="s3://bucket/key1",
                    content_type="text/plain",
                    size_bytes=100,
                    status="ready",
                ),
                Artifact(
                    id="art-2",
                    bucket="bucket",
                    key="key2",
                    s3_url="s3://bucket/key2",
                    content_type="application/pdf",
                    size_bytes=2000,
                    status="processing",
                ),
            ],
        )

        assert response.success is True
        assert len(response.artifacts) == 2
        assert response.artifacts[0].id == "art-1"
        assert response.artifacts[1].id == "art-2"

    def test_empty_list(self):
        """Test creating a response with empty artifact list."""
        response = ListArtifactsResponse(success=True, message="ok", artifacts=[])

        assert response.success is True
        assert len(response.artifacts) == 0


class TestFinalizeArtifactRequest:
    """Test FinalizeArtifactRequest model."""

    def test_valid_request(self):
        """Test creating a valid finalize request."""
        request = FinalizeArtifactRequest(
            artifact_id="art-123",
            bucket="bucket",
            key="key",
            version_id="v123",
            size_bytes=1000,
            content_type="text/plain",
            etag="etag-123",
            checksum_sha256="sha256-hash",
        )

        assert request.artifact_id == "art-123"
        assert request.bucket == "bucket"
        assert request.key == "key"
        assert request.version_id == "v123"

    def test_minimal_request(self):
        """Test creating a minimal finalize request."""
        request = FinalizeArtifactRequest(
            artifact_id="art-123", bucket="bucket", key="key"
        )

        assert request.artifact_id == "art-123"
        assert request.version_id is None
        assert request.etag is None


class TestArtifactWebhookPayload:
    """Test ArtifactWebhookPayload model."""

    def test_valid_payload(self):
        """Test creating a valid webhook payload."""
        payload = ArtifactWebhookPayload(
            artifact_id="art-123",
            corpus_id="corpus-456",
            bucket="bucket",
            key="key",
            version_id="v1",
            size_bytes=1000,
            content_type="application/pdf",
            etag="etag-123",
            checksum_sha256="sha256",
            status="uploaded",
        )

        assert payload.artifact_id == "art-123"
        assert payload.corpus_id == "corpus-456"
        assert payload.status == "uploaded"

    def test_failed_status_with_error(self):
        """Test webhook payload for failed upload."""
        payload = ArtifactWebhookPayload(
            artifact_id="art-123",
            bucket="bucket",
            key="key",
            status="failed",
            error_code="S3_UPLOAD_FAILED",
        )

        assert payload.status == "failed"
        assert payload.error_code == "S3_UPLOAD_FAILED"
