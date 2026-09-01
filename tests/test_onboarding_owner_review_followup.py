from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_placement_instruction import build_onboarding_placement_instruction
from contextcanon.onboarding_structure import STRUCTURE_PROPOSAL_SCHEMA, create_or_load_structure_markdown
from contextcanon.onboarding_structure_instruction import build_onboarding_structure_instruction
from contextcanon.onboarding_structure_materialize import (
    materialize_structure_skeletons,
    preview_structure_materialization,
)
from contextcanon.onboarding_workspace import open_onboarding_workspace, update_workspace_checkpoint


ROOT_ID = "11111111-2222-4333-8444-555555555555"


class OnboardingOwnerReviewFollowupTests(unittest.TestCase):
    def make_project(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text(
            "# Knowledge Project\n"
            "Operations, architecture, and user guidance currently live together as documents.\n",
            encoding="utf-8",
        )
        (repo / "CONTEXT.src.md").write_text(
            "# Knowledge Project — Local Context Source\n"
            f'<!-- ctx:node id="{ROOT_ID}" version="0.1.0" -->\n\n'
            "## Overview\n\nExisting accepted root.\n",
            encoding="utf-8",
        )
        prepared = prepare_onboarding_evidence(repo)
        entry = next(item for item in prepared.included if item.path == "README.md")
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        proposal = {
            "schema": STRUCTURE_PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "nodes": [
                {
                    "key": "N-001",
                    "name": "Knowledge Project",
                    "parent_key": None,
                    "suggested_path": ".",
                    "lifecycle": "current",
                    "purpose": "Orient work on the project.",
                    "rationale": "The evidence describes one project containing several knowledge areas.",
                    "confidence": "high",
                    "evidence": [
                        {
                            "path": "README.md",
                            "sha256": entry.sha256,
                            "start_line": 1,
                            "end_line": 2,
                        }
                    ],
                }
            ],
            "knowledge_bodies": [],
            "source_reuses": [],
        }
        workspace.structure_proposal_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
        create_or_load_structure_markdown(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        return repo, prepared, workspace

    def test_structure_instruction_says_semantic_nodes_may_use_new_directories(self):
        _, prepared, _ = self.make_project()
        instruction = build_onboarding_structure_instruction(prepared.snapshot_root)

        self.assertIn("not the taxonomy you must preserve", instruction.text)
        self.assertIn("a new repository-relative directory that does not exist yet", instruction.text)
        self.assertIn("document-heavy repositories", instruction.text)
        self.assertIn("does not have to exist yet", instruction.text)

    def test_human_structure_can_create_a_new_semantic_directory(self):
        repo, prepared, workspace = self.make_project()
        text = workspace.structure_path.read_text(encoding="utf-8")
        root_line = "- **Knowledge Project** (`.`) <!-- cc:key=N-001 -->"
        text = text.replace(
            root_line,
            root_line + "\n  - **Operations knowledge** (`knowledge/operations`)",
            1,
        )
        workspace.structure_path.write_text(text, encoding="utf-8")

        preview = preview_structure_materialization(
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
        self.assertIn("concise human orientation plus a link/reference", instruction.text)
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
            prepared.snapshot_root,
            stage="human placement review",
            next_action="Edit `placement.md`, then preview.",
            source_catalog_inputs=("C:/contextcanon/development-workflow",),
            owner_source_specs=("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40",),
        )
        checkpoint = workspace.plan_path.read_text(encoding="utf-8")
        self.assertIn("Reuse these exact `--catalog-package` inputs", checkpoint)
        self.assertIn("C:/contextcanon/development-workflow", checkpoint)
        self.assertIn("do not repeat on preview/publish", checkpoint)
        self.assertIn("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40", checkpoint)


if __name__ == "__main__":
    unittest.main()
