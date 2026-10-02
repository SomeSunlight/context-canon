from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_handoff import build_semantic_handoff
from contextcanon.onboarding_placement import PLACEMENT_PROPOSAL_SCHEMA, load_onboarding_placement_proposal
from contextcanon.onboarding_placement_instruction import build_onboarding_placement_instruction
from contextcanon.onboarding_placement_publish import build_placement_publication_preview, publish_placement_review
from contextcanon.onboarding_placement_review import create_or_load_placement_review
from contextcanon.onboarding_structure import (
    STRUCTURE_PROPOSAL_SCHEMA,
    create_or_load_structure_markdown,
    load_onboarding_structure_proposal,
    load_structure_markdown,
)
from contextcanon.onboarding_structure_instruction import build_onboarding_structure_instruction
from contextcanon.onboarding_structure_materialize import materialize_structure_skeletons, preview_structure_materialization
from contextcanon.onboarding_workspace import open_onboarding_workspace
from contextcanon.outputs import write_outputs
from contextcanon.parser import parse_node


class OnboardingSubtreeTests(unittest.TestCase):
    def make_repo(self) -> tuple[Path, Path]:
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "doc").mkdir()
        (repo / "doc" / "Grundlagen.md").write_text(
            "# Grundlagen von A\nAlle Entwicklungsprojekte arbeiten im Kontext von A.\n",
            encoding="utf-8",
        )
        (repo / "CONTEXT.src.md").write_text(
            "# Project A — Local Context Source\n"
            '<!-- ctx:node id="node-a" name="Project A" version="1.0.0" -->\n\n'
            "## Local Rules\n\n"
            "### Development\n\n"
            "- **Develop in A context:** Subprojects must preserve A's project-wide constraints.\n"
            "  Why: Their work changes A.\n"
            '  <!-- ctx:rule id="A-001" -->\n\n'
            "## Local Topics\n\n"
            "### Foundations\n\n"
            "When a development project needs the foundations of A:\n\n"
            "Required:\n"
            "- Resource: `doc/Grundlagen.md`\n"
            '  <!-- ctx:resource id="RESOURCE-A-FOUNDATIONS" -->\n\n'
            '<!-- ctx:topic id="A-FOUNDATIONS" -->\n',
            encoding="utf-8",
        )
        write_outputs(Compiler(repo).compile(repo))

        subtree = repo / "B"
        subtree.mkdir()
        (subtree / "README.md").write_text(
            "# Project B\nSmall development project for A.\n",
            encoding="utf-8",
        )
        return repo, subtree

    def prepare_structure(self, repo: Path, subtree: Path):
        prepared = prepare_onboarding_evidence(subtree)
        self.assertEqual([item.path for item in prepared.included], ["README.md"])
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        readme = prepared.included[0]
        raw = {
            "schema": STRUCTURE_PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "nodes": [
                {
                    "key": "N-B",
                    "name": "Project B",
                    "parent_key": None,
                    "suggested_path": ".",
                    "lifecycle": "current",
                    "purpose": "Development work for A.",
                    "rationale": "B is one small coherent project.",
                    "confidence": "high",
                    "evidence": [
                        {
                            "path": "README.md",
                            "sha256": readme.sha256,
                            "start_line": 1,
                            "end_line": 2,
                        }
                    ],
                }
            ],
            "knowledge_bodies": [],
            "source_reuses": [],
        }
        workspace.structure_proposal_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        create_or_load_structure_markdown(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        return prepared, workspace

    def test_subtree_inherits_enclosing_context_and_repository_check_sees_both(self):
        repo, subtree = self.make_repo()
        prepared, workspace = self.prepare_structure(repo, subtree)

        structure_instruction = build_onboarding_structure_instruction(prepared.snapshot_root)
        self.assertIn("Enclosing accepted Context", structure_instruction.text)
        self.assertIn("Project A", structure_instruction.text)
        self.assertIn("A-001", structure_instruction.text)
        self.assertIn("A-FOUNDATIONS", structure_instruction.text)

        materialization = preview_structure_materialization(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        self.assertEqual(materialization.project_root, subtree.resolve())
        self.assertEqual(len(materialize_structure_skeletons(materialization)), 1)

        placement_instruction = build_onboarding_placement_instruction(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        self.assertIsNotNone(placement_instruction.enclosing_parent_package)
        self.assertEqual(placement_instruction.enclosing_parent_package.metadata.id, "node-a")
        self.assertIn("Develop in A context", placement_instruction.text)
        self.assertIn("A-FOUNDATIONS", placement_instruction.text)
        workspace.placement_instruction_path.write_text(placement_instruction.text, encoding="utf-8")
        handoff = build_semantic_handoff(
            prepared.snapshot_root,
            workspace.root,
            step=8,
            instruction_path=workspace.placement_instruction_path,
        )
        inherited_foundations = list(handoff.root.rglob("Grundlagen.md"))
        self.assertEqual(len(inherited_foundations), 1)
        self.assertIn(
            "Alle Entwicklungsprojekte arbeiten im Kontext von A.",
            inherited_foundations[0].read_text(encoding="utf-8"),
        )
        manifest = json.loads(handoff.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["enclosing_parent"]["node_id"], "node-a")
        self.assertEqual(manifest["enclosing_parent"]["package_digest"], placement_instruction.enclosing_parent_package.package_digest)

        structure_proposal = load_onboarding_structure_proposal(
            workspace.structure_proposal_path,
            prepared.snapshot_root,
        )
        structure = load_structure_markdown(workspace.structure_path, structure_proposal)
        placement_raw = {
            "schema": PLACEMENT_PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "structure_digest": structure.structure_digest,
            "items": [],
            "source_edits": [],
            "source_reuses": [],
        }
        workspace.placement_proposal_path.write_text(
            json.dumps(placement_raw, indent=2),
            encoding="utf-8",
        )
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        review, _ = create_or_load_placement_review(
            workspace.placement_path,
            proposal,
            prepared.snapshot_root,
        )
        self.assertTrue(review.is_complete)

        preview = build_placement_publication_preview(
            proposal,
            review,
            prepared.snapshot_root,
        )
        self.assertEqual(preview.project_root, subtree.resolve())
        self.assertEqual(len(preview.parents), 1)
        parent = preview.parents[0]
        self.assertEqual(parent.child_key, "N-B")
        self.assertEqual(parent.parent_key, "@enclosing")
        self.assertEqual(parent.parent_node_id, "node-a")

        publish_placement_review(
            preview,
            review,
            snapshot_root=prepared.snapshot_root,
            acceptance_path=prepared.snapshot_root / "placement-acceptance.json",
        )

        parsed = parse_node(subtree, repo)
        self.assertEqual(len(parsed.parents), 1)
        self.assertEqual(parsed.parents[0].id, "node-a")
        compiled = Compiler(repo).compile(subtree)
        self.assertEqual(compiled.parent_package.metadata.id, "node-a")
        self.assertIn("A-001", {rule.id for rule in compiled.rules})
        self.assertIn("A-FOUNDATIONS", {topic.id for topic in compiled.topics})
        self.assertTrue(
            (subtree / ".context" / "sources" / compiled.parent_package.package_digest).is_dir()
        )

        self.assertEqual(main(["check", "--all", str(repo)]), 0)


if __name__ == "__main__":
    unittest.main()
