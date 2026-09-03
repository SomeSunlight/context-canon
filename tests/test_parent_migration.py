from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.onboarding_placement_publish import build_placement_publication_preview, publish_placement_review
from contextcanon.onboarding_reset import reset_onboarding, run_journaled
from contextcanon.outputs import write_outputs
from contextcanon.parser import ContextCanonError
from contextcanon.sources import install_source_package
from tests.test_onboarding_placement_publish import PlacementPublicationTests


PARENT_BLOCK_RE = re.compile(
    r"\n## (?:Parent Context Node|Parent)\n\n<!-- contextcanon-placement-parent:start -->\n.*?\n<!-- contextcanon-placement-parent:end -->\n?(?=\n## |\Z)",
    re.DOTALL,
)


def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class LegacyParentMigrationTests(unittest.TestCase):
    def make_legacy_publication(self):
        helper = PlacementPublicationTests()
        repo, prepared, workspace, source_root, proposal, review, _ = helper.make_case()
        preview = build_placement_publication_preview(
            proposal,
            review,
            prepared.snapshot_root,
            catalog_package_roots=[source_root],
            project_root=repo,
        )

        # Materialize exactly the old placement semantics: reviewed local
        # content and Source reuse, but no semantic Parent blocks/packages.
        for delta in preview.nodes:
            legacy = PARENT_BLOCK_RE.sub("\n", delta.after).rstrip() + "\n"
            delta.source_path.write_text(legacy, encoding="utf-8")
        for document in preview.documents:
            document.source_path.write_text(document.after, encoding="utf-8")
        install_source_package(repo, source_root)

        compiled_nodes = {}
        for delta in preview.nodes:
            compiled = Compiler(repo).compile(delta.source_path.parent)
            write_outputs(compiled)
            compiled_nodes[delta.key] = compiled

        nodes = {}
        for delta in preview.nodes:
            compiled = Compiler(repo).compile(delta.source_path.parent)
            nodes[delta.key] = {
                "node_id": compiled.metadata.id,
                "path": delta.path,
                "normalized_digest": compiled.normalized_digest,
                "package_digest": compiled.package_digest,
                "source_sha256": sha(delta.source_path.read_bytes()),
            }
        legacy_acceptance = {
            "schema": "contextcanon/onboarding-placement-acceptance/v1",
            "evidence_digest": preview.evidence_digest,
            "structure_digest": preview.structure_digest,
            "proposal_digest": preview.proposal_digest,
            "review_digest": preview.review_digest,
            "nodes": nodes,
            "sources": [],
            "followups": [],
            "source_edits": [],
            "documents": [],
        }
        acceptance = prepared.snapshot_root / "placement-acceptance.json"
        encoded = (json.dumps(legacy_acceptance, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        acceptance.write_bytes(encoded)
        return repo, prepared, workspace, source_root, proposal, review, acceptance, encoded

    def test_legacy_published_tree_migrates_idempotently_and_reset_restores_old_acceptance(self):
        repo, prepared, workspace, source_root, proposal, review, acceptance, legacy_bytes = self.make_legacy_publication()
        child = repo / "compose" / "goose"
        legacy_child = (child / "CONTEXT.src.md").read_bytes()

        preview = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root,
            catalog_package_roots=[source_root], project_root=repo,
        )
        self.assertEqual(len(preview.parents), 1)
        self.assertTrue(any(delta.changed for delta in preview.nodes))

        args = [
            "onboard", "placement-publish", str(prepared.snapshot_root),
            "--catalog-package", str(source_root), "--project", str(repo),
        ]
        self.assertEqual(run_journaled(args, main), 0)
        migrated = json.loads(acceptance.read_text(encoding="utf-8"))
        self.assertEqual(len(migrated["parents"]), 1)
        child_text = (child / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("ctx:parent", child_text)
        child_compiled = Compiler(repo).compile(child)
        self.assertIsNotNone(child_compiled.parent_package)
        parent_store = child / ".context" / "sources" / child_compiled.parent_package.package_digest
        self.assertTrue(parent_store.is_dir())

        second = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root,
            catalog_package_roots=[source_root], project_root=repo,
        )
        self.assertTrue(all(not delta.changed for delta in second.nodes))
        second_result = publish_placement_review(
            second, review, snapshot_root=prepared.snapshot_root,
            catalog_package_roots=[source_root], acceptance_path=acceptance,
        )
        self.assertEqual(acceptance.read_bytes(), (json.dumps(migrated, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        self.assertTrue(second_result.acceptance_digest)

        reset = reset_onboarding(prepared.snapshot_root, from_step=9)
        self.assertGreaterEqual(reset["journal_records_reversed"], 1)
        self.assertEqual((child / "CONTEXT.src.md").read_bytes(), legacy_child)
        self.assertEqual(acceptance.read_bytes(), legacy_bytes)
        self.assertFalse(parent_store.exists())
        restored_child = Compiler(repo).compile(child)
        self.assertIsNone(restored_child.parent_package)

    def test_legacy_acceptance_with_later_child_edit_refuses_automatic_parent_migration(self):
        repo, prepared, _, source_root, proposal, review, acceptance, legacy_bytes = self.make_legacy_publication()
        child = repo / "compose" / "goose"
        source = child / "CONTEXT.src.md"
        source.write_text(source.read_text(encoding="utf-8") + "\n<!-- later human edit -->\n", encoding="utf-8")
        before = source.read_bytes()
        preview = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root,
            catalog_package_roots=[source_root], project_root=repo,
        )
        with self.assertRaisesRegex(ContextCanonError, "changed after the legacy placement acceptance"):
            publish_placement_review(
                preview, review, snapshot_root=prepared.snapshot_root,
                catalog_package_roots=[source_root], acceptance_path=acceptance,
            )
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(acceptance.read_bytes(), legacy_bytes)


if __name__ == "__main__":
    unittest.main()
