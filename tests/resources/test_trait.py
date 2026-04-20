"""Network-level Trait resource tests using pytest-httpx."""

from __future__ import annotations

import json

from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.models.v1.trait import Trait

from tests.resources._payloads import BASE_URL, PAGING_EMPTY, TRAIT_PAYLOAD


class TestTrait:
    async def test_create(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/traits",
            method="POST",
            json=TRAIT_PAYLOAD,
        )

        result = await client.v1.trait.create(
            name="openness",
            namespace="SYSTEM",
            category="personality",
            display_name="Openness",
            type="NUMERIC",
            visibility="PUBLIC",
            description="Openness to experience",
        )

        assert isinstance(result, Trait)
        assert result.id == "tr-123"
        assert result.name == "openness"
        assert result.namespace == "SYSTEM"
        assert result.category == "personality"
        assert result.display_name == "Openness"
        assert result.type == "NUMERIC"
        assert result.visibility == "PUBLIC"
        assert result.numeric_config is not None
        assert result.numeric_config.min == 0.0
        assert result.numeric_config.max == 1.0

        request = mock_auth.get_requests()[-1]
        assert request.method == "POST"
        assert str(request.url).endswith("/v1/traits")

        body = json.loads(request.content)
        assert body["name"] == "openness"
        assert body["namespace"] == "SYSTEM"
        assert body["category"] == "personality"
        assert body["display_name"] == "Openness"
        assert body["type"] == "NUMERIC"
        assert body["visibility"] == "PUBLIC"
        assert body["description"] == "Openness to experience"

    async def test_get(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/traits/tr-123",
            method="GET",
            json=TRAIT_PAYLOAD,
        )

        result = await client.v1.trait.get("tr-123")

        assert isinstance(result, Trait)
        assert result.id == "tr-123"
        assert result.name == "openness"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert str(request.url).endswith("/v1/traits/tr-123")

    async def test_list(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            method="GET",
            json={
                "data": [TRAIT_PAYLOAD],
                "paging": PAGING_EMPTY,
            },
        )

        result = await client.v1.trait.list(limit=10, order="ASC")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Trait)
        assert result[0].id == "tr-123"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert "/v1/traits" in str(request.url)
        assert "limit=10" in str(request.url)
        assert "order=ASC" in str(request.url)

    async def test_update(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/traits/tr-123",
            method="PUT",
            json=TRAIT_PAYLOAD,
        )

        result = await client.v1.trait.update(
            trait_id="tr-123",
            category="personality",
            display_name="Openness Updated",
            description="Updated description",
            type="NUMERIC",
            default_learning_rate=0.2,
            supports_dyadic=True,
            visibility="ORG",
        )

        assert isinstance(result, Trait)
        assert result.id == "tr-123"

        request = mock_auth.get_requests()[-1]
        assert request.method == "PUT"
        assert str(request.url).endswith("/v1/traits/tr-123")

        body = json.loads(request.content)
        assert body["category"] == "personality"
        assert body["display_name"] == "Openness Updated"
        assert body["description"] == "Updated description"
        assert body["type"] == "NUMERIC"
        assert body["default_learning_rate"] == 0.2
        assert body["supports_dyadic"] is True
        assert body["visibility"] == "ORG"

    async def test_patch(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/traits/tr-123",
            method="PATCH",
            json=TRAIT_PAYLOAD,
        )

        result = await client.v1.trait.patch(
            trait_id="tr-123",
            display_name="Openness Patched",
            visibility="PUBLIC",
        )

        assert isinstance(result, Trait)
        assert result.id == "tr-123"

        request = mock_auth.get_requests()[-1]
        assert request.method == "PATCH"
        assert str(request.url).endswith("/v1/traits/tr-123")

        body = json.loads(request.content)
        assert body["display_name"] == "Openness Patched"
        assert body["visibility"] == "PUBLIC"
        # Fields not passed should not be in the body (exclude_none)
        assert "category" not in body

    async def test_delete(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/traits/tr-123",
            method="DELETE",
            json={},
        )

        await client.v1.trait.delete("tr-123")

        request = mock_auth.get_requests()[-1]
        assert request.method == "DELETE"
        assert str(request.url).endswith("/v1/traits/tr-123")
