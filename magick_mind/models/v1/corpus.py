"""
Corpus models for Magick Mind SDK v1 API.

Provides Pydantic models for corpus (knowledge base) management.
Corpus represents a collection of artifacts that can be used for
RAG (Retrieval Augmented Generation) workflows.
"""

from typing import Optional

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


class CreateCorpusResponse(BaseModel):
    """Response for corpus creation."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    corpus: Optional[Corpus] = Field(None, description="The created corpus (Relaxed)")


class GetCorpusResponse(BaseModel):
    """Response for getting corpus (single or list per spec variant)."""

    success: Optional[bool] = Field(None, description="Request success status")
    message: Optional[str] = Field(None, description="Response message")
    corpus: Optional[Corpus | list[Corpus]] = Field(
        None, description="Corpus data - single or array depending on endpoint"
    )


class ListCorpusResponse(BaseModel):
    """Response for listing corpus."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    corpus: list[Corpus] = Field(..., description="List of corpus")


class UpdateCorpusRequest(BaseModel):
    """Request for updating an existing corpus."""

    name: Optional[str] = Field(None, description="Corpus name (Relaxed)")
    description: Optional[str] = Field(None, description="Corpus description (Relaxed)")
    artifact_ids: Optional[list[str]] = Field(
        None, description="List of artifact IDs (Relaxed)"
    )


class UpdateCorpusResponse(BaseModel):
    """Response for corpus update."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    corpus: Optional[Corpus] = Field(None, description="The updated corpus (Relaxed)")


class DeleteCorpusResponse(BaseModel):
    """Response for deleting a corpus."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
