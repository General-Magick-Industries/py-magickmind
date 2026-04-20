"""Network-level Project resource tests using pytest-httpx."""

from __future__ import annotations

import json

from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.models.v1.project import Project

import pytest

from magick_mind.exceptions import ProblemDetailsException

from tests.resources._payloads import BASE_URL, ERROR_ENVELOPE, PAGING_EMPTY, PROJECT_PAYLOAD


class TestProject:
    async def test_create(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/projects",
            method="POST",
            json=PROJECT_PAYLOAD,
        )

        result = await client.v1.project.create(
            name="Test Project",
            description="test",
        )

        assert isinstance(result, Project)
        assert result.id == "proj-123"
        assert result.name == "Test Project"
        assert result.created_by == "user-1"

        request = mock_auth.get_requests()[-1]
        assert request.method == "POST"
        assert str(request.url).endswith("/v1/projects")

        body = json.loads(request.content)
        assert body["name"] == "Test Project"
        assert body["description"] == "test"

    async def test_get(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/projects/proj-123",
            method="GET",
            json=PROJECT_PAYLOAD,
        )

        result = await client.v1.project.get("proj-123")

        assert isinstance(result, Project)
        assert result.id == "proj-123"
        assert result.name == "Test Project"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert str(request.url).endswith("/v1/projects/proj-123")

    async def test_list(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/projects",
            method="GET",
            json={
                "data": [PROJECT_PAYLOAD],
                "paging": PAGING_EMPTY,
            },
        )

        result = await client.v1.project.list()

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Project)
        assert result[0].id == "proj-123"

    async def test_delete(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/projects/proj-123",
            method="DELETE",
            json={},
        )

        await client.v1.project.delete("proj-123")

        request = mock_auth.get_requests()[-1]
        assert request.method == "DELETE"
        assert str(request.url).endswith("/v1/projects/proj-123")

    async def test_get_404_raises_problem_details(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/projects/missing",
            method="GET",
            status_code=404,
            json=ERROR_ENVELOPE,
        )

        with pytest.raises(ProblemDetailsException) as exc:
            await client.v1.project.get("missing")

        assert exc.value.status == 404
        assert exc.value.title == "Not Found"
