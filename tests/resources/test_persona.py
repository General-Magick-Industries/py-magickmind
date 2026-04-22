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
    PreparePersonaResponseFactory,
)
from tests.resources._payloads import (
    BASE_URL,
    ERROR_500_ENVELOPE as ERROR_500,
    PAGING_EMPTY,
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

    async def test_versioning_methods_happy_path(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        version = PersonaVersionFactory.build(
            id="pv-2",
            persona_id="p-2",
            version="2.0",
            is_active=False,
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
            url=f"{BASE_URL}/v1/persona/p-2/version/active",
            method="PUT",
            json=version.model_dump(mode="json"),
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
        assert set_active.id == "pv-2"
        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body == {"version": "2.0"}

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
