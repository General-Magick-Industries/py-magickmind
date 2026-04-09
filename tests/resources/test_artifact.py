"""Network-level tests for Artifact Resource using pytest-httpx."""

from __future__ import annotations

from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from tests.resources._payloads import (
    BASE_URL,
    ARTIFACT_PAYLOAD
)



class TestArtifact:
    async def test_get_returns_artifact(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts/art-123",
            method="GET",
            json={"artifact": ARTIFACT_PAYLOAD},
        )

        from magick_mind.models.v1.artifact import Artifact

        result = await client.v1.artifact.get("art-123")

        assert isinstance(result, Artifact)
        assert result.id == "art-123"
        assert result.status == "ready"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert str(request.url).endswith("/v1/artifacts/art-123")

    async def test_list_returns_artifacts(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            method="GET",
            json={"data": [ARTIFACT_PAYLOAD]},
        )

        from magick_mind.models.v1.artifact import Artifact

        result = await client.v1.artifact.list()

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Artifact)
        assert result[0].id == "art-123"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert "/v1/artifacts" in str(request.url)

    async def test_list_with_filters(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            method="GET",
            json={"data": [ARTIFACT_PAYLOAD]},
        )

        await client.v1.artifact.list(status="ready", cursor="tok-1", limit=10)

        request = mock_auth.get_requests()[-1]
        assert "status=ready" in str(request.url)
        assert "cursor=tok-1" in str(request.url)
        assert "limit=10" in str(request.url)
        # corpus_id must NOT appear
        assert "corpus_id" not in str(request.url)

    async def test_list_no_corpus_id_param(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        """Regression: corpus_id was removed from list(); ensure it's not sent."""
        mock_auth.add_response(
            method="GET",
            json={"data": []},
        )

        await client.v1.artifact.list(end_user_id="eu-1")

        request = mock_auth.get_requests()[-1]
        assert "corpus_id" not in str(request.url)
        assert "end_user_id=eu-1" in str(request.url)

    async def test_delete_sends_delete(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts/art-123",
            method="DELETE",
            status_code=204,
            json={},
        )

        await client.v1.artifact.delete("art-123")

        request = mock_auth.get_requests()[-1]
        assert request.method == "DELETE"
        assert str(request.url).endswith("/v1/artifacts/art-123")

    async def test_download_url_returns_response(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts/art-123/download",
            method="GET",
            json={
                "download_url": "https://s3.example.com/art-123?token=abc",
                "expires_at": 1700003600,
                "file_name": "document.pdf",
            },
        )

        from magick_mind.models.v1.artifact import DownloadUrlResponse

        result = await client.v1.artifact.download_url("art-123")

        assert isinstance(result, DownloadUrlResponse)
        assert result.download_url == "https://s3.example.com/art-123?token=abc"
        assert result.expires_at == 1700003600
        assert result.file_name == "document.pdf"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert str(request.url).endswith("/v1/artifacts/art-123/download")
