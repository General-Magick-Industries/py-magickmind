"""
Corpus resource for Magick Mind SDK v1 API.

Provides methods for managing corpus (knowledge base) resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from magick_mind.models.v1.corpus import (
    AddArtifactsRequest,
    AddArtifactsResponse,
    ArtifactStatus,
    Corpus,
    CreateCorpusRequest,
    ListArtifactStatusesResponse,
    ListCorpusResponse,
    UpdateCorpusRequest,
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
    ) -> Corpus:
        """
        Create a new corpus.

        Args:
            name: Corpus name
            description: Corpus description
            artifact_ids: Optional list of artifact IDs to include

        Returns:
            Corpus object

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

        return Corpus(**resp.json())

    def get(self, corpus_id: str) -> Corpus:
        """
        Get a corpus by ID.

        Args:
            corpus_id: The corpus ID

        Returns:
            Corpus object

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        resp = self.http.get(Routes.corpus(corpus_id))
        resp.raise_for_status()

        return Corpus(**resp.json())

    def list(
        self,
        user_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> ListCorpusResponse:
        """
        List all corpus, optionally filtered by user_id.

        Args:
            user_id: Optional user ID to filter by
            cursor: Pagination cursor (opaque string from PageInfo.cursors.after/before)
            limit: Maximum number of results per page (default 20, max 100)

        Returns:
            ListCorpusResponse with list of corpus and pagination info

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        params = {}
        if user_id:
            params["user_id"] = user_id
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = str(limit)

        resp = self.http.get(Routes.CORPUS, params=params)
        resp.raise_for_status()

        return ListCorpusResponse(**resp.json())

    def update(
        self,
        corpus_id: str,
        name: str,
        description: str,
        artifact_ids: list[str],
    ) -> Corpus:
        """
        Update an existing corpus.

        Args:
            corpus_id: The corpus ID to update
            name: New corpus name
            description: New corpus description
            artifact_ids: New list of artifact IDs

        Returns:
            Corpus object

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

        return Corpus(**resp.json())

    def delete(self, corpus_id: str) -> None:
        """
        Delete a corpus.

        Args:
            corpus_id: The corpus ID to delete

        Returns:
            None (Bifrost returns 204 No Content)

        Example:
            client.v1.corpus.delete(corpus_id="corpus-123")
            print("Corpus deleted successfully")

        Raises:
            httpx.HTTPStatusError: If request fails
        """
        self.http.delete(Routes.corpus(corpus_id))

    def add_artifact(self, corpus_id: str, artifact_id: str) -> AddArtifactsResponse:
        """
        Add a single artifact to corpus and trigger ingestion.

        Args:
            corpus_id: The corpus ID
            artifact_id: The artifact ID to add

        Returns:
            AddArtifactsResponse with result

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        return self.add_artifacts(corpus_id, [artifact_id])

    def add_artifacts(
        self, corpus_id: str, artifact_ids: list[str]
    ) -> AddArtifactsResponse:
        """
        Add multiple artifacts to corpus (max 20) and trigger batch ingestion.

        Note: Only text-based formats (text/*, JSON, XML) and PDF are supported.

        Args:
            corpus_id: The corpus ID
            artifact_ids: List of artifact IDs to add (max 20)

        Returns:
            AddArtifactsResponse with result

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        payload = AddArtifactsRequest(artifact_ids=artifact_ids)

        resp = self.http.post(
            Routes.corpus_artifacts(corpus_id), json=payload.model_dump()
        )
        resp.raise_for_status()

        return AddArtifactsResponse(**resp.json())

    def remove_artifact(self, corpus_id: str, artifact_id: str) -> None:
        """
        Remove artifact from corpus.

        Args:
            corpus_id: The corpus ID
            artifact_id: The artifact ID to remove

        Returns:
            None

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        resp = self.http.delete(Routes.corpus_artifact(corpus_id, artifact_id))
        resp.raise_for_status()

    def get_artifact_status(self, corpus_id: str, artifact_id: str) -> ArtifactStatus:
        """
        Get ingestion status for a single artifact.

        Args:
            corpus_id: The corpus ID
            artifact_id: The artifact ID

        Returns:
            ArtifactStatus object

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        resp = self.http.get(Routes.corpus_artifact_status(corpus_id, artifact_id))
        resp.raise_for_status()

        return ArtifactStatus(**resp.json())

    def list_artifact_statuses(
        self, corpus_id: str, artifact_ids: Optional[list[str]] = None
    ) -> list[ArtifactStatus]:
        """
        List ingestion statuses for artifacts in corpus.

        Args:
            corpus_id: The corpus ID
            artifact_ids: Optional list of specific artifact IDs to filter

        Returns:
            List of ArtifactStatus objects

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        params = {}
        if artifact_ids:
            params["artifact_ids"] = artifact_ids

        resp = self.http.get(Routes.corpus_artifacts_status(corpus_id), params=params)
        resp.raise_for_status()

        data = ListArtifactStatusesResponse(**resp.json())
        return data.statuses
