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


patch(
    "tests/test_onboarding_owner_review_followup.py",
    '''    def test_workspace_readme_orients_and_plan_tracks_steps_and_source_inputs(self):\n        _, prepared, workspace = self.make_project()\n        readme = workspace.readme_path.read_text(encoding="utf-8")\n        plan = workspace.plan_path.read_text(encoding="utf-8")\n\n        self.assertIn("stable orientation page", readme)\n        self.assertIn("PLAN.md", readme)\n        self.assertNotIn("## Checklist", readme)\n        self.assertIn("## Checklist", plan)\n        self.assertIn("- [ ] 1. Freeze Evidence", plan)\n        self.assertIn("- [ ] 8. Publication preview", plan)\n        self.assertIn("- [ ] 9. Publish placement", plan)\n        self.assertIn("LLM handoff 1", plan)\n        self.assertIn("LLM handoff 2", plan)\n        self.assertIn("Human gate 1", plan)\n        self.assertIn("Human gate 2", plan)\n        self.assertIn("directories that did not exist", readme)\n\n        update_workspace_checkpoint(\n            workspace,\n            prepared.snapshot_root,\n            stage="human placement review",\n            next_action="Edit `placement.md`, then preview.",\n            source_catalog_inputs=("C:/contextcanon/development-workflow",),\n            owner_source_specs=("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40",),\n        )\n        checkpoint = workspace.plan_path.read_text(encoding="utf-8")\n        self.assertIn("Reuse these exact `--catalog-package` inputs", checkpoint)\n        self.assertIn("C:/contextcanon/development-workflow", checkpoint)\n        self.assertIn("do not repeat on preview/publish", checkpoint)\n        self.assertIn("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40", checkpoint)\n''',
    '''    def test_workspace_readme_orients_and_plan_keeps_domain_inputs_out_of_orchestration(self):\n        _, prepared, workspace = self.make_project()\n        readme = workspace.readme_path.read_text(encoding="utf-8")\n        plan = workspace.plan_path.read_text(encoding="utf-8")\n\n        self.assertIn("stable orientation page", readme)\n        self.assertIn("PLAN.md", readme)\n        self.assertNotIn("## Checklist", readme)\n        self.assertNotIn("## Checklist", plan)\n        self.assertIn("## Onboarding steps", plan)\n        # A freshly opened workspace has no snapshot-bound checkpoint yet, so\n        # the integrated STEP chapters are inserted only when ContextCanon first\n        # records run state. The stable human-gate summary already names STEP 05.\n        self.assertIn("STEP-05-reusable-contexts.md", plan)\n        self.assertIn("LLM handoff 1", plan)\n        self.assertIn("LLM handoff 2", plan)\n        self.assertIn("Human gate 1", plan)\n        self.assertIn("Human gate 2", plan)\n        self.assertIn("Reusable Context gate", plan)\n        self.assertIn("directories that did not exist", readme)\n\n        update_workspace_checkpoint(\n            workspace,\n            prepared.snapshot_root,\n            stage="human placement review",\n            next_action="Edit `STEP-08-placement.md`, then preview.",\n            source_catalog_inputs=("C:/contextcanon/development-workflow",),\n            owner_source_specs=("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40",),\n        )\n        checkpoint = workspace.plan_path.read_text(encoding="utf-8")\n        self.assertIn("### STEP 05 — Reusable Contexts", checkpoint)\n        self.assertIn("### STEP 09 — Publication preview", checkpoint)\n        self.assertIn("### STEP 10 — Publish placement", checkpoint)\n        # The machine cache may remember legacy inputs, but the PLAN is pure\n        # orchestration and must not become a second configuration surface.\n        self.assertNotIn("--catalog-package", checkpoint)\n        self.assertNotIn("C:/contextcanon/development-workflow", checkpoint)\n        self.assertNotIn("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40", checkpoint)\n        self.assertIn("STEP-08-placement.md", checkpoint)\n''',
)

patch(
    "tests/test_onboarding_workspace_checkpoint.py",
    '''        self.assertIn("C:/catalog/workflow", first)\n        self.assertIn("placement-preview", first)\n        self.assertIn("- [x] 5. Placement proposal", first)\n        self.assertIn("- [x] 6. Placement validate", first)\n        self.assertIn("- [ ] 7. Placement review", first)\n''',
    '''        self.assertNotIn("C:/catalog/workflow", first)\n        self.assertIn("placement-preview", first)\n        self.assertIn("### STEP 05 — Reusable Contexts", first)\n        self.assertIn("### STEP 07 — Placement validate", first)\n        self.assertIn("### STEP 08 — Placement review", first)\n        self.assertIn("### STEP 05 — Reusable Contexts\\n- [x] **Done**", first)\n        self.assertIn("### STEP 07 — Placement validate\\n- [x] **Done**", first)\n        self.assertIn("### STEP 08 — Placement review\\n- [ ] **Done**", first)\n''',
)
patch(
    "tests/test_onboarding_workspace_checkpoint.py",
    '''        self.assertIn("- [x] 9. Publish placement", second)\n''',
    '''        self.assertIn("### STEP 10 — Publish placement\\n- [x] **Done**", second)\n''',
)
