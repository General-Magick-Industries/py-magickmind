"""
Contract Testing Utilities.
Handles schema extraction and JSON pointer resolution.
"""

import json
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


def get_schema_from_spec(spec: dict, schema_name: str) -> dict | None:
    """
    Robustly finds a schema in the OpenAPI spec.
    Searches: components/schemas, components/requestBodies, components/responses
    Returns the schema dict.
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


def get_schema_pointer(spec: dict, schema_name: str) -> str | None:
    """
    Returns the JSON Pointer to the schema definition.
    Uses 'urn:root' as the base URI to force registry lookup.
    """
    components = spec.get("components", {})

    base_uri = "urn:root"

    # 1. Standard Schemas
    if schema_name in components.get("schemas", {}):
        return f"{base_uri}#/components/schemas/{schema_name}"

    # 2. Request Bodies
    if schema_name in components.get("requestBodies", {}):
        return f"{base_uri}#/components/requestBodies/{schema_name}/content/application/json/schema"

    # 3. Responses
    if schema_name in components.get("responses", {}):
        return f"{base_uri}#/components/responses/{schema_name}/content/application/json/schema"

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
    pointer = get_schema_pointer(full_spec, schema_name)
    if not pointer:
        raise LookupError(f"Schema '{schema_name}' not found in spec")

    # Create Registry for $ref resolution
    # We add the full spec as the root resource (URI "urn:root")
    resource = Resource.from_contents(full_spec, default_specification=DRAFT202012)
    registry = Registry().with_resource("urn:root", resource)

    # We validate against a wrapper schema that points to the definition inside the full spec.
    wrapper_schema = {"$ref": pointer}

    validator = Draft202012Validator(wrapper_schema, registry=registry)
    validator.validate(payload)
