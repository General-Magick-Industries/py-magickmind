# Contributing to Magick Mind SDK

## Development Setup

```bash
git clone https://github.com/General-Magick-Industries/py-magickmind.git
cd py-magickmind
uv sync --all-extras
```

## Running Tests

```bash
# All tests
uv run pytest

# Contract tests only
uv run pytest -m contract -v

# Unit tests
uv run pytest tests/ -v
```

## Contract Testing Workflow

We use serialization-based contract testing to ensure SDK models match the Magick Mind API.

### How It Works

1. **Spec snapshots** in `specs/` represent the API contract
2. **Tests** validate that SDK payloads match the spec
3. **Serializers** transform optional SDK fields to API-required defaults

### Updating Specs

When the Magick Mind API changes, download the updated OpenAPI spec and replace the
relevant file in `specs/` (e.g. `specs/openapi.dev.json`), then run the contract tests:

```bash
uv run pytest -m contract -v
```

Fix any failures by updating the SDK models to match the new spec.

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

1. Create a feature branch from `main`
2. Make your changes
3. Run tests: `uv run pytest`
4. Run contract tests: `uv run pytest -m contract`
5. Ensure lint and formatting pass: `uv run ruff check . && uv run ruff format --check .`
6. Submit a pull request against `main`
