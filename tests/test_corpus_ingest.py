"""Tests for corpus convenience ingest methods.

Covers:
- CorpusResourceV1.ingest()
- CorpusResourceV1.upload_and_ingest()
- CorpusResourceV1.ingest_and_poll()
- IngestResult model
"""

from __future__ import annotations

import io
import json
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.models.v1.corpus import IngestResult, IngestionStatus

BASE_URL = "https://api.test"
S3_PRESIGNED_URL = "https://s3.example.com/presigned-upload?token=abc"

# ---------------------------------------------------------------------------
# Reusable fixtures / payloads
# ---------------------------------------------------------------------------

ADD_ARTIFACTS_RESPONSE = {"added_count": 1, "failed_artifact_ids": []}

INGESTION_STATUS_PENDING = {
    "statuses": [
        {
            "artifact_id": "art-1",
            "status": "PENDING",
            "content_summary": None,
            "content_length": None,
            "created_at": None,
            "updated_at": None,
            "error": None,
        }
    ]
}

INGESTION_STATUS_PROCESSED = {
    "statuses": [
        {
            "artifact_id": "art-1",
            "status": "PROCESSED",
            "content_summary": "Some summary",
            "content_length": 1024,
            "created_at": None,
            "updated_at": None,
            "error": None,
        }
    ]
}

INGESTION_STATUS_FAILED = {
    "statuses": [
        {
            "artifact_id": "art-1",
            "status": "FAILED",
            "content_summary": None,
            "content_length": None,
            "created_at": None,
            "updated_at": None,
            "error": "parsing failed",
        }
    ]
}

PRESIGN_RESPONSE: dict[str, Any] = {
    "success": True,
    "id": "art-1",
    "bucket": "mm-bucket",
    "key": "uploads/art-1/file.txt",
    "upload_url": "https://s3.example.com/presigned-upload?token=abc",
    "expires_at": 1700003600,
    "required_headers": None,
}

FINALIZE_RESPONSE: dict[str, Any] = {"success": True, "message": "finalized"}


# ---------------------------------------------------------------------------
# TestIngestResult model
# ---------------------------------------------------------------------------


class TestIngestResultModel:
    def test_fields_are_accessible(self) -> None:
        status = IngestionStatus(status="PENDING")
        result = IngestResult(
            artifact_id="art-1",
            corpus_id="corp-1",
            ingestion_status=status,
        )
        assert result.artifact_id == "art-1"
        assert result.corpus_id == "corp-1"
        assert result.ingestion_status.status == "PENDING"

    def test_ingestion_status_fields_propagate(self) -> None:
        status = IngestionStatus(
            status="PROCESSED",
            content_summary="doc summary",
            content_length=512,
            error=None,
        )
        result = IngestResult(
            artifact_id="art-42",
            corpus_id="corp-99",
            ingestion_status=status,
        )
        assert result.ingestion_status.content_summary == "doc summary"
        assert result.ingestion_status.content_length == 512


# ---------------------------------------------------------------------------
# TestIngest
# ---------------------------------------------------------------------------


