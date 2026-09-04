from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_workspace import (
    CHECKPOINT_END,
    CHECKPOINT_START,
    PLAN_MARKER,
    open_onboarding_workspace,
    update_workspace_checkpoint,
)


class WorkspaceCheckpointTests(unittest.TestCase):
    def test_checkpoint_is_framework_owned_replaced_not_duplicated_and_resume_ready(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text("# Project\n", encoding="utf-8")
        prepared = prepare_onboarding_evidence(repo)
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)

        readme = workspace.readme_path.read_text(encoding="utf-8")
        self.assertIn("stable orientation page", readme)
        self.assertNotIn(CHECKPOINT_START, readme)

        update_workspace_checkpoint(
            workspace,
            prepared.snapshot_root,
            stage="human placement review",
            structure_digest="1" * 64,
            placement_proposal_digest="2" * 64,
            placement_review_digest="3" * 64,
            placement_review_complete=False,
            source_catalog=("source-id · Workflow · 1.0.0 · " + "4" * 64,),
            source_catalog_inputs=("C:/catalog/workflow",),
            next_action="Edit `placement.md`, then run `contextcanon onboard placement-preview ...`.",
        )
        first = workspace.plan_path.read_text(encoding="utf-8")
        self.assertIn(PLAN_MARKER, first)
        self.assertEqual(first.count(CHECKPOINT_START), 1)
        self.assertEqual(first.count(CHECKPOINT_END), 1)
        self.assertIn(prepared.evidence_digest, first)
        self.assertIn("human placement review", first)
        self.assertIn("1" * 64, first)
        self.assertIn("still has pending decisions", first)
        self.assertNotIn("C:/catalog/workflow", first)
        self.assertIn("placement-preview", first)
        self.assertIn("### STEP 05 — Reusable Contexts", first)
        self.assertIn("### STEP 07 — Placement validate", first)
        self.assertIn("### STEP 08 — Placement review", first)
        self.assertIn("### STEP 05 — Reusable Contexts\n- [x] **Done**", first)
        self.assertIn("### STEP 07 — Placement validate\n- [x] **Done**", first)
        self.assertIn("### STEP 08 — Placement review\n- [ ] **Done**", first)

        update_workspace_checkpoint(
            workspace,
            prepared.snapshot_root,
            stage="placement published",
            structure_digest="1" * 64,
            placement_proposal_digest="2" * 64,
            placement_review_digest="5" * 64,
            placement_review_complete=True,
            acceptance_digest="6" * 64,
            next_action="Review `placement-followup.md`.",
        )
        second = workspace.plan_path.read_text(encoding="utf-8")
        self.assertEqual(second.count(CHECKPOINT_START), 1)
        self.assertNotIn("still has pending decisions", second)
        self.assertIn("placement published", second)
        self.assertIn("6" * 64, second)
        self.assertIn("placement-followup.md", second)
        self.assertIn("### STEP 10 — Publish placement\n- [x] **Done**", second)

    def test_existing_owned_workspace_gains_plan_without_recreating_human_review_files(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text("# Project\n", encoding="utf-8")
        prepared = prepare_onboarding_evidence(repo)
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        workspace.plan_path.unlink()
        workspace.placement_path.write_text("human review stays\n", encoding="utf-8")

        reopened = open_onboarding_workspace(prepared.snapshot_root, create=False)
        self.assertTrue(reopened.plan_path.is_file())
        self.assertIn(PLAN_MARKER, reopened.plan_path.read_text(encoding="utf-8"))
        self.assertEqual(reopened.placement_path.read_text(encoding="utf-8"), "human review stays\n")


if __name__ == "__main__":
    unittest.main()
