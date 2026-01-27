# Contributing to Magick Mind SDK

Thank you for your interest in contributing to the Magick Mind SDK!

## For SDK Users

If you're looking to **use** the SDK, see the main [README](../../README.md).

## For SDK Contributors

This section is for developers who want to **extend** the SDK by adding new resources, features, or improvements.

### Adding Resources

See [Resource Implementation Guide](resource_implementation_guide/) for a complete working example of adding a chat resource with:
- Pydantic models (v1, v2)
- Resource classes
- Version handling

### Project Structure

```
magick_mind/
├── auth/           # Authentication providers
├── http/           # HTTP client
├── models/         # Pydantic request/response models
├── resources/      # API resource clients
├── config.py       # Configuration
└── exceptions.py   # Error hierarchy
```

### Development Setup

```bash
# Clone the repo
git clone <repo-url>
cd AGD_Magick_Mind_SDK

# Install with dev dependencies
uv sync

# Run tests
uv run pytest
```

### Guidelines

- **Follow existing patterns** - See `magick_mind/resources/README.md`
- **Use versioned folders** - `models/v1/`, `resources/v1/` etc.
- **Add type hints** - All functions should have type annotations
- **Write tests** - Add tests for new functionality
- **Update docs** - Keep README and docstrings up to date

### Questions?

Open an issue or discuss in the project's communication channels.
