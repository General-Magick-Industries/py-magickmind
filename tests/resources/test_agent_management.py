"""Network-level tests for the agent-management half of EndUserResourceV1."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException

from tests.resources._payloads import BASE_URL, END_USER_PAYLOAD, _error_envelope

AGENT_PAYLOAD = {
    **END_USER_PAYLOAD,
    "id": "agent-1",
    "name": "Aria",
    "persona_id": "p-1",
    "active_persona_version_id": "pv-2",
    "participant_type": "AGENT",
}


class TestAgentLifecycle:
    async def test_create_agent_with_persona(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-users", method="POST", json=AGENT_PAYLOAD
        )

        agent = await client.v1.end_user.create(
            name="Aria", participant_type="AGENT", persona_id="p-1"
        )

        assert agent.participant_type == "AGENT"
        assert agent.persona_id == "p-1"
        assert agent.active_persona_version_id == "pv-2"
        assert json.loads(mock_auth.get_requests()[-1].content) == {
            "name": "Aria",
            "persona_id": "p-1",
            "participant_type": "AGENT",
        }

    async def test_query_by_participant_type(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            method="GET",
            json={
                "data": [AGENT_PAYLOAD],
                "paging": {
                    "cursors": {"after": None, "before": None},
                    "has_more": False,
                    "has_previous": False,
                },
            },
        )

        agents = await client.v1.end_user.query(participant_type="AGENT")

        assert [a.id for a in agents] == ["agent-1"]
        assert "participant_type=AGENT" in str(mock_auth.get_requests()[-1].url)

    async def test_attach_persona(self, client: MagickMind, mock_auth: HTTPXMock):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-users/agent-1/persona",
            method="POST",
            json=AGENT_PAYLOAD,
        )

        agent = await client.v1.end_user.attach_persona(
            "agent-1", persona_id="p-1", version_id="pv-2"
        )

        assert agent.persona_id == "p-1"
        request = mock_auth.get_requests()[-1]
        assert request.method == "POST"
        assert json.loads(request.content) == {
            "persona_id": "p-1",
            "version_id": "pv-2",
        }

    async def test_set_persona_version(self, client: MagickMind, mock_auth: HTTPXMock):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-users/agent-1/persona/version",
            method="PATCH",
            json={**AGENT_PAYLOAD, "active_persona_version_id": "pv-3"},
        )

        agent = await client.v1.end_user.set_persona_version(
            "agent-1", version_id="pv-3"
        )

        assert agent.active_persona_version_id == "pv-3"
        request = mock_auth.get_requests()[-1]
        assert request.method == "PATCH"
        assert json.loads(request.content) == {"version_id": "pv-3"}


class TestTokenLifecycle:
    async def test_mint_supervised_token(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-users/tokens",
            method="POST",
            json={
                "token": "jwt-abc",
                "expires_at": "2026-07-22T12:00:00Z",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        )

        minted = await client.v1.end_user.mint_token("agent-1", supervised=True)

        assert minted.expires_in == 3600
        assert json.loads(mock_auth.get_requests()[-1].content) == {
            "subject_id": "agent-1",
            "supervised": True,
        }

    async def test_refresh_own_token(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/tokens/refresh",
            method="POST",
            json={
                "token": "jwt-new",
                "expires_at": "2026-07-22T13:00:00Z",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        )
        agent = MagickMind.from_token(BASE_URL, "jwt-old")

        minted = await agent.v1.end_user.refresh_own_token(ttl_seconds=3600)

        assert minted.token == "jwt-new"
        request = httpx_mock.get_requests()[-1]
        assert request.headers["Authorization"] == "Bearer jwt-old"
        assert json.loads(request.content) == {"ttl_seconds": 3600}
        await agent.close()

    async def test_refresh_own_token_hints_on_supervised(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/tokens/refresh",
            method="POST",
            status_code=403,
            json=_error_envelope(403, "Forbidden", "supervised token"),
        )
        agent = MagickMind.from_token(BASE_URL, "jwt-supervised")

        with pytest.raises(ProblemDetailsException) as exc:
            await agent.v1.end_user.refresh_own_token()

        assert "supervised token cannot refresh itself" in str(exc.value)
        assert exc.value.status == 403
        await agent.close()

    async def test_revoke_own_token(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/tokens/revoke",
            method="POST",
            json={"revoked": True, "disconnected": True},
        )
        agent = MagickMind.from_token(BASE_URL, "jwt-abc")

        result = await agent.v1.end_user.revoke_own_token(disconnect=True)

        assert result.revoked is True
        assert result.disconnected is True
        assert json.loads(httpx_mock.get_requests()[-1].content) == {"disconnect": True}
        await agent.close()
