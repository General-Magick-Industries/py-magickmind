"""Network-level tests for PersonaResourceV1 using pytest-httpx."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException

from tests.factories import (
    PersonaFactory,
    PersonaVersionFactory,
    PrepareAgentPersonaResponseFactory,
    PreparePersonaResponseFactory,
)
from tests.resources._payloads import (
    BASE_URL,
    ERROR_500_ENVELOPE as ERROR_500,
    PAGING_EMPTY,
    _error_envelope,
)


class TestPersonaResource:
    async def test_crud_prepare_and_from_blueprint(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        persona = PersonaFactory.build(id="p-1", name="Aria", role="assistant")
        updated = PersonaFactory.build(id="p-1", name="Aria v2", role="assistant")
        prepared = PreparePersonaResponseFactory.build(system_prompt="You are Aria.")

        version = PersonaVersionFactory.build(
            id="pv-1",
            persona_id="p-1",
            version="1.0",
            is_active=True,
        )

        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona",
            method="POST",
            json=persona.model_dump(mode="json"),
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/p-1",
            method="GET",
            json=persona.model_dump(mode="json"),
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/p-1",
            method="PUT",
            json=updated.model_dump(mode="json"),
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/p-1/prepare",
            method="POST",
            json=prepared.model_dump(mode="json"),
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/from-blueprint",
            method="POST",
            json={
                "persona": persona.model_dump(mode="json"),
                "version": version.model_dump(mode="json"),
            },
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/p-1",
            method="DELETE",
            json={},
        )

        created = await client.v1.persona.create(name="Aria", role="assistant")
        assert created.id == "p-1"
        assert (
            json.loads(mock_auth.get_requests()[-1].content)["background_story"] == ""
        )

        fetched = await client.v1.persona.get("p-1")
        assert fetched.id == "p-1"

        result = await client.v1.persona.update(
            persona_id="p-1", name="Aria v2", role="assistant"
        )
        assert result.name == "Aria v2"

        prep = await client.v1.persona.prepare("p-1")
        assert prep.system_prompt == "You are Aria."
        prep_body = json.loads(mock_auth.get_requests()[-1].content)
        assert prep_body == {}

        pwv = await client.v1.persona.create_from_blueprint(
            blueprint_id="bp-1", name="Aria", role="assistant"
        )
        assert pwv.persona.id == "p-1"
        assert pwv.version.version == "1.0"

        await client.v1.persona.delete("p-1")
        assert mock_auth.get_requests()[-1].method == "DELETE"

    async def test_prepare_for_agent_uses_agent_keyed_route(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        prepared = PrepareAgentPersonaResponseFactory.build(
            agent_id="a-1",
            persona_id="p-1",
            user_id="u-1",
            system_prompt="You are Aria.",
            ttl_seconds=300,
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-users/a-1/persona/prepare",
            method="POST",
            json=prepared.model_dump(mode="json"),
        )

        prep = await client.v1.persona.prepare_for_agent("a-1", user_id="u-1")

        assert prep.system_prompt == "You are Aria."
        assert prep.agent_id == "a-1"
        assert prep.persona_id == "p-1"
        assert prep.ttl_seconds == 300
        assert json.loads(mock_auth.get_requests()[-1].content) == {"user_id": "u-1"}

    async def test_prepare_for_agent_404_hints_persona_vs_agent(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-users/p-1/persona/prepare",
            method="POST",
            status_code=404,
            json=_error_envelope(404, "Not Found", "Agent not found"),
        )

        with pytest.raises(ProblemDetailsException) as exc_info:
            await client.v1.persona.prepare_for_agent("p-1")

        exc = exc_info.value
        assert "keyed by agent" in str(exc)
        assert "'p-1'" in str(exc)
        assert "Agent not found" in str(exc)
        assert exc.status == 404
        assert exc.request_id == "req-abc123"  # rich fields preserved

    async def test_prepare_for_agent_403_hints_token_subject(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-users/a-1/persona/prepare",
            method="POST",
            status_code=403,
            json=_error_envelope(403, "Forbidden", "not permitted"),
        )

        with pytest.raises(ProblemDetailsException) as exc_info:
            await client.v1.persona.prepare_for_agent("a-1")

        exc = exc_info.value
        assert "does not match the token subject" in str(exc)
        assert "prepare_own_persona()" in str(exc)
        assert exc.status == 403

    async def test_prepare_own_persona_uses_idless_route(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        prepared = PrepareAgentPersonaResponseFactory.build(
            agent_id="a-self",
            persona_id="p-1",
            user_id=None,
            system_prompt="You are Aria.",
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-user/persona/prepare",
            method="POST",
            json=prepared.model_dump(mode="json"),
        )

        prep = await client.v1.persona.prepare_own_persona()

        assert prep.system_prompt == "You are Aria."
        assert prep.agent_id == "a-self"
        request = mock_auth.get_requests()[-1]
        assert str(request.url).endswith("/v1/end-user/persona/prepare")
        assert "/end-users/" not in str(request.url)
        assert json.loads(request.content) == {}

    async def test_prepare_own_persona_401_hints_wrong_credential(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/end-user/persona/prepare",
            method="POST",
            status_code=401,
            json=_error_envelope(401, "Unauthorized", "missing end-user claims"),
        )

        with pytest.raises(ProblemDetailsException) as exc_info:
            await client.v1.persona.prepare_own_persona()

        exc = exc_info.value
        assert "needs an end-user JWT" in str(exc)
        assert "prepare_for_agent" in str(exc)
        assert exc.status == 401

    async def test_versioning_methods_happy_path(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        version = PersonaVersionFactory.build(
            id="pv-2",
            persona_id="p-2",
            version="2.0",
            is_active=False,
        )
        persona = PersonaFactory.build(
            id="p-2",
            name="Test",
            role="assistant",
            active_version="pv-2",
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/p-2/version",
            method="POST",
            json=version.model_dump(mode="json"),
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/p-2/version",
            method="GET",
            json={"data": [version.model_dump(mode="json")], "paging": PAGING_EMPTY},
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/p-2/version/2.0",
            method="GET",
            json=version.model_dump(mode="json"),
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/p-2/version/active",
            method="GET",
            json=version.model_dump(mode="json"),
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/p-2/version/2.0/activate",
            method="POST",
            json=persona.model_dump(mode="json"),
        )

        created = await client.v1.persona.create_version(
            persona_id="p-2", version="2.0"
        )
        assert created.version == "2.0"

        listed = await client.v1.persona.list_versions("p-2")
        assert listed.data[0].id == "pv-2"

        got = await client.v1.persona.get_version("p-2", "2.0")
        assert got.persona_id == "p-2"

        active = await client.v1.persona.get_active_version("p-2")
        assert active.id == "pv-2"

        set_active = await client.v1.persona.set_active_version("p-2", "2.0")
        assert set_active.id == "p-2"
        assert set_active.active_version == "pv-2"
        last_request = mock_auth.get_requests()[-1]
        assert last_request.method == "POST"
        assert last_request.url.path == "/v1/persona/p-2/version/2.0/activate"

    async def test_get_500_raises_problem_details(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/persona/p-err",
            method="GET",
            json=ERROR_500,
            status_code=500,
        )

        with pytest.raises(ProblemDetailsException) as exc:
            await client.v1.persona.get("p-err")

        assert exc.value.status == 500
