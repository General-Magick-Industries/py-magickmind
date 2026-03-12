"""
Corpus resource for Magick Mind SDK v1 API.

Provides methods for managing corpus (knowledge base) resources.
"""

from __future__ import annotations

from typing import Optional

from magick_mind.models.v1.corpus import (
    AddArtifactsRequest,
    AddArtifactsResponse,
    ArtifactStatus,
    Corpus,
    CreateCorpusRequest,
    ListArtifactStatusesResponse,
    ListCorpusResponse,
    QueryCorpusRequest,
    QueryCorpusResponse,
    UpdateCorpusRequest,
)
from magick_mind.resources.base import BaseResource
from magick_mind.routes import Routes


class CorpusResourceV1(BaseResource):
    """Resource client for corpus operations."""

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
            MagickMindError: If the request fails
        """
        payload = CreateCorpusRequest(
            name=name,
            description=description,
            artifact_ids=artifact_ids or [],
        )

        resp = self._http.post(Routes.CORPUS, json=payload.model_dump())
        return Corpus(**resp)

    def get(self, corpus_id: str) -> Corpus:
        """
        Get a corpus by ID.

        Args:
            corpus_id: The corpus ID

        Returns:
            Corpus object

        Raises:
            MagickMindError: If the request fails
        """
        resp = self._http.get(Routes.corpus(corpus_id))
        return Corpus(**resp)

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
            MagickMindError: If the request fails
        """
        params = {}
        if user_id:
            params["user_id"] = user_id
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = str(limit)

        resp = self._http.get(Routes.CORPUS, params=params)
        return ListCorpusResponse(**resp)

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
            MagickMindError: If the request fails
        """
        payload = UpdateCorpusRequest(
            name=name,
            description=description,
            artifact_ids=artifact_ids,
        )

        resp = self._http.put(Routes.corpus(corpus_id), json=payload.model_dump())
        return Corpus(**resp)

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
            MagickMindError: If request fails
        """
        self._http.delete(Routes.corpus(corpus_id))

    def add_artifact(
        self, corpus_id: str, artifact_id: str, api_key: str = ""
    ) -> AddArtifactsResponse:
        """
        Add a single artifact to corpus and trigger ingestion.

        Args:
            corpus_id: The corpus ID
            artifact_id: The artifact ID to add
            api_key: API key for ApiKeyMiddleware (required by Bifrost)

        Returns:
            AddArtifactsResponse with result

        Raises:
            MagickMindError: If the request fails
        """
        return self.add_artifacts(corpus_id, [artifact_id], api_key=api_key)

    def add_artifacts(
        self, corpus_id: str, artifact_ids: list[str], api_key: str = ""
    ) -> AddArtifactsResponse:
        """
        Add multiple artifacts to corpus (max 20) and trigger batch ingestion.

        Note: Only text-based formats (text/*, JSON, XML) and PDF are supported.

        Args:
            corpus_id: The corpus ID
            artifact_ids: List of artifact IDs to add (max 20)
            api_key: API key for ApiKeyMiddleware (required by Bifrost)

        Returns:
            AddArtifactsResponse with result

        Raises:
            MagickMindError: If the request fails
        """
        payload = AddArtifactsRequest(artifact_ids=artifact_ids)

        resp = self._http.post(
            Routes.corpus_artifacts(corpus_id),
            json=payload.model_dump(),
            headers={"x-api-key": api_key} if api_key else {},
        )
        return AddArtifactsResponse(**resp)

    def remove_artifact(self, corpus_id: str, artifact_id: str) -> None:
        """
        Remove artifact from corpus.

        Args:
            corpus_id: The corpus ID
            artifact_id: The artifact ID to remove

        Returns:
            None

        Raises:
            MagickMindError: If the request fails
        """
        self._http.delete(Routes.corpus_artifact(corpus_id, artifact_id))

    def get_artifact_status(self, corpus_id: str, artifact_id: str) -> ArtifactStatus:
        """
        Get ingestion status for a single artifact.

        Args:
            corpus_id: The corpus ID
            artifact_id: The artifact ID

        Returns:
            ArtifactStatus object

        Raises:
            MagickMindError: If the request fails
        """
        resp = self._http.get(Routes.corpus_artifact_status(corpus_id, artifact_id))
        return ArtifactStatus(**resp)

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
            MagickMindError: If the request fails
        """
        params = {}
        if artifact_ids:
            params["artifact_ids"] = artifact_ids

        resp = self._http.get(Routes.corpus_artifacts_status(corpus_id), params=params)
        data = ListArtifactStatusesResponse(**resp)
        return data.statuses

    def query(
        self,
        corpus_id: str,
        query: str,
        mode: str = "hybrid",
        api_key: str = "",
    ) -> QueryCorpusResponse:
        """
        Query a corpus using semantic search.

        Args:
            corpus_id: The corpus ID to query
            query: Query text
            mode: Query mode — naive | local | global | hybrid (default: hybrid)
            api_key: API key for ApiKeyMiddleware (required by Bifrost)

        Returns:
            QueryCorpusResponse with result text

        Raises:
            MagickMindError: If the request fails
        """
        payload = QueryCorpusRequest(query=query, mode=mode)
        resp = self._http.post(
            Routes.corpus_query(corpus_id),
            json=payload.model_dump(),
            headers={"x-api-key": api_key} if api_key else {},
        )
        return QueryCorpusResponse(**resp)
