import pytest
import warnings
from tests.contract.schema_registry import (
    RESPONSES,
    REQUESTS,
    SHARED_MODELS,
    SchemaStatus,
)


def get_all_schema_names(spec):
    """Simple extraction of all keys from relevant spec sections."""
    schemas = set(spec.get("components", {}).get("schemas", {}).keys())
    responses = set(spec.get("components", {}).get("responses", {}).keys())
    return schemas | responses


def format_missing_report(missing_schemas: set) -> str:
    """
    Categorizes missing schemas by name pattern to make the report readable.
    """
    requests = []
    responses = []
    models = []

    for name in sorted(missing_schemas):
        lower = name.lower()
        if name.endswith("Req") or name.endswith("Request") or "request" in lower:
            requests.append(name)
        elif (
            name.endswith("Resp")
            or name.endswith("Response")
            or name.endswith("Res")
            or "response" in lower
        ):
            responses.append(name)
        else:
            models.append(name)

    report = ["\n\n🔎  UNTRACKED SCHEMAS REPORT"]
    report.append("==================================================")

    if requests:
        report.append(f"\n📨  Likely REQUESTS ({len(requests)}):")
        report.append("    (Add to registry.py -> REQUESTS)")
        for r in requests:
            report.append(f"    ❌ {r}")

    if responses:
        report.append(f"\n📦  Likely RESPONSES ({len(responses)}):")
        report.append("    (Add to registry.py -> RESPONSES)")
        for r in responses:
            report.append(f"    ❌ {r}")

    if models:
        report.append(f"\n🧩  Shared MODELS / COMPONENTS ({len(models)}):")
        report.append(
            "    (Usually internal parts of other schemas. Mark SKIPPED if generic.)"
        )
        for m in models:
            report.append(f"    ❓ {m}")

    report.append("\n==================================================")
    report.append("👉 Action: Copy these names into tests/contract/registry.py")

    return "\n".join(report)


@pytest.mark.contract
def test_schema_coverage(contract):
    """
    Ensures every schema in the spec is accounted for in registry.py.
    Reports on what's TESTED, SKIPPED (and why), and UNTRACKED.
    """
    spec_schemas = get_all_schema_names(contract)

    # What we know about
    all_defs = RESPONSES + REQUESTS + SHARED_MODELS
    known_responses = {r.schema_name for r in RESPONSES}
    known_requests = {r.schema_name for r in REQUESTS}
    known_shared = {r.schema_name for r in SHARED_MODELS}
    all_known = known_responses | known_requests | known_shared

    # Identify Missing
    missing = spec_schemas - all_known

    # Identify Stats
    tested_count = len(
        [r for r in RESPONSES + REQUESTS if r.status == SchemaStatus.TESTED]
    )
    skipped_count = len(
        [
            r
            for r in RESPONSES + REQUESTS + SHARED_MODELS
            if r.status == SchemaStatus.SKIPPED
        ]
    )

    print(
        f"\n📊 COVERAGE STATS: Tested={tested_count}, Skipped={skipped_count}, Untracked={len(missing)}"
    )

    # Report on UNTRACKED schemas
    if missing:
        report = format_missing_report(missing)
        warnings.warn(report, UserWarning, stacklevel=2)

    # Report on SKIPPED schemas (Why are we skipping things?)
    skipped = [r for r in all_defs if r.status == SchemaStatus.SKIPPED]

    if skipped:
        from collections import defaultdict

        by_reason = defaultdict(list)
        for r in skipped:
            by_reason[r.reason].append(r.schema_name)

        print("\n📉 SKIPPED SCHEMA REPORT (Why we aren't testing these)")
        print("==================================================")

        for reason, names in sorted(by_reason.items()):
            count = len(names)
            print(f"\n🏷️  {reason} ({count}):")

            # Special: If reason is "Missing Model", print ALL of them (This is your Todo list!)
            if "Missing Model" in reason:
                for name in sorted(names):
                    print(f"    🔴 [TODO] {name}")
            else:
                # For other reasons, just show count (they're intentionally skipped)
                print(f"    ✓ Intentionally skipped")

        print("\n==================================================")
        print(
            f"💡 TIP: {len(by_reason.get('Missing Model', []))} schemas need SDK models"
        )
