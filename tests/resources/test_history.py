"""Network-level History resource tests using pytest-httpx."""

from __future__ import annotations

from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.models.v1.history import HistoryResponse

import pytest

from tests.resources._payloads import BASE_URL, ERROR_ENVELOPE, HISTORY_PAYLOAD
from magick_mind.exceptions import ProblemDetailsException


class TestHistory:
    async def test_get_messages(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        # Don't specify url so it matches GET regardless of query params
        mock_auth.add_response(
            method="GET",
            json=HISTORY_PAYLOAD,
        )

        result = await client.v1.history.get_messages("ms-1", limit=10)

        assert isinstance(result, HistoryResponse)
        assert len(result.data) == 1
        assert result.data[0].id == "msg-1"
        assert result.data[0].content == "Hello"
        assert result.has_more is False

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert "/v1/magickspaces/ms-1/messages" in str(request.url)
        assert "limit=10" in str(request.url)

    async def test_get_messages_with_cursor(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        # Don't specify url so it matches GET regardless of query params
        mock_auth.add_response(
            method="GET",
            json={
                "data": [],
                "paging": {
                    "cursors": {"after": "msg-10", "before": None},
                    "has_more": True,
                    "has_previous": False,
                },
            },
        )

        result = await client.v1.history.get_messages("ms-1", cursor="msg-5", limit=10)

        assert result.has_more is True

        request = mock_auth.get_requests()[-1]
        assert "/v1/magickspaces/ms-1/messages" in str(request.url)
        assert "cursor=msg-5" in str(request.url)

    async def test_get_messages_404_raises_problem_details(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/magickspaces/missing/messages",
            method="GET",
            status_code=404,
            json=ERROR_ENVELOPE,
        )

        with pytest.raises(ProblemDetailsException) as exc:
            await client.v1.history.get_messages("missing")

        assert exc.value.status == 404
