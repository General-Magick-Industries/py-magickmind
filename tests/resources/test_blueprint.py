"""Network-level tests for BlueprintResourceV1 using pytest-httpx."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException
from magick_mind.models.v1 import Blueprint, BlueprintTrait, TraitConstraint, TraitValue

from tests.factories import BlueprintFactory
from tests.resources._payloads import (
    BASE_URL,
    ERROR_ENVELOPE as ERROR_404,
    PAGING_EMPTY,
)


def _blueprint(**overrides: Any) -> Blueprint:
    fields: dict[str, Any] = {
        "id": "bp-1",
        "blueprint_id": "friendly-bot",
        "name": "Friendly Bot",
        "category": "social",
        "visibility": "PRIVATE",
        "traits": [],
    }
    fields.update(overrides)
    return BlueprintFactory.build(**fields)


class TestBlueprintResource:
    async def test_create_sends_expected_body_and_deserializes(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints",
            method="POST",
            json=_blueprint().model_dump(mode="json"),
        )

        result = await client.v1.blueprint.create(
            blueprint_id="friendly-bot",
            name="Friendly Bot",
            category="social",
            visibility="PRIVATE",
            traits=[
                BlueprintTrait(
                    trait_ref="warmth",
                    type="NUMERIC",
                    required=True,
                    default=TraitConstraint(
                        trait_ref="warmth", value=TraitValue(numeric_value=70)
                    ),
                )
            ],
        )

        assert result.id == "bp-1"
        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body["blueprint_id"] == "friendly-bot"
        assert body["visibility"] == "PRIVATE"
        assert "namespace" not in body
        assert "description" not in body
        assert body["traits"][0]["trait_ref"] == "warmth"
        assert body["traits"][0]["type"] == "NUMERIC"

    async def test_blueprint_trait_requires_a_type(self):
        with pytest.raises(ValueError):
            BlueprintTrait.model_validate({"trait_ref": "warmth"})

    async def test_get_returns_blueprint_with_revision(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1",
            method="GET",
            json=_blueprint(revision=3, visibility="PUBLIC").model_dump(mode="json"),
        )

        result = await client.v1.blueprint.get("bp-1")

        assert result.id == "bp-1"
        assert result.revision == 3
        assert result.visibility == "PUBLIC"

    async def test_get_by_key_defaults_to_the_caller(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(method="GET", json=_blueprint().model_dump(mode="json"))

        await client.v1.blueprint.get_by_key(blueprint_id="friendly-bot")

        url = str(mock_auth.get_requests()[-1].url)
        assert "/v1/blueprints/by-key" in url
        assert "blueprint_id=friendly-bot" in url
        assert "owner_id" not in url
        assert "namespace" not in url

    async def test_get_by_key_with_owner(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(method="GET", json=_blueprint().model_dump(mode="json"))

        await client.v1.blueprint.get_by_key(blueprint_id="b-1", owner_id="owner-1")

        url = str(mock_auth.get_requests()[-1].url)
        assert "owner_id=owner-1" in url
        assert "blueprint_id=b-1" in url

    async def test_list_empty_data(self, client: MagickMind, mock_auth: HTTPXMock):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints",
            method="GET",
            json={"data": [], "paging": PAGING_EMPTY},
        )

        result = await client.v1.blueprint.list()
        assert result.data == []

    async def test_update_sends_put_and_returns_blueprint(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1",
            method="PUT",
            json=_blueprint(name="Friendly Bot v2").model_dump(mode="json"),
        )

        result = await client.v1.blueprint.update(
            blueprint_id="bp-1",
            name="Friendly Bot v2",
            description="desc",
            category="social",
            visibility="PRIVATE",
        )

        assert result.name == "Friendly Bot v2"
        request = mock_auth.get_requests()[-1]
        assert request.method == "PUT"
        body = json.loads(request.content)
        assert body["description"] == "desc"
        assert body["visibility"] == "PRIVATE"
        assert body["traits"] == []

    async def test_patch_excludes_none_fields(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1",
            method="PATCH",
            json=_blueprint(name="Patched").model_dump(mode="json"),
        )

        await client.v1.blueprint.patch("bp-1", name="Patched")

        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body == {"name": "Patched"}

    async def test_patch_can_clear_default_configs(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1",
            method="PATCH",
            json=_blueprint().model_dump(mode="json"),
        )

        await client.v1.blueprint.patch("bp-1", clear_default_growth=True)

        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body == {"clear_default_growth": True}

    async def test_set_visibility_uses_its_own_route(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1/visibility",
            method="PATCH",
            json=_blueprint(visibility="PUBLIC").model_dump(mode="json"),
        )

        result = await client.v1.blueprint.set_visibility("bp-1", "PUBLIC")

        assert result.visibility == "PUBLIC"
        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body == {"visibility": "PUBLIC"}

    async def test_delete_sends_delete(self, client: MagickMind, mock_auth: HTTPXMock):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1",
            method="DELETE",
            json={},
        )

        await client.v1.blueprint.delete("bp-1")
        req = mock_auth.get_requests()[-1]
        assert req.method == "DELETE"
        assert str(req.url).endswith("/v1/blueprints/bp-1")

    async def test_clone_sends_only_the_new_key(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1/clone",
            method="POST",
            json=_blueprint(id="bp-3", blueprint_id="mine").model_dump(mode="json"),
        )

        await client.v1.blueprint.clone("bp-1", new_blueprint_id="mine")

        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body == {"new_blueprint_id": "mine"}

    async def test_clone_without_a_key_sends_an_empty_body(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1/clone",
            method="POST",
            json=_blueprint(id="bp-3").model_dump(mode="json"),
        )

        await client.v1.blueprint.clone("bp-1")

        assert json.loads(mock_auth.get_requests()[-1].content) == {}

    async def test_get_404_raises_problem_details(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/missing",
            method="GET",
            json=ERROR_404,
            status_code=404,
        )

        with pytest.raises(ProblemDetailsException) as exc:
            await client.v1.blueprint.get("missing")

        assert exc.value.status == 404
