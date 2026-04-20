"""Network-level tests for CorpusResourceV1.query using pytest-httpx."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.models.v1.corpus import QueryCorpusResponse

from tests.factories import QueryCorpusResponseFactory

BASE_URL = "https://api.test"


class TestCorpusQueryResourceV1:
    @pytest.mark.parametrize("enable_rerank", [None, True, False])
    async def test_query_enable_rerank_payload_and_structured_response(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
        enable_rerank: bool | None,
    ):
        response = QueryCorpusResponseFactory.build(
            result="legacy",
            llm_response="synth",
            entities=[],
            relationships=[],
            chunks=[],
            references=[],
            metadata={"query_mode": "hybrid", "rerank_applied": True},
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/corpus/c-1/query",
            method="POST",
            json=response.model_dump(mode="json"),
        )

        result = await client.v1.corpus.query(
            "c-1",
            query="hello",
            mode="hybrid",
            enable_rerank=enable_rerank,
            api_key="sk-test",
        )

        assert isinstance(result, QueryCorpusResponse)
        assert result.result == "legacy"
        assert result.llm_response == "synth"
        assert result.metadata is not None
        assert result.metadata.query_mode == "hybrid"
        assert result.metadata.rerank_applied is True

        req = mock_auth.get_requests()[-1]
        assert req.headers.get("x-api-key") == "sk-test"
        body = json.loads(req.content)
        assert body["query"] == "hello"
        assert body["mode"] == "hybrid"
        assert body["only_need_context"] is False
        if enable_rerank is None:
            assert "enable_rerank" not in body
        else:
            assert body["enable_rerank"] is enable_rerank
