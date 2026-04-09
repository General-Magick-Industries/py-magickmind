"""
Corpus resource for Magick Mind SDK v1 API.

Provides methods for managing corpus (knowledge base) resources.
"""

from __future__ import annotations

import asyncio
import warnings
from typing import IO, Optional, Union

import httpx

from magick_mind.models.v1.corpus import (
    AddArtifactsRequest,
    AddArtifactsResponse,
    ArtifactStatus,
    Corpus,
    CorpusArtifactItem,
    CreateCorpusRequest,
    IngestResult,
    IngestionStatus,
    ListArtifactStatusesResponse,
    ListCorpusResponse,
    QueryCorpusRequest,
    QueryCorpusResponse,
    UpdateCorpusRequest,
)
from magick_mind.models.v1.artifact import (
    FinalizeArtifactRequest,
    PresignArtifactRequest,
    PresignArtifactResponse,
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

    # ------------------------------------------------------------------
    # Convenience ingest methods
    # ------------------------------------------------------------------

    async def ingest(
        self,
        corpus_id: str,
        *,
        artifact_id: str,
        api_key: Optional[str] = None,
    ) -> IngestResult:
        """
        Add an already-uploaded artifact to a corpus and return an IngestResult.

        This is a thin wrapper around :meth:`add_artifact` that returns the
        consolidated :class:`~magick_mind.models.v1.corpus.IngestResult` type
        instead of the raw ``AddArtifactsResponse``.

        Args:
            corpus_id: The corpus to ingest the artifact into.
            artifact_id: ID of an existing artifact to add.
            api_key: Optional API key forwarded to :meth:`add_artifact`.

        Returns:
            IngestResult with ``ingestion_status.status`` set to ``"PENDING"``
            (or whatever the server returns immediately after the add call).

        Raises:
            ProblemDetailsException: If the request fails.
        """
        await self.add_artifact(corpus_id, artifact_id, api_key=api_key)
        ingestion = await self.get_ingestion(corpus_id, artifact_id)
        return IngestResult(
            artifact_id=artifact_id,
            corpus_id=corpus_id,
            ingestion_status=ingestion,
        )

    async def upload_and_ingest(
        self,
        corpus_id: str,
        *,
        file: Optional[IO[bytes]] = None,
        content: Optional[bytes] = None,
        file_name: Optional[str] = None,
        content_type: str = "application/octet-stream",
        api_key: Optional[str] = None,
    ) -> IngestResult:
        """
        Upload a file and add it to the corpus in one call.

        Exactly one of *file* or *content* must be supplied.

        The method performs the full presign → S3 upload → finalize →
        add_artifact sequence and returns an :class:`IngestResult`.

        Args:
            corpus_id: The corpus to ingest the artifact into.
            file: A file-like object opened in binary mode.  The caller is
                responsible for opening and closing the file.
            content: Raw bytes to upload.
            file_name: File name to register with the artifact. Required when
                *content* is provided; optional (but recommended) when *file*
                is provided.
            content_type: MIME type of the content
                (default ``"application/octet-stream"``).
            api_key: Optional API key forwarded to :meth:`add_artifact`.

        Returns:
            IngestResult with the artifact and initial ingestion status.

        Raises:
            ValueError: If both or neither of *file*/*content* are provided,
                or if *file_name* is missing when *content* is used.
            ProblemDetailsException: If any API call fails.
        """
        # --- Validate inputs ---
        if file is None and content is None:
            raise ValueError("Exactly one of 'file' or 'content' must be provided.")
        if file is not None and content is not None:
            raise ValueError("Exactly one of 'file' or 'content' must be provided.")

        if content is not None:
            if not file_name:
                raise ValueError("'file_name' is required when 'content' is provided.")
            data = content
            name = file_name
        else:
            # file is guaranteed non-None here (validated above)
            assert file is not None  # satisfy type checker
            import os

            data = file.read()
            name = file_name or os.path.basename(getattr(file, "name", "upload"))

        size_bytes = len(data)

        # --- Presign ---
        presign_req = PresignArtifactRequest(
            file_name=name,
            content_type=content_type,
            size_bytes=size_bytes,
            corpus_id=corpus_id,
        )
        presign_resp_raw = await self._http.post(
            Routes.ARTIFACTS_PRESIGN,
            json=presign_req.model_dump(exclude_none=True),
        )
        presign = PresignArtifactResponse(**presign_resp_raw)

        if not presign.upload_url:
            raise ValueError("Presign response is missing 'upload_url'.")
        if not presign.id:
            raise ValueError("Presign response is missing artifact 'id'.")

        # --- S3 upload ---
        async with httpx.AsyncClient() as s3_client:
            s3_resp = await s3_client.put(
                presign.upload_url,
                content=data,
                headers={"Content-Type": content_type},
            )
        s3_resp.raise_for_status()

        # --- Finalize ---
        finalize_req = FinalizeArtifactRequest(
            artifact_id=presign.id,
            bucket=presign.bucket or "",
            key=presign.key or "",
        )
        await self._http.post(
            Routes.corpus_artifacts_finalize(corpus_id),
            json=finalize_req.model_dump(exclude_none=True),
        )

        # --- Add artifact to corpus ---
        await self.add_artifact(corpus_id, presign.id, api_key=api_key)

        ingestion = await self.get_ingestion(corpus_id, presign.id)
        return IngestResult(
            artifact_id=presign.id,
            corpus_id=corpus_id,
            ingestion_status=ingestion,
        )

    async def ingest_and_poll(
        self,
        corpus_id: str,
        *,
        artifact_id: Optional[str] = None,
        file: Optional[IO[bytes]] = None,
        content: Optional[bytes] = None,
        file_name: Optional[str] = None,
        content_type: str = "application/octet-stream",
        api_key: Optional[str] = None,
        timeout: float = 300.0,
        initial_interval: float = 2.0,
        max_interval: float = 30.0,
        backoff_factor: float = 1.5,
    ) -> IngestResult:
        """
        Ingest an artifact and poll until ingestion completes (or times out).

        Dispatch rules:

        * If *artifact_id* is supplied: calls :meth:`ingest`.
        * Otherwise: calls :meth:`upload_and_ingest` with *file*/*content*.

        After the initial ingest call the method polls
        :meth:`get_ingestion` with exponential back-off until the status
        is ``PROCESSED`` or ``FAILED``, or *timeout* seconds elapse.

        Args:
            corpus_id: The target corpus.
            artifact_id: Existing artifact ID (mutually exclusive with
                *file*/*content*).
            file: File-like object (binary). Forwarded to
                :meth:`upload_and_ingest`.
            content: Raw bytes. Forwarded to :meth:`upload_and_ingest`.
            file_name: File name hint. Forwarded to
                :meth:`upload_and_ingest`.
            content_type: MIME type. Forwarded to
                :meth:`upload_and_ingest`.
            api_key: Optional API key forwarded to the underlying ingest
                methods.
            timeout: Maximum seconds to wait for ingestion to finish
                (default 300).
            initial_interval: Seconds to wait before the first poll
                (default 2.0).
            max_interval: Maximum seconds between polls (default 30.0).
            backoff_factor: Multiplier applied after each poll (default 1.5).

        Returns:
            IngestResult reflecting the terminal ingestion status.

        Raises:
            TimeoutError: If ingestion does not complete within *timeout*
                seconds.
            ProblemDetailsException: If any underlying API call fails.
        """
        if artifact_id is not None:
            result = await self.ingest(
                corpus_id, artifact_id=artifact_id, api_key=api_key
            )
        else:
            result = await self.upload_and_ingest(
                corpus_id,
                file=file,
                content=content,
                file_name=file_name,
                content_type=content_type,
                api_key=api_key,
            )

        aid = result.artifact_id
        elapsed = 0.0
        interval = initial_interval

        while result.ingestion_status.status.upper() not in ("PROCESSED", "FAILED"):
            if elapsed >= timeout:
                raise TimeoutError(
                    f"Ingestion of artifact '{aid}' in corpus '{corpus_id}' "
                    f"did not complete within {timeout}s. "
                    f"Last status: {result.ingestion_status.status}"
                )
            sleep_for = min(interval, max(0.0, timeout - elapsed))
            await asyncio.sleep(sleep_for)
            elapsed += sleep_for
            interval = min(interval * backoff_factor, max_interval)

            ingestion = await self.get_ingestion(corpus_id, aid)
            result = IngestResult(
                artifact_id=aid,
                corpus_id=corpus_id,
                ingestion_status=ingestion,
            )

        return result
