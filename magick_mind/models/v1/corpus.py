"""
Corpus models for Magick Mind SDK v1 API.

Provides Pydantic models for corpus (knowledge base) management.
Corpus represents a collection of artifacts that can be used for
RAG (Retrieval Augmented Generation) workflows.
"""

from pydantic import BaseModel, ConfigDict, Field


class Corpus(BaseModel):
    """
    Canonical corpus model representing a knowledge base.

    A corpus is a collection of artifacts (documents, files) that can be
    used for semantic search and retrieval augmented generation.
    """

    model_config = ConfigDict(
        extra="allow"
    )  # Allow additional fields from API responses

    id: str = Field(..., description="Unique corpus identifier")
    name: str = Field(..., description="Corpus name")
    description: str = Field(..., description="Corpus description")
    artifact_ids: list[str] = Field(
        default_factory=list, description="List of artifact IDs in this corpus"
    )
    created_by: str = Field(..., description="Account ID that created the corpus")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")


class CreateCorpusRequest(BaseModel):
    """Request for creating a new corpus."""

    name: str = Field(..., description="Corpus name")
    description: str = Field(..., description="Corpus description")
    artifact_ids: list[str] = Field(
        default_factory=list,
        description="Optional list of artifact IDs to include initially",
    )


class CreateCorpusResponse(BaseModel):
    """Response for corpus creation."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    corpus: Corpus = Field(..., description="The created corpus")


class GetCorpusResponse(BaseModel):
    """Response for getting a single corpus by ID."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    corpus: Corpus = Field(..., description="The corpus data")


class ListCorpusResponse(BaseModel):
    """Response for listing corpus."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    corpus: list[Corpus] = Field(..., description="List of corpus")


class UpdateCorpusRequest(BaseModel):
    """Request for updating an existing corpus."""

    name: str = Field(..., description="Corpus name")
    description: str = Field(..., description="Corpus description")
    artifact_ids: list[str] = Field(
        default_factory=list, description="List of artifact IDs in this corpus"
    )


class UpdateCorpusResponse(BaseModel):
    """Response for corpus update."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    corpus: Corpus = Field(..., description="The updated corpus")


class DeleteCorpusResponse(BaseModel):
    """Response for deleting a corpus."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
