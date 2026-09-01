from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_reset import RESET_JOURNAL_NAME, reset_onboarding, run_journaled
from contextcanon.onboarding_workspace import (
    PLACEMENT_REVIEW_NAME,
    STRUCTURE_INSTRUCTION_NAME,
    STRUCTURE_PROPOSAL_NAME,
    open_onboarding_workspace,
    update_workspace_checkpoint,
)
from contextcanon.outputs import write_outputs


ROOT_SOURCE = """# Root — Local Context Source
<!-- ctx:node id="11111111-1111-4111-8111-111111111111" version="0.1.0" -->

## Overview

Root context.
"""

CHILD_SOURCE = """# Child — Local Context Source
<!-- ctx:node id="22222222-2222-4222-8222-222222222222" version="0.1.0-draft" -->

## Overview

Journal-created child.
"""

LEGACY_SKELETON = """# Child — Local Context Source
<!-- ctx:node id="33333333-3333-4333-8333-333333333333" version="0.1.0-draft" -->

## Overview

This Node skeleton reserves the accepted onboarding landing point before detailed project knowledge is distributed.

The later placement pass will add only the Rules, Topics, Sources, or mappings reviewed for this area.
"""


class OnboardingResetTests(unittest.TestCase):
    def make_repo(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text("# Project\n", encoding="utf-8")
        (repo / "CONTEXT.src.md").write_text(ROOT_SOURCE, encoding="utf-8")
        write_outputs(Compiler(repo).compile(repo))
        prepared = prepare_onboarding_evidence(repo)
        return repo, prepared

    def test_plan_is_numbered_copy_paste_console_with_explicit_placement_validate(self):
        _, prepared = self.make_repo()
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        update_workspace_checkpoint(
            workspace,
            prepared.snapshot_root,
            stage="placement proposal validated",
            source_catalog_inputs=("/tmp/catalog workflow",),
            next_action="Review the exact next command.",
        )
        plan = workspace.plan_path.read_text(encoding="utf-8")
        self.assertIn("6. Placement validate", plan)
        self.assertIn("contextcanon onboard placement-validate", plan)
        self.assertIn("--catalog-package", plan)
        self.assertIn("/tmp/catalog workflow", plan)
        self.assertIn("contextcanon onboard reset", plan)
        self.assertEqual(STRUCTURE_INSTRUCTION_NAME, "STEP-02a-structure-instruction.md")
        self.assertEqual(STRUCTURE_PROPOSAL_NAME, "STEP-02b-structure-proposal.json")
        self.assertEqual(PLACEMENT_REVIEW_NAME, "STEP-07-placement.md")

    def test_journaled_materialization_reset_restores_only_contextcanon_managed_bytes(self):
        repo, prepared = self.make_repo()

        def fake_materialize(_argv):
            child = repo / "child"
            child.mkdir()
            (child / "CONTEXT.src.md").write_text(CHILD_SOURCE, encoding="utf-8")
            write_outputs(Compiler(repo).compile(child))
            return 0

        result = run_journaled(
            ["onboard", "structure-materialize", str(prepared.snapshot_root)],
            fake_materialize,
        )
        self.assertEqual(result, 0)
        self.assertTrue((prepared.snapshot_root / RESET_JOURNAL_NAME).is_file())
        self.assertTrue((repo / "child" / "CONTEXT.md").is_file())

        reset = reset_onboarding(prepared.snapshot_root, from_step=4)
        self.assertEqual(reset["journal_records_reversed"], 1)
        self.assertFalse((repo / "child" / "CONTEXT.src.md").exists())
        self.assertFalse((repo / "child" / "CONTEXT.md").exists())
        self.assertTrue((repo / "CONTEXT.src.md").is_file())
        self.assertTrue((repo / "README.md").is_file())

    def test_reset_refuses_to_overwrite_managed_file_changed_after_journal(self):
        repo, prepared = self.make_repo()

        def fake_materialize(_argv):
            child = repo / "child"
            child.mkdir()
            (child / "CONTEXT.src.md").write_text(CHILD_SOURCE, encoding="utf-8")
            write_outputs(Compiler(repo).compile(child))
            return 0

        run_journaled(["onboard", "structure-materialize", str(prepared.snapshot_root)], fake_materialize)
        (repo / "child" / "CONTEXT.src.md").write_text(CHILD_SOURCE + "\nHuman edit.\n", encoding="utf-8")
        with self.assertRaisesRegex(Exception, "changed after ContextCanon recorded"):
            reset_onboarding(prepared.snapshot_root, from_step=4)
        self.assertIn("Human edit", (repo / "child" / "CONTEXT.src.md").read_text(encoding="utf-8"))

    def test_pre_journal_untouched_skeleton_can_be_removed_conservatively(self):
        repo, prepared = self.make_repo()
        child = repo / "legacy-child"
        child.mkdir()
        (child / "CONTEXT.src.md").write_text(LEGACY_SKELETON, encoding="utf-8")
        write_outputs(Compiler(repo).compile(child))

        reset = reset_onboarding(prepared.snapshot_root, from_step=4)
        self.assertEqual(reset["journal_records_reversed"], 0)
        self.assertFalse((child / "CONTEXT.src.md").exists())
        self.assertFalse((child / "CONTEXT.md").exists())
        self.assertTrue((repo / "CONTEXT.src.md").exists())


if __name__ == "__main__":
    unittest.main()
