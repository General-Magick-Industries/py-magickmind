"""Network-level tests for magickspace-scoped and end-user artifact operations."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind

from tests.resources._payloads import BASE_URL

BIFROST_ARTIFACT = {
    "id": "art-1",
    "bucket": "mm-bucket",
    "key": "spaces/ms-1/art-1.png",
    "s3_url": "s3://mm-bucket/spaces/ms-1/art-1.png",
    "content_type": "image/png",
    "size_bytes": 2048,
    "status": "ready",
    "tenant_id": "t-1",
    "end_user_id": "agent-1",
    "original_filename": "snap.png",
    "created_at": "2026-08-31T00:00:00Z",
    "updated_at": "2026-08-31T00:00:00Z",
}

PRESIGN_RESPONSE = {
    "id": "art-1",
    "bucket": "mm-bucket",
    "key": "spaces/ms-1/art-1.png",
    "s3_url": "s3://mm-bucket/spaces/ms-1/art-1.png",
    "upload_url": "https://s3.test/put",
    "expires_at": 1_800_000_000,
    "required_headers": {"Content-Type": "image/png"},
}


@pytest.fixture
async def agent():
    client = MagickMind.from_token(BASE_URL, "jwt-agent")
    yield client
    await client.close()


class TestServiceUserScoped:
    async def test_list_sends_bifrost_pagination_params(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        """The server's list route pages with page_size/page_token; the
        cursor/limit names were silently ignored."""
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts?status=ready&page_token=p2&page_size=5",
            method="GET",
            json={"artifacts": [BIFROST_ARTIFACT], "next_page_token": "p3"},
        )

        artifacts = await client.v1.artifact.list(status="ready", cursor="p2", limit=5)

        assert [a.id for a in artifacts] == ["art-1"]

    async def test_presign_upload_to_magickspace(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/magickspaces/ms-1/artifacts/presign",
            method="POST",
            json=PRESIGN_RESPONSE,
        )

        presigned = await client.v1.artifact.presign_upload_to_magickspace(
            "ms-1", content_type="image/png", size_bytes=2048, end_user_id="agent-1"
        )

        assert presigned.upload_url == "https://s3.test/put"
        assert json.loads(mock_auth.get_requests()[-1].content) == {
            "content_type": "image/png",
            "size_bytes": 2048,
            "end_user_id": "agent-1",
        }


class TestEndUserScoped:
    async def test_presign_and_finalize_own(
        self, agent: MagickMind, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/magickspaces/ms-1/artifacts/presign",
            method="POST",
            json=PRESIGN_RESPONSE,
        )
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/magickspaces/ms-1/artifacts/finalize",
            method="POST",
            json={},
        )

        presigned = await agent.v1.artifact.presign_own_upload(
            "ms-1", content_type="image/png", size_bytes=2048, file_name="snap.png"
        )
        assert presigned.id == "art-1"
        assert json.loads(httpx_mock.get_requests()[-1].content) == {
            "file_name": "snap.png",
            "content_type": "image/png",
            "size_bytes": 2048,
        }

        await agent.v1.artifact.finalize_own(
            "ms-1", artifact_id="art-1", bucket="mm-bucket", key="spaces/ms-1/art-1.png"
        )
        assert json.loads(httpx_mock.get_requests()[-1].content) == {
            "artifact_id": "art-1",
            "bucket": "mm-bucket",
            "key": "spaces/ms-1/art-1.png",
        }

    async def test_list_own_reads_bifrost_envelope(
        self, agent: MagickMind, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            method="GET",
            json={"artifacts": [BIFROST_ARTIFACT], "next_page_token": "p2"},
        )

        page = await agent.v1.artifact.list_own("ms-1", status="ready", page_size=1)

        assert page.data[0].id == "art-1"
        assert page.data[0].created_at == "2026-08-31T00:00:00Z"
        assert page.next_page_token == "p2"
        url = str(httpx_mock.get_requests()[-1].url)
        assert "/v1/end-user/magickspaces/ms-1/artifacts?" in url
        assert "status=ready" in url and "page_size=1" in url

    async def test_get_download_delete_own(
        self, agent: MagickMind, httpx_mock: HTTPXMock
    ):
        base = f"{BASE_URL}/v1/end-user/magickspaces/ms-1/artifacts/art-1"
        httpx_mock.add_response(url=base, method="GET", json=BIFROST_ARTIFACT)
        httpx_mock.add_response(
            url=f"{base}/download",
            method="GET",
            json={
                "id": "art-1",
                "download_url": "https://s3.test/get",
                "expires_at": 1_800_000_000,
                "content_type": "image/png",
                "file_name": "snap.png",
            },
        )
        httpx_mock.add_response(
            url=base, method="DELETE", json={"success": True, "already_deleted": False}
        )

        artifact = await agent.v1.artifact.get_own("ms-1", "art-1")
        assert artifact.original_filename == "snap.png"

        download = await agent.v1.artifact.download_url_own("ms-1", "art-1")
        assert download.download_url == "https://s3.test/get"
        assert download.content_type == "image/png"

        deleted = await agent.v1.artifact.delete_own("ms-1", "art-1")
        assert deleted.success is True
        assert deleted.already_deleted is False


class TestOwned:
    async def test_owned_operations_need_no_membership(
        self, agent: MagickMind, httpx_mock: HTTPXMock
    ):
        base = f"{BASE_URL}/v1/end-user/artifacts/art-1"
        httpx_mock.add_response(url=base, method="GET", json=BIFROST_ARTIFACT)
        httpx_mock.add_response(
            url=f"{base}/download",
            method="GET",
            json={"download_url": "https://s3.test/get", "expires_at": 1},
        )
        httpx_mock.add_response(
            url=base, method="DELETE", json={"success": True, "already_deleted": True}
        )

        assert (await agent.v1.artifact.get_uploaded("art-1")).id == "art-1"
        assert (
            await agent.v1.artifact.download_url_uploaded("art-1")
        ).download_url == "https://s3.test/get"
        assert (
            await agent.v1.artifact.delete_uploaded("art-1")
        ).already_deleted is True
