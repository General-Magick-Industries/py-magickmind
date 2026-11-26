"""Network-level tests for episodic memory reads (search and date range)."""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException

from tests.resources._payloads import BASE_URL, _error_envelope

EPISODE_PAYLOAD = {
    "id": "ep-1",
    "mindspace_id": "ms-1",
    "topic": "travel",
    "subtopics": None,
    "summarized_conversation": "Planned a trip.",
    "what_worked": "",
    "what_to_avoid": "",
    "participant_ids": ["u-1", "agent-1"],
    "entities": ["Paris"],
}


def _query(httpx_mock: HTTPXMock) -> dict[str, list[str]]:
    return parse_qs(urlparse(str(httpx_mock.get_requests()[-1].url)).query)


class TestSearch:
    async def test_search_with_agent_lens(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(method="GET", json={"memory_content": "recalled"})

        result = await client.v1.episode.search(
            "trip", agent_id="agent-1", magickspace_id="ms-1", limit=5
        )

        assert result.memory_content == "recalled"
        url = str(mock_auth.get_requests()[-1].url)
        assert url.startswith(f"{BASE_URL}/v1/episodes/search?")
        assert _query(mock_auth) == {
            "q": ["trip"],
            "agent_id": ["agent-1"],
            "mindspace_id": ["ms-1"],
            "limit": ["5"],
        }

    async def test_search_own_has_no_agent_id(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(method="GET", json={"memory_content": ""})
        agent = MagickMind.from_token(BASE_URL, "jwt-agent")

        await agent.v1.episode.search_own("trip", magickspace_ids=["ms-1", "ms-2"])

        url = str(httpx_mock.get_requests()[-1].url)
        assert url.startswith(f"{BASE_URL}/v1/end-user/episodes/search?")
        assert _query(httpx_mock) == {"q": ["trip"], "mindspace_ids": ["ms-1", "ms-2"]}
        await agent.close()

    async def test_search_own_hints_on_401(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/episodes/search?q=trip",
            method="GET",
            status_code=401,
            json=_error_envelope(401, "Unauthorized", "bad token"),
        )
        agent = MagickMind.from_token(BASE_URL, "jwt-agent")

        with pytest.raises(ProblemDetailsException) as exc:
            await agent.v1.episode.search_own("trip")

        assert "end-user JWT" in str(exc.value)
        assert "non-_own method with agent_id" in str(exc.value)
        assert (
            httpx_mock.get_requests()[-1].headers["Authorization"] == "Bearer jwt-agent"
        )
        await agent.close()


class TestRange:
    async def test_list_range(self, client: MagickMind, mock_auth: HTTPXMock):
        mock_auth.add_response(method="GET", json={"data": [EPISODE_PAYLOAD]})

        result = await client.v1.episode.list_range(
            date_start="2026-08-01",
            date_end="2026-08-31",
            agent_id="__neutral__",
            magickspace_id="ms-1",
            limit=10,
        )

        episode = result.data[0]
        assert episode.id == "ep-1"
        assert episode.subtopics == []
        assert episode.entities == ["Paris"]
        url = str(mock_auth.get_requests()[-1].url)
        assert url.startswith(f"{BASE_URL}/v1/episodes/range?")
        assert _query(mock_auth) == {
            "date_start": ["2026-08-01"],
            "date_end": ["2026-08-31"],
            "agent_id": ["__neutral__"],
            "mindspace_id": ["ms-1"],
            "limit": ["10"],
        }

    async def test_list_range_own(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(method="GET", json={"data": None})
        agent = MagickMind.from_token(BASE_URL, "jwt-agent")

        result = await agent.v1.episode.list_range_own(
            date_start="2026-08-01", date_end="2026-08-02"
        )

        assert result.data == []
        url = str(httpx_mock.get_requests()[-1].url)
        assert url.startswith(f"{BASE_URL}/v1/end-user/episodes/range?")
        assert "agent_id" not in url
        await agent.close()


class TestProcessIdempotency:
    async def test_process_own_sends_client_message_id(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/episodes/process",
            method="POST",
            json={"message_processed": True, "deduplicated": True},
        )
        agent = MagickMind.from_token(BASE_URL, "jwt-agent")

        result = await agent.v1.episode.process_own(
            magickspace_id="ms-1",
            sender_id="u-1",
            message="hi",
            message_id="m-1",
            client_message_id="c-1",
        )

        assert result.deduplicated is True
        body = json.loads(httpx_mock.get_requests()[-1].content)
        assert body["client_message_id"] == "c-1"
        await agent.close()
