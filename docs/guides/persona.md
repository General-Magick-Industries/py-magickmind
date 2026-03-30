# Persona & Prepare Guide

A guide to building AI personas with the Magick Mind SDK — from creation and versioning to generating ready-to-use system prompts with `prepare()`.

## Overview

The persona system gives your AI a stable, configurable identity. Four resources work together:

**Persona** (`client.v1.persona`) — The AI's identity: a name, role, list of traits, tones, and a background story. This is the top-level object you create and manage.

**Blueprint** (`client.v1.blueprint`) — Reusable trait templates. A blueprint defines a set of trait slots with defaults and constraints that multiple personas can share. Use blueprints when you want consistent personality foundations across many personas.

**PersonaVersion** — A snapshot of a persona's trait constraints, growth configuration, and dyadic settings. Versions let you evolve a persona's behaviour over time without losing history. The active version is what `prepare()` uses.

**Runtime** (`client.v1.runtime`) — The effective (blended) personality at runtime, merging authored traits with learned values. Useful for inspection and debugging.

**`prepare()`** is the key operation: given a `persona_id` (and optionally a `user_id`), it resolves the persona's traits, active version constraints, and any user-specific context into a single `system_prompt` string — ready to inject directly into a chat API call.

## Quick Start

Create a persona and get a system prompt in four lines:

```python
import asyncio
from magick_mind import MagickMind

async def main():
    async with MagickMind(
        base_url="https://api.magickmind.ai",
        email="user@example.com",
        password="password",
    ) as client:
        # 1. Create a persona
        persona = await client.v1.persona.create(
            name="Aria",
            role="customer support specialist",
            traits=["empathetic", "concise", "solution-focused"],
            tones=["warm", "professional"],
            background_story="Aria has five years of experience resolving complex support cases.",
        )

        # 2. Prepare — get a ready-to-use system prompt
        result = await client.v1.persona.prepare(persona.id)

        # 3. Use it
        print(result.system_prompt)
        # → "You are Aria, a customer support specialist. You are empathetic,
        #    concise, and solution-focused. Your tone is warm and professional.
        #    Background: Aria has five years of experience..."

asyncio.run(main())
```

`result.system_prompt` is a plain string. Pass it as the `system` message in any chat API call.

## The Prepare Endpoint

`client.v1.persona.prepare()` is the bridge between persona configuration and a live chat session.

### What it resolves

When you call `prepare()`, the API:

1. Loads the persona's name, role, traits, tones, and background story
2. Fetches the **active version** and applies its `constraints` (trait locks, value overrides, allowed ranges)
3. If `user_id` is provided, incorporates **dyadic** (per-user) learned values from the active version's `DyadicConfig`
4. Renders everything into a single coherent `system_prompt` string

### Global mode vs per-user mode

```python
# Global mode — same prompt for all users
result = await client.v1.persona.prepare(persona_id)

# Per-user mode — adapts to a specific user's interaction history
result = await client.v1.persona.prepare(persona_id, user_id="user-abc-123")
```

Use **global mode** when the persona behaves identically for everyone (e.g. a public-facing bot, a content generation assistant).

Use **per-user mode** when the persona has dyadic learning enabled and should adapt its tone or emphasis based on what it has learned about a specific user.

### The response

`PreparePersonaResponse` has a single field:

```python
result.system_prompt  # str — inject this directly into your chat call
```

### Using it with chat

```python
import openai

async def chat_with_persona(client, persona_id: str, user_message: str, user_id: str):
    # Prepare the system prompt for this user
    prepared = await client.v1.persona.prepare(persona_id, user_id=user_id)

    # Inject as the system message
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prepared.system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content
```

> **Tip:** Call `prepare()` once per session (or when the persona version changes) rather than on every message. The system prompt is stable between calls unless you update the persona or switch the active version.

## Creating Personas

### Direct Creation

```python
async with MagickMind(...) as client:
    persona = await client.v1.persona.create(
        name="Max",
        role="sales development representative",
        traits=["persuasive", "curious", "resilient"],
        tones=["energetic", "friendly"],
        background_story=(
            "Max specialises in outbound prospecting for B2B SaaS companies. "
            "He asks thoughtful discovery questions and never pushes too hard."
        ),
    )
    print(persona.id)   # "p-abc-123"
    print(persona.name) # "Max"
```

All fields except `name` and `role` are optional. A persona with no traits or tones is valid — `prepare()` will still produce a usable prompt.

### From Blueprint

Blueprints let you stamp out personas with a consistent trait foundation:

```python
async with MagickMind(...) as client:
    # Create from an existing blueprint
    result = await client.v1.persona.create_from_blueprint(
        blueprint_id="bp-support-agent",
        name="Aria",
        role="customer support specialist",
        background_story="Aria handles tier-1 support for the EMEA region.",
    )

    persona = result.persona   # Persona object
    version = result.version   # Initial PersonaVersion (auto-created from blueprint)

    print(persona.id)
    print(version.version)  # e.g. "1.0"
```

`create_from_blueprint()` returns a `PersonaWithVersion` — both the persona and its initial version are created in one call.

