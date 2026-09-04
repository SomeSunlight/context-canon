from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.package import artifact_files
from contextcanon.parser import ContextCanonError
from contextcanon.sources import accept_parent_candidate, review_parent_candidate


PARENT_TEMPLATE = """# Project Parent — Local Context Source
<!-- ctx:node id="node-parent" version="{version}" -->

## Rules

### Policy

- **Parent policy:** {statement}
  Why: Descendants consume only accepted Parent snapshots.
  <!-- ctx:rule id="PARENT-001" -->
"""


def child_text(parent) -> str:
    return f"""# Child — Local Context Source
<!-- ctx:node id="node-child" version="0.1.0" -->

## Parent

- [Project Parent](../parent) — `{parent.metadata.version}`
  <!-- ctx:parent id="node-parent" version="{parent.metadata.version}" normalized-digest="{parent.normalized_digest}" package-digest="{parent.package_digest}" -->
"""


class ParentAcceptanceTests(unittest.TestCase):
    def make_case(self):
        repo = Path(tempfile.mkdtemp())
        (repo / ".git").mkdir()
        parent_root = repo / "parent"
        child_root = repo / "child"
        parent_root.mkdir()
        child_root.mkdir()
        (parent_root / "CONTEXT.src.md").write_text(
            PARENT_TEMPLATE.format(version="1.0.0", statement="Use accepted parent policy v1."),
            encoding="utf-8",
        )
        parent_v1 = Compiler(repo).compile(parent_root)
        destination = child_root / ".context" / "sources" / parent_v1.package_digest
        for rel, content in artifact_files(parent_v1).items():
            path = destination / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        (child_root / "CONTEXT.src.md").write_text(child_text(parent_v1), encoding="utf-8")
        return repo, parent_root, child_root, parent_v1

    def test_live_parent_change_is_non_live_until_review_and_accept(self):
        repo, parent_root, child_root, parent_v1 = self.make_case()
        before = Compiler(repo).compile(child_root)
        self.assertEqual(before.parent_package.package_digest, parent_v1.package_digest)
        self.assertEqual(before.inherited_rules[0].statement, "Use accepted parent policy v1.")

        (parent_root / "CONTEXT.src.md").write_text(
            PARENT_TEMPLATE.format(version="2.0.0", statement="Use reviewed parent policy v2."),
            encoding="utf-8",
        )
        still_v1 = Compiler(repo).compile(child_root)
        self.assertEqual(still_v1.parent_package.package_digest, parent_v1.package_digest)
        self.assertEqual(still_v1.inherited_rules[0].statement, "Use accepted parent policy v1.")

        diff, receipt = review_parent_candidate(child_root)
        self.assertFalse(diff.is_empty)
        self.assertTrue(receipt.is_file())
        reviewed_source = (child_root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn(f'package-digest="{parent_v1.package_digest}"', reviewed_source)
        still_v1_after_review = Compiler(repo).compile(child_root)
        self.assertEqual(still_v1_after_review.parent_package.package_digest, parent_v1.package_digest)

        # The review is an exact snapshot. Later live Parent edits must not move
        # what accept means.
        (parent_root / "CONTEXT.src.md").write_text(
            PARENT_TEMPLATE.format(version="3.0.0", statement="Unreviewed parent policy v3."),
            encoding="utf-8",
        )
        accepted = accept_parent_candidate(child_root)
        self.assertEqual(accepted.metadata.version, "2.0.0")
        self.assertNotEqual(accepted.package_digest, parent_v1.package_digest)
        child_source = (child_root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("— `2.0.0`", child_source)
        self.assertIn(f'package-digest="{accepted.package_digest}"', child_source)
        compiled = Compiler(repo).compile(child_root)
        self.assertEqual(compiled.parent_package.package_digest, accepted.package_digest)
        self.assertEqual(compiled.inherited_rules[0].statement, "Use reviewed parent policy v2.")

    def test_child_edit_after_review_invalidates_parent_receipt(self):
        _, parent_root, child_root, _ = self.make_case()
        (parent_root / "CONTEXT.src.md").write_text(
            PARENT_TEMPLATE.format(version="2.0.0", statement="Use reviewed parent policy v2."),
            encoding="utf-8",
        )
        review_parent_candidate(child_root)
        source = child_root / "CONTEXT.src.md"
        source.write_text(source.read_text(encoding="utf-8") + "\n<!-- human child edit -->\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "changed after Parent review"):
            accept_parent_candidate(child_root)

    def test_cli_parent_review_and_accept_keep_explicit_gate(self):
        repo, parent_root, child_root, parent_v1 = self.make_case()
        (parent_root / "CONTEXT.src.md").write_text(
            PARENT_TEMPLATE.format(version="2.0.0", statement="Use reviewed parent policy v2."),
            encoding="utf-8",
        )
        self.assertEqual(main(["parent", "review", "--node", str(child_root)]), 0)
        self.assertEqual(Compiler(repo).compile(child_root).parent_package.package_digest, parent_v1.package_digest)
        self.assertEqual(main(["parent", "accept", "--node", str(child_root)]), 0)
        self.assertEqual(Compiler(repo).compile(child_root).parent_package.metadata.version, "2.0.0")

    def test_parent_commands_require_semantic_parent(self):
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(
            '# Lone Node — Local Context Source\n<!-- ctx:node id="node-lone" version="0.1.0" -->\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "has no semantic Parent"):
            review_parent_candidate(root)


if __name__ == "__main__":
    unittest.main()
