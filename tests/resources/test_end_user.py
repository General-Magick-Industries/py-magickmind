"""Network-level EndUser resource tests using pytest-httpx."""

from __future__ import annotations

import json

from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.models.v1.end_user import EndUser

from tests.resources._payloads import BASE_URL, END_USER_PAYLOAD, PAGING_EMPTY


class TestEndUser:
    async def test_create(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-users",
            method="POST",
            json=END_USER_PAYLOAD,
        )

        result = await client.v1.end_user.create(
            name="John Doe",
            external_id="ext-123",
        )

        assert isinstance(result, EndUser)
        assert result.id == "eu-123"
        assert result.name == "John Doe"
        assert result.external_id == "ext-123"

        request = mock_auth.get_requests()[-1]
        assert request.method == "POST"
        assert str(request.url).endswith("/v1/end-users")

        body = json.loads(request.content)
        assert body["name"] == "John Doe"
        assert body["external_id"] == "ext-123"

    async def test_get(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-users/eu-123",
            method="GET",
            json=END_USER_PAYLOAD,
        )

        result = await client.v1.end_user.get("eu-123")

        assert isinstance(result, EndUser)
        assert result.id == "eu-123"
        assert result.name == "John Doe"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert str(request.url).endswith("/v1/end-users/eu-123")

    async def test_query(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        # Don't specify url so it matches GET regardless of query params
        mock_auth.add_response(
            method="GET",
            json={
                "data": [END_USER_PAYLOAD],
                "paging": PAGING_EMPTY,
            },
        )

        result = await client.v1.end_user.query(name="John")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], EndUser)
        assert result[0].id == "eu-123"

        request = mock_auth.get_requests()[-1]
        assert "/v1/end-users" in str(request.url)
        assert "name=John" in str(request.url)

    async def test_delete(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-users/eu-123",
            method="DELETE",
            json={},
        )

        await client.v1.end_user.delete("eu-123")

        request = mock_auth.get_requests()[-1]
        assert request.method == "DELETE"
        assert str(request.url).endswith("/v1/end-users/eu-123")

