"""Network-level Chat resource tests using pytest-httpx."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException, RateLimitError
from magick_mind.models.v1.chat import ConfigSchema

from tests.resources._payloads import BASE_URL, ERROR_ENVELOPE


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
