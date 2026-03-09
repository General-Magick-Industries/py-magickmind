# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-04

### Breaking Changes
- **Mindspace**: `user_ids` renamed to `participant_ids` across MindSpace model, create/update requests, and `add_users()` → `add_participants()` (deprecated alias kept)
- **Mindspace list**: `list(user_id=...)` parameter replaced with `participant_id`, `project_id`, `type`, `name`, `cursor`, `limit`, `order`

### Added
- **Blueprint resource** (`client.v1.blueprint`): Full CRUD for reusable persona trait templates
    - `create`, `get`, `get_by_key`, `list`, `update`, `patch`, `delete`, `clone`, `validate`, `hydrate`
- **Persona resource** (`client.v1.persona`): Persona management with versioning
    - `create`, `get`, `update`, `delete`, `create_from_blueprint`
    - Versioning: `create_version`, `list_versions`, `get_version`, `get_active_version`, `set_active_version`
- **Runtime resource** (`client.v1.runtime`): Effective personality computation
    - `get_effective_personality`, `invalidate_cache`
- **Mindspace context** (`client.v1.mindspace.prepare_context`): Composable multi-source context retrieval (chat history, corpus, Pelican episodic memory)
- **Mindspace LiveKit**: Token generation and agent signalling
    - `get_livekit_token`, `livekit_join`
- **Shared personality models** (`models.v1.personality`): `TraitValue`, `TraitConstraint`, `GrowthConfig`, `DyadicConfig`, `BlueprintTrait`, and more
- **HTTP PATCH support**: Added `patch()` method to HTTP client
- **Corpus artifact management** (`client.v1.corpus`): `add_artifact`, `add_artifacts` (batch, max 20), `remove_artifact`, `get_artifact_status`, `list_artifact_statuses`; supports text/*, JSON, XML, and PDF

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

