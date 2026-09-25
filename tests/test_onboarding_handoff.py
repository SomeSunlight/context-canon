from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_handoff import (
    HANDOFF_CONTROL_DIR,
    HANDOFF_INSTRUCTION_NAME,
    HANDOFF_MANIFEST_NAME,
    HANDOFF_PLAN_NAME,
    HANDOFF_RESULT_NAME,
    build_semantic_handoff,
    import_semantic_handoff_result,
)
from contextcanon.onboarding_reset import reset_onboarding
from contextcanon.onboarding_workspace import (
    STRUCTURE_INSTRUCTION_NAME,
    STRUCTURE_PROPOSAL_NAME,
    open_onboarding_workspace,
    write_utf8,
)
from contextcanon.parser import ContextCanonError


class OnboardingHandoffTests(unittest.TestCase):
    def make_run(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text("# Demo\nSemantic onboarding demo.\n", encoding="utf-8")
        (repo / "docs").mkdir()
        (repo / "docs" / "guide.md").write_text("# Guide\nImportant project knowledge.\n", encoding="utf-8")
        (repo / "data").mkdir()
        (repo / "data" / "table.csv").write_text("name,value\nalpha,1\nbeta,2\n", encoding="utf-8")
        prepared = prepare_onboarding_evidence(
            repo,
            explicit_paths=["docs/guide.md", "data/table.csv"],
        )
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        write_utf8(
            workspace.structure_instruction_path,
            "# Structure task\nReturn one JSON object.\n",
        )
        return repo, prepared, workspace

    def test_handoff_materializes_repository_relative_evidence_and_deterministic_zip(self):
        _, prepared, workspace = self.make_run()

        first = build_semantic_handoff(
            prepared.snapshot_root,
            workspace.root,
            step=4,
            instruction_path=workspace.structure_instruction_path,
        )
        first_zip_sha = hashlib.sha256(first.zip_path.read_bytes()).hexdigest()

        self.assertTrue((first.root / "docs" / "guide.md").is_file())
        self.assertTrue((first.root / "data" / "table.csv").is_file())
        self.assertFalse((first.root / "evidence").exists())
        self.assertTrue((first.root / HANDOFF_CONTROL_DIR / HANDOFF_PLAN_NAME).is_file())
        self.assertEqual(
            (first.root / HANDOFF_CONTROL_DIR / HANDOFF_INSTRUCTION_NAME).read_bytes(),
            workspace.structure_instruction_path.read_bytes(),
        )

        manifest = json.loads((first.root / HANDOFF_CONTROL_DIR / HANDOFF_MANIFEST_NAME).read_text(encoding="utf-8"))
        self.assertEqual(manifest["step"], 4)
        self.assertEqual(manifest["evidence_digest"], prepared.evidence_digest)
        self.assertEqual(manifest["canonical_result_name"], STRUCTURE_PROPOSAL_NAME)

        with zipfile.ZipFile(first.zip_path) as archive:
            names = archive.namelist()
        self.assertIn("STEP-04-structure/docs/guide.md", names)
        self.assertIn("STEP-04-structure/data/table.csv", names)
        self.assertIn(
            f"STEP-04-structure/{HANDOFF_CONTROL_DIR}/{HANDOFF_PLAN_NAME}",
            names,
        )
        self.assertNotIn(
            f"STEP-04-structure/{HANDOFF_CONTROL_DIR}/{HANDOFF_RESULT_NAME}",
            names,
        )

        second = build_semantic_handoff(prepared.snapshot_root, workspace.root, step=4)
        second_zip_sha = hashlib.sha256(second.zip_path.read_bytes()).hexdigest()
        self.assertFalse(second.created)
        self.assertEqual(first.handoff_digest, second.handoff_digest)
        self.assertEqual(first_zip_sha, second_zip_sha)

    def test_same_handoff_preserves_result_but_changed_inputs_require_explicit_refresh(self):
        _, prepared, workspace = self.make_run()
        handoff = build_semantic_handoff(prepared.snapshot_root, workspace.root, step=4)
        handoff.result_path.write_text('{"schema":"old"}\n', encoding="utf-8")

        repeated = build_semantic_handoff(prepared.snapshot_root, workspace.root, step=4)
        self.assertEqual(repeated.result_path.read_text(encoding="utf-8"), '{"schema":"old"}\n')

        write_utf8(workspace.structure_instruction_path, "# Changed structure task\nReturn JSON.\n")
        with self.assertRaisesRegex(ContextCanonError, "inputs changed but RESULT.json already exists"):
            build_semantic_handoff(prepared.snapshot_root, workspace.root, step=4)

        refreshed = build_semantic_handoff(
            prepared.snapshot_root,
            workspace.root,
            step=4,
            refresh=True,
        )
        self.assertTrue(refreshed.created)
        self.assertFalse(refreshed.result_path.exists())

    def test_import_is_mechanical_and_writes_canonical_proposal_without_validation(self):
        _, prepared, workspace = self.make_run()
        handoff = build_semantic_handoff(prepared.snapshot_root, workspace.root, step=4)
        external = Path(tempfile.mkdtemp()) / "answer.json"
        external.write_text('{"z":2,"a":1}\n', encoding="utf-8")

        imported = import_semantic_handoff_result(
            prepared.snapshot_root,
            workspace.root,
            step=4,
            result_path=external,
        )

        expected = '{\n  "a": 1,\n  "z": 2\n}\n'
        self.assertEqual(imported.result_path.read_text(encoding="utf-8"), expected)
        self.assertEqual(workspace.structure_proposal_path.read_text(encoding="utf-8"), expected)
        self.assertEqual(imported.canonical_result_path, workspace.structure_proposal_path)

    def test_reset_from_step4_removes_disposable_handoff_and_zip(self):
        repo, prepared, workspace = self.make_run()
        handoff = build_semantic_handoff(prepared.snapshot_root, workspace.root, step=4)
        self.assertTrue(handoff.root.is_dir())
        self.assertTrue(handoff.zip_path.is_file())

        result = reset_onboarding(repo, from_step=4)

        self.assertFalse(handoff.root.exists())
        self.assertFalse(handoff.zip_path.exists())
        self.assertIn("handoffs/STEP-04-structure/", result["workspace_files_removed"])
        self.assertIn("handoffs/STEP-04-structure.zip", result["workspace_files_removed"])


if __name__ == "__main__":
    unittest.main()
