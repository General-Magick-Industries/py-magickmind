# Contract Tests - Agent Instructions

## The One Rule

**DO NOT add `SKIPPED` for unimplemented features.** Leave them out of the registry entirely.

| Situation | Action | Result |
|-----------|--------|--------|
| Schema needs SDK model (not built yet) | **Don't add to registry** | ❌ Shows as warning (technical debt) |
| Schema is internal/irrelevant | Add with `SKIPPED` | Silent (intentional) |

## Why?

- Unregistered schemas automatically show as ❌ warnings
- This tracks technical debt without manual effort
- Adding SKIPPED hides debt - **don't do it**

## What Qualifies as SKIPPED?

Only these categories should be SKIPPED:

```python
# Internal RPC/Webhooks (not for SDK users)
ContractDef("CentrifugoRpcRequest", status=SchemaStatus.SKIPPED, reason="Internal RPC")
ContractDef("ArtifactWebhookReq", status=SchemaStatus.SKIPPED, reason="Internal Webhook")

# Path parameters only (no JSON body)
ContractDef("GetProjectByIdReq", status=SchemaStatus.SKIPPED, reason="Path Param Only")

# OpenAI compatibility layer (pass-through, not SDK's concern)
ContractDef("ChatCompletionsReq", status=SchemaStatus.SKIPPED, reason="OpenAI Compat")

# Shared components (internal building blocks, not standalone)
ContractDef("BaseSchema", status=SchemaStatus.SKIPPED, reason="Component")
ContractDef("TokenSchema", status=SchemaStatus.SKIPPED, reason="Component")
```

## What Should NOT be SKIPPED?

Features not yet implemented in SDK:

```python
# WRONG - hides technical debt
ContractDef("CreateTraitRequest", status=SchemaStatus.SKIPPED, reason="Not supported")

# CORRECT - just don't add it, it shows as ❌ warning automatically
# (no entry for CreateTraitRequest)
```

## Quick Reference

```
Spec has schema → Is it in registry?
                      │
                      ├─ YES with TESTED → ✅ Validated
                      ├─ YES with SKIPPED → ⏭️ Silent (internal/irrelevant)
                      └─ NO → ❌ Warning (technical debt to implement)
```

## Running Tests

```bash
uv run pytest tests/contract/ -v
```

Check the coverage report at the end - ❌ items are your debt backlog.
