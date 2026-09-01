from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.onboarding_placement import load_onboarding_placement_proposal
from contextcanon.onboarding_placement_publish import (
    build_placement_publication_preview,
    publish_placement_review,
    render_placement_publication_preview,
)
from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review
from contextcanon.onboarding_structure import create_or_load_structure_markdown
from contextcanon.outputs import write_outputs
from contextcanon.parser import ContextCanonError, parse_node
from tests.test_onboarding_placement import OnboardingPlacementTests


class PlacementPublicationTests(unittest.TestCase):
    def make_case(self):
        helper = OnboardingPlacementTests()
        repo, prepared, workspace, readme, architecture, source_root, package = helper.make_case()

        structure_raw = json.loads(workspace.structure_proposal_path.read_text(encoding="utf-8"))
        structure_raw["knowledge_bodies"] = [
            {
                "key": "K-001",
                "kind": "authoritative-reference",
                "name": "README authority",
                "suggested_node_key": "N-001",
                "paths": ["README.md"],
                "purpose": "Exercise fixed Markdown authority handling in placement publication.",
                "rationale": "The test intentionally treats README as fixed only after Pass 1 proposed it as a knowledge body.",
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
        ]
        workspace.structure_proposal_path.write_text(json.dumps(structure_raw, indent=2), encoding="utf-8")
        workspace.structure_path.unlink()
        create_or_load_structure_markdown(
            prepared.snapshot_root, workspace.structure_proposal_path, workspace.structure_path
        )
        structure_text = workspace.structure_path.read_text(encoding="utf-8")
        structure_text = structure_text.replace(
            "<!-- contextcanon-fixed-markdown:start -->\n<!-- contextcanon-fixed-markdown:end -->",
            "<!-- contextcanon-fixed-markdown:start -->\n- `README.md`\n<!-- contextcanon-fixed-markdown:end -->",
        )
        workspace.structure_path.write_text(structure_text, encoding="utf-8")

        (repo / "CONTEXT.src.md").write_text(
            "# AI Workstation — Local Context Source\n"
            '<!-- ctx:node id="aea56adf-2a26-43f0-b712-3bbeab7a3097" version="0.1.0" -->\n\n'
            "## Overview\n\n"
            "Existing authored root orientation that placement must preserve.\n",
            encoding="utf-8",
        )
        goose = repo / "compose" / "goose"
        goose.mkdir(parents=True)
        (goose / "CONTEXT.src.md").write_text(
            "# Goose — Local Context Source\n"
            '<!-- ctx:node id="11111111-2222-4333-8444-555555555555" version="0.1.0-draft" -->\n\n'
            "## Overview\n\n"
            "Existing authored Goose orientation.\n",
            encoding="utf-8",
        )
        write_outputs(Compiler(repo).compile(repo))
        write_outputs(Compiler(repo).compile(goose))

        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        raw["items"][1]["destination_node_key"] = "N-002"
        raw["items"].extend(
            [
                {
                    "id": "P-003",
                    "title": "Goose changes stay reviewed",
                    "kind": "rule",
                    "action": "promote",
                    "destination_node_key": "N-002",
                    "rationale": "This is local durable Goose development governance.",
                    "confidence": "high",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 4, "end_line": 4}],
                    "payload": {
                        "statement": "Goose changes are developed through reviewed pull requests.",
                        "why": "Keep local Goose changes reviewable.",
                        "wording_origin": "exact",
                    },
                },
                {
                    "id": "P-004",
                    "title": "Root responsibility",
                    "kind": "overview",
                    "action": "promote",
                    "destination_node_key": "N-001",
                    "rationale": "Stable project orientation belongs at the root Node.",
                    "confidence": "high",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 2}],
                    "payload": {"text": "AI Workstation owns reproducible workstation setup.", "wording_origin": "synthesized"},
                },
                {
                    "id": "P-005",
                    "title": "Current migration state",
                    "kind": "state",
                    "action": "promote",
                    "destination_node_key": "N-001",
                    "rationale": "State is reviewed but not forced into current Context source grammar.",
                    "confidence": "medium",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 1}],
                    "payload": {"text": "Migration is in progress.", "wording_origin": "synthesized"},
                },
                {
                    "id": "P-007",
                    "title": "Next reviewed work",
                    "kind": "plan",
                    "action": "promote",
                    "destination_node_key": "N-001",
                    "rationale": "The next intended work belongs in the root Node plan.",
                    "confidence": "medium",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 4, "end_line": 4}],
                    "payload": {"text": "Continue Goose changes through reviewed pull requests.", "wording_origin": "synthesized"},
                },
                {
                    "id": "P-006",
                    "title": "README authority mapping",
                    "kind": "authority-mapping",
                    "action": "map",
                    "destination_node_key": "N-001",
                    "rationale": "Fixed Markdown remains authoritative.",
                    "confidence": "high",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 2}],
                    "payload": {
                        "authority_paths": ["README.md"],
                        "mapping": "README remains the fixed first-contact authority for this test.",
                        "wording_origin": "synthesized",
                    },
                },
            ]
        )
        workspace.placement_proposal_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review, created = create_or_load_placement_review(
            workspace.placement_path, proposal, prepared.snapshot_root
        )
        self.assertTrue(created)
        review_text = workspace.placement_path.read_text(encoding="utf-8").replace(
            "Decision: `pending`", "Decision: `accept`"
        ).replace("Source edit decision: `pending`", "Source edit decision: `accept`")
        workspace.placement_path.write_text(review_text, encoding="utf-8")
        review = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertTrue(review.is_complete)

        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "ContextCanon Test"], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "remote", "add", "origin", "https://example.test/context-canon.git"], check=True
        )
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "test baseline"], check=True)
        head = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, text=True, capture_output=True
        ).stdout.strip()
        return repo, prepared, workspace, source_root, proposal, review, head

    def test_preview_is_non_mutating_destination_aware_and_keeps_followups(self):
        repo, prepared, workspace, source_root, proposal, review, head = self.make_case()
        root_before = (repo / "CONTEXT.src.md").read_bytes()
        child_before = (repo / "compose" / "goose" / "CONTEXT.src.md").read_bytes()
        preview = build_placement_publication_preview(
            proposal,
            review,
            prepared.snapshot_root,
            catalog_package_roots=[source_root],
            project_root=repo,
        )
        text = render_placement_publication_preview(preview)
        self.assertTrue(preview.review_complete)
        self.assertEqual((repo / "CONTEXT.src.md").read_bytes(), root_before)
        self.assertEqual((repo / "compose" / "goose" / "CONTEXT.src.md").read_bytes(), child_before)
        self.assertEqual({delta.key for delta in preview.nodes}, {"N-001", "N-002"})
        child = next(delta for delta in preview.nodes if delta.key == "N-002")
        self.assertIn("Resource: `../../docs/architecture.md`", child.after)
        self.assertIn("Existing authored Goose orientation.", child.after)
        self.assertEqual({item.kind for item in preview.followups}, {"authority-mapping"})
        root = next(delta for delta in preview.nodes if delta.key == "N-001")
        self.assertIn("## State", root.after)
        self.assertIn("Migration is in progress.", root.after)
        self.assertIn("## Plan", root.after)
        self.assertIn("Continue Goose changes through reviewed pull requests.", root.after)
        self.assertIn(head, text)
        self.assertIn("Development Workflow", text)
        self.assertIn("origin: `evidence-derived`", text)
        self.assertIn(proposal.source_reuses[0].source_package_digest, text)
        self.assertEqual(len(preview.documents), 1)
        self.assertEqual(preview.documents[0].path, "docs/architecture.md")
        self.assertTrue(preview.documents[0].changed)
        self.assertIn("Reviewed source-document deltas", text)

    def test_publish_preserves_node_identity_and_project_markdown_then_is_idempotent(self):
        repo, prepared, workspace, source_root, proposal, review, head = self.make_case()
        readme_before = (repo / "README.md").read_bytes()
        architecture_before = (repo / "docs" / "architecture.md").read_bytes()
        root_id = parse_node(repo, repo).metadata.id
        child_root = repo / "compose" / "goose"
        child_id = parse_node(child_root, repo).metadata.id
        preview = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root, catalog_package_roots=[source_root], project_root=repo
        )
        acceptance = prepared.snapshot_root / "placement-acceptance.json"
        result = publish_placement_review(
            preview,
            review,
            snapshot_root=prepared.snapshot_root,
            catalog_package_roots=[source_root],
            acceptance_path=acceptance,
        )
        self.assertTrue(acceptance.is_file())
        self.assertEqual((repo / "README.md").read_bytes(), readme_before)
        self.assertNotEqual((repo / "docs" / "architecture.md").read_bytes(), architecture_before)
        self.assertIn("maintained in [AI Workstation Context]", (repo / "docs" / "architecture.md").read_text(encoding="utf-8"))
        self.assertEqual(parse_node(repo, repo).metadata.id, root_id)
        self.assertEqual(parse_node(child_root, repo).metadata.id, child_id)
        root_text = (repo / "CONTEXT.src.md").read_text(encoding="utf-8")
        child_text = (child_root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("Existing authored root orientation that placement must preserve.", root_text)
        self.assertIn("contextcanon-placement-rules:start", root_text)
        self.assertIn("contextcanon-placement-state:start", root_text)
        self.assertIn("contextcanon-placement-plan:start", root_text)
        parsed_root = parse_node(repo, repo)
        self.assertIn("Migration is in progress.", parsed_root.state)
        self.assertIn("Continue Goose changes through reviewed pull requests.", parsed_root.plan)
        self.assertIn('transport="git"', root_text)
        self.assertIn(f'ref="{head}"', root_text)
        self.assertIn("../../docs/architecture.md", child_text)
        Compiler(repo).compile(repo)
        Compiler(repo).compile(child_root)
        payload = json.loads(acceptance.read_text(encoding="utf-8"))
        self.assertEqual({item["kind"] for item in payload["followups"]}, {"authority-mapping"})

        second = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root, catalog_package_roots=[source_root], project_root=repo
        )
        self.assertTrue(all(not delta.changed for delta in second.nodes))
        self.assertTrue(all(not document.changed for document in second.documents))
        second_result = publish_placement_review(
            second,
            review,
            snapshot_root=prepared.snapshot_root,
            catalog_package_roots=[source_root],
            acceptance_path=acceptance,
        )
        self.assertEqual(second_result.acceptance_digest, result.acceptance_digest)
        self.assertEqual(second_result.changed_sources, ())

    def test_publish_rejects_stale_node_source_after_preview(self):
        repo, prepared, workspace, source_root, proposal, review, _ = self.make_case()
        preview = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root, catalog_package_roots=[source_root], project_root=repo
        )
        root_source = repo / "CONTEXT.src.md"
        root_source.write_text(root_source.read_text(encoding="utf-8") + "\nHuman edit after preview.\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "changed after publication preview"):
            publish_placement_review(
                preview,
                review,
                snapshot_root=prepared.snapshot_root,
                catalog_package_roots=[source_root],
                acceptance_path=prepared.snapshot_root / "placement-acceptance.json",
            )

    def test_cli_preview_and_publish_use_visible_workspace_artifacts(self):
        repo, prepared, workspace, source_root, proposal, review, _ = self.make_case()
        args = [
            "onboard", "placement-preview", str(prepared.snapshot_root),
            "--catalog-package", str(source_root), "--project", str(repo),
        ]
        self.assertEqual(main(args), 0)
        self.assertTrue(workspace.placement_preview_path.is_file())
        self.assertFalse((prepared.snapshot_root / "placement-acceptance.json").exists())
        args[1] = "placement-publish"
        self.assertEqual(main(args), 0)
        self.assertTrue((prepared.snapshot_root / "placement-acceptance.json").is_file())
        self.assertTrue(workspace.placement_followup_path.is_file())


if __name__ == "__main__":
    unittest.main()
