# Apidog vs Magick Mind API Reality - Divergence Report

**Generated:** 2026-02-01  
**API Sync:** `fb381fa` (latest)  
**Apidog Main Export:** 102KB  
**Apidog Develop Export:** 42KB (schema-only, incomplete)

## Executive Summary

The SDK was built from Apidog documentation which **incorrectly documented response structures**. The actual Magick Mind API implementation (Go .api files) returns different formats. This document tracks the divergence and the fixes applied.

## Root Cause

Apidog was manually documented without contract tests. Documentation drifted from implementation over time.

**Going forward:**
- ✅ Magick Mind API `.api` files = source of truth
- ✅ OpenAPI generated from the API via `goctl`
- ✅ SDK models validated against API-generated spec
- ⚠️ Apidog updated manually from generated spec (if needed for frontend docs)

## Critical Response Structure Mismatches

### 1. CRUD Operations Return FLAT Schemas (Not Wrapped)

| Endpoint | Apidog Documented | API Reality | Status |
|----------|-------------------|-----------------|--------|
| `POST /v1/projects` | `{success, message, project: {...}}` | **FLAT** `ProjectSchema` | ❌ BREAKING |
| `GET /v1/projects/{id}` | `{success, message, project: {...}}` | **FLAT** `ProjectSchema` | ❌ BREAKING |
| `PUT /v1/projects/{id}` | `{success, message, project: {...}}` | **FLAT** `ProjectSchema` | ❌ BREAKING |
| `POST /v1/mindspaces` | `{success, message, mindspace: {...}}` | **FLAT** `MindSpaceSchema` | ❌ BREAKING |
| `GET /v1/mindspaces/{id}` | `{success, message, mindspace: {...}}` | **FLAT** `MindSpaceSchema` | ❌ BREAKING |
| `PUT /v1/mindspaces/{id}` | `{success, message, mindspace: {...}}` | **FLAT** `MindSpaceSchema` | ❌ BREAKING |
| `POST /v1/mindspaces/{id}/users` | `{success, message, mindspace: {...}}` | **FLAT** `MindSpaceSchema` | ❌ BREAKING |
| `POST /v1/corpus` | `{success, message, corpus: {...}}` | **FLAT** `CorpusSchema` | ❌ BREAKING |
| `GET /v1/corpus/{id}` | `{success, message, corpus: {...}}` | **FLAT** `CorpusSchema` | ❌ BREAKING |
| `PUT /v1/corpus/{id}` | `{success, message, corpus: {...}}` | **FLAT** `CorpusSchema` | ❌ BREAKING |
| `POST /v1/end-users` | `{success, message, ...}` | **FLAT** `EndUserSchema` | ❌ BREAKING |
| `GET /v1/end-users/{id}` | `{success, message, ...}` | **FLAT** `EndUserSchema` | ❌ BREAKING |
| `PUT /v1/end-users/{id}` | `{success, message, ...}` | **FLAT** `EndUserSchema` | ❌ BREAKING |

**Evidence:** The API `.api` files define return types as `returns (ProjectSchema)`, not `returns (CreateProjectResponse)`.

### 2. List Endpoints Use Standardized Pagination

| Endpoint | Apidog Documented | API Reality | Status |
|----------|-------------------|-----------------|--------|
| `GET /v1/projects` | `{success, message, projects: [...]}` | `{data: [...], paging: {}}` | ❌ BREAKING |
| `GET /v1/mindspaces` | `{success, message, mindspaces: [...]}` | `{data: [...], paging: {}}` | ❌ BREAKING |
| `GET /v1/corpus` | `{success, message, corpus: [...]}` | `{data: [...], paging: {}}` | ❌ BREAKING |
| `GET /v1/end-users` | `{data: [...], paging: {}}` | `{data: [...], paging: {}}` | ✅ CORRECT |
| `GET /v1/mindspaces/{id}/messages` | `{chat_histories: [...], last_id, ...}` | `{data: [...], paging: {}}` | ✅ FIXED |

**The API standardized pagination structure (from `common.api`):**
```json
{
  "data": [...],
  "paging": {
    "cursors": {
      "after": "cursor-string-or-null",
      "before": "cursor-string-or-null"
    },
    "has_more": true,
    "has_previous": false
  }
}
```

### 3. Chat Response Has No Wrapper

| Endpoint | Apidog Documented | API Reality | Status |
|----------|-------------------|-----------------|--------|
| `POST /v1/chat/magickmind` | `{success, message, content: {...}}` | `{content: {...}}` | ❌ BREAKING |

**Evidence:** `magickmind.api` defines `ChatResponse { Content *ChatSchema }` - only one field.

### 4. Field Optionality Differences

| Schema.Field | Apidog | API | Impact |
|--------------|--------|---------|--------|
| `UpdateEndUserRequest.name` | Required | Optional | ⚠️ SDK over-validates |
| `UpdateProjectRequest.name` | Optional | **Required** | ⚠️ SDK under-validates |
| `UpdateProjectRequest.corpus_ids` | Optional | **Required** | ⚠️ SDK under-validates |
| `CreateProjectRequest.corpus_ids` | Required (dev) / Optional (main) | **Optional** | ⚠️ Apidog inconsistency |

### 5. ChatHistoryMessage Field Mismatch

