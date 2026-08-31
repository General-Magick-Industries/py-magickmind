"""Network-level tests for the end-user magickspace surface and message models."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException
from magick_mind.models.v1.mindspace import (
    ChatHistoryItem,
    ChatHistoryParams,
    ContextPrepareResponse,
    is_control_message,
    is_signal_message,
)

from tests.resources._payloads import (
    BASE_URL,
    MINDSPACE_PAYLOAD,
    PAGING_EMPTY,
    _error_envelope,
)

MESSAGE_PAYLOAD = {
    "id": "msg-1",
    "magickspace_id": "ms-1",
    "sent_by_user_id": "agent-1",
    "sent_by_user_name": "Aria",
    "magickspace_type": "MAGICKSPACE_TYPE_GROUP",
    "content": "hello",
    "reply_to_message_id": None,
    "status": "SENT",
    "artifact_ids": None,
    "message_type": "TEXT",
    "client_message_id": "c-1",
    "create_at": "2026-08-31T00:00:00Z",
    "update_at": "2026-08-31T00:00:00Z",
}


@pytest.fixture
def agent() -> MagickMind:
    return MagickMind.from_token(BASE_URL, "jwt-agent")


class TestChatHistoryItem:
    def test_accepts_bifrost_shape(self):
        item = ChatHistoryItem.model_validate(MESSAGE_PAYLOAD)

        assert item.magickspace_id == "ms-1"
        assert item.mindspace_id == "ms-1"
        assert item.sent_by_user_name == "Aria"
        assert item.magickspace_type == "GROUP"
        assert item.artifact_ids == []
        assert item.deduplicated is False

    def test_accepts_legacy_mindspace_id(self):
        item = ChatHistoryItem.model_validate(
            {"id": "m", "mindspace_id": "ms-9", "sent_by_user_id": "u", "content": "x"}
        )
        assert item.magickspace_id == "ms-9"

    def test_message_type_helpers(self):
        assert is_signal_message("SIGNAL_START")
        assert not is_signal_message("TEXT")
        assert is_control_message("TOOL_MANIFEST")
        assert not is_control_message("SIGNAL_END")


class TestOwnMagickspaces:
    async def test_list_own(self, agent: MagickMind, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="GET", json={"data": [MINDSPACE_PAYLOAD], "paging": PAGING_EMPTY}
        )

        result = await agent.v1.magickspaces.list_own(type="PRIVATE", limit=5)

        assert [m.id for m in result.data] == ["ms-123"]
        url = str(httpx_mock.get_requests()[-1].url)
        assert "/v1/end-user/magickspaces?" in url
        assert "type=PRIVATE" in url and "limit=5" in url
        assert "participant_id" not in url

    async def test_get_own_messages(self, agent: MagickMind, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="GET", json={"data": [MESSAGE_PAYLOAD], "paging": PAGING_EMPTY}
        )

        result = await agent.v1.magickspaces.get_own_messages(
            "ms-1", limit=50, order="desc"
        )

        message = result.data[0]
        assert message.magickspace_id == "ms-1"
        assert message.message_type == "TEXT"
        assert message.sent_by_user_name == "Aria"
        url = str(httpx_mock.get_requests()[-1].url)
        assert "/v1/end-user/magickspaces/ms-1/messages?" in url
        assert "limit=50" in url and "order=desc" in url

    async def test_send_own_message(self, agent: MagickMind, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/magickspaces/ms-1/messages",
            method="POST",
            json=MESSAGE_PAYLOAD,
        )

        sent = await agent.v1.magickspaces.send_own_message(
            "ms-1",
            content="hello",
            reply_to_message_id="msg-0",
            tools=[{"name": "peek", "description": "look", "schema": {}}],
            context={"topic": "weather"},
        )

        assert sent.id == "msg-1"
        assert json.loads(httpx_mock.get_requests()[-1].content) == {
            "content": "hello",
            "reply_to_message_id": "msg-0",
            "artifact_ids": [],
            "message_type": "TEXT",
            "broadcast": True,
            "tools": [{"name": "peek", "description": "look", "schema": {}}],
            "context": {"topic": "weather"},
        }

    async def test_send_own_signal_without_content(
        self, agent: MagickMind, httpx_mock: HTTPXMock
    ):
        """A turn signal is an indicator, not speech: no content, no sender_id."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/magickspaces/ms-1/messages",
            method="POST",
            json={**MESSAGE_PAYLOAD, "message_type": "SIGNAL_START", "content": ""},
        )

        await agent.v1.magickspaces.send_own_message(
            "ms-1", message_type="SIGNAL_START"
        )

        body = json.loads(httpx_mock.get_requests()[-1].content)
        assert body["message_type"] == "SIGNAL_START"
        assert "content" not in body
        assert "sender_id" not in body

    async def test_send_own_message_hints_on_403(
        self, agent: MagickMind, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/magickspaces/ms-1/messages",
            method="POST",
            status_code=403,
            json=_error_envelope(403, "Forbidden", "not a participant"),
        )

        with pytest.raises(ProblemDetailsException) as exc:
            await agent.v1.magickspaces.send_own_message("ms-1", content="hi")

        assert "not a participant" in str(exc.value)
        assert exc.value.request_id == "req-abc123"

    async def test_prepare_own_context(self, agent: MagickMind, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/magickspaces/ms-1/context",
            method="POST",
            json={
                "magickspace_id": "ms-1",
                "magickspace_type": "GROUP",
                "participant_id": "agent-1",
                "chat_history": [MESSAGE_PAYLOAD],
                "corpora": [
                    {"id": "c-1", "name": "Handbook", "description": "HR policy"},
                    {"id": "c-2", "name": "Granted", "description": ""},
                ],
            },
        )

        prepared = await agent.v1.magickspaces.prepare_own_context(
            "ms-1",
            chat_history=ChatHistoryParams(limit=10),
            catalog_corpus_ids=["c-2"],
        )

        assert isinstance(prepared, ContextPrepareResponse)
        assert prepared.magickspace_id == "ms-1"
        assert prepared.magickspace_type == "GROUP"
        assert [c.id for c in prepared.corpora] == ["c-1", "c-2"]
        assert prepared.chat_history[0].sent_by_user_name == "Aria"
        assert json.loads(httpx_mock.get_requests()[-1].content) == {
            "chat_history": {"limit": 10},
            "catalog_corpus_ids": ["c-2"],
        }

    async def test_prepare_own_context_without_catalog(
        self, agent: MagickMind, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/magickspaces/ms-1/context",
            method="POST",
            json={"magickspace_id": "ms-1", "participant_id": "agent-1"},
        )

        prepared = await agent.v1.magickspaces.prepare_own_context("ms-1")

        assert prepared.corpora == []
        assert prepared.magickspace_type is None
        assert json.loads(httpx_mock.get_requests()[-1].content) == {}


class TestServiceUserAdditions:
    async def test_prepare_context_sends_catalog_corpus_ids(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/magickspaces/ms-1/context",
            method="POST",
            json={"mindspace_id": "ms-1", "participant_id": "u-1", "corpora": None},
        )

        prepared = await client.v1.magickspaces.prepare_context(
            "ms-1", participant_id="u-1", catalog_corpus_ids=["c-9"]
        )

        assert prepared.magickspace_id == "ms-1"
        assert prepared.corpora == []
        assert json.loads(mock_auth.get_requests()[-1].content) == {
            "participant_id": "u-1",
            "catalog_corpus_ids": ["c-9"],
        }

    async def test_send_message_idempotency_key(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/magickspaces/ms-1/messages",
            method="POST",
            json={**MESSAGE_PAYLOAD, "deduplicated": True},
        )

        sent = await client.v1.magickspaces.send_message(
            "ms-1",
            content="hello",
            sender_id="u-1",
            client_message_id="c-1",
            record_neutral_memory=True,
        )

        assert sent.deduplicated is True
        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body["client_message_id"] == "c-1"
        assert body["record_neutral_memory"] is True
