"""Network-level tests for BlueprintResourceV1 using pytest-httpx."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.exceptions import ProblemDetailsException

from tests.factories import (
    BlueprintFactory,
    ValidateBlueprintResponseFactory,
)
from tests.resources._payloads import (
    BASE_URL,
    ERROR_ENVELOPE as ERROR_404,
    PAGING_EMPTY,
)


class TestBlueprintResource:
    async def test_create_sends_expected_body_and_deserializes(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        blueprint = BlueprintFactory.build(
            id="bp-1",
            blueprint_id="friendly-bot",
            name="Friendly Bot",
            category="social",
            namespace="USER",
            visibility="PRIVATE",
            traits=[],
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints",
            method="POST",
            json=blueprint.model_dump(mode="json"),
        )

        result = await client.v1.blueprint.create(
            blueprint_id="friendly-bot",
            name="Friendly Bot",
            category="social",
            namespace="USER",
            visibility="PRIVATE",
        )

        assert result.id == "bp-1"
        request = mock_auth.get_requests()[-1]
        body = json.loads(request.content)
        assert body["blueprint_id"] == "friendly-bot"
        assert body["name"] == "Friendly Bot"
        assert body["category"] == "social"
        assert body["namespace"] == "USER"
        assert body["visibility"] == "PRIVATE"
        assert body["traits"] == []
        assert "description" not in body

    async def test_get_returns_blueprint(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        blueprint = BlueprintFactory.build(
            id="bp-1",
            blueprint_id="friendly-bot",
            name="Friendly Bot",
            category="social",
            namespace="USER",
            visibility="PRIVATE",
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1",
            method="GET",
            json=blueprint.model_dump(mode="json"),
        )

        result = await client.v1.blueprint.get("bp-1")

        assert result.id == "bp-1"
        req = mock_auth.get_requests()[-1]
        assert req.method == "GET"
        assert str(req.url).endswith("/v1/blueprints/bp-1")

    async def test_get_by_key_uses_query_params(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        blueprint = BlueprintFactory.build(
            id="bp-2",
            blueprint_id="b-1",
            name="BP",
            category="cat",
            namespace="ORG",
            visibility="ORG",
        )
        mock_auth.add_response(
            method="GET",
            json=blueprint.model_dump(mode="json"),
        )

        result = await client.v1.blueprint.get_by_key(
            namespace="ORG",
            owner_id="owner-1",
            blueprint_id="b-1",
        )

        assert result.id == "bp-2"
        url = str(mock_auth.get_requests()[-1].url)
        assert "/v1/blueprints/by-key" in url
        assert "namespace=ORG" in url
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
        updated = BlueprintFactory.build(
            id="bp-1",
            blueprint_id="friendly-bot",
            name="Friendly Bot v2",
            category="social",
            namespace="USER",
            visibility="PRIVATE",
            traits=[],
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1",
            method="PUT",
            json=updated.model_dump(mode="json"),
        )

        result = await client.v1.blueprint.update(
            blueprint_id="bp-1",
            name="Friendly Bot v2",
            description="desc",
            category="social",
            visibility="PRIVATE",
            traits=None,
        )

        assert result.name == "Friendly Bot v2"
        request = mock_auth.get_requests()[-1]
        assert request.method == "PUT"
        body = json.loads(request.content)
        assert body["name"] == "Friendly Bot v2"
        assert body["description"] == "desc"
        assert body["traits"] == []

    async def test_patch_excludes_none_fields(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        patched = BlueprintFactory.build(
            id="bp-1",
            blueprint_id="friendly-bot",
            name="Patched",
            category="social",
            namespace="USER",
            visibility="PRIVATE",
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1",
            method="PATCH",
            json=patched.model_dump(mode="json"),
        )

        await client.v1.blueprint.patch("bp-1", name="Patched")

        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body == {"name": "Patched"}

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

    async def test_clone_sends_expected_body(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        cloned = BlueprintFactory.build(
            id="bp-3",
            blueprint_id="cloned",
            name="Cloned",
            category="social",
            namespace="ORG",
            visibility="PRIVATE",
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1/clone",
            method="POST",
            json=cloned.model_dump(mode="json"),
        )

        await client.v1.blueprint.clone(
            blueprint_id="bp-1",
            new_owner_id="owner-2",
            new_namespace="ORG",
        )

        body = json.loads(mock_auth.get_requests()[-1].content)
        assert body["new_owner_id"] == "owner-2"
        assert body["new_namespace"] == "ORG"
        assert "new_blueprint_id" not in body

    async def test_validate_returns_response_model(
        self, client: MagickMind, mock_auth: HTTPXMock
    ):
        validate = ValidateBlueprintResponseFactory.build(valid=True, errors=[])
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/validate",
            method="POST",
            json=validate.model_dump(mode="json"),
        )

        result = await client.v1.blueprint.validate(
            blueprint_id="friendly-bot",
            name="Friendly",
            category="social",
            namespace="USER",
            visibility="PRIVATE",
        )

        assert result.valid is True

    async def test_hydrate_deserializes(self, client: MagickMind, mock_auth: HTTPXMock):
        blueprint = BlueprintFactory.build(
            id="bp-1",
            blueprint_id="friendly-bot",
            name="Friendly Bot",
            category="social",
            namespace="USER",
            visibility="PRIVATE",
        )
        mock_auth.add_response(
            url=f"{BASE_URL}/v1/blueprints/bp-1/hydrate",
            method="GET",
            json={
                "blueprint": blueprint.model_dump(mode="json"),
                "hydrated_traits": [],
            },
        )

        result = await client.v1.blueprint.hydrate("bp-1")
        assert result.blueprint.id == "bp-1"
        assert result.hydrated_traits == []

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
