"""Network-level resource tests using pytest-httpx.

Tests verify that each resource makes the correct HTTP requests and correctly
deserializes the responses. All resources share the same HTTPClient._handle_response,
so error-handling tests are only in TestChatSend.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException, RateLimitError
from magick_mind.models.v1.chat import ConfigSchema
from magick_mind.models.v1.end_user import EndUser
from magick_mind.models.v1.history import HistoryResponse
from magick_mind.models.v1.mindspace import (
    GetMindSpaceListResponse,
    MindSpace,
    MindspaceMessagesResponse,
)
from magick_mind.models.v1.project import Project
from magick_mind.models.v1.trait import Trait

BASE_URL = "https://api.test"

# ---------------------------------------------------------------------------
# Reusable response payloads
# ---------------------------------------------------------------------------

MINDSPACE_PAYLOAD = {
    "id": "ms-123",
    "name": "Test Space",
    "type": "PRIVATE",
    "description": "test",
    "project_id": "proj-1",
    "created_by": "user-1",
    "updated_by": "user-1",
    "corpus_ids": [],
    "participant_ids": [],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

PROJECT_PAYLOAD = {
    "id": "proj-123",
    "name": "Test Project",
    "description": "test",
    "corpus_ids": [],
    "created_by": "user-1",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

END_USER_PAYLOAD = {
    "id": "eu-123",
    "name": "John Doe",
    "external_id": "ext-123",
    "tenant_id": "t-1",
    "created_by": None,
    "updated_by": None,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

HISTORY_PAYLOAD = {
    "data": [
        {
            "id": "msg-1",
            "mindspace_id": "ms-1",
            "content": "Hello",
            "sent_by_user_id": "user-1",
            "create_at": "2024-01-01T00:00:00Z",
            "update_at": "2024-01-01T00:00:00Z",
        }
    ],
    "paging": {
        "cursors": {"after": None, "before": None},
        "has_more": False,
        "has_previous": False,
    },
}

PAGING_EMPTY = {
    "cursors": {"after": None, "before": None},
    "has_more": False,
    "has_previous": False,
}

TRAIT_PAYLOAD = {
    "id": "tr-123",
    "name": "openness",
    "namespace": "SYSTEM",
    "owner_id": None,
    "category": "personality",
    "display_name": "Openness",
    "description": "Openness to experience",
    "type": "NUMERIC",
    "numeric_config": {"min": 0.0, "max": 1.0, "default": 0.5},
    "categorical_config": None,
    "multilabel_config": None,
    "default_lock": None,
    "default_learning_rate": 0.1,
    "supports_dyadic": False,
    "visibility": "PUBLIC",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

ERROR_ENVELOPE = {
    "error": {
        "type": "https://example.com/not-found",
        "title": "Not Found",
        "status": 404,
        "detail": "Resource not found",
        "request_id": "req-abc123",
    }
}


# ---------------------------------------------------------------------------
# TestChatSend
# ---------------------------------------------------------------------------


class TestChatSend:
    @pytest.fixture
    def chat_response(self) -> dict[str, Any]:
        return {
            "content": {
                "message_id": "msg-1",
                "content": "Hi!",
                "reply_to": None,
            }
        }

    async def test_sends_correct_request(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
        chat_response: dict[str, Any],
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/chat/magickmind",
            method="POST",
            json=chat_response,
        )

        await client.chat.send(
            api_key="sk-test",
            mindspace_id="ms-1",
            message="Hello",
            enduser_id="u-1",
            fast_model_id="gpt-4",
            smart_model_ids=["gpt-4"],
            compute_power=50,
        )

        request = mock_auth.get_requests()[-1]
        assert request.method == "POST"
        assert "/v1/chat/magickmind" in str(request.url)

        body = json.loads(request.content)
        assert body["api_key"] == "sk-test"
        assert body["mindspace_id"] == "ms-1"
        assert body["message"] == "Hello"
        assert body["enduser_id"] == "u-1"
        assert body["config"]["fast_model_id"] == "gpt-4"

    async def test_includes_optional_params(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
        chat_response: dict[str, Any],
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/chat/magickmind",
            method="POST",
            json=chat_response,
        )

        await client.chat.send(
            api_key="sk-test",
            mindspace_id="ms-1",
            message="Reply",
            enduser_id="u-1",
            fast_model_id="gpt-4",
            smart_model_ids=["gpt-4"],
            reply_to_message_id="msg-0",
            additional_context="Some context",
            artifact_ids=["art-1", "art-2"],
        )

        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body["reply_to_message_id"] == "msg-0"
        assert body["additional_context"] == "Some context"
        assert body["artifact_ids"] == ["art-1", "art-2"]

    async def test_deserializes_response(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
        chat_response: dict[str, Any],
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/chat/magickmind",
            method="POST",
            json=chat_response,
        )

        from magick_mind.models.v1.chat import ChatSendResponse

        result = await client.chat.send(
            api_key="sk-test",
            mindspace_id="ms-1",
            message="Hello",
            enduser_id="u-1",
            fast_model_id="gpt-4",
            smart_model_ids=["gpt-4"],
        )

        assert isinstance(result, ChatSendResponse)
        assert result.content is not None
        assert result.content.message_id == "msg-1"
        assert result.content.content == "Hi!"

    async def test_config_override_takes_precedence(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
        chat_response: dict[str, Any],
    ):
        """Passing config= directly overrides flat model params (backward compat)."""
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/chat/magickmind",
            method="POST",
            json=chat_response,
        )

        await client.chat.send(
            api_key="sk-test",
            mindspace_id="ms-1",
            message="Hello",
            enduser_id="u-1",
            config=ConfigSchema(
                fast_model_id="gpt-4-override",
                smart_model_ids=["gpt-4-override"],
                compute_power=99,
            ),
        )

        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body["config"]["fast_model_id"] == "gpt-4-override"
        assert body["config"]["compute_power"] == 99

    async def test_404_raises_problem_details(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/chat/magickmind",
            method="POST",
            status_code=404,
            json=ERROR_ENVELOPE,
        )

        with pytest.raises(ProblemDetailsException) as exc_info:
            await client.chat.send(
                api_key="sk-test",
                mindspace_id="ms-1",
                message="Hello",
                enduser_id="u-1",
                fast_model_id="gpt-4",
                smart_model_ids=["gpt-4"],
            )

        exc = exc_info.value
        assert exc.status == 404
        assert exc.title == "Not Found"
        assert exc.request_id == "req-abc123"

    async def test_429_raises_rate_limit(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/chat/magickmind",
            method="POST",
            status_code=429,
            json={
                "error": {
                    "type": "about:blank",
                    "title": "Too Many Requests",
                    "status": 429,
                    "detail": "Rate limit exceeded",
                    "request_id": "req-ratelimit",
                }
            },
        )

        with pytest.raises(RateLimitError):
            await client.chat.send(
                api_key="sk-test",
                mindspace_id="ms-1",
                message="Hello",
                enduser_id="u-1",
                fast_model_id="gpt-4",
                smart_model_ids=["gpt-4"],
            )


# ---------------------------------------------------------------------------
# TestMindspace
# ---------------------------------------------------------------------------


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
            type="PRIVATE",
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

        result = await client.mindspace.create(name="Test Space", type="PRIVATE")

        assert isinstance(result, MindSpace)
        assert result.id == "ms-123"
        assert result.name == "Test Space"
        assert result.type == "PRIVATE"
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


# ---------------------------------------------------------------------------
# TestProject
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TestEndUser
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TestTrait
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TestHistory
# ---------------------------------------------------------------------------


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
        assert "/v1/mindspaces/ms-1/messages" in str(request.url)
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
        assert "/v1/mindspaces/ms-1/messages" in str(request.url)
        assert "cursor=msg-5" in str(request.url)


# ---------------------------------------------------------------------------
# TestArtifact
# ---------------------------------------------------------------------------

ARTIFACT_PAYLOAD = {
    "id": "art-123",
    "bucket": "mm-bucket",
    "key": "uploads/art-123/document.pdf",
    "s3_url": "s3://mm-bucket/uploads/art-123/document.pdf",
    "content_type": "application/pdf",
    "size_bytes": 102400,
    "status": "ready",
    "corpus_id": None,
    "end_user_id": "eu-1",
    "created_by": "acc-1",
    "created_at": 1700000000,
    "updated_at": 1700000100,
    "etag": None,
    "version_id": None,
    "error_code": None,
}


class TestArtifact:
    async def test_get_returns_artifact(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts/art-123",
            method="GET",
            json={"artifact": ARTIFACT_PAYLOAD},
        )

        from magick_mind.models.v1.artifact import Artifact

        result = await client.v1.artifact.get("art-123")

        assert isinstance(result, Artifact)
        assert result.id == "art-123"
        assert result.status == "ready"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert str(request.url).endswith("/v1/artifacts/art-123")

    async def test_list_returns_artifacts(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            method="GET",
            json={"data": [ARTIFACT_PAYLOAD]},
        )

        from magick_mind.models.v1.artifact import Artifact

        result = await client.v1.artifact.list()

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Artifact)
        assert result[0].id == "art-123"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert "/v1/artifacts" in str(request.url)

    async def test_list_with_filters(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            method="GET",
            json={"data": [ARTIFACT_PAYLOAD]},
        )

        await client.v1.artifact.list(status="ready", cursor="tok-1", limit=10)

        request = mock_auth.get_requests()[-1]
        assert "status=ready" in str(request.url)
        assert "cursor=tok-1" in str(request.url)
        assert "limit=10" in str(request.url)
        # corpus_id must NOT appear
        assert "corpus_id" not in str(request.url)

    async def test_list_no_corpus_id_param(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        """Regression: corpus_id was removed from list(); ensure it's not sent."""
        mock_auth.add_response(
            method="GET",
            json={"data": []},
        )

        await client.v1.artifact.list(end_user_id="eu-1")

        request = mock_auth.get_requests()[-1]
        assert "corpus_id" not in str(request.url)
        assert "end_user_id=eu-1" in str(request.url)

    async def test_delete_sends_delete(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts/art-123",
            method="DELETE",
            status_code=204,
            json={},
        )

        await client.v1.artifact.delete("art-123")

        request = mock_auth.get_requests()[-1]
        assert request.method == "DELETE"
        assert str(request.url).endswith("/v1/artifacts/art-123")

    async def test_download_url_returns_response(
        self,
        client: MagickMind,
        mock_auth: HTTPXMock,
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/artifacts/art-123/download",
            method="GET",
            json={
                "download_url": "https://s3.example.com/art-123?token=abc",
                "expires_at": 1700003600,
                "file_name": "document.pdf",
            },
        )

        from magick_mind.models.v1.artifact import DownloadUrlResponse

        result = await client.v1.artifact.download_url("art-123")

        assert isinstance(result, DownloadUrlResponse)
        assert result.download_url == "https://s3.example.com/art-123?token=abc"
        assert result.expires_at == 1700003600
        assert result.file_name == "document.pdf"

        request = mock_auth.get_requests()[-1]
        assert request.method == "GET"
        assert str(request.url).endswith("/v1/artifacts/art-123/download")
