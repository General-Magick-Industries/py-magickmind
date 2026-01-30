"""
Contract test fixtures.

Loads OpenAPI specs from specs/ folder for contract validation.
Source of truth: Apidog exports (openapi.dev.json, openapi.main.json)
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Optional


# Spec locations
SPECS_DIR = Path(__file__).parents[2] / "specs"
DEV_SPEC_PATH = SPECS_DIR / "openapi.dev.json"  # Apidog dev export
MAIN_SPEC_PATH = SPECS_DIR / "openapi.main.json"  # Apidog main export


def _load_json(path: Path) -> Optional[dict]:
    """Load JSON file, return None if missing."""
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def spec_dev() -> dict:
    """
    Load DEV spec (Apidog dev environment export).

    Fails if missing - dev spec is required for development.
    """
    data = _load_json(DEV_SPEC_PATH)
    if not data:
        pytest.fail(
            f"Dev spec not found at {DEV_SPEC_PATH}\n"
            "Export from Apidog and save to specs/openapi.dev.json"
        )
    return data


@pytest.fixture(scope="session")
def spec_main() -> Optional[dict]:
    """
    Load MAIN spec (Apidog production environment export).

    Returns None if missing (allows dev work without blocking).
    """
    return _load_json(MAIN_SPEC_PATH)


def pytest_addoption(parser):
    """Add CLI option to select spec."""
    parser.addoption(
        "--spec",
        action="store",
        default="dev",
        choices=["dev", "main"],
        help="Which OpenAPI spec to test against: dev or main",
    )


@pytest.fixture(scope="session")
def contract(request, spec_dev, spec_main) -> dict:
    """Primary contract spec for testing (configurable via --spec)."""
    spec_choice = request.config.getoption("--spec")

    if spec_choice == "main":
        if not spec_main:
            pytest.fail("Main spec not found at specs/openapi.main.json")
        return spec_main
    else:  # dev (default)
        return spec_dev


def get_schema_from_spec(spec: dict, schema_name: str) -> Optional[dict]:
    """Extract a schema definition from OpenAPI spec."""
    return spec.get("components", {}).get("schemas", {}).get(schema_name)
