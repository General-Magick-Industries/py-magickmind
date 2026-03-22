# Contributing to Magick Mind SDK

## Development Setup

```bash
# Clone and install
git clone <repo>
cd AGD_Magick_Mind_SDK
uv sync
```

## Running Tests

```bash
# All tests
uv run pytest

# Contract tests only
uv run pytest -m contract -v

# Unit tests
uv run pytest tests/unit/ -v
```

## Contract Testing Workflow

We use serialization-based contract testing to ensure SDK models match the Magick Mind API.

### How It Works

1. **Spec snapshots** in `specs/` represent the API contract
2. **Tests** validate that SDK payloads match the spec
3. **Serializers** transform optional SDK fields to API-required defaults

### Updating Specs

When the Magick Mind API changes:

```bash
# 1. Generate new spec in the API gateway (services/bifrost)
cd ../bifrost
goctl api plugin -p goctl-openapi -api api/v1/*.api -dir .

# 2. Copy to SDK (dev or main depending on branch)
cp api/openapi.json ../AGD_Magick_Mind_SDK/specs/openapi.dev.json

# 3. Run contract tests
cd ../AGD_Magick_Mind_SDK
uv run pytest -m contract -v

# 4. Fix any failures by updating SDK models
```

### Adding New Models

1. Add model to `tests/contract/test_payloads.py` → `MODEL_REGISTRY`
2. Add instance creation in `create_minimal_instance()`
3. Add `@field_serializer` for optional fields if needed

See `tests/contract/README.md` for detailed instructions.

## Code Style

- Format: `uv run ruff format .`
- Lint: `uv run ruff check .`
- Type check: `uv run pyright`

## Pull Request Process

1. Create feature branch
2. Make changes
3. Run tests: `uv run pytest`
4. Run contract tests: `uv run pytest -m contract`
5. Submit PR
