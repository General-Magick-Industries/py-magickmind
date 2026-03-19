# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-18

### Breaking Changes
- **Async-first client** — `MagickMind` is now fully async. All resource methods
  require `await`, context manager is `async with`, `close()` is a coroutine.
  `HTTPClient` uses `httpx.AsyncClient` internally.
- **Auth provider async-only** — Sync methods removed from `EmailPasswordAuth`
  (`get_headers`, `get_token`, `refresh_if_needed`, `_login`, `_refresh`).
  Use `get_headers_async()`, `get_token_async()`, `refresh_if_needed_async()`.
- **Realtime overhaul** — `RealtimeEventHandler` (subclass pattern) replaced by
  `EventRouter` (decorator-based routing with `@router.on("event_type")`).
- **Renamed export** — `ChatPayload` → `ChatAck`.
- **Mindspace**: `user_ids` → `participant_ids` across model, create/update
  requests, and `add_users()` → `add_participants()` (deprecated alias kept).
- **Mindspace list**: `list(user_id=...)` replaced with `participant_id`,
  `project_id`, `type`, `name`, `cursor`, `limit`, `order` params.
- **Removed `/v1/models`** — Ghost endpoint that Bifrost never implemented.

### Added
- **OpenAI-compatible completions** — `client.openai_client(api_key=...)` returns
  an `AsyncOpenAI` instance pointed at Bifrost's `/v1/chat/completions`.
  Supports streaming and non-streaming. Install with `pip install magickmind[openai]`.
- **Trait resource** (`client.v1.traits`) — Full CRUD for `/v1/traits`:
  `create`, `get`, `list`, `update`, `patch`, `delete`.
- **Typed realtime events** — `ChatMessageEvent`, `ChatMessagePayload`,
  `ImageGenerationEvent`, `ArtifactPayload`, `ArtifactData`, `UnknownEvent`,
  `WsEvent` union type, and `parse_ws_event()` parser.
- **`client.get_user_id()`** — Extract authenticated user ID from JWT `sub`
  claim. Handy for subscribing to your own realtime channel.
- **Flat chat params** — `chat.send()` accepts `fast_model_id`,
  `smart_model_ids`, `compute_power` directly. `config=` kwarg still accepted.
- **Blueprint resource** (`client.v1.blueprint`): Full CRUD for persona trait templates
    - `create`, `get`, `get_by_key`, `list`, `update`, `patch`, `delete`, `clone`, `validate`, `hydrate`
- **Persona resource** (`client.v1.persona`): Persona management with versioning
    - `create`, `get`, `update`, `delete`, `create_from_blueprint`
    - Versioning: `create_version`, `list_versions`, `get_version`, `get_active_version`, `set_active_version`
- **Runtime resource** (`client.v1.runtime`): Effective personality computation
    - `get_effective_personality`, `invalidate_cache`
- **Mindspace context** (`client.v1.mindspace.prepare_context`): Composable multi-source context retrieval
- **Mindspace LiveKit**: `get_livekit_token`, `livekit_join`
- **Shared personality models** (`models.v1.personality`): `TraitValue`, `TraitConstraint`, `GrowthConfig`, `DyadicConfig`, `BlueprintTrait`, etc.
- **HTTP PATCH support**: Added `patch()` method to HTTP client
- **Corpus artifact management** (`client.v1.corpus`): `add_artifact`, `add_artifacts`, `remove_artifact`, `get_artifact_status`, `list_artifact_statuses`
- **Corpus `api_key` param** — `add_artifact()` and `add_artifacts()` accept optional `api_key` kwarg for dev/prod corpus-scoped operations.
- **`completions.py` example** — New example demonstrating OpenAI-compatible streaming and non-streaming completions.

### Fixed
- Removed `pytest-asyncio` from production dependencies (was in `[project.dependencies]`; now dev-only).
- Added `asyncio_mode = "auto"` to `[tool.pytest.ini_options]`.
- Handle Bifrost proto enums returned as strings and null slices returned as `null` instead of `[]`.
- Examples now load `.env` via `load_dotenv()` and use correct dev environment URLs.

### Changed
- All examples updated for async API usage.
- Test suite updated for async patterns (`pytest-httpx`).
- Contract schema registry updated for new models.

### Migration Guide

**Client usage (sync → async):**
```python
# Before (0.1.x)
client = MagickMind(auth=auth)
response = client.v1.chat.send(...)
client.close()

# After (0.2.0)
async with MagickMind(auth=auth) as client:
    response = await client.v1.chat.send(...)
```

**Chat send (ConfigSchema → flat params):**
```python
# Before
response = client.v1.chat.send(..., config=ConfigSchema(fast_model_id="gpt-4", ...))

# After
response = await client.v1.chat.send(..., fast_model_id="gpt-4", smart_model_ids=["gpt-4"])
```

**Realtime events (subclass → decorator):**
```python
# Before
class MyHandler(RealtimeEventHandler):
    async def on_message(self, user_id, payload):
        print(payload)
await client.realtime.connect(events=MyHandler())

# After
from magick_mind import EventRouter, ChatMessageEvent
router = EventRouter()

@router.on("chat_message")
async def handle_chat(event: ChatMessageEvent):
    print(event.payload.message)

await client.realtime.connect(event_handler=router)
```

---

## [0.0.1] - 2026-01-20

### Added
- **Realtime WebSocket Client**: Full support for real-time interaction in `magick_mind.realtime`.
- **Resources**:
    - `Chat` and `History` resources for messaging.
    - `Mindspace`, `Project`, `EndUser`, `Corpus` resources for management.
- **Artifacts**: Support for file uploads and attachment handling.
- **Examples**:
    - Detailed `setup_resources.py` script.
    - Complete examples for Realtime Chat and Backend integration.
