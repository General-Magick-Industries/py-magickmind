"""
Corpus models for Magick Mind SDK v1 API.

Provides Pydantic models for corpus (knowledge base) management.
Corpus represents a collection of artifacts that can be used for
RAG (Retrieval Augmented Generation) workflows.
"""

from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from magick_mind.models.v1.end_user import PageInfo


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

    Matches Bifrost's {data: list[Corpus], paging: PageInfo} structure.
    """

    data: list[Corpus] = Field(..., description="List of corpus")
    paging: "PageInfo" = Field(..., description="Pagination information")


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

    Bifrost returns 204 No Content with no response body.
    """

    pass
