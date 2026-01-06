"""
Request Serialization Contract Tests.

Verifies that SDK models serialize to valid JSON matching the OpenAPI schema.
Uses factories from schema_registry.py - no manual instance creation needed.
"""

import pytest
from jsonschema import ValidationError

from tests.contract.schema_registry import get_tested_requests
from tests.contract.utils import validate_payload


@pytest.mark.contract
class TestPayloads:
    @pytest.mark.parametrize(
        "contract_def", get_tested_requests(), ids=lambda r: r.schema_name
    )
    def test_serialize_request(self, contract, contract_def):
        """Ensure SDK models serialize to valid OpenAPI JSON."""

        # 1. Use factory from registry
        if not contract_def.factory:
            pytest.fail(
                f"Model {contract_def.schema_name} is TESTED but has no factory in registry!"
            )

        instance = contract_def.factory()

        # 2. Serialize
        payload = instance.model_dump(by_alias=True, mode="json")

        # 3. Validate against Spec
        try:
            validate_payload(payload, contract_def.schema_name, contract)
        except ValidationError as e:
            pytest.fail(f"Contract Violation ({contract_def.schema_name}): {e.message}")
        except LookupError:
            pytest.skip(f"Schema {contract_def.schema_name} missing from contract")
