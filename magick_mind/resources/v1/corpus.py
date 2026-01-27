"""
Corpus resource for Magick Mind SDK v1 API.

Provides methods for managing corpus (knowledge base) resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.corpus import (
    CreateCorpusRequest,
    CreateCorpusResponse,
    DeleteCorpusResponse,
    GetCorpusResponse,
    ListCorpusResponse,
    UpdateCorpusRequest,
    UpdateCorpusResponse,
)
from magick_mind.routes import Routes

if TYPE_CHECKING:
    import httpx


class CorpusResourceV1:
    """Resource client for corpus operations."""

    def __init__(self, http_client: httpx.Client):
        """
        Initialize the corpus resource.

        Args:
            http_client: Authenticated httpx client
        """
        self.http = http_client

    def create(
        self,
        name: str,
        description: str,
        artifact_ids: Optional[list[str]] = None,
    ) -> CreateCorpusResponse:
        """
        Create a new corpus.

        Args:
            name: Corpus name
            description: Corpus description
            artifact_ids: Optional list of artifact IDs to include

        Returns:
            CreateCorpusResponse with the created corpus

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        payload = CreateCorpusRequest(
            name=name,
            description=description,
            artifact_ids=artifact_ids or [],
        )

        resp = self.http.post(Routes.CORPUS, json=payload.model_dump())
        resp.raise_for_status()

        return CreateCorpusResponse(**resp.json())

    def get(self, corpus_id: str) -> GetCorpusResponse:
        """
        Get a corpus by ID.

        Args:
            corpus_id: The corpus ID

        Returns:
            GetCorpusResponse with the corpus data

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        resp = self.http.get(Routes.corpus(corpus_id))
        resp.raise_for_status()

        return GetCorpusResponse(**resp.json())

    def list(self, user_id: Optional[str] = None) -> ListCorpusResponse:
        """
        List all corpus, optionally filtered by user_id.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            ListCorpusResponse with list of corpus

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        params = {}
        if user_id:
            params["user_id"] = user_id

        resp = self.http.get(Routes.CORPUS, params=params)
        resp.raise_for_status()

        return ListCorpusResponse(**resp.json())

    def update(
        self,
        corpus_id: str,
        name: str,
        description: str,
        artifact_ids: list[str],
    ) -> UpdateCorpusResponse:
        """
        Update an existing corpus.

        Args:
            corpus_id: The corpus ID to update
            name: New corpus name
            description: New corpus description
            artifact_ids: New list of artifact IDs

        Returns:
            UpdateCorpusResponse with the updated corpus

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        payload = UpdateCorpusRequest(
            name=name,
            description=description,
            artifact_ids=artifact_ids,
        )

        resp = self.http.put(Routes.corpus(corpus_id), json=payload.model_dump())
        resp.raise_for_status()

        return UpdateCorpusResponse(**resp.json())

    def delete(self, corpus_id: str) -> DeleteCorpusResponse:
        """
        Delete a corpus.

        Args:
            corpus_id: The corpus ID to delete

        Returns:
            DeleteCorpusResponse

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        resp = self.http.delete(Routes.corpus(corpus_id))
        resp.raise_for_status()

        return DeleteCorpusResponse(**resp.json())
