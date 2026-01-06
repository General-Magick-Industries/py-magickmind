"""
Contract test fixtures.

Loads OpenAPI specs from specs/ folder for contract validation.
Both dev and main are manually updated snapshots.
"""

import json
import pytest
from pathlib import Path


# Spec locations (both in SDK repo)
SPECS_DIR = Path(__file__).parents[2] / "specs"
DEV_SPEC_PATH = SPECS_DIR / "openapi.dev.json"  # Current default
MAIN_SPEC_PATH = SPECS_DIR / "openapi.main.json"
APIDOG_SPEC_PATH = SPECS_DIR / "apidog.dev.json"  # Apidog export
GOCTL_SPEC_PATH = SPECS_DIR / "openapi.goctl.json"  # goctl generated


def _load_json(path: Path) -> dict | None:
    """Load JSON file, return None if missing."""
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def spec_dev() -> dict:
    """
    Load DEV spec (bleeding edge features).

    Fails if missing - dev spec is required for development.
    """
    data = _load_json(DEV_SPEC_PATH)
    if not data:
        pytest.fail(
            f"Dev spec not found at {DEV_SPEC_PATH}\n"
            "Copy from bifrost: cp ../bifrost/api/openapi.json specs/openapi.dev.json"
        )
    return data


@pytest.fixture(scope="session")
def spec_main() -> dict | None:
    """
    Load MAIN spec (UAT/production snapshot).

    Returns None if missing (allows dev work without blocking).
    """
    return _load_json(MAIN_SPEC_PATH)


@pytest.fixture(scope="session")
def spec_apidog() -> dict | None:
    """Load Apidog export spec."""
    return _load_json(APIDOG_SPEC_PATH)


@pytest.fixture(scope="session")
def spec_goctl() -> dict | None:
    """Load goctl-generated spec."""
    return _load_json(GOCTL_SPEC_PATH)


@pytest.fixture(scope="session")
def contract(spec_goctl) -> dict:
    """Primary contract spec for testing (switched to goctl)."""
    return spec_goctl


def get_schema_from_spec(spec: dict, schema_name: str) -> dict | None:
    """Extract a schema definition from OpenAPI spec."""
    return spec.get("components", {}).get("schemas", {}).get(schema_name)


def get_request_body_schema(spec: dict, schema_name: str) -> dict | None:
    """
    Extract schema from requestBodies (goctl style).

    goctl puts schemas under components/requestBodies/Name/content/application/json/schema
    """
    request_body = spec.get("components", {}).get("requestBodies", {}).get(schema_name)
    if not request_body:
        return None
    try:
        return request_body["content"]["application/json"]["schema"]
    except KeyError:
        return None
