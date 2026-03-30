"""
Example: Persona Workflow

Demonstrates the full persona lifecycle using the Magick Mind SDK:
- Creating a persona with traits, tones, and a background story
- Preparing a system prompt (global mode — no user context)
- Preparing a per-user system prompt (dyadic/user-specific mode)
- Version management: creating, listing, and activating versions
- How prepared system prompts integrate with chat requests

The `prepare` endpoint is the star of this example — it resolves a persona's
traits, active version constraints, and optional user context into a
ready-to-use system prompt string that can be injected directly into any
LLM chat call.
"""

import asyncio
import os

from dotenv import load_dotenv

from magick_mind import MagickMind
from magick_mind.models.v1.personality import TraitConstraint, TraitValue

load_dotenv()


async def main():
    """Demonstrate the persona creation, prepare, and versioning workflow."""
    base_url = os.getenv("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")
    email = os.getenv("MAGICKMIND_EMAIL", "user@example.com")
    password = os.getenv("MAGICKMIND_PASSWORD", "your-password")

    async with MagickMind(base_url=base_url, email=email, password=password) as client:
        print("=" * 60)
        print("Persona Workflow Example")
        print("=" * 60)

        # ====================================================================
        # PART 1: CREATE & PREPARE (the core workflow)
        # ====================================================================
        print("\n" + "=" * 60)
        print("PART 1: Create & Prepare")
        print("=" * 60)

        # 1. Create a persona named "Aria"
        print("\n1. Creating persona 'Aria'...")
        persona = await client.v1.persona.create(
            name="Aria",
            role="assistant",
            traits=["empathetic", "knowledgeable", "patient"],
            tones=["warm", "professional"],
            background_story=(
                "Aria is a thoughtful AI assistant designed to help users navigate "
                "complex topics with patience and clarity. She draws on broad knowledge "
                "while maintaining a warm, approachable communication style."
            ),
        )
        print(f"✓ Created persona: {persona.id}")
        print(f"  Name:   {persona.name}")
        print(f"  Role:   {persona.role}")
        print(f"  Traits: {persona.traits}")
        print(f"  Tones:  {persona.tones}")

        # 2. Prepare the persona — global mode (no user_id)
        print(f"\n2. Preparing persona {persona.id} (global mode)...")
        try:
            global_prep = await client.v1.persona.prepare(persona.id)
            print("✓ Global system prompt generated:")
            print("-" * 40)
            print(global_prep.system_prompt)
            print("-" * 40)
        except Exception as e:
            print(f"✗ Prepare failed: {e}")
            global_prep = None

        # 3. Print the system_prompt (already printed above, summarise length)
        if global_prep:
            print(f"\n3. System prompt length: {len(global_prep.system_prompt)} chars")
            print("   This prompt is ready to inject into any LLM chat request.")

        # 4. Prepare with user_id — per-user / dyadic mode
        print(f"\n4. Preparing persona {persona.id} with user_id='user-demo-001'...")
        try:
            user_prep = await client.v1.persona.prepare(
                persona.id, user_id="user-demo-001"
            )
            print("✓ Per-user system prompt generated:")
            print("-" * 40)
            print(user_prep.system_prompt)
            print("-" * 40)
        except Exception as e:
            print(f"✗ Per-user prepare failed: {e}")
            user_prep = None

        # 5. Note differences between global and per-user prompts
        print("\n5. Comparing global vs per-user prompts:")
        if global_prep and user_prep:
            global_len = len(global_prep.system_prompt)
            user_len = len(user_prep.system_prompt)
            print(f"   Global prompt:   {global_len} chars")
            print(f"   Per-user prompt: {user_len} chars")
            if user_len != global_len:
                print(
                    "   → Per-user prompt differs: user context / dyadic memory "
                    "has been incorporated."
                )
            else:
                print(
                    "   → Prompts are identical (no dyadic config set yet — "
                    "see Part 2 for version-based customisation)."
                )
        else:
            print("   (One or both prepare calls failed — skipping comparison)")

        # ====================================================================
        # PART 2: VERSION MANAGEMENT
        # ====================================================================
        print("\n" + "=" * 60)
        print("PART 2: Version Management")
        print("=" * 60)

        # 6. Create version "1.1" with a trait constraint
        print(f"\n6. Creating version '1.1' for persona {persona.id}...")
        try:
            version_1_1 = await client.v1.persona.create_version(
                persona_id=persona.id,
                version="1.1",
                constraints=[
                    TraitConstraint(
                        trait_ref="empathetic",
                        value=TraitValue(numeric_value=0.9),
                    ),
                ],
            )
            print(f"✓ Created version: {version_1_1.version}")
            print(f"  Version ID:  {version_1_1.id}")
            print(f"  Is active:   {version_1_1.is_active}")
            print(f"  Constraints: {len(version_1_1.constraints)} constraint(s)")
            for c in version_1_1.constraints:
                val = c.value.numeric_value if c.value else None
                print(f"    - {c.trait_ref}: numeric_value={val}")
        except Exception as e:
            print(f"✗ Create version failed: {e}")
            version_1_1 = None

        # 7. List all versions
        print(f"\n7. Listing versions for persona {persona.id}...")
        try:
            versions_resp = await client.v1.persona.list_versions(persona.id)
            print(f"✓ Found {len(versions_resp.data)} version(s):")
            for v in versions_resp.data:
                active_marker = " ← active" if v.is_active else ""
                print(f"  - {v.version} (ID: {v.id}){active_marker}")
        except Exception as e:
            print(f"✗ List versions failed: {e}")

        # 8. Set version "1.1" as active
        if version_1_1:
            print(f"\n8. Setting version '1.1' as active for persona {persona.id}...")
            try:
                activated = await client.v1.persona.set_active_version(
                    persona.id, "1.1"
                )
                print(f"✓ Active version is now: {activated.version}")
                print(f"  Is active: {activated.is_active}")
            except Exception as e:
                print(f"✗ Set active version failed: {e}")
        else:
            print("\n8. Skipping set_active_version (version creation failed)")

        # 9. Prepare again — version constraints now affect the output
        print(f"\n9. Preparing persona {persona.id} again (version 1.1 now active)...")
        try:
            versioned_prep = await client.v1.persona.prepare(persona.id)
            print("✓ Versioned system prompt generated:")
            print("-" * 40)
            print(versioned_prep.system_prompt)
            print("-" * 40)
            print(
                "   → The active version's trait constraints (empathetic=0.9) "
                "are now reflected in the prompt."
            )
        except Exception as e:
            print(f"✗ Versioned prepare failed: {e}")

        # ====================================================================
        # PART 3: USING PREPARE WITH CHAT (integration pattern)
        # ====================================================================
        print("\n" + "=" * 60)
        print("PART 3: Using Prepare with Chat (Integration Pattern)")
        print("=" * 60)

        print("\n10. Integration pattern: prepare → inject system_prompt into chat")
        print(
            """
   The `prepare` endpoint is designed to be called immediately before
   starting (or resuming) a chat session. The returned `system_prompt`
   is injected as the system message in your chat request:

   ┌─────────────────────────────────────────────────────────────┐
   │  # 1. Resolve the persona's system prompt                   │
   │  prep = await client.v1.persona.prepare(                    │
   │      persona_id,                                            │
   │      user_id=current_user_id,   # optional, for dyadic      │
   │  )                                                          │
   │                                                             │
   │  # 2. Send a chat message with the resolved system prompt   │
   │  await client.v1.chat.send(                                 │
   │      mindspace_id=mindspace_id,                             │
   │      message="Hello, can you help me?",                     │
   │      system_prompt=prep.system_prompt,                      │
   │  )                                                          │
   └─────────────────────────────────────────────────────────────┘

   Key benefits:
   • Trait constraints from the active version are automatically applied
   • Per-user dyadic memory is incorporated when user_id is supplied
   • The system prompt is always up-to-date with the latest version
   • No manual prompt engineering required — the SDK handles assembly
"""
        )

        # ====================================================================
        # CLEANUP
        # ====================================================================
        print("=" * 60)
        print("CLEANUP")
        print("=" * 60)

        print(f"\n1. Deleting persona {persona.id}...")
        try:
            await client.v1.persona.delete(persona.id)
            print(f"✓ Deleted persona: {persona.id}")
        except Exception as e:
            print(f"✗ Failed to delete persona: {e}")

        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
