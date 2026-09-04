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


rel = "tests/test_onboarding_reset.py"

patch(
    rel,
    '''        self.assertIn("6. Placement validate", plan)\n        self.assertIn("contextcanon onboard placement-validate", plan)\n        self.assertIn("--catalog-package", plan)\n        self.assertIn("/tmp/catalog workflow", plan)\n        self.assertIn("contextcanon onboard reset", plan)\n        self.assertIn("Exact commands:** the checklist is the overview", plan)\n        self.assertIn("Set this run variable once in your terminal", plan)\n        self.assertIn("$SNAPSHOT", plan)\n        self.assertEqual(STRUCTURE_INSTRUCTION_NAME, "STEP-02a-structure-instruction.md")\n        self.assertEqual(STRUCTURE_PROPOSAL_NAME, "STEP-02b-structure-proposal.json")\n        self.assertEqual(PLACEMENT_REVIEW_NAME, "STEP-07-placement.md")\n        self.assertEqual(PLACEMENT_AUDIT_NAME, "STEP-07a-source-audit.md")\n        self.assertIn(PLACEMENT_AUDIT_NAME, plan)\n''',
    '''        self.assertIn("STEP 05 — Reusable Contexts", plan)\n        self.assertIn("STEP 07 — Placement validate", plan)\n        self.assertIn("contextcanon onboard placement-validate", plan)\n        self.assertNotIn("--catalog-package", plan)\n        self.assertNotIn("/tmp/catalog workflow", plan)\n        self.assertIn("contextcanon onboard reset", plan)\n        self.assertIn("Each step keeps its explanation, completion checkbox, exact command", plan)\n        self.assertIn("Set this run variable once in your terminal", plan)\n        self.assertIn("$SNAPSHOT", plan)\n        self.assertEqual(STRUCTURE_INSTRUCTION_NAME, "STEP-02a-structure-instruction.md")\n        self.assertEqual(STRUCTURE_PROPOSAL_NAME, "STEP-02b-structure-proposal.json")\n        self.assertEqual(PLACEMENT_REVIEW_NAME, "STEP-08-placement.md")\n        self.assertEqual(PLACEMENT_AUDIT_NAME, "STEP-08a-source-audit.md")\n        self.assertIn(PLACEMENT_AUDIT_NAME, plan)\n''',
)

patch(rel, "def test_reset_from_step7_removes_generated_source_audit(self):", "def test_reset_from_step8_removes_generated_source_audit(self):")
patch(rel, "reset = reset_onboarding(prepared.snapshot_root, from_step=7)", "reset = reset_onboarding(prepared.snapshot_root, from_step=8)")

patch(rel, '        self.assertIn("restart at numbered step 2", plan)\n', '        self.assertIn("Restart at numbered step 2", plan)\n')

patch(
    rel,
    '''            (["onboard", "placement-instruction", "--help"], ("STEP-02b-structure-proposal.json", "STEP-03-structure.md", "STEP-05a-placement-instruction.md")),\n            (["onboard", "placement-review", "--help"], ("STEP-05b-placement-proposal.json", "STEP-07-placement.md")),\n''',
    '''            (["onboard", "placement-instruction", "--help"], ("STEP-02b-structure-proposal.json", "STEP-03-structure.md", "STEP-06a-placement-instruction.md")),\n            (["onboard", "placement-review", "--help"], ("STEP-06b-placement-proposal.json", "STEP-08-placement.md")),\n''',
)

# Stale-plan recovery should prove that the current integrated runbook replaces
# old/split wording rather than preserving old numbering.
start = '''        stale = workspace.plan_path.read_text(encoding="utf-8")\n        stale = stale.replace(\n            "- [ ] 6. Placement validate — validate the LLM proposal against the frozen Evidence, accepted structure, and exact Source catalog.\\n",\n            "",\n        )\n        stale = stale.replace("7. Placement review", "6. Placement review")\n        stale = stale.replace("8. Publication preview", "7. Publication preview")\n        stale = stale.replace("9. Publish placement", "8. Publish placement")\n        stale = stale.replace("STEP-07-placement.md", "placement.md")\n        workspace.plan_path.write_text(stale, encoding="utf-8")\n\n        reset_onboarding(prepared.snapshot_root, from_step=5)\n        refreshed = workspace.plan_path.read_text(encoding="utf-8")\n        self.assertIn("6. Placement validate", refreshed)\n        self.assertIn("7. Placement review", refreshed)\n        self.assertIn("STEP-07-placement.md", refreshed)\n        self.assertIn("contextcanon onboard reset", refreshed)\n'''
replacement = '''        stale = workspace.plan_path.read_text(encoding="utf-8")\n        stale = stale.replace("### STEP 07 — Placement validate", "### OLD STEP — Placement validate")\n        stale = stale.replace("STEP-08-placement.md", "placement.md")\n        workspace.plan_path.write_text(stale, encoding="utf-8")\n\n        reset_onboarding(prepared.snapshot_root, from_step=5)\n        refreshed = workspace.plan_path.read_text(encoding="utf-8")\n        self.assertIn("STEP 05 — Reusable Contexts", refreshed)\n        self.assertIn("STEP 07 — Placement validate", refreshed)\n        self.assertIn("STEP 08 — Placement review", refreshed)\n        self.assertIn("STEP-08-placement.md", refreshed)\n        self.assertIn("contextcanon onboard reset", refreshed)\n'''
patch(rel, start, replacement)

patch(
    rel,
    '''        plan = reopened.plan_path.read_text(encoding="utf-8")\n        self.assertIn("C:/catalog/development-workflow", plan)\n        self.assertIn("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40", plan)\n''',
    '''        plan = reopened.plan_path.read_text(encoding="utf-8")\n        # Machine compatibility state survives, but the orchestration PLAN must\n        # not leak domain configuration or opaque Source IDs back to the human.\n        state = (prepared.snapshot_root / "run-inputs.json").read_text(encoding="utf-8")\n        self.assertIn("C:/catalog/development-workflow", state)\n        self.assertIn("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40", state)\n        self.assertNotIn("C:/catalog/development-workflow", plan)\n        self.assertNotIn("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40", plan)\n        self.assertIn("STEP 05 — Reusable Contexts", plan)\n''',
)

patch(rel, 'review = root / "STEP-07-placement.md"', 'review = root / "STEP-08-placement.md"')
patch(rel, "def test_step9_journal_restores_reviewed_source_document(self):", "def test_step10_journal_restores_reviewed_source_document(self):")
patch(rel, "reset_onboarding(prepared.snapshot_root, from_step=9)", "reset_onboarding(prepared.snapshot_root, from_step=10)")