**Why use blueprints?**
- **Consistency** — all personas from the same blueprint share the same trait vocabulary and defaults
- **Reusability** — update the blueprint once; new personas inherit the changes
- **Overrides** — you can still customise per-persona via `trait_overrides`, `additional_traits`, `remove_traits`, `growth_override`, and `dyadic_override`

```python
from magick_mind.models.v1.personality import TraitConstraint, TraitValue

result = await client.v1.persona.create_from_blueprint(
    blueprint_id="bp-support-agent",
    name="Aria (EMEA)",
    role="customer support specialist",
    # Override a specific trait's value
    trait_overrides=[
        TraitConstraint(
            trait_ref="formality",
            value=TraitValue(numeric_value=0.8),  # More formal for EMEA
        )
    ],
    # Remove a trait that doesn't apply
    remove_traits=["casual-language"],
)
```

## Version Management

Versions are snapshots of a persona's trait constraints. The **active version** is what `prepare()` uses. If no version is active, `prepare()` falls back to the persona's base traits.

### Creating a version

```python
from magick_mind.models.v1.personality import (
    TraitConstraint,
    TraitValue,
    GrowthConfig,
    DyadicConfig,
)

async with MagickMind(...) as client:
    version = await client.v1.persona.create_version(
        persona_id="p-abc-123",
        version="1.0",
        constraints=[
            TraitConstraint(
                trait_ref="empathy",
                value=TraitValue(numeric_value=0.9),
            ),
            TraitConstraint(
                trait_ref="verbosity",
                value=TraitValue(numeric_value=0.4),  # Keep responses concise
            ),
        ],
    )
    print(version.id)
    print(version.is_active)  # False — not active yet
```

### Activating a version

```python
async with MagickMind(...) as client:
    # Set version "1.0" as active
    active = await client.v1.persona.set_active_version("p-abc-123", "1.0")
    print(active.is_active)  # True

    # Confirm which version is active
    current = await client.v1.persona.get_active_version("p-abc-123")
    print(current.version)  # "1.0"
```

### How versions affect prepare output

Once a version is active, `prepare()` applies its constraints on top of the persona's base traits. A `HARD` lock fixes a trait value; a `SOFT` lock sets a default that can drift with learning. Constraints narrow the range within which a trait can evolve.

```python
from magick_mind.models.v1.personality import Constraint, LockType

version = await client.v1.persona.create_version(
    persona_id="p-abc-123",
    version="2.0",
    constraints=[
        TraitConstraint(
            trait_ref="tone",
            lock="HARD",                              # Cannot change
            value=TraitValue(string_value="formal"),
        ),
        TraitConstraint(
            trait_ref="empathy",
            lock="SOFT",                              # Can drift within bounds
            constraint=Constraint(min_bound=0.7, max_bound=1.0),
        ),
    ],
)
await client.v1.persona.set_active_version("p-abc-123", "2.0")

# prepare() now reflects the v2.0 constraints
result = await client.v1.persona.prepare("p-abc-123")
```

### Listing versions

```python
async with MagickMind(...) as client:
    response = await client.v1.persona.list_versions("p-abc-123")
    for v in response.data:
        status = "✓ active" if v.is_active else ""
        print(f"  {v.version} {status}")
```

## Common Patterns

### Pattern 1: Static Persona (no growth)

The simplest setup — a persona with fixed traits and no version constraints:

```python
async def setup_static_persona(client):
    persona = await client.v1.persona.create(
        name="Sage",
        role="knowledge assistant",
        traits=["precise", "thorough", "neutral"],
        tones=["calm", "authoritative"],
        background_story="Sage answers questions using only verified information.",
    )

    # prepare() works immediately — no version needed
    result = await client.v1.persona.prepare(persona.id)
    return persona.id, result.system_prompt
```

### Pattern 2: Blueprint-Based Personas

Stamp out multiple personas from a shared template:

```python
async def create_regional_agents(client, blueprint_id: str):
    regions = [
        ("Aria", "EMEA Support Specialist", "Aria covers the EMEA region."),
        ("Kai",  "APAC Support Specialist", "Kai covers the APAC region."),
        ("Sam",  "AMER Support Specialist", "Sam covers the Americas."),
    ]

    personas = []
    for name, role, story in regions:
        result = await client.v1.persona.create_from_blueprint(
            blueprint_id=blueprint_id,
            name=name,
            role=role,
            background_story=story,
        )
        personas.append(result.persona)
        print(f"Created {name}: {result.persona.id} (version {result.version.version})")

    return personas
```

### Pattern 3: Per-User Adaptation (Dyadic)

Enable dyadic learning so the persona adapts to each user over time:

