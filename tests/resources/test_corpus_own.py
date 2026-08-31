"""Network-level tests for the end-user corpus query."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException

from tests.resources._payloads import BASE_URL, _error_envelope

QUERY_RESPONSE = {
    "result": "",
    "entities": [],
    "relationships": [],
    "chunks": [{"content": "Policy text", "score": 0.9}],
    "references": [],
    "llm_response": "Answer",
}


class TestQueryOwn:
    async def test_query_own(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/corpus/c-1/query",
            method="POST",
            json=QUERY_RESPONSE,
        )
        agent = MagickMind.from_token(BASE_URL, "jwt-agent")

        result = await agent.v1.corpus.query_own(
            "c-1", query="leave policy", enable_rerank=True, api_key="mm_key"
        )

        assert result.llm_response == "Answer"
        request = httpx_mock.get_requests()[-1]
        assert request.headers["x-api-key"] == "mm_key"
        assert request.headers["Authorization"] == "Bearer jwt-agent"
        assert json.loads(request.content) == {
            "query": "leave policy",
            "only_need_context": False,
            "enable_rerank": True,
        }
        await agent.close()

    async def test_query_own_omits_api_key_header_when_unset(
        self, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/corpus/c-1/query",
            method="POST",
            json=QUERY_RESPONSE,
        )
        agent = MagickMind.from_token(BASE_URL, "jwt-agent")

        await agent.v1.corpus.query_own("c-1", query="q", mode="local")

        request = httpx_mock.get_requests()[-1]
        assert "x-api-key" not in request.headers
        assert json.loads(request.content)["mode"] == "local"
        await agent.close()

    async def test_query_own_hints_on_unknown_corpus(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/corpus/c-x/query",
            method="POST",
            status_code=404,
            json=_error_envelope(404, "Not Found", "corpus not found"),
        )
        agent = MagickMind.from_token(BASE_URL, "jwt-agent")

        with pytest.raises(ProblemDetailsException) as exc:
            await agent.v1.corpus.query_own("c-x", query="q")

        assert "'c-x' is unknown to this tenant" in str(exc.value)
        await agent.close()
