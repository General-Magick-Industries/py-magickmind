"""
Artifact models for Magick Mind SDK v1 API.

Provides Pydantic models for file upload and artifact management using
presigned S3 URLs and webhook-based completion confirmation.
"""

from __future__ import annotations

from typing import ClassVar, Optional, Union
from enum import Enum

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ArtifactStatusEnum(str, Enum):
    """Lifecycle status values for an artifact."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class Artifact(BaseModel):
    """
    Canonical artifact model representing an uploaded file.

    Artifacts are files (documents, images, etc.) uploaded to S3 and
    associated with a corpus or other container in the backend.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow"
    )  # Allow additional fields from API responses

    id: str = Field(..., description="Unique artifact identifier")
    bucket: Optional[str] = Field(default=None, description="S3 bucket name")
    key: Optional[str] = Field(default=None, description="S3 object key")
    s3_url: Optional[str] = Field(default=None, description="S3 URL (s3://bucket/key)")
    content_type: Optional[str] = Field(
        default=None, description="MIME type of the artifact"
    )
    size_bytes: Optional[int] = Field(default=None, description="Size in bytes")
    etag: Optional[str] = Field(default=None, description="S3 ETag")
    version_id: Optional[str] = Field(default=None, description="S3 version ID")
    status: str = Field(
        ...,
        description="Artifact status (uploaded, processing, ready, failed, deleted)",
    )
    corpus_id: Optional[str] = Field(default=None, description="Associated corpus ID")
    end_user_id: Optional[str] = Field(
        None, description="End user who uploaded the artifact"
    )
    created_by: Optional[str] = Field(
        None, description="Account ID that created the artifact"
    )
    created_at: Optional[Union[int, str]] = Field(
        None, description="Creation timestamp (unix seconds or RFC 3339)"
    )
    updated_at: Optional[Union[int, str]] = Field(
        None, description="Last update timestamp (unix seconds or RFC 3339)"
    )
    error_code: Optional[str] = Field(
        None, description="Error code if status is failed"
    )
    original_filename: Optional[str] = Field(default=None, description="Name at upload")


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
    """

    success: Optional[bool] = Field(default=None, description="Request success status")
    message: Optional[str] = Field(default=None, description="Response message")
    id: Optional[str] = Field(default=None, description="Artifact ID (Relaxed)")
    bucket: Optional[str] = Field(default=None, description="S3 bucket (Relaxed)")
    key: Optional[str] = Field(default=None, description="S3 object key (Relaxed)")
    s3_url: Optional[str] = Field(default=None, description="S3 URL (Relaxed)")
    upload_url: Optional[str] = Field(
        default=None, description="Presigned PUT URL (Relaxed)"
    )
    expires_at: Optional[int] = Field(
        default=None, description="URL expiration time (Relaxed)"
    )
    required_headers: Optional[dict[str, str]] = Field(
        None, description="HTTP headers (Relaxed)"
    )


class GetArtifactResponse(BaseModel):
    """Response for getting a single artifact by ID.

    Matches the ``{"artifact": {...}}`` envelope returned by
    ``GET /v1/artifacts/{id}``.
    """

    artifact: Artifact = Field(..., description="The artifact data")


class ListArtifactsResponse(BaseModel):
    """Response for listing/querying artifacts.

    Accepts both the ``{"data": [...]}`` envelope and Bifrost's
    ``{"artifacts": [...], "next_page_token": ...}`` shape.
    """

    data: list[Artifact] = Field(
        ...,
        validation_alias=AliasChoices("data", "artifacts"),
        description="List of artifacts",
    )
    next_page_token: Optional[str] = Field(
        None, description="Opaque token for the next page, if any"
    )


class ScopedPresignRequest(BaseModel):
    """Presign an upload into a magickspace."""

    file_name: Optional[str] = Field(
        default=None, description="Derived server-side if omitted"
    )
    content_type: str
    size_bytes: int = Field(..., gt=0)
    end_user_id: Optional[str] = Field(
        default=None, description="Association only (service-user route)"
    )


class DownloadUrlResponse(BaseModel):
    """Response for retrieving a presigned artifact download URL.

    Returned by ``GET /v1/artifacts/{id}/download``.
    """

    id: Optional[str] = Field(default=None, description="Artifact ID")
    download_url: str = Field(..., description="Presigned S3 download URL")
    expires_at: Optional[int] = Field(
        None, description="URL expiration timestamp (unix seconds)"
    )
    content_type: Optional[str] = Field(default=None, description="MIME type")
    file_name: Optional[str] = Field(default=None, description="Original file name")


class DeleteArtifactResponse(BaseModel):
    """Response for deleting an artifact."""

    success: bool = Field(..., description="Request success status")
    message: Optional[str] = Field(default=None, description="Response message")
    already_deleted: bool = Field(
        default=False, description="The artifact was already gone"
    )


class FinalizeArtifactRequest(BaseModel):
    """
    Client-driven finalize request (fallback when webhook is unavailable).
    """

    artifact_id: str = Field(..., description="Artifact ID")
    bucket: str = Field(..., description="S3 bucket")
    key: str = Field(..., description="S3 object key")
    version_id: Optional[str] = Field(default=None, description="S3 version ID")
    size_bytes: Optional[int] = Field(default=None, description="Actual uploaded size")
    content_type: Optional[str] = Field(default=None, description="Content type")
    etag: Optional[str] = Field(default=None, description="S3 ETag")
    checksum_sha256: Optional[str] = Field(default=None, description="SHA256 checksum")


class FinalizeArtifactResponse(BaseModel):
    """Response for finalize operation."""

    success: Optional[bool] = Field(default=None, description="Request success status")
    message: Optional[str] = Field(default=None, description="Response message")


class ArtifactWebhookPayload(BaseModel):
    """
    Webhook payload sent from S3 Lambda or client finalize.

    This is the shape of data sent to the webhook endpoint after
    an artifact upload is complete.
    """

    artifact_id: str = Field(..., description="Artifact ID")
    corpus_id: Optional[str] = Field(
        default=None, description="Corpus ID if applicable"
    )
    bucket: str = Field(..., description="S3 bucket")
    key: str = Field(..., description="S3 object key")
    version_id: Optional[str] = Field(default=None, description="S3 version ID")
    size_bytes: Optional[int] = Field(default=None, description="File size in bytes")
    content_type: Optional[str] = Field(default=None, description="MIME type")
    etag: Optional[str] = Field(default=None, description="S3 ETag")
    checksum_sha256: Optional[str] = Field(default=None, description="SHA256 checksum")
    status: str = Field(..., description="Status: uploaded, processing, ready, failed")
    error_code: Optional[str] = Field(default=None, description="Error code if failed")
