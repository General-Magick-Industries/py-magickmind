# Contract Testing

Validates that SDK models serialize to JSON payloads matching the OpenAPI spec.

## Quick Start

```bash
# Run contract tests
uv run pytest tests/contract/ -v

# Run only contract tests in full suite
uv run pytest -m contract -v
```

## Philosophy

**Serialization Testing** - We test the *output*, not the class structure:
- SDK can have optional args (good DX)
- Serializers transform `None` → default values (API compliant)
- jsonschema validates the final payload

## Files

| File | Purpose |
|------|---------|
| `conftest.py` | Loads `spec_dev` and `spec_main` fixtures |
| `test_payloads.py` | Validates SDK payloads against specs |

## Spec Files

Located in `specs/`:
- `openapi.dev.json` - Dev branch snapshot (bleeding edge)
- `openapi.main.json` - Main branch snapshot (UAT/production)

**To update specs:**
```bash
# From API gateway repo, generate new spec
goctl api plugin -p goctl-openapi -api api/v1/*.api -dir .

# Copy to SDK
cp ../bifrost/api/openapi.json specs/openapi.dev.json
```

## Adding New Models

1. Add to `MODEL_REGISTRY`:
   ```python
   MODEL_REGISTRY = [
       (ChatSendRequest, "ChatReq"),
       (MindspaceCreateRequest, "CreateMindSpaceReq"),  # Add here
   ]
   ```

2. Add instance creation in `create_minimal_instance()`:
   ```python
   if model_class == MindspaceCreateRequest:
       return MindspaceCreateRequest(
           name="test",
           # ... required fields
       )
   ```

3. For optional SDK fields where API requires a default value:
   ```python
   @field_serializer("optional_field")
   def serialize_optional_field(self, v):
       return v or []  # Default value for API
   ```

## Schema Status Concepts

The test runner categorizes schemas into three buckets:

| Status | Meaning | Action |
|--------|---------|--------|
| **TESTED** | SDK model exists and is validated against spec | ✅ Green |
| **SKIPPED** | Intentionally excluded (internal, OpenAI compat, path params, components) | ⏭️ Ignored |
| **NOT REGISTERED** | Schema exists in spec but no SDK model. **Technical Debt.** | ❌ Warning |

### When to use each:

- **TESTED**: Default. SDK model serializes to spec-compliant JSON.
- **SKIPPED**: Use for:
  - Internal schemas (`CentrifugoRpcRequest`, `ArtifactWebhookReq`)
  - OpenAI compatibility layer (`ChatCompletionsReq`, `ModelsListResp`)
  - Path-parameter-only requests (`GetProjectByIdReq`)
  - Shared components (`BaseSchema`, `MindspaceType`, `TokenSchema`)
- **NOT REGISTERED**: Leave out of registry entirely. Test runner warns about these as debt.

```python
# Example: Skipped schema
ContractDef("BaseSchema", status=SchemaStatus.SKIPPED, reason="Component")

# Example: Unimplemented (just don't add it - shows as warning)
# SignUpRequest - not in registry, test runner will flag it
```

