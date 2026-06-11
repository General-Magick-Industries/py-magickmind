"""
Example: Persona Workflow

Demonstrates the full persona lifecycle using the Magick Mind SDK:

  1. Create a persona (name, role, traits, tones, background story)
  2. Create a version (trait constraints, growth config, dyadic config)
  3. Set the version as active
  4. Prepare the system prompt (requires an active version)

The flow is strictly sequential — you MUST have an active version before
calling `prepare`. The prepare endpoint resolves the active version's trait
constraints, growth rules, and optional user context into a system prompt
string ready for any LLM chat call.
"""

import asyncio
import os

from dotenv import load_dotenv

from magick_mind import MagickMind
from magick_mind.models.v1.personality import (
    Constraint,
    DyadicConfig,
    GrowthConfig,
    TraitConstraint,
    TraitValue,
)

load_dotenv()


async def main():
    """Demonstrate the persona creation → versioning → prepare workflow."""
    base_url = os.getenv("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")
    email = os.getenv("MAGICKMIND_EMAIL", "user@example.com")
    password = os.getenv("MAGICKMIND_PASSWORD", "your-password")

    async with MagickMind(base_url=base_url, email=email, password=password) as client:
        print("=" * 60)
        print("Persona Workflow Example")
        print("=" * 60)

        # ==================================================================
        # STEP 1: CREATE PERSONA
        # ==================================================================
        # A persona defines the character's identity — name, role,
        # descriptive traits, communication tones, and backstory.
        # This does NOT make the persona usable yet; it needs a version.
        # ==================================================================
        print("\n--- Step 1: Create Persona ---")

        persona = await client.v1.persona.create(
            name="Aria",
            role="assistant",
            traits=["empathetic", "knowledgeable", "patient"],
            tones=["warm", "professional"],
            background_story=(
                "Aria is a thoughtful AI assistant designed to help users "
                "navigate complex topics with patience and clarity. She draws "
                "on broad knowledge while maintaining a warm, approachable "
                "communication style."
            ),
        )
        print(f"Created persona: {persona.id}")
        print(f"  Name:   {persona.name}")
        print(f"  Role:   {persona.role}")
        print(f"  Traits: {persona.traits}")
        print(f"  Tones:  {persona.tones}")

        # ==================================================================
        # STEP 2: CREATE VERSION
        # ==================================================================
        # A version is a snapshot of the persona's trait constraints, growth
        # configuration, and dyadic settings. You can create multiple
        # versions, but only one can be active at a time.
        #
        # - constraints: pin traits to values or ranges with locks
        # - growth: controls how traits evolve (FIXED = no change)
        # - dyadic: controls per-user relationship adaptation
        #
        # All list fields in GrowthConfig and DyadicConfig must be provided
        # explicitly (do not rely on defaults).
        # ==================================================================
        print("\n--- Step 2: Create Version ---")

        version = await client.v1.persona.create_version(
            persona_id=persona.id,
            version="1.0.0",
            constraints=[
                TraitConstraint(
                    trait_ref="empathetic",
                    value=TraitValue(numeric_value=85.0),
                    lock="HARD",
                ),
                TraitConstraint(
                    trait_ref="patience",
                    value=TraitValue(numeric_value=70.0),
                    lock="SOFT",
                    constraint=Constraint(
                        min_bound=50.0,
                        max_bound=90.0,
                        learning_rate=0.1,
                    ),
                ),
            ],
            growth=GrowthConfig(
                type="FIXED",
                domain_rates=None,
                triggers=[],
                goal_states=[],
                boundaries=[],
            ),
            dyadic=DyadicConfig(
                enabled=False,
                max_relationships=0,
                learnable_traits=[],
                initial_weight=0.0,
                max_weight=0.0,
                confidence_threshold=0,
            ),
        )
        print(f"Created version: {version.version} (ID: {version.id})")
        print(f"  Is active:   {version.is_active}")
        print(f"  Constraints: {len(version.constraints)} constraint(s)")
        for c in version.constraints:
            val = c.value.numeric_value if c.value else None
            print(f"    - {c.trait_ref}: {val} (lock={c.lock})")

        # ==================================================================
        # STEP 3: SET ACTIVE VERSION
        # ==================================================================
        # Activate the version so the prepare endpoint knows which trait
        # configuration to resolve. Pass the version's ID (not the label).
        #
        # Returns the updated Persona object with active_version set.
        # ==================================================================
        print("\n--- Step 3: Set Active Version ---")

        updated_persona = await client.v1.persona.set_active_version(
            persona.id, version.id
        )
        print(f"Active version set: {updated_persona.active_version}")

        # ==================================================================
        # STEP 4: PREPARE THE SYSTEM PROMPT
        # ==================================================================
        # Now that an active version exists, the prepare endpoint resolves
        # the persona's traits, active version constraints, and optional
        # user context into a system prompt string.
        #
        # Without an active version, prepare will fail.
        #
        # Global mode (no user_id):
        #   Returns a prompt based on the persona + active version only.
        #
        # Per-user mode (with user_id):
        #   Incorporates dyadic/relationship-specific context if dyadic
        #   is enabled on the active version.
        # ==================================================================
        print("\n--- Step 4: Prepare System Prompt ---")

        # 4a. Global mode — no user context
        print("\n4a. Preparing (global mode)...")
        result = await client.v1.persona.prepare(persona.id)
        print(f"System prompt ({len(result.system_prompt)} chars):")
        print("-" * 40)
        print(result.system_prompt)
        print("-" * 40)

        # 4b. Per-user mode — with user context
        print("\n4b. Preparing (per-user mode, user_id='user-demo-001')...")
        user_result = await client.v1.persona.prepare(
            persona.id, user_id="user-demo-001"
        )
        print(f"Per-user system prompt ({len(user_result.system_prompt)} chars):")
        print("-" * 40)
        print(user_result.system_prompt)
        print("-" * 40)

        # ==================================================================
        # INTEGRATION PATTERN: PREPARE → CHAT
        # ==================================================================
        # Call prepare before starting or resuming a chat session.
        # Inject the returned system_prompt as the system message:
        #
        #   prep = await client.v1.persona.prepare(
        #       persona_id, user_id=current_user_id
        #   )
        #   await client.v1.chat.send(
        #       magickspace_id=magickspace_id,
        #       message="Hello, can you help me?",
        #       system_prompt=prep.system_prompt,
        #   )
        # ==================================================================

        # ==================================================================
        # ADDITIONAL: VERSION MANAGEMENT
        # ==================================================================
        print("\n--- Additional: Version Management ---")

        # List all versions
        print("\nListing all versions...")
        versions_resp = await client.v1.persona.list_versions(persona.id)
        print(f"Found {len(versions_resp.data)} version(s):")
        for v in versions_resp.data:
            marker = " <-- active" if v.is_active else ""
            print(f"  - {v.version} (ID: {v.id}){marker}")

        # Get the active version directly
        print("\nGetting active version...")
        active = await client.v1.persona.get_active_version(persona.id)
        print(f"Active: {active.version} (ID: {active.id})")

        # ==================================================================
        # CLEANUP
        # ==================================================================
        print("\n--- Cleanup ---")

        await client.v1.persona.delete(persona.id)
        print(f"Deleted persona: {persona.id}")

        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
