"""Network-level tests for EpisodeResourceV1 using pytest-httpx."""

from __future__ import annotations

import inspect
import json

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException
from magick_mind.resources.v1.episode import EpisodeResourceV1

from tests.resources._payloads import BASE_URL, _error_envelope


class TestEpisodeResource:
    async def test_process_sends_agent_id_in_body(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/episodes/process",
            method="POST",
            json={"message_processed": True},
        )

        result = await client.v1.episode.process(
            magickspace_id="ms-1",
            sender_id="eu-1",
            message="hello",
            message_id="msg-1",
            agent_id="agent-1",
            display_name="John",
            is_group=True,
        )

        assert result.message_processed is True

        request = mock_auth.get_requests()[-1]
        assert str(request.url).endswith("/v1/episodes/process")
        assert json.loads(request.content) == {
            "agent_id": "agent-1",
            "magickspace_id": "ms-1",
            "sender_id": "eu-1",
            "message": "hello",
            "message_id": "msg-1",
            "display_name": "John",
            "is_group": True,
            "skip_persona": False,
        }

    def test_process_requires_keyword_only_agent_id(self):
        """A write always needs an owner: the server rejects an absent or empty
        agent_id with 400, so agent_id must be required rather than defaulted.

        Everything is keyword-only too -- the call takes several same-typed
        string ids, and a positional swap would be silent.
        """
        sig = inspect.signature(EpisodeResourceV1.process)
        agent_id = sig.parameters["agent_id"]
        assert agent_id.default is inspect.Parameter.empty, "agent_id must be required"
        assert all(
            p.kind is inspect.Parameter.KEYWORD_ONLY
            for name, p in sig.parameters.items()
            if name != "self"
        ), "all parameters must be keyword-only"

    async def test_process_omits_display_name_when_unset(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        """The server falls back to the end user's own name; sending "" would
        override that with an empty string."""
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/episodes/process",
            method="POST",
            json={"message_processed": True},
        )

        await client.v1.episode.process(
            agent_id="agent-1",
            magickspace_id="ms-1",
            sender_id="eu-1",
            message="hello",
            message_id="msg-1",
        )

        body = json.loads(mock_auth.get_requests()[-1].content)
        assert "display_name" not in body
        assert body["agent_id"] == "agent-1"

    async def test_process_own_uses_idless_route(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-user/episodes/process",
            method="POST",
            json={"message_processed": True},
        )

        result = await client.v1.episode.process_own(
            magickspace_id="ms-1",
            sender_id="eu-1",
            message="hello",
            message_id="msg-1",
        )

        assert result.message_processed is True

        request = mock_auth.get_requests()[-1]
        assert str(request.url).endswith("/v1/end-user/episodes/process")
        body = json.loads(request.content)
        assert "agent_id" not in body, "end-user route must not send an agent id"
        assert body["magickspace_id"] == "ms-1"

    async def test_process_403_hints_wrong_credential(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/episodes/process",
            method="POST",
            status_code=403,
            json=_error_envelope(403, "Forbidden", "not permitted"),
        )

        with pytest.raises(ProblemDetailsException) as exc_info:
            await client.v1.episode.process(
                magickspace_id="ms-1",
                sender_id="eu-1",
                message="hello",
                message_id="msg-1",
                agent_id="agent-1",
            )

        exc = exc_info.value
        assert "participant of this magickspace" in str(exc)
        assert "process_own()" in str(exc)
        assert exc.status == 403
        assert exc.request_id == "req-abc123"  # rich fields preserved

    async def test_process_401_hints_wrong_credential(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        """Mirror of the process_own 401: an end-user JWT fails verification
        on the service-user route."""
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/episodes/process",
            method="POST",
            status_code=401,
            json=_error_envelope(
                401, "Unauthorized", "token is unverifiable: unexpected signing method"
            ),
        )

        with pytest.raises(ProblemDetailsException) as exc_info:
            await client.v1.episode.process(
                magickspace_id="ms-1",
                sender_id="eu-1",
                message="hello",
                message_id="msg-1",
                agent_id="agent-1",
            )

        exc = exc_info.value
        assert "needs service-user credentials" in str(exc)
        assert "process_own()" in str(exc)
        assert exc.status == 401

    async def test_process_own_401_hints_wrong_credential(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-user/episodes/process",
            method="POST",
            status_code=401,
            json=_error_envelope(401, "Unauthorized", "missing end-user claims"),
        )

        with pytest.raises(ProblemDetailsException) as exc_info:
            await client.v1.episode.process_own(
                magickspace_id="ms-1",
                sender_id="eu-1",
                message="hello",
                message_id="msg-1",
            )

        exc = exc_info.value
        assert "unrevoked end-user JWT" in str(exc)
        assert "process(agent_id=...)" in str(exc)
        assert exc.status == 401
