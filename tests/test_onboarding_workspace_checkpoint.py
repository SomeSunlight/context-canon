from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
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
    write_utf8,
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
        self.assertIn("### STEP 07 — Reusable Contexts", first)
        self.assertIn("### STEP 09 — Placement validate", first)
        self.assertIn("### STEP 10 — Placement review", first)
        self.assertIn("### STEP 07 — Reusable Contexts\n- [x] **Done**", first)
        self.assertIn("### STEP 09 — Placement validate\n- [x] **Done**", first)
        self.assertIn("### STEP 10 — Placement review\n- [ ] **Done**", first)

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
        self.assertIn("### STEP 12 — Publish placement\n- [x] **Done**", second)

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


    def test_write_utf8_retries_transient_windows_style_replace_lock(self):
        root = Path(tempfile.mkdtemp())
        path = root / "run-inputs.json"
        path.write_text("before\n", encoding="utf-8")
        real_replace = os.replace
        attempts = 0

        def flaky_replace(source, destination):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise PermissionError(5, "simulated transient Windows lock")
            return real_replace(source, destination)

        with mock.patch("contextcanon.onboarding_workspace.os.replace", side_effect=flaky_replace), mock.patch(
            "contextcanon.onboarding_workspace.time.sleep"
        ):
            write_utf8(path, "after\n")

        self.assertEqual(attempts, 3)
        self.assertEqual(path.read_text(encoding="utf-8"), "after\n")
        self.assertEqual([item for item in root.iterdir() if item.name.startswith(".run-inputs.json.")], [])

    def test_write_utf8_reports_exhausted_replace_lock_and_cleans_temp(self):
        from contextcanon.parser import ContextCanonError

        root = Path(tempfile.mkdtemp())
        path = root / "run-inputs.json"
        path.write_text("before\n", encoding="utf-8")

        with mock.patch(
            "contextcanon.onboarding_workspace.os.replace",
            side_effect=PermissionError(5, "simulated persistent Windows lock"),
        ), mock.patch("contextcanon.onboarding_workspace.time.sleep"):
            with self.assertRaisesRegex(ContextCanonError, "after retrying a temporary filesystem lock"):
                write_utf8(path, "after\n")

        self.assertEqual(path.read_text(encoding="utf-8"), "before\n")
        self.assertEqual([item for item in root.iterdir() if item.name.startswith(".run-inputs.json.")], [])


if __name__ == "__main__":
    unittest.main()
