from __future__ import annotations

import contextlib
import io
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
from contextcanon.onboarding_placement import PLACEMENT_PROPOSAL_SCHEMA, load_onboarding_placement_proposal, render_placement_review
from contextcanon.onboarding_placement_instruction import build_onboarding_placement_instruction
from contextcanon.onboarding_structure import STRUCTURE_PROPOSAL_SCHEMA, create_or_load_structure_markdown, load_structure_markdown, load_onboarding_structure_proposal
from contextcanon.onboarding_workspace import open_onboarding_workspace
from contextcanon.outputs import write_outputs
from contextcanon.package import load_package
from contextcanon.parser import ContextCanonError


class OnboardingPlacementTests(unittest.TestCase):
    def make_case(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text(
            "# AI Workstation\n"
            "The repository is the installation specification.\n"
            "Running containers and manually modified hosts are not treated as the source of truth.\n"
            "Goose changes are developed through reviewed pull requests.\n",
            encoding="utf-8",
        )
        (repo / "docs").mkdir()
        (repo / "docs" / "architecture.md").write_text(
            "# Architecture\nThe repository is the installation specification.\n",
            encoding="utf-8",
        )
        prepared = prepare_onboarding_evidence(repo)
        readme = next(item for item in prepared.included if item.path == "README.md")
        architecture = next(item for item in prepared.included if item.path == "docs/architecture.md")
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)

        structure_raw = {
            "schema": STRUCTURE_PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "nodes": [
                {
                    "key": "N-001",
                    "name": "AI Workstation",
                    "parent_key": None,
                    "suggested_path": ".",
                    "lifecycle": "current",
                    "purpose": "Root project context.",
                    "rationale": "One project root.",
                    "confidence": "high",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 4}],
                },
                {
                    "key": "N-002",
                    "name": "Goose",
                    "parent_key": "N-001",
                    "suggested_path": "compose/goose",
                    "lifecycle": "current",
                    "purpose": "Goose-specific work.",
                    "rationale": "Goose has its own work area.",
                    "confidence": "high",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 4, "end_line": 4}],
                },
            ],
            "knowledge_bodies": [],
            "source_reuses": [],
        }
        workspace.structure_proposal_path.write_text(json.dumps(structure_raw, indent=2), encoding="utf-8")
        create_or_load_structure_markdown(prepared.snapshot_root, workspace.structure_proposal_path, workspace.structure_path)

        source_root = repo / "catalog-workflow"
        source_root.mkdir()
        (source_root / "CONTEXT.src.md").write_text(
            "# Development Workflow — Local Context Source\n"
            '<!-- ctx:node id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.2.0-draft" -->\n\n'
            "## Rules\n\n"
            "### Review\n"
            "- **Review before merge:** Keep coherent changes under human review before merge.\n"
            "  Why: Automation does not decide product acceptance.\n"
            '  <!-- ctx:rule id="CCW-006" -->\n',
            encoding="utf-8",
        )
        write_outputs(Compiler(repo).compile(source_root))
        package = load_package(source_root)
        return repo, prepared, workspace, readme, architecture, source_root, package

    def placement_dict(self, prepared, workspace, readme, architecture, package):
        structure_proposal = load_onboarding_structure_proposal(workspace.structure_proposal_path, prepared.snapshot_root)
        structure = load_structure_markdown(workspace.structure_path, structure_proposal)
        return {
            "schema": PLACEMENT_PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "structure_digest": structure.structure_digest,
            "items": [
                {
                    "id": "P-001",
                    "title": "Repository is the installation specification",
                    "kind": "rule",
                    "action": "move",
                    "destination_node_key": "N-001",
                    "rationale": "This is durable repository-wide governance and the existing wording is already precise.",
                    "confidence": "high",
                    "evidence": [{"path": "docs/architecture.md", "sha256": architecture.sha256, "start_line": 2, "end_line": 2}],
                    "payload": {
                        "statement": "The repository is the installation specification.",
                        "why": "Running state must not become undocumented authority.",
                        "wording_origin": "exact",
                    },
                },
                {
                    "id": "P-002",
                    "title": "Architecture documentation",
                    "kind": "topic-resource",
                    "action": "reference",
                    "destination_node_key": "N-001",
                    "rationale": "The architecture document is already in a natural documentation location.",
                    "confidence": "high",
                    "evidence": [{"path": "docs/architecture.md", "sha256": architecture.sha256, "start_line": 1, "end_line": 2}],
                    "payload": {
                        "condition": "When changing architecture or installation authority:",
                        "resource_paths": ["docs/architecture.md"],
                    },
                },
            ],
            "source_reuses": [
                {
                    "id": "S-001",
                    "target_node_key": "N-001",
                    "source_node_id": package.metadata.id,
                    "source_name": package.metadata.name,
                    "source_version": package.metadata.version,
                    "source_normalized_digest": package.normalized_digest,
                    "source_package_digest": package.package_digest,
                    "reason": "The evidence describes reviewed development workflow guidance already covered by this reusable Source.",
                    "confidence": "medium",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 4, "end_line": 4}],
                }
            ],
        }

    def test_instruction_is_bound_to_human_structure_and_preserves_source_language(self):
        _, prepared, workspace, _, _, source_root, _ = self.make_case()
        instruction = build_onboarding_placement_instruction(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        self.assertIn("place the books onto the already accepted shelves", instruction.text)
        self.assertIn("Do not redesign it in this pass", instruction.text)
        self.assertIn("wording_origin", instruction.text)
        self.assertIn("use it verbatim", instruction.text)
        self.assertIn("Development Workflow", instruction.text)
        self.assertIn(instruction.structure_digest, instruction.text)

    def test_placement_validates_exact_evidence_structure_and_catalog(self):
        _, prepared, workspace, readme, architecture, source_root, package = self.make_case()
        raw = self.placement_dict(prepared, workspace, readme, architecture, package)
        workspace.placement_proposal_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

        first = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        second = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        self.assertEqual(first.proposal_digest, second.proposal_digest)
        self.assertEqual(first.items[0].payload["wording_origin"], "exact")
        self.assertEqual(first.source_reuses[0].source_node_id, package.metadata.id)

    def test_placement_rejects_stale_structure_and_unsupplied_source(self):
        _, prepared, workspace, readme, architecture, source_root, package = self.make_case()
        raw = self.placement_dict(prepared, workspace, readme, architecture, package)
        raw["structure_digest"] = "0" * 64
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "structure_digest does not match"):
            load_onboarding_placement_proposal(
                workspace.placement_proposal_path,
                prepared.snapshot_root,
                workspace.structure_proposal_path,
                workspace.structure_path,
                catalog_package_roots=[source_root],
            )

        raw = self.placement_dict(prepared, workspace, readme, architecture, package)
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "not supplied in the verified catalog"):
            load_onboarding_placement_proposal(
                workspace.placement_proposal_path,
                prepared.snapshot_root,
                workspace.structure_proposal_path,
                workspace.structure_path,
            )

    def test_review_shows_source_excerpt_destination_action_and_wording_origin(self):
        _, prepared, workspace, readme, architecture, source_root, package = self.make_case()
        workspace.placement_proposal_path.write_text(
            json.dumps(self.placement_dict(prepared, workspace, readme, architecture, package), indent=2),
            encoding="utf-8",
        )
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review = render_placement_review(proposal, prepared.snapshot_root)
        self.assertIn("action: `move`", review)
        self.assertIn("Destination: AI Workstation (`.`)", review)
        self.assertIn("Wording origin: **exact**", review)
        self.assertIn("The repository is the installation specification.", review)
        self.assertIn("reuse Development Workflow", review)

    def test_cli_writes_instruction_validates_and_renders_review_without_redirects(self):
        _, prepared, workspace, readme, architecture, source_root, package = self.make_case()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([
                "onboard", "placement-instruction", str(prepared.snapshot_root),
                "--catalog-package", str(source_root),
            ])
        self.assertEqual(result, 0)
        self.assertTrue(workspace.placement_instruction_path.is_file())
        self.assertIn(str(workspace.placement_proposal_path), stdout.getvalue())

        workspace.placement_proposal_path.write_text(
            json.dumps(self.placement_dict(prepared, workspace, readme, architecture, package), indent=2),
            encoding="utf-8",
        )
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([
                "onboard", "placement-validate", str(prepared.snapshot_root),
                "--catalog-package", str(source_root),
            ])
        self.assertEqual(result, 0)
        self.assertIn("Placement items: 2", stdout.getvalue())
        self.assertIn("Source reuses: 1", stdout.getvalue())

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([
                "onboard", "placement-review", str(prepared.snapshot_root),
                "--catalog-package", str(source_root),
            ])
        self.assertEqual(result, 0)
        self.assertTrue(workspace.placement_path.is_file())
        self.assertIn("Wording origin: **exact**", workspace.placement_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