class TestIngest:
    async def test_calls_add_artifact_then_get_ingestion(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        # add_artifact
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        # get_ingestion → list_ingestion endpoint
        mock_auth.add_response(
            method="GET",
            json=INGESTION_STATUS_PENDING,
        )

        result = await client.v1.corpus.ingest("corp-1", artifact_id="art-1")

        assert isinstance(result, IngestResult)
        assert result.artifact_id == "art-1"
        assert result.corpus_id == "corp-1"
        assert result.ingestion_status.status == "PENDING"

        requests = mock_auth.get_requests()
        # login + add_artifact + get_ingestion = 3 calls
        assert any(
            r.method == "POST" and "/v1/corpus/corp-1/artifacts" in str(r.url)
            for r in requests
        )
        assert any(
            r.method == "GET" and "/v1/corpus/corp-1/artifacts/status" in str(r.url)
            for r in requests
        )

    async def test_returns_ingest_result_type(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PENDING)

        result = await client.v1.corpus.ingest("corp-1", artifact_id="art-1")

        assert isinstance(result, IngestResult)

    async def test_forwards_api_key_header(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PENDING)

        await client.v1.corpus.ingest(
            "corp-1", artifact_id="art-1", api_key="sk-secret"
        )

        post_req = next(
            r
            for r in mock_auth.get_requests()
            if r.method == "POST" and "/v1/corpus/corp-1/artifacts" in str(r.url)
        )
        assert post_req.headers.get("x-api-key") == "sk-secret"


# ---------------------------------------------------------------------------
# TestUploadAndIngest
# ---------------------------------------------------------------------------


class TestUploadAndIngest:
    @pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
    async def test_rejects_no_file_or_content(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        with pytest.raises(ValueError, match="Exactly one"):
            await client.v1.corpus.upload_and_ingest("corp-1")

    @pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
    async def test_rejects_both_file_and_content(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        with pytest.raises(ValueError, match="Exactly one"):
            await client.v1.corpus.upload_and_ingest(
                "corp-1",
                file=io.BytesIO(b"data"),
                content=b"data",
            )

    @pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
    async def test_requires_file_name_with_content(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        with pytest.raises(ValueError, match="file_name"):
            await client.v1.corpus.upload_and_ingest("corp-1", content=b"hello")

    async def test_full_flow_with_content(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        # presign
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts/presign",
            method="POST",
            json=PRESIGN_RESPONSE,
        )
        # S3 presigned upload
        mock_auth.add_response(
            url=S3_PRESIGNED_URL,
            method="PUT",
            status_code=200,
        )
        # finalize
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts/finalize",
            method="POST",
            json=FINALIZE_RESPONSE,
        )
        # add_artifact
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        # get_ingestion
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PENDING)

        result = await client.v1.corpus.upload_and_ingest(
            "corp-1",
            content=b"hello world",
            file_name="hello.txt",
            content_type="text/plain",
        )

        assert isinstance(result, IngestResult)
        assert result.artifact_id == "art-1"
        assert result.corpus_id == "corp-1"
        assert result.ingestion_status.status == "PENDING"

        # Verify S3 PUT was called with presigned URL
        requests = mock_auth.get_requests()
        s3_req = next(
            r for r in requests if r.method == "PUT" and "s3.example.com" in str(r.url)
        )
        assert str(s3_req.url) == S3_PRESIGNED_URL
        assert s3_req.content == b"hello world"

    async def test_full_flow_with_file_object(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts/presign",
            method="POST",
            json=PRESIGN_RESPONSE,
        )
        # S3 presigned upload
        mock_auth.add_response(
            url=S3_PRESIGNED_URL,
            method="PUT",
            status_code=200,
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts/finalize",
            method="POST",
            json=FINALIZE_RESPONSE,
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PENDING)

        buf = io.BytesIO(b"file content")
        result = await client.v1.corpus.upload_and_ingest(
            "corp-1",
            file=buf,
            file_name="doc.pdf",
            content_type="application/pdf",
        )

        assert isinstance(result, IngestResult)
        assert result.artifact_id == "art-1"

    async def test_presign_sends_corpus_id(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts/presign",
            method="POST",
            json=PRESIGN_RESPONSE,
        )
        # S3 presigned upload
        mock_auth.add_response(
            url=S3_PRESIGNED_URL,
            method="PUT",
            status_code=200,
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts/finalize",
            method="POST",
            json=FINALIZE_RESPONSE,
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PENDING)

        await client.v1.corpus.upload_and_ingest(
            "corp-1",
            content=b"data",
            file_name="test.txt",
        )

        presign_req = next(
            r
            for r in mock_auth.get_requests()
            if r.method == "POST" and "/v1/artifacts/presign" in str(r.url)
        )
        body = json.loads(presign_req.content)
        assert body["corpus_id"] == "corp-1"
        assert body["file_name"] == "test.txt"
        assert body["size_bytes"] == 4  # len(b"data")


# ---------------------------------------------------------------------------
# TestIngestAndPoll
# ---------------------------------------------------------------------------


class TestIngestAndPoll:
    async def test_returns_immediately_when_processed(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        # ingest path: add_artifact + get_ingestion (already PROCESSED)
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PROCESSED)

        result = await client.v1.corpus.ingest_and_poll(
            "corp-1",
            artifact_id="art-1",
        )

        assert isinstance(result, IngestResult)
        assert result.ingestion_status.status == "PROCESSED"

    async def test_polls_until_processed(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        # First get_ingestion → PENDING
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PENDING)
        # Second get_ingestion (poll 1) → PENDING
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PENDING)
        # Third get_ingestion (poll 2) → PROCESSED
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PROCESSED)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.v1.corpus.ingest_and_poll(
                "corp-1",
                artifact_id="art-1",
                initial_interval=0.01,
                max_interval=0.1,
            )

        assert result.ingestion_status.status == "PROCESSED"

    async def test_stops_on_failed_status(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        # Initial get_ingestion → PENDING
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PENDING)
        # Poll → FAILED
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_FAILED)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.v1.corpus.ingest_and_poll(
                "corp-1",
                artifact_id="art-1",
                initial_interval=0.01,
            )

        assert result.ingestion_status.status == "FAILED"
        assert result.ingestion_status.error == "parsing failed"

    @pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
    async def test_raises_timeout_error(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        # Always PENDING
        for _ in range(5):
            mock_auth.add_response(method="GET", json=INGESTION_STATUS_PENDING)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TimeoutError, match="did not complete"):
                await client.v1.corpus.ingest_and_poll(
                    "corp-1",
                    artifact_id="art-1",
                    timeout=0.001,  # tiny timeout so first sleep exhausts it
                    initial_interval=1.0,
                )

    async def test_dispatches_to_upload_and_ingest_without_artifact_id(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ) -> None:
        # upload_and_ingest path
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts/presign",
            method="POST",
            json=PRESIGN_RESPONSE,
        )
        # S3 presigned upload
        mock_auth.add_response(
            url=S3_PRESIGNED_URL,
            method="PUT",
            status_code=200,
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts/finalize",
            method="POST",
            json=FINALIZE_RESPONSE,
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/corp-1/artifacts",
            method="POST",
            json=ADD_ARTIFACTS_RESPONSE,
        )
        # Initial get_ingestion (from upload_and_ingest) → PROCESSED directly
        mock_auth.add_response(method="GET", json=INGESTION_STATUS_PROCESSED)

        result = await client.v1.corpus.ingest_and_poll(
            "corp-1",
            content=b"hello",
            file_name="hello.txt",
        )

        assert isinstance(result, IngestResult)
        assert result.artifact_id == "art-1"
        assert result.ingestion_status.status == "PROCESSED"
