import pytest
from hypothesis import settings, given, HealthCheck
from hypothesis_jsonschema import from_schema
from pydantic import ValidationError

from tests.contract.schema_registry import get_tested_responses
from tests.contract.utils import get_schema_from_spec, to_hypothesis_schema


@pytest.mark.contract
@pytest.mark.slow
class TestResponses:
    @pytest.mark.parametrize("model_class,schema_name", get_tested_responses())
    def test_fuzz_response(self, contract, model_class, schema_name):
        """Fuzz test SDK models against OpenAPI schemas."""

        # 1. Get Schema
        raw_schema = get_schema_from_spec(contract, schema_name)
        if not raw_schema:
            pytest.skip(f"Schema {schema_name} not found in contract.")

        # 2. Prepare for Hypothesis
        hyp_schema = to_hypothesis_schema(raw_schema, contract)

        # 3. Run Fuzz Test
        @settings(
            max_examples=50,
            suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
        )
        @given(payload=from_schema(hyp_schema))
        def run_fuzz(payload):
            try:
                model_class.model_validate(payload)
            except ValidationError as e:
                raise AssertionError(
                    f"SDK CRASHED ON VALID DATA!\nSchema: {schema_name}\nPayload: {payload}\nError: {e}"
                )

        run_fuzz()
