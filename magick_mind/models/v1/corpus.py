"""
Corpus models for Magick Mind SDK v1 API.

Provides Pydantic models for corpus (knowledge base) management.
Corpus represents a collection of artifacts that can be used for
RAG (Retrieval Augmented Generation) workflows.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from magick_mind.models.common import PageInfo


class Corpus(BaseModel):
    """
    Canonical corpus model representing a knowledge base.

    A corpus is a collection of artifacts (documents, files) that can be
    used for semantic search and retrieval augmented generation.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Unique corpus identifier")
    name: str = Field(..., description="Corpus name")
    description: Optional[str] = Field(None, description="Corpus description")
    artifact_ids: Optional[list[str]] = Field(
        None, description="List of artifact IDs in this corpus"
    )
    created_by: Optional[str] = Field(
        None, description="Account ID that created the corpus"
    )
    created_at: Optional[str] = Field(
        None, description="Creation timestamp (ISO format)"
    )
    updated_at: Optional[str] = Field(
        None, description="Last update timestamp (ISO format)"
    )


class CreateCorpusRequest(BaseModel):
    """Request for creating a new corpus."""

    name: Optional[str] = Field(None, description="Corpus name (Relaxed)")
    description: Optional[str] = Field(None, description="Corpus description (Relaxed)")
    artifact_ids: Optional[list[str]] = Field(
        None, description="Optional list of artifact IDs (Relaxed)"
    )


class ListCorpusResponse(BaseModel):
    """
    Response for listing corpus.

    Matches the API's {data: list[Corpus], paging: PageInfo} structure.
    """

    data: list[Corpus] = Field(..., description="List of corpus")
    paging: PageInfo = Field(..., description="Pagination information")


class UpdateCorpusRequest(BaseModel):
    """Request for updating an existing corpus."""

    name: Optional[str] = Field(None, description="Corpus name (Relaxed)")
    description: Optional[str] = Field(None, description="Corpus description (Relaxed)")
    artifact_ids: Optional[list[str]] = Field(
        None, description="List of artifact IDs (Relaxed)"
    )


class DeleteCorpusResponse:
    """
    Response for deleting a corpus.

    The API returns 204 No Content with no response body.
    """

    pass


class AddArtifactsRequest(BaseModel):
    """Request for adding artifacts to a corpus."""

    artifact_ids: list[str] = Field(..., min_length=1, max_length=20)


class AddArtifactsResponse(BaseModel):
    """Response for adding artifacts to a corpus."""

    added_count: int
    failed_artifact_ids: list[str] = Field(default_factory=list)


class ArtifactStatus(BaseModel):
    """Status of an artifact in a corpus."""

    artifact_id: str
    status: str  # PENDING, PROCESSING, PROCESSED, FAILED
    content_summary: Optional[str] = None
    content_length: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error: Optional[str] = None


class ListArtifactStatusesResponse(BaseModel):
    """Response for listing artifact statuses."""

    statuses: list[ArtifactStatus]
