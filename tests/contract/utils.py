"""
Contract Testing Utilities.
Handles schema extraction and JSON pointer resolution.
"""

import json
import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7


def get_schema_from_spec(spec: dict, schema_name: str) -> dict:
    """
    Robustly finds a schema in the OpenAPI spec.
    Searches: components/schemas, components/requestBodies, components/responses
    """
    components = spec.get("components", {})

    # 1. Standard Schemas
    if schema := components.get("schemas", {}).get(schema_name):
        return schema

    # 2. Request Bodies (goctl style)
    if body := components.get("requestBodies", {}).get(schema_name):
        return body.get("content", {}).get("application/json", {}).get("schema")

    # 3. Responses (goctl/apidog style)
    if resp := components.get("responses", {}).get(schema_name):
        return resp.get("content", {}).get("application/json", {}).get("schema")

    return None


def to_hypothesis_schema(target_schema: dict, full_spec: dict) -> dict:
    """
    Prepares a schema for Hypothesis generation by resolving refs.
    """
    # Create a synthetic root that includes all definitions
    all_schemas = full_spec.get("components", {}).get("schemas", {}).copy()
    root = {
        "definitions": all_schemas,
        "$ref": "#/definitions/TARGET",
    }
    root["definitions"]["TARGET"] = target_schema

    # Hack: Fix OpenAPI '#/components/schemas' -> JSON Schema '#/definitions'
    json_str = json.dumps(root)
    fixed_json_str = json_str.replace("#/components/schemas/", "#/definitions/")
    return json.loads(fixed_json_str)


def validate_payload(payload: dict, schema_name: str, full_spec: dict):
    """
    Validates a payload using jsonschema and referencing for $ref support.
    """
    schema = get_schema_from_spec(full_spec, schema_name)
    if not schema:
        raise LookupError(f"Schema '{schema_name}' not found in spec")

    # Create Registry for $ref resolution
    resource = Resource.from_contents(full_spec, default_specification=DRAFT7)
    registry = Registry().with_resource("", resource)

    validator = Draft7Validator(schema, registry=registry)
    validator.validate(payload)