| Field | SDK Has | API Has | Status |
|-------|---------|-------------|--------|
| `artifact_ids` | ✅ Yes | ❌ No (not in API's `ChatHistoryItem`) | Ghost field - remove |
| `create_at` | ✅ Yes (alias) | ✅ Yes | Correct |
| `update_at` | ✅ Yes (alias) | ✅ Yes | Correct |

## Apidog Export Issues

### Develop Branch Export (42KB)

**Problem:** `paths: {}` is empty - schema-only export

This appears to be an Apidog export configuration issue. The develop branch should have paths defined.

**Recommendation:** Report to Apidog maintainer or re-export with correct settings.

### Main Branch Export (102KB)

**Problem:** Has paths but incorrect response schemas (wrapped instead of flat)

**Root cause:** Manual documentation that drifted from implementation.

## SDK Fixes Applied

### Breaking Changes (v2.0.0)

All response models updated to match the Magick Mind API reality:

| Model | Before | After |
|-------|--------|-------|
| `CreateMindSpaceResponse` | `BaseResponse + {mindspace}` | Type alias for `MindSpace` (flat) |
| `UpdateMindSpaceResponse` | `BaseResponse + {mindspace}` | Type alias for `MindSpace` (flat) |
| `GetMindSpaceListResponse` | `BaseResponse + {mindspaces: []}` | `{data: [], paging: PageInfo}` |
| `CreateProjectResponse` | `{project: ...}` | Type alias for `Project` (flat) |
| `GetProjectResponse` | `{project: ...}` | Type alias for `Project` (flat) |
| `UpdateProjectResponse` | `{project: ...}` | Type alias for `Project` (flat) |
| `GetProjectListResponse` | `{projects: []}` | `{data: [], paging: PageInfo}` |
| `CreateCorpusResponse` | `BaseResponse + {corpus}` | Type alias for `Corpus` (flat) |
| `UpdateCorpusResponse` | `BaseResponse + {corpus}` | Type alias for `Corpus` (flat) |
| `ListCorpusResponse` | `BaseResponse + {corpus: []}` | `{data: [], paging: PageInfo}` |
| `ChatSendResponse` | `BaseResponse + {content}` | `{content: ChatPayload}` (no wrapper) |
| `MindspaceMessagesResponse` | Custom cursors | `{data: [], paging: PageInfo}` |

### Request Model Fixes

| Model | Field | Before | After |
|-------|-------|--------|-------|
| `UpdateEndUserRequest` | `name` | Required | Optional (partial update) |
| `UpdateProjectRequest` | `name` | Optional | **Required** |
| `UpdateProjectRequest` | `corpus_ids` | Optional | **Required** |

### Removed Fields

| Model | Field | Reason |
|-------|-------|--------|
| `ChatHistoryMessage` | `artifact_ids` | Not in API's `ChatHistoryItem` |

## How to Validate Against the Magick Mind API

### Generate Latest Spec

```bash
cd services/bifrost  # API gateway service
goctl api plugin -p goctl-openapi -api bifrost.api -dir .
cp openapi.json ../../libs/sdk/tests/contract/api-actual.json
```

### Run Contract Tests

```bash
cd libs/sdk
uv run pytest tests/contract/ -v
```

Tests now validate against `api-actual.json` (API-generated), not Apidog exports.

## Migration Guide for SDK Users

### Before (v1.x - WRONG)

```python
# List projects
response = client.v1.project.list()
# Expected: {success: true, message: "...", projects: [...]}
for project in response.projects:  # BREAKS
    print(project.name)

# Create project
response = client.v1.project.create(name="Test")
# Expected: {success: true, message: "...", project: {...}}
print(response.project.id)  # BREAKS
```

### After (v2.0 - CORRECT)

```python
# List projects
response = client.v1.project.list()
# Actual: {data: [...], paging: {...}}
for project in response.data:  # CORRECT
    print(project.name)

# Navigate pagination
if response.paging.has_more:
    next_response = client.v1.project.list(cursor=response.paging.cursors.after)

# Create project
project = client.v1.project.create(name="Test")
# Returns flat Project object
print(project.id)  # CORRECT
```

## Recommendations for Team

### For Backend Devs

1. **Trust the API .api files** - This is what the server actually implements
2. **Don't trust Apidog alone** - Verify against generated OpenAPI or actual API calls
3. **Use goctl-generated spec** - `goctl api plugin -p goctl-openapi` for source of truth

### For Frontend Devs

1. **SDK v2.0 has breaking changes** - Update your response handling code
2. **Pagination is standardized** - All list responses use `{data: [], paging: {}}`
3. **No more success/message wrappers** - CRUD operations return resources directly

### For QA/Integration

1. **Contract tests now validate API reality** - Not Apidog documentation
2. **Run tests before releases** - `uv run pytest tests/contract/`
3. **Check coverage report** - ❌ warnings indicate unimplemented features (technical debt)

## Technical Debt

Documented in contract tests as "NOT REGISTERED":
- Traits resource (new feature, SDK support pending)
- Persona resource (documented debt)
- Signup endpoints (website-only, not SDK scope)

## Appendix: Source Files

| Source | Location | Purpose |
|--------|----------|---------|
| API definitions | `services/bifrost/api/v1/*.api` | Server implementation (SOURCE OF TRUTH) |
| API-generated OpenAPI | `services/bifrost/openapi.json` | Generated via goctl |
| SDK contract spec | `libs/sdk/tests/contract/api-actual.json` | Copy of API-generated |
| Apidog legacy | `libs/sdk/tests/contract/apidog-legacy.json` | Historical reference (WRONG!) |
| SDK models | `libs/sdk/magick_mind/models/v1/*.py` | Python Pydantic models |
