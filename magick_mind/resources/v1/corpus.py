"""
Corpus resource for Magick Mind SDK v1 API.

Provides methods for managing corpus (knowledge base) resources.
"""

from __future__ import annotations

import warnings
from typing import Optional

from magick_mind.models.v1.corpus import (
    AddArtifactsRequest,
    AddArtifactsResponse,
    ArtifactStatus,
    Corpus,
    CorpusArtifactItem,
    CreateCorpusRequest,
    IngestionStatus,
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

    async def create(
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
            ProblemDetailsException: If the request fails
        """
        payload = CreateCorpusRequest(
            name=name,
            description=description,
            artifact_ids=artifact_ids or [],
        )

        resp = await self._http.post(Routes.CORPUS, json=payload.model_dump())

        return Corpus(**resp)

    async def get(self, corpus_id: str) -> Corpus:
        """
        Get a corpus by ID.

        Args:
            corpus_id: The corpus ID

        Returns:
            Corpus object

        Raises:
            ProblemDetailsException: If the request fails
        """
        resp = await self._http.get(Routes.corpus(corpus_id))

        return Corpus(**resp)

    async def list(
        self,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        search: Optional[str] = None,
        end_user_id: Optional[str] = None,
    ) -> ListCorpusResponse:
        """
        List corpus, with optional filtering and pagination.

        Args:
            cursor: Pagination cursor (opaque string from PageInfo.cursors.after/before)
            limit: Maximum number of results per page (default 20, max 100)
            order: Sort order — ``"asc"`` or ``"desc"`` (default: asc)
            search: Free-text search filter
            end_user_id: Filter by end-user ID

        Returns:
            ListCorpusResponse with list of corpus and pagination info

        Raises:
            ProblemDetailsException: If the request fails
        """
        params: dict[str, object] = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order
        if search is not None:
            params["search"] = search
        if end_user_id is not None:
            params["end_user_id"] = end_user_id

        resp = await self._http.get(Routes.CORPUS, params=params if params else None)

        return ListCorpusResponse(**resp)

    async def update(
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
            ProblemDetailsException: If the request fails
        """
        payload = UpdateCorpusRequest(
            name=name,
            description=description,
            artifact_ids=artifact_ids,
        )

        resp = await self._http.put(Routes.corpus(corpus_id), json=payload.model_dump())

        return Corpus(**resp)

    async def delete(self, corpus_id: str) -> None:
        """
        Delete a corpus.

        Args:
            corpus_id: The corpus ID to delete

        Returns:
            None (The API returns 204 No Content)

        Example:
            await client.v1.corpus.delete(corpus_id="corpus-123")
            print("Corpus deleted successfully")

        Raises:
            ProblemDetailsException: If request fails
        """
        await self._http.delete(Routes.corpus(corpus_id))

    async def add_artifact(
        self,
        corpus_id: str,
        artifact_id: str,
        *,
        api_key: Optional[str] = None,
    ) -> AddArtifactsResponse:
        """
        Add a single artifact to corpus and trigger ingestion.

        Args:
            corpus_id: The corpus ID
            artifact_id: The artifact ID to add
            api_key: Optional API key (sent as x-api-key header). Required for
                corpus-scoped operations on dev/prod.

        Returns:
            AddArtifactsResponse with result

        Raises:
            ProblemDetailsException: If the request fails
        """
        return await self.add_artifacts(corpus_id, [artifact_id], api_key=api_key)

    async def add_artifacts(
        self,
        corpus_id: str,
        artifact_ids: list[str],
        *,
        api_key: Optional[str] = None,
    ) -> AddArtifactsResponse:
        """
        Add multiple artifacts to corpus (max 20) and trigger batch ingestion.

        Note: Only text-based formats (text/*, JSON, XML) and PDF are supported.

        Args:
            corpus_id: The corpus ID
            artifact_ids: List of artifact IDs to add (max 20)
            api_key: Optional API key (sent as x-api-key header). Required for
                corpus-scoped operations on dev/prod.

        Returns:
            AddArtifactsResponse with result

        Raises:
            ProblemDetailsException: If the request fails
        """
        payload = AddArtifactsRequest(artifact_ids=artifact_ids)

        headers = {}
        if api_key:
            headers["x-api-key"] = api_key

        resp = await self._http.post(
            Routes.corpus_artifacts(corpus_id),
            json=payload.model_dump(),
            headers=headers if headers else None,
        )

        return AddArtifactsResponse(**resp)

    async def remove_artifact(self, corpus_id: str, artifact_id: str) -> None:
        """
        Remove artifact from corpus.

        Args:
            corpus_id: The corpus ID
            artifact_id: The artifact ID to remove

        Returns:
            None

        Raises:
            ProblemDetailsException: If the request fails
        """
        await self._http.delete(Routes.corpus_artifact(corpus_id, artifact_id))

    async def list_artifacts(
        self,
        corpus_id: str,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> list[CorpusArtifactItem]:
        """
        List artifacts in a corpus with their ingestion statuses.

        Returns a combined view of each artifact and its current ingestion
        state, suitable for polling or displaying corpus contents.

        Args:
            corpus_id: The corpus ID
            cursor: Pagination cursor (opaque string from PageInfo.cursors.after/before)
            limit: Maximum number of results per page (default 20, max 100)

        Returns:
            List of CorpusArtifactItem objects (artifact + ingestion status)

        Raises:
            ProblemDetailsException: If the request fails
        """
        params: dict[str, object] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor

        resp = await self._http.get(Routes.corpus_artifacts(corpus_id), params=params)

        items: list[CorpusArtifactItem] = []
        for item in resp.get("data", resp if isinstance(resp, list) else []):
            items.append(CorpusArtifactItem(**item))
        return items

    async def list_ingestion(
        self, corpus_id: str, artifact_ids: Optional[list[str]] = None
    ) -> list[IngestionStatus]:
        """
        List ingestion statuses for artifacts in a corpus.

        Args:
            corpus_id: The corpus ID
            artifact_ids: Optional list of specific artifact IDs to filter

        Returns:
            List of IngestionStatus objects

        Raises:
            ProblemDetailsException: If the request fails
        """
        params: dict[str, object] = {}
        if artifact_ids:
            params["artifact_ids"] = artifact_ids

        resp = await self._http.get(
            Routes.corpus_artifacts_status(corpus_id), params=params
        )

        data = ListArtifactStatusesResponse(**resp)
        return [
            IngestionStatus(
                status=s.status,
                content_summary=s.content_summary,
                content_length=s.content_length,
                error=s.error,
            )
            for s in data.statuses
        ]

    async def get_ingestion(self, corpus_id: str, artifact_id: str) -> IngestionStatus:
        """
        Get ingestion status for a single artifact.

        Args:
            corpus_id: The corpus ID
            artifact_id: The artifact ID

        Returns:
            IngestionStatus object

        Raises:
            ProblemDetailsException: If the request fails
        """
        resp = await self._http.get(
            Routes.corpus_artifacts_status(corpus_id),
            params={"artifact_ids": [artifact_id]},
        )
        data = ListArtifactStatusesResponse(**resp)
        if not data.statuses:
            return IngestionStatus(status="NOT_FOUND")
        s = data.statuses[0]
        return IngestionStatus(
            status=s.status,
            content_summary=s.content_summary,
            content_length=s.content_length,
            error=s.error,
        )

    async def get_artifact_status(
        self, corpus_id: str, artifact_id: str
    ) -> ArtifactStatus:
        """
        Get ingestion status for a single artifact.

        .. deprecated::
            Use :meth:`get_ingestion` instead, which returns the updated
            ``IngestionStatus`` model.

        Args:
            corpus_id: The corpus ID
            artifact_id: The artifact ID

        Returns:
            ArtifactStatus object

        Raises:
            ProblemDetailsException: If the request fails
        """
        warnings.warn(
            "get_artifact_status() is deprecated; use get_ingestion() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        resp = await self._http.get(
            Routes.corpus_artifacts_status(corpus_id),
            params={"artifact_ids": [artifact_id]},
        )
        data = ListArtifactStatusesResponse(**resp)
        if not data.statuses:
            return ArtifactStatus(artifact_id=artifact_id, status="NOT_FOUND")
        return data.statuses[0]

    async def list_artifact_statuses(
        self, corpus_id: str, artifact_ids: Optional[list[str]] = None
    ) -> list[ArtifactStatus]:
        """
        List ingestion statuses for artifacts in corpus.

        .. deprecated::
            Use :meth:`list_ingestion` instead, which returns the updated
            ``IngestionStatus`` model.

        Args:
            corpus_id: The corpus ID
            artifact_ids: Optional list of specific artifact IDs to filter

        Returns:
            List of ArtifactStatus objects

        Raises:
            ProblemDetailsException: If the request fails
        """
        warnings.warn(
            "list_artifact_statuses() is deprecated; use list_ingestion() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        params: dict[str, object] = {}
        if artifact_ids:
            params["artifact_ids"] = artifact_ids

        resp = await self._http.get(
            Routes.corpus_artifacts_status(corpus_id), params=params
        )

        data = ListArtifactStatusesResponse(**resp)
        return data.statuses

    async def query(
        self,
        corpus_id: str,
        *,
        query: str,
        mode: Optional[str] = None,
        only_need_context: bool = False,
        enable_rerank: Optional[bool] = None,
        api_key: Optional[str] = None,
    ) -> QueryCorpusResponse:
        """
        Query a corpus using semantic search.

        Args:
            corpus_id: The corpus ID to query
            query: The search query text
            mode: Query mode — one of naive|local|global|hybrid.
                Omit to let the server choose (defaults to hybrid).
            only_need_context: If True, return raw context without LLM synthesis.
            enable_rerank: Override rerank behavior. None = server default
                (on if provider configured), True = force on, False = force off.
            api_key: Optional API key (sent as x-api-key header). Required for
                corpus-scoped operations on dev/prod.

        Returns:
            QueryCorpusResponse with the result text

        Raises:
            ProblemDetailsException: If the request fails
        """
        payload = QueryCorpusRequest(
            query=query,
            mode=mode,
            only_need_context=only_need_context,
            enable_rerank=enable_rerank,
        )

        headers = {}
        if api_key:
            headers["x-api-key"] = api_key

        resp = await self._http.post(
            Routes.corpus_query(corpus_id),
            json=payload.model_dump(exclude_none=True),
            headers=headers if headers else None,
        )

        return QueryCorpusResponse(**resp)
