"""Tests for ArtifactResourceV1."""

from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from magick_mind.models.v1.artifact import (
    Artifact,
    FinalizeArtifactResponse,
    PresignArtifactResponse,
)
from magick_mind.resources.v1.artifact import ArtifactResourceV1


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing."""
    return MagicMock()


@pytest.fixture
def artifact_resource(mock_http_client):
    """Create an ArtifactResourceV1 instance with mock HTTP client."""
    return ArtifactResourceV1(mock_http_client)


class TestPresignUpload:
    """Tests for presign_upload method."""

    def test_presign_upload_success(self, artifact_resource, mock_http_client):
        """Test successful presign upload."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "message": "ok",
            "id": "art-123",
            "bucket": "test-bucket",
            "key": "artifacts/test.pdf",
            "s3_url": "s3://test-bucket/artifacts/test.pdf",
            "upload_url": "https://s3.amazonaws.com/presigned",
            "expires_at": 1700000000,
            "required_headers": {"Content-Type": "application/pdf"},
        }
        mock_http_client.post.return_value = mock_response

        # Call method
        result = artifact_resource.presign_upload(
            file_name="test.pdf",
            content_type="application/pdf",
            size_bytes=1024000,
            corpus_id="corpus-123",
        )

        # Verify HTTP call
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == "/v1/artifacts/presign"

        # Verify result
        assert isinstance(result, PresignArtifactResponse)
        assert result.id == "art-123"
        assert result.bucket == "test-bucket"
        assert result.upload_url == "https://s3.amazonaws.com/presigned"

    def test_presign_upload_minimal(self, artifact_resource, mock_http_client):
        """Test presign upload with minimal parameters."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "message": "ok",
            "id": "art-456",
            "bucket": "bucket",
            "key": "key",
            "s3_url": "s3://bucket/key",
            "upload_url": "https://s3.com/url",
            "expires_at": 1700000000,
            "required_headers": {},
        }
        mock_http_client.post.return_value = mock_response

        result = artifact_resource.presign_upload(
            file_name="file.txt", content_type="text/plain", size_bytes=100
        )

        assert result.id == "art-456"


class TestUploadFile:
    """Tests for upload_file convenience method."""

    @patch("builtins.open", new_callable=mock_open, read_data=b"test content")
    @patch("os.path.getsize", return_value=1000)
    @patch("os.path.basename", return_value="test.txt")
    @patch("httpx.put")
    def test_upload_file_success(
        self,
        mock_put,
        mock_basename,
        mock_getsize,
        mock_file,
        artifact_resource,
        mock_http_client,
    ):
        """Test successful file upload."""
        # Mock presign response
        presign_mock = Mock()
        presign_mock.json.return_value = {
            "success": True,
            "message": "ok",
            "id": "art-789",
            "bucket": "bucket",
            "key": "key",
            "s3_url": "s3://bucket/key",
            "upload_url": "https://s3.com/upload",
            "expires_at": 1700000000,
            "required_headers": {"Content-Type": "text/plain"},
        }
        mock_http_client.post.return_value = presign_mock

        # Mock S3 upload response
        upload_mock = Mock()
        upload_mock.status_code = 200
        mock_put.return_value = upload_mock

        # Call method
        presign_resp, upload_resp = artifact_resource.upload_file(
            file_path="/tmp/test.txt", content_type="text/plain", corpus_id="corpus-123"
        )

        # Verify presign was called
        assert mock_http_client.post.called

        # Verify S3 upload
        mock_put.assert_called_once()
        assert upload_resp.status_code == 200

        # Verify result
        assert presign_resp.id == "art-789"


class TestGet:
    """Tests for get method."""

    def test_get_artifact_success(self, artifact_resource, mock_http_client):
        """Test successful get artifact."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "message": "ok",
            "artifact": {
                "id": "art-111",
                "bucket": "bucket",
                "key": "key",
                "s3_url": "s3://bucket/key",
                "content_type": "text/plain",
                "size_bytes": 500,
                "status": "ready",
            },
        }
        mock_http_client.get.return_value = mock_response

        result = artifact_resource.get(artifact_id="art-111")

        # Verify HTTP call
        mock_http_client.get.assert_called_once_with("/v1/artifacts/art-111")

        # Verify result
        assert isinstance(result, Artifact)
        assert result.id == "art-111"
        assert result.status == "ready"


class TestList:
    """Tests for list method."""

    def test_list_all(self, artifact_resource, mock_http_client):
        """Test list all artifacts."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "message": "ok",
            "artifacts": [
                {
                    "id": "art-1",
                    "bucket": "bucket",
                    "key": "key1",
                    "s3_url": "s3://bucket/key1",
                    "content_type": "text/plain",
                    "size_bytes": 100,
                    "status": "ready",
                },
                {
                    "id": "art-2",
                    "bucket": "bucket",
                    "key": "key2",
                    "s3_url": "s3://bucket/key2",
                    "content_type": "application/pdf",
                    "size_bytes": 2000,
                    "status": "processing",
                },
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = artifact_resource.list()

        # Verify HTTP call
        mock_http_client.get.assert_called_once_with("/v1/artifacts", params={})

        # Verify result
        assert len(result) == 2
        assert all(isinstance(a, Artifact) for a in result)
        assert result[0].id == "art-1"
        assert result[1].id == "art-2"

    def test_list_with_filters(self, artifact_resource, mock_http_client):
        """Test list with filters."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "message": "ok",
            "artifacts": [],
        }
        mock_http_client.get.return_value = mock_response

        artifact_resource.list(
            corpus_id="corpus-123", end_user_id="user-456", status="ready"
        )

        # Verify filters were passed
        call_args = mock_http_client.get.call_args
        assert call_args[1]["params"]["corpus_id"] == "corpus-123"
        assert call_args[1]["params"]["end_user_id"] == "user-456"
        assert call_args[1]["params"]["status"] == "ready"


class TestDelete:
    """Tests for delete method."""

    def test_delete_artifact(self, artifact_resource, mock_http_client):
        """Test delete artifact."""
        artifact_resource.delete(artifact_id="art-999")

        # Verify HTTP call
        mock_http_client.delete.assert_called_once_with("/v1/artifacts/art-999")


class TestFinalize:
    """Tests for finalize method."""

    def test_finalize_with_corpus(self, artifact_resource, mock_http_client):
        """Test finalize with corpus ID."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "message": "finalized"}
        mock_http_client.post.return_value = mock_response

        result = artifact_resource.finalize(
            artifact_id="art-777",
            bucket="bucket",
            key="key",
            corpus_id="corpus-123",
            size_bytes=1000,
        )

        # Verify HTTP call to corpus-scoped endpoint
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == "/v1/corpus/corpus-123/artifacts/finalize"

        # Verify result
        assert isinstance(result, FinalizeArtifactResponse)
        assert result.success is True

    def test_finalize_without_corpus(self, artifact_resource, mock_http_client):
        """Test finalize without corpus ID."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "message": "finalized"}
        mock_http_client.post.return_value = mock_response

        artifact_resource.finalize(artifact_id="art-888", bucket="bucket", key="key")

        # Verify HTTP call to generic endpoint
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == "/v1/artifacts/finalize"
