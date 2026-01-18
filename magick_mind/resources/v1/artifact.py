"""
Artifact resource for Magick Mind SDK v1 API.

Provides methods for file upload via presigned S3 URLs and artifact management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import httpx

from magick_mind.models.v1.artifact import (
    Artifact,
    FinalizeArtifactRequest,
    FinalizeArtifactResponse,
    GetArtifactResponse,
    ListArtifactsResponse,
    PresignArtifactRequest,
    PresignArtifactResponse,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes

if TYPE_CHECKING:
    from httpx import Response


class ArtifactResourceV1(BaseResource):
    """
    Artifact resource for managing file uploads and artifacts.

    Implements presigned S3 upload flow:
    1. Call presign_upload() to get a presigned URL
    2. Upload file directly to S3 using the presigned URL
    3. Webhook or finalize() confirms completion
    4. Use get() or list() to retrieve artifact metadata
    """

    def presign_upload(
        self,
        file_name: str,
        content_type: str,
        size_bytes: int,
        end_user_id: Optional[str] = None,
        corpus_id: Optional[str] = None,
    ) -> PresignArtifactResponse:
        """
        Get a presigned S3 URL for uploading a file.

        Args:
            file_name: Name of the file to upload (required)
            content_type: MIME type of the file (e.g., 'application/pdf', 'image/png')
            size_bytes: File size in bytes (must be > 0)
            end_user_id: Optional end user identifier
            corpus_id: Optional corpus ID to associate artifact with

        Returns:
            PresignArtifactResponse containing upload_url and metadata

        Example:
            # Get presigned URL
            response = client.v1.artifact.presign_upload(
                file_name="document.pdf",
                content_type="application/pdf",
                size_bytes=1024000,
                corpus_id="corpus-123"
            )

            # Upload file to S3 using httpx
            import httpx
            with open("document.pdf", "rb") as f:
                httpx.put(
                    response.upload_url,
                    content=f,
                    headers=response.required_headers
                )

            print(f"Artifact ID: {response.id}")
        """
        request = PresignArtifactRequest(
            file_name=file_name,
            content_type=content_type,
            size_bytes=size_bytes,
            end_user_id=end_user_id,
            corpus_id=corpus_id,
        )

        # Use generic presign endpoint
        response = self._http.post(
            Routes.ARTIFACTS_PRESIGN, json=request.model_dump(exclude_none=True)
        )
        return PresignArtifactResponse(**response.json())

    def upload_file(
        self,
        file_path: str,
        content_type: str,
        end_user_id: Optional[str] = None,
        corpus_id: Optional[str] = None,
    ) -> tuple[PresignArtifactResponse, "Response"]:
        """
        Convenience method to presign and upload a file in one call.

        This is a high-level wrapper that:
        1. Gets the file size
        2. Obtains presigned URL
        3. Uploads the file to S3

        Args:
            file_path: Path to the file to upload
            content_type: MIME type of the file
            end_user_id: Optional end user identifier
            corpus_id: Optional corpus ID to associate artifact with

        Returns:
            Tuple of (PresignArtifactResponse, S3 upload response)

        Example:
            presign_resp, upload_resp = client.v1.artifact.upload_file(
                file_path="./document.pdf",
                content_type="application/pdf",
                corpus_id="corpus-123"
            )

            if upload_resp.status_code == 200:
                print(f"Upload successful! Artifact ID: {presign_resp.id}")
        """
        import os

        # Get file size
        size_bytes = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        # Get presigned URL
        presign_response = self.presign_upload(
            file_name=file_name,
            content_type=content_type,
            size_bytes=size_bytes,
            end_user_id=end_user_id,
            corpus_id=corpus_id,
        )

        # Upload to S3 using httpx
        with open(file_path, "rb") as f:
            upload_response = httpx.put(
                presign_response.upload_url,
                content=f,
                headers=presign_response.required_headers,
            )

        upload_response.raise_for_status()
        return presign_response, upload_response

    def get(self, artifact_id: str) -> Artifact:
        """
        Get artifact metadata by ID.

        Args:
            artifact_id: The artifact ID to retrieve

        Returns:
            Artifact object with metadata

        Example:
            artifact = client.v1.artifact.get(artifact_id="art-123")
            print(f"Status: {artifact.status}")
            print(f"S3 URL: {artifact.s3_url}")
        """
        response = self._http.get(Routes.artifact(artifact_id))
        get_response = GetArtifactResponse(**response.json())
        return get_response.artifact

    def list(
        self,
        corpus_id: Optional[str] = None,
        end_user_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[Artifact]:
        """
        List/query artifacts with optional filters.

        Args:
            corpus_id: Filter by corpus ID (optional)
            end_user_id: Filter by end user ID (optional)
            status: Filter by status (uploaded, processing, ready, failed)

        Returns:
            List of Artifact objects

        Example:
            # Get all artifacts for a corpus
            artifacts = client.v1.artifact.list(corpus_id="corpus-123")
            for artifact in artifacts:
                print(f"- {artifact.id}: {artifact.status}")

            # Get ready artifacts
            ready = client.v1.artifact.list(status="ready")
        """
        params = {}
        if corpus_id is not None:
            params["corpus_id"] = corpus_id
        if end_user_id is not None:
            params["end_user_id"] = end_user_id
        if status is not None:
            params["status"] = status

        response = self._http.get(Routes.ARTIFACTS, params=params)
        list_response = ListArtifactsResponse(**response.json())
        return list_response.artifacts

    def delete(self, artifact_id: str) -> None:
        """
        Delete an artifact.

        Args:
            artifact_id: The artifact ID to delete

        Example:
            client.v1.artifact.delete(artifact_id="art-123")
            print("Artifact deleted successfully")
        """
        self._http.delete(Routes.artifact(artifact_id))

    def finalize(
        self,
        artifact_id: str,
        bucket: str,
        key: str,
        version_id: Optional[str] = None,
        size_bytes: Optional[int] = None,
        content_type: Optional[str] = None,
        etag: Optional[str] = None,
        checksum_sha256: Optional[str] = None,
        corpus_id: Optional[str] = None,
    ) -> FinalizeArtifactResponse:
        """
        Client-driven finalize (fallback when webhook is unavailable).

        This is typically used in local development or when the S3 Lambda
        webhook path is not available. In production, webhooks handle
        finalization automatically.

        Args:
            artifact_id: Artifact ID from presign response
            bucket: S3 bucket name
            key: S3 object key
            version_id: S3 version ID (optional)
            size_bytes: Actual uploaded size (optional)
            content_type: Content type (optional)
            etag: S3 ETag (optional)
            checksum_sha256: SHA256 checksum (optional)
            corpus_id: Corpus ID to finalize under (optional)

        Returns:
            FinalizeArtifactResponse

        Example:
            # After uploading to S3
            response = client.v1.artifact.finalize(
                artifact_id=presign_resp.id,
                bucket=presign_resp.bucket,
                key=presign_resp.key,
                corpus_id="corpus-123"
            )
            print(f"Finalize status: {response.success}")
        """
        request = FinalizeArtifactRequest(
            artifact_id=artifact_id,
            bucket=bucket,
            key=key,
            version_id=version_id,
            size_bytes=size_bytes,
            content_type=content_type,
            etag=etag,
            checksum_sha256=checksum_sha256,
        )

        # Route to corpus-scoped finalize if corpus_id provided
        if corpus_id:
            endpoint = Routes.corpus_artifacts_finalize(corpus_id)
        else:
            # Generic finalize endpoint (if available)
            endpoint = Routes.ARTIFACTS_FINALIZE

        response = self._http.post(endpoint, json=request.model_dump(exclude_none=True))
        return FinalizeArtifactResponse(**response.json())
