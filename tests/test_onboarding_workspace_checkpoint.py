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

        update_workspace_checkpoint(
            workspace,
            prepared.snapshot_root,
            stage="human placement review",
            structure_digest="1" * 64,
            placement_proposal_digest="2" * 64,
            placement_review_digest="3" * 64,
            placement_review_complete=False,
            source_catalog=("source-id · Workflow · 1.0.0 · " + "4" * 64,),
            next_action="Edit `placement.md`, then run `contextcanon onboard placement-preview ...`.",
        )
        first = workspace.readme_path.read_text(encoding="utf-8")
        self.assertEqual(first.count(CHECKPOINT_START), 1)
        self.assertEqual(first.count(CHECKPOINT_END), 1)
        self.assertIn(prepared.evidence_digest, first)
        self.assertIn("human placement review", first)
        self.assertIn("1" * 64, first)
        self.assertIn("still has pending decisions", first)
        self.assertIn("placement-preview", first)

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
        second = workspace.readme_path.read_text(encoding="utf-8")
        self.assertEqual(second.count(CHECKPOINT_START), 1)
        self.assertNotIn("still has pending decisions", second)
        self.assertIn("placement published", second)
        self.assertIn("6" * 64, second)
        self.assertIn("placement-followup.md", second)


if __name__ == "__main__":
    unittest.main()
