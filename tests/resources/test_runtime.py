"""Network-level tests for RuntimeResourceV1 using pytest-httpx."""

from __future__ import annotations

import json

from pytest_httpx import HTTPXMock

from magick_mind import MagickMind

import pytest

from magick_mind.exceptions import ProblemDetailsException

from tests.factories import EffectivePersonalityFactory
from tests.resources._payloads import BASE_URL, ERROR_ENVELOPE, ERROR_500_ENVELOPE


class TestRuntimeResource:
    async def test_get_effective_personality_with_and_without_user_id(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        payload = EffectivePersonalityFactory.build(
            persona_id="p-1",
            user_id=None,
            traits=[],
            computed_at="2024-01-01T00:00:00Z",
            ttl_seconds=60,
        )
        payload_dyadic = EffectivePersonalityFactory.build(
            persona_id="p-1",
            user_id="u-1",
            traits=[],
            computed_at="2024-01-01T00:00:00Z",
            ttl_seconds=60,
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/runtime/effective-personality/p-1",
            method="GET",
            json=payload.model_dump(mode="json"),
        )
        mock_auth.add_response(
            method="GET",
            json=payload_dyadic.model_dump(mode="json"),
        )

        result = await client.v1.runtime.get_effective_personality("p-1")
        assert result.persona_id == "p-1"
        assert "user_id=" not in str(mock_auth.get_requests()[-1].url)

        result2 = await client.v1.runtime.get_effective_personality(
            "p-1", user_id="u-1"
        )
        assert result2.user_id == "u-1"
        assert "user_id=u-1" in str(mock_auth.get_requests()[-1].url)

    async def test_invalidate_cache_posts_expected_body(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/runtime/invalidate-cache",
            method="POST",
            json={},
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/runtime/invalidate-cache",
            method="POST",
            json={},
        )

        await client.v1.runtime.invalidate_cache("p-1")
        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body == {"persona_id": "p-1"}

        await client.v1.runtime.invalidate_cache("p-1", user_id="u-1")
        body2 = json.loads(mock_auth.get_requests()[-1].content)
        assert body2 == {"persona_id": "p-1", "user_id": "u-1"}

    async def test_get_effective_personality_404_raises_problem_details(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/runtime/effective-personality/missing",
            method="GET",
            status_code=404,
            json=ERROR_ENVELOPE,
        )

        with pytest.raises(ProblemDetailsException) as exc:
            await client.v1.runtime.get_effective_personality("missing")

        assert exc.value.status == 404
        assert exc.value.title == "Not Found"

    async def test_invalidate_cache_500_raises_problem_details(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/runtime/invalidate-cache",
            method="POST",
            status_code=500,
            json=ERROR_500_ENVELOPE,
        )

        with pytest.raises(ProblemDetailsException) as exc:
            await client.v1.runtime.invalidate_cache("p-err")

        assert exc.value.status == 500
