"""Tests for token-based client construction (MagickMind.from_token)."""

from __future__ import annotations

import base64
import json

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.auth import StaticTokenAuth

BASE_URL = "https://api.test"


def _jwt(sub: str) -> str:
    """A structurally valid unsigned JWT; only the payload is ever read."""

    def seg(d: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

    return f"{seg({'alg': 'HS256'})}.{seg({'sub': sub, 'token_use': 'end_user'})}.sig"


class TestStaticTokenAuth:
    async def test_presents_bearer_token(self):
        auth = StaticTokenAuth("jwt-abc")

        assert await auth.get_headers_async() == {"Authorization": "Bearer jwt-abc"}
        assert await auth.get_token_async() == "jwt-abc"
        assert auth.is_authenticated() is True

    async def test_refresh_is_a_noop(self):
        """A static token cannot be renewed; refreshing must not raise."""
        auth = StaticTokenAuth("jwt-abc")

        assert await auth.refresh_if_needed_async() is None
        assert await auth.get_token_async() == "jwt-abc"

    def test_empty_token_rejected(self):
        with pytest.raises(ValueError):
            StaticTokenAuth("")


class TestFromToken:
    def test_builds_a_usable_client(self):
        client = MagickMind.from_token(BASE_URL, "jwt-abc")

        assert isinstance(client.auth, StaticTokenAuth)
        assert client.config.base_url == BASE_URL
        assert client.is_authenticated() is True
        # the end-user surface this credential exists for
        assert hasattr(client.v1.persona, "prepare_for_own_agent")
        assert hasattr(client.v1.episode, "process_own")

    def test_rejects_empty_token(self):
        with pytest.raises(ValueError):
            MagickMind.from_token(BASE_URL, "")

    def test_does_not_require_email_password(self):
        """The whole point: an agent process holds a token, not credentials."""
        client = MagickMind.from_token(BASE_URL, "jwt-abc")
        assert client.auth is not None

    async def test_sends_token_and_never_logs_in(self, httpx_mock: HTTPXMock):
        """No auth/login round-trip: the token is used as given."""
        prepared = {
            "agent_id": "a-1",
            "persona_id": "p-1",
            "active_persona_version_id": "pv-1",
            "user_id": None,
            "system_prompt": "You are Aria.",
            "computed_at": "2026-07-23T00:00:00Z",
            "ttl_seconds": 300,
        }
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/persona/prepare",
            method="POST",
            json=prepared,
        )

        client = MagickMind.from_token(BASE_URL, "jwt-abc")
        result = await client.v1.persona.prepare_for_own_agent()

        assert result.system_prompt == "You are Aria."
        requests = httpx_mock.get_requests()
        assert all("/v1/auth/login" not in str(r.url) for r in requests)
        assert requests[-1].headers["Authorization"] == "Bearer jwt-abc"
        await client.close()

    async def test_get_user_id_reads_the_token_subject(self):
        """For a minted end-user token the subject is the agent itself."""
        client = MagickMind.from_token(BASE_URL, _jwt("agent-123"))

        assert await client.get_user_id() == "agent-123"

    async def test_closes_cleanly(self):
        async with MagickMind.from_token(BASE_URL, "jwt-abc") as client:
            assert client.is_authenticated()
