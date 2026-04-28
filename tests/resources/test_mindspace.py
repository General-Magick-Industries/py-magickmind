"""Network-level Mindspace resource tests using pytest-httpx."""

from __future__ import annotations

import json

from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind import MindSpaceType
from magick_mind.models.v1.mindspace import (
    GetMindSpaceListResponse,
    MindSpace,
    MindspaceMessagesResponse,
)

import pytest

from magick_mind.exceptions import ProblemDetailsException

from tests.resources._payloads import (
    BASE_URL,
    ERROR_500_ENVELOPE,
    ERROR_ENVELOPE,
    HISTORY_PAYLOAD,
    MINDSPACE_PAYLOAD,
    PAGING_EMPTY,
)


class TestMindspace:
    async def test_create_sends_correct_request(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/mindspaces",
            method="POST",
            json=MINDSPACE_PAYLOAD,
        )

        await client.mindspace.create(
            name="Test Space",
            type=MindSpaceType.PRIVATE,
            description="test",
            project_id="proj-1",
        )

        request = mock_auth.get_requests()[-1]
        assert request.method == "POST"
        assert "/v1/mindspaces" in str(request.url)

        body = json.loads(request.content)
        assert body["name"] == "Test Space"
        assert body["type"] == "PRIVATE"
        assert body["description"] == "test"
        assert body["project_id"] == "proj-1"

    async def test_create_returns_mindspace(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/mindspaces",
            method="POST",
            json=MINDSPACE_PAYLOAD,
        )

        result = await client.mindspace.create(
            name="Test Space",
            type=MindSpaceType.PRIVATE,
        )

        assert isinstance(result, MindSpace)
        assert result.id == "ms-123"
        assert result.name == "Test Space"
        assert result.type == MindSpaceType.PRIVATE
        assert result.project_id == "proj-1"

    async def test_get_returns_mindspace(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/mindspaces/ms-123",
            method="GET",
            json=MINDSPACE_PAYLOAD,
        )

        result = await client.mindspace.get("ms-123")

        assert isinstance(result, MindSpace)
        assert result.id == "ms-123"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert str(request.url).endswith("/v1/mindspaces/ms-123")

    async def test_list_returns_response(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        # Don't specify url so it matches GET regardless of query params
        mock_auth.add_response(
            method="GET",
            json={
                "data": [MINDSPACE_PAYLOAD],
                "paging": PAGING_EMPTY,
            },
        )

        result = await client.mindspace.list(participant_id="user-1")

        assert isinstance(result, GetMindSpaceListResponse)
        assert len(result.data) == 1
        assert result.data[0].id == "ms-123"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert "/v1/mindspaces" in str(request.url)
        assert "participant_id=user-1" in str(request.url)

    async def test_update_sends_put(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        updated = {**MINDSPACE_PAYLOAD, "name": "Updated Space"}
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/mindspaces/ms-123",
            method="PUT",
            json=updated,
        )

        result = await client.mindspace.update(
            mindspace_id="ms-123",
            name="Updated Space",
        )

        assert isinstance(result, MindSpace)
        assert result.name == "Updated Space"

        request = mock_auth.get_requests()[-1]
        assert request.method == "PUT"
        assert str(request.url).endswith("/v1/mindspaces/ms-123")

        body = json.loads(request.content)
        assert body["name"] == "Updated Space"

    async def test_delete_sends_delete(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/mindspaces/ms-123",
            method="DELETE",
            json={},
        )

        await client.mindspace.delete("ms-123")

        request = mock_auth.get_requests()[-1]
        assert request.method == "DELETE"
        assert str(request.url).endswith("/v1/mindspaces/ms-123")

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

        result = await client.mindspace.get_messages("ms-1", limit=20)

        assert isinstance(result, MindspaceMessagesResponse)
        assert len(result.data) == 1
        assert result.data[0].id == "msg-1"
        assert result.data[0].content == "Hello"

        request = mock_auth.get_requests()[-1]
        assert "/v1/mindspaces/ms-1/messages" in str(request.url)
        assert "limit=20" in str(request.url)

    async def test_get_404_raises_problem_details(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/mindspaces/missing",
            method="GET",
            status_code=404,
            json=ERROR_ENVELOPE,
        )

        with pytest.raises(ProblemDetailsException) as exc:
            await client.mindspace.get("missing")

        assert exc.value.status == 404
        assert exc.value.title == "Not Found"

    async def test_create_500_raises_problem_details(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/mindspaces",
            method="POST",
            status_code=500,
            json=ERROR_500_ENVELOPE,
        )

        with pytest.raises(ProblemDetailsException) as exc:
            await client.mindspace.create(
                name="Broken Space", type=MindSpaceType.PRIVATE
            )

        assert exc.value.status == 500
