"""
Artifact models for Magick Mind SDK v1 API.

Provides Pydantic models for file upload and artifact management using
presigned S3 URLs and webhook-based completion confirmation.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Artifact(BaseModel):
    """
    Canonical artifact model representing an uploaded file.

    Artifacts are files (documents, images, etc.) uploaded to S3 and
    associated with a corpus or other container in the bifrost backend.
    """

    model_config = ConfigDict(
        extra="allow"
    )  # Allow additional fields from API responses

    id: str = Field(..., description="Unique artifact identifier")
    bucket: str = Field(..., description="S3 bucket name")
    key: str = Field(..., description="S3 object key")
    s3_url: str = Field(..., description="S3 URL (s3://bucket/key)")
    content_type: str = Field(..., description="MIME type of the artifact")
    size_bytes: int = Field(..., description="Size in bytes")
    etag: Optional[str] = Field(None, description="S3 ETag")
    version_id: Optional[str] = Field(None, description="S3 version ID")
    status: str = Field(
        ..., description="Artifact status (uploaded, processing, ready, failed)"
    )
    corpus_id: Optional[str] = Field(None, description="Associated corpus ID")
    end_user_id: Optional[str] = Field(
        None, description="End user who uploaded the artifact"
    )
    created_by: Optional[str] = Field(
        None, description="Account ID that created the artifact"
    )
    created_at: Optional[int] = Field(
        None, description="Creation timestamp (unix seconds)"
    )
    updated_at: Optional[int] = Field(
        None, description="Last update timestamp (unix seconds)"
    )
    error_code: Optional[str] = Field(
        None, description="Error code if status is failed"
    )


class PresignArtifactRequest(BaseModel):
    """Request for obtaining a presigned S3 upload URL."""

    file_name: str = Field(..., description="Name of the file to upload")
    content_type: str = Field(..., description="MIME type of the file")
    size_bytes: int = Field(..., description="File size in bytes", gt=0)
    end_user_id: Optional[str] = Field(
        None, description="End user identifier (optional)"
    )
    corpus_id: Optional[str] = Field(
        None, description="Corpus to associate with (optional)"
    )


class PresignArtifactResponse(BaseModel):
    """
    Response containing presigned upload URL and metadata.

    The client must use the upload_url to PUT the file data to S3,
    including all headers specified in required_headers.
    """

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    id: str = Field(..., description="Artifact ID")
    bucket: str = Field(..., description="S3 bucket")
    key: str = Field(..., description="S3 object key")
    s3_url: str = Field(..., description="S3 URL (s3://bucket/key)")
    upload_url: str = Field(..., description="Presigned PUT URL (use this to upload)")
    expires_at: int = Field(..., description="URL expiration time (unix seconds)")
    required_headers: dict[str, str] = Field(
        ..., description="HTTP headers that MUST be included in the PUT request"
    )


class GetArtifactResponse(BaseModel):
    """Response for getting a single artifact by ID."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    artifact: Artifact = Field(..., description="The artifact data")


class ListArtifactsResponse(BaseModel):
    """Response for listing/querying artifacts."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    artifacts: list[Artifact] = Field(..., description="List of artifacts")


class DeleteArtifactResponse(BaseModel):
    """Response for deleting an artifact."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")


class FinalizeArtifactRequest(BaseModel):
    """
    Client-driven finalize request (fallback when webhook is unavailable).

    Used in local development or when S3 Lambda webhook path is not available.
    """

    artifact_id: str = Field(..., description="Artifact ID from presign response")
    bucket: str = Field(..., description="S3 bucket")
    key: str = Field(..., description="S3 object key")
    version_id: Optional[str] = Field(None, description="S3 version ID")
    size_bytes: Optional[int] = Field(None, description="Actual uploaded size")
    content_type: Optional[str] = Field(None, description="Content type")
    etag: Optional[str] = Field(None, description="S3 ETag")
    checksum_sha256: Optional[str] = Field(None, description="SHA256 checksum")


class FinalizeArtifactResponse(BaseModel):
    """Response for finalize operation."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")


class ArtifactWebhookPayload(BaseModel):
    """
    Webhook payload sent from S3 Lambda or client finalize.

    This is the shape of data sent to the webhook endpoint after
    an artifact upload is complete.
    """

    artifact_id: str = Field(..., description="Artifact ID")
    corpus_id: Optional[str] = Field(None, description="Corpus ID if applicable")
    bucket: str = Field(..., description="S3 bucket")
    key: str = Field(..., description="S3 object key")
    version_id: Optional[str] = Field(None, description="S3 version ID")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    content_type: Optional[str] = Field(None, description="MIME type")
    etag: Optional[str] = Field(None, description="S3 ETag")
    checksum_sha256: Optional[str] = Field(None, description="SHA256 checksum")
    status: str = Field(..., description="Status: uploaded, processing, ready, failed")
    error_code: Optional[str] = Field(None, description="Error code if failed")
