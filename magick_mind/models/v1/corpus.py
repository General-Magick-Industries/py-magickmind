"""
Corpus models for Magick Mind SDK v1 API.

Provides Pydantic models for corpus (knowledge base) management.
Corpus represents a collection of artifacts that can be used for
RAG (Retrieval Augmented Generation) workflows.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from magick_mind.models.common import PageInfo
from magick_mind.models.v1.artifact import Artifact


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
    end_user_id: Optional[str] = Field(
        None, description="Associated end-user ID (optional)"
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


class QueryCorpusRequest(BaseModel):
    """Request for querying a corpus."""

    query: str = Field(..., description="The search query text")
    mode: Optional[str] = Field(
        None,
        description="Query mode: naive|local|global|hybrid (server defaults to hybrid)",
    )
    only_need_context: bool = Field(
        False,
        description="If true, return raw retrieved context without LLM synthesis",
    )
    enable_rerank: Optional[bool] = Field(
        None,
        description="Override rerank behavior. None=server default, True=force on, False=force off.",
    )


class Entity(BaseModel):
    """An entity extracted from the knowledge graph."""

    name: str = Field(..., description="Entity name")
    type: str = Field(default="", description="Entity type")
    description: str = Field(default="", description="Entity description")
    score: float = Field(default=0.0, description="Relevance score")


class Relationship(BaseModel):
    """A relationship between entities in the knowledge graph."""

    source: str = Field(..., description="Source entity name")
    target: str = Field(..., description="Target entity name")
    relationship: str = Field(default="", description="Relationship type")
    description: str = Field(default="", description="Relationship description")
    score: float = Field(default=0.0, description="Relevance score")


class Chunk(BaseModel):
    """A text chunk retrieved from the corpus."""

    content: str = Field(..., description="Chunk text content")
    source_id: str = Field(default="", description="Source document ID")
    score: float = Field(default=0.0, description="Relevance score")


class Reference(BaseModel):
    """A reference to a source document."""

    source_id: str = Field(..., description="Source document ID")
    content: str = Field(default="", description="Reference content")


class QueryMetadata(BaseModel):
    """Metadata about the query execution."""

    query_mode: str = Field(default="", description="Query mode used")
    high_level_keywords: list[str] = Field(
        default_factory=list, description="High-level keywords extracted"
    )
    low_level_keywords: list[str] = Field(
        default_factory=list, description="Low-level keywords extracted"
    )
    rerank_applied: bool = Field(
        default=False,
        description="True if reranking actually ran. False on failure or when disabled.",
    )


class QueryCorpusResponse(BaseModel):
    """Response for querying a corpus.

    Contains both the legacy JSON result string and structured fields.
    The structured fields are populated when the server supports them.
    """

    result: str = Field(default="", description="Query result text (legacy JSON blob)")
    entities: list[Entity] = Field(
        default_factory=list, description="Extracted entities"
    )
    relationships: list[Relationship] = Field(
        default_factory=list, description="Entity relationships"
    )
    chunks: list[Chunk] = Field(
        default_factory=list, description="Retrieved text chunks"
    )
    references: list[Reference] = Field(
        default_factory=list, description="Source references"
    )
    metadata: Optional[QueryMetadata] = Field(
        None, description="Query execution metadata"
    )
    llm_response: str = Field(default="", description="LLM synthesis response text")


class IngestionStatus(BaseModel):
    """
    Ingestion status for an artifact within a corpus.

    Represents the processing state of an artifact after it has been
    added to a corpus for indexing.
    """

    status: str = Field(
        ..., description="Ingestion status (PENDING, PROCESSING, PROCESSED, FAILED)"
    )
    content_summary: Optional[str] = Field(
        default=None, description="Summary of the ingested content"
    )
    content_length: Optional[int] = Field(
        default=None, description="Length of the ingested content"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if status is FAILED"
    )
    completed_at: Optional[str] = Field(
        default=None, description="Timestamp when ingestion completed (ISO format)"
    )


class CorpusArtifactItem(BaseModel):
    """
    Combined artifact and its ingestion status within a corpus.

    Returned by the list_artifacts endpoint, pairing the artifact metadata
    with its current ingestion state.
    """

    artifact: Artifact = Field(..., description="The artifact metadata")
    ingestion: IngestionStatus = Field(
        ..., description="Current ingestion status of the artifact"
    )