```python
from magick_mind.models.v1.personality import DyadicConfig

async def setup_adaptive_persona(client):
    # Create the persona
    persona = await client.v1.persona.create(
        name="Nova",
        role="personal productivity coach",
        traits=["motivating", "structured", "adaptive"],
        tones=["encouraging", "direct"],
        background_story="Nova tailors coaching style to each individual's working patterns.",
    )

    # Create a version with dyadic learning enabled
    version = await client.v1.persona.create_version(
        persona_id=persona.id,
        version="1.0",
        dyadic=DyadicConfig(
            enabled=True,
            max_relationships=1000,
            learnable_traits=["tone", "verbosity", "encouragement-level"],
            initial_weight=0.1,
            max_weight=0.4,
            confidence_threshold=10,  # Interactions before dyadic weight kicks in
        ),
    )
    await client.v1.persona.set_active_version(persona.id, "1.0")

    return persona.id


async def get_prompt_for_user(client, persona_id: str, user_id: str):
    # Each user gets a personalised system prompt
    result = await client.v1.persona.prepare(persona_id, user_id=user_id)
    return result.system_prompt
```

### Pattern 4: Using Prepare with Chat

A complete request handler that prepares a persona and calls a chat model:

```python
import os
import openai
from magick_mind import MagickMind

async def handle_chat_request(
    persona_id: str,
    user_id: str,
    conversation_history: list[dict],
    new_message: str,
) -> str:
    async with MagickMind(
        base_url=os.getenv("MAGICKMIND_BASE_URL"),
        email=os.getenv("MAGICKMIND_EMAIL"),
        password=os.getenv("MAGICKMIND_PASSWORD"),
    ) as client:
        # Resolve persona → system prompt (per-user for dyadic adaptation)
        prepared = await client.v1.persona.prepare(persona_id, user_id=user_id)

    # Build the message list
    messages = [
        {"role": "system", "content": prepared.system_prompt},
        *conversation_history,
        {"role": "user", "content": new_message},
    ]

    # Call your LLM
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )
    return response.choices[0].message.content
```

> **Caching tip:** `prepare()` is a network call. In high-throughput scenarios, cache `system_prompt` per `(persona_id, user_id)` pair and invalidate when the active version changes or when you explicitly call `client.v1.runtime.invalidate_cache(persona_id)`.

## API Reference

### `create()`

Create a new persona.

**Parameters:**
- `name` (str, required): Persona name
- `role` (str, required): Persona role description
- `artifact_id` (str, optional): Associated artifact ID (e.g. avatar image)
- `traits` (list[str], optional): Trait names (default: `[]`)
- `tones` (list[str], optional): Tone names (default: `[]`)
- `background_story` (str, optional): Narrative background (default: `""`)

**Returns:** `Persona`

---

### `prepare()`

Resolve a persona into a ready-to-use system prompt.

**Parameters:**
- `persona_id` (str, required): Persona ID
- `user_id` (str, optional): User ID for per-user dyadic adaptation

**Returns:** `PreparePersonaResponse`
- `system_prompt` (str): The generated system prompt string

---

### `create_from_blueprint()`

Create a persona and its initial version from a blueprint template.

**Parameters:**
- `blueprint_id` (str, required): Source blueprint ID
- `name` (str, required): Persona name
- `role` (str, required): Persona role
- `background_story` (str, optional): Background narrative
- `artifact_id` (str, optional): Associated artifact ID
- `trait_overrides` (list[TraitConstraint], optional): Override specific blueprint traits
- `additional_traits` (list[TraitConstraint], optional): Add traits not in the blueprint
- `remove_traits` (list[str], optional): Remove trait refs from the blueprint
- `growth_override` (GrowthConfig, optional): Override the blueprint's growth config
- `dyadic_override` (DyadicConfig, optional): Override the blueprint's dyadic config

**Returns:** `PersonaWithVersion` (`persona`, `version`)

---

### `create_version()`

Create a new version snapshot for a persona.

**Parameters:**
- `persona_id` (str, required): Persona ID
- `version` (str, required): Version string (e.g. `"1.0"`, `"2.1"`)
- `constraints` (list[TraitConstraint], optional): Trait constraints for this version
- `growth` (GrowthConfig, optional): Growth configuration
- `dyadic` (DyadicConfig, optional): Dyadic learning configuration

**Returns:** `PersonaVersion`

---

### `set_active_version()`

Activate a version. `prepare()` will use this version from now on.

**Parameters:**
- `persona_id` (str, required): Persona ID
- `version` (str, required): Version string to activate

**Returns:** `PersonaVersion`

---

### `get_active_version()`

Get the currently active version.

**Parameters:**
- `persona_id` (str, required): Persona ID

**Returns:** `PersonaVersion`

---

### `list_versions()`

List all versions for a persona.

**Parameters:**
- `persona_id` (str, required): Persona ID
- `cursor` (str, optional): Pagination cursor
- `limit` (int, optional): Maximum results

**Returns:** `ListPersonaVersionsResponse` (`data`, `paging`)

## Related Resources

- [Advanced Usage Guide](./advanced_usage.md) — Async patterns, context managers, error handling
- [Backend Integration Guide](./backend_integration.md) — Integrating the SDK into a backend service
- [Blueprint Resource](../resources/) — Managing reusable trait templates with `client.v1.blueprint`
- [Runtime Resource](../resources/) — Inspecting effective personality with `client.v1.runtime`
