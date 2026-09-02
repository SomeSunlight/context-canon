from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_placement_instruction import build_onboarding_placement_instruction
from contextcanon.onboarding_structure import (
    STRUCTURE_PROPOSAL_SCHEMA,
    create_or_load_structure_markdown,
    load_onboarding_structure_proposal,
)
from contextcanon.onboarding_structure_materialize import materialize_structure_skeletons, preview_structure_materialization
from contextcanon.onboarding_workspace import open_onboarding_workspace, update_workspace_checkpoint
from contextcanon.outputs import write_outputs


class OnboardingOwnerReviewFollowupTests(unittest.TestCase):
    def make_project(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text(
            "# Knowledge Project\n"
            "Operational notes, architecture and policies currently share the docs directory.\n",
            encoding="utf-8",
        )
        prepared = prepare_onboarding_evidence(repo)
        readme = next(item for item in prepared.included if item.path == "README.md")
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        raw = {
            "schema": STRUCTURE_PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "nodes": [
                {
                    "key": "N-001",
                    "name": "Knowledge Project",
                    "parent_key": None,
                    "suggested_path": ".",
                    "lifecycle": "current",
                    "purpose": "Project root.",
                    "rationale": "One root.",
                    "confidence": "high",
                    "evidence": [
                        {"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 2}
                    ],
                }
            ],
            "knowledge_bodies": [],
            "source_reuses": [],
        }
        workspace.structure_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        create_or_load_structure_markdown(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        return repo, prepared, workspace

    def test_structure_instruction_says_semantic_nodes_may_use_new_directories(self):
        _, prepared, workspace = self.make_project()
        from contextcanon.onboarding_structure_instruction import build_onboarding_structure_instruction

        instruction = build_onboarding_structure_instruction(prepared.snapshot_root)
        self.assertIn("new repository-relative directory", instruction.text)
        self.assertIn("does not exist yet", instruction.text)
        self.assertIn("do not preserve the repository directory tree", instruction.text.lower())

    def test_human_structure_can_create_a_new_semantic_directory(self):
        repo, prepared, workspace = self.make_project()
        structure_text = workspace.structure_path.read_text(encoding="utf-8")
        structure_text = structure_text.replace(
            "- **Knowledge Project** (`.`)",
            "- **Knowledge Project** (`.`)\n  - **Operations Knowledge** (`knowledge/operations`)",
            1,
        )
        workspace.structure_path.write_text(structure_text, encoding="utf-8")

        preview = preview_structure_materialization(
            repo,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        item = next(item for item in preview.items if item.path == "knowledge/operations")
        self.assertEqual(item.status, "create")
        self.assertFalse(item.directory_exists)

        created = materialize_structure_skeletons(preview)
        self.assertIn(repo / "knowledge" / "operations" / "CONTEXT.src.md", created)
        self.assertTrue((repo / "knowledge" / "operations" / "CONTEXT.md").is_file())

    def test_promote_instruction_requires_one_canonical_maintenance_surface(self):
        _, prepared, workspace = self.make_project()
        instruction = build_onboarding_placement_instruction(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )

        self.assertIn("one canonical maintenance surface", instruction.text)
        self.assertIn("single canonical maintenance surface for that meaning", instruction.text)
        self.assertIn("temporary duplicate may exist during migration", instruction.text)
        self.assertIn("real plain-language summary", instruction.text)
        self.assertIn("A reader should learn the gist without following the link", instruction.text)
        self.assertIn("Do not plan to maintain the same full rule or explanation in both places", instruction.text)

    def test_workspace_readme_orients_and_plan_tracks_steps_and_source_inputs(self):
        _, prepared, workspace = self.make_project()
        readme = workspace.readme_path.read_text(encoding="utf-8")
        plan = workspace.plan_path.read_text(encoding="utf-8")

        self.assertIn("stable orientation page", readme)
        self.assertIn("PLAN.md", readme)
        self.assertNotIn("## Checklist", readme)
        self.assertIn("## Checklist", plan)
        self.assertIn("- [ ] 1. Freeze Evidence", plan)
        self.assertIn("- [ ] 8. Publication preview", plan)
        self.assertIn("- [ ] 9. Publish placement", plan)
        self.assertIn("LLM handoff 1", plan)
        self.assertIn("LLM handoff 2", plan)
        self.assertIn("Human gate 1", plan)
        self.assertIn("Human gate 2", plan)
        self.assertIn("directories that did not exist", readme)

        update_workspace_checkpoint(
            workspace,
            checkpoint="structure-reviewed",
            next_command="contextcanon onboard structure-preview SNAPSHOT",
            catalog_package_roots=[Path("/tmp/catalog-a"), Path("/tmp/catalog-b")],
        )
        plan = workspace.plan_path.read_text(encoding="utf-8")
        self.assertIn("/tmp/catalog-a", plan)
        self.assertIn("/tmp/catalog-b", plan)
        self.assertIn("structure-preview", plan)


if __name__ == "__main__":
    unittest.main()
