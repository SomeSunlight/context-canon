from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(rel: str, old: str, new: str, *, count: int = 1) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"{rel}: expected {count} occurrence(s), found {actual}: {old[:120]!r}")
    path.write_text(text.replace(old, new, count), encoding="utf-8", newline="\n")


# Keep Markdown examples syntactically clear: label and value are separate code spans.
patch(
    "src/contextcanon/onboarding_reusable_contexts.py",
    "Set `Decision: `accept`` when the Catalog and assignments are the intended reusable-context composition for this onboarding.",
    "Set `Decision` to `accept` when the Catalog and assignments are the intended reusable-context composition for this onboarding.",
)
patch(
    "src/contextcanon/onboarding_workspace.py",
    "set `Decision: `accept`` when correct",
    "set `Decision` to `accept` when correct",
)
patch(
    "docs/onboarding.md",
    "Set `Decision: `accept`` only when the Catalog and sparse relationships are what you intend.",
    "Set `Decision` to `accept` only when the Catalog and sparse relationships are what you intend.",
)

# Normal structure discovery no longer asks the human for a reusable Source
# catalog; Source discovery/selection has one dedicated concern in STEP 05.
patch(
    "docs/onboarding.md",
    "- exact reusable Source matches only when a verified Source catalog was supplied;\n",
    "",
)

# The permanent walkthrough assertion should match prose semantically rather
# than depend on sentence-initial capitalization that is not part of the contract.
patch(
    "tests/test_onboarding_walkthrough_current.py",
    'self.assertIn("Why this whole reusable Context", text)',
    'self.assertIn("why this whole reusable Context", text)',
)
