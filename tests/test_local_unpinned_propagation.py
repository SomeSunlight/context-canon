"""Issue #134/#139: local unpinned Parents must remain reviewable after a bump."""
from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from contextcanon.cli import main as cli_main
from contextcanon.compiler import Compiler
from contextcanon.outputs import check_outputs
from contextcanon.package import compiled_package, load_package
from contextcanon.parser import ContextCanonError, parse_node
from contextcanon.sources import accept_parent_candidate, review_parent_candidate
from contextcanon.version_history import publish_outputs
from contextcanon.version_store import version_path


class LocalUnpinnedPropagationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        (self.repo / ".git").mkdir()
        self.parent = self.repo / "parent"
        self.parent.mkdir()
        self.guide = self.parent / "docs" / "guide.md"
        self.guide.parent.mkdir()
        self.guide.write_text("# Guide\nOriginal resource.\n", encoding="utf-8")
        self.child = self.repo / "child"
        self.child.mkdir()
        self._parent_source("0.3.9-draft", "Old guidance.")
        self.original = compiled_package(self._publish(self.parent))
        self._child_source("0.3.9-draft")
        self._publish(self.child)
        self.child_original = load_package(self.child)

    def tearDown(self):
        self.temp.cleanup()

    def _parent_source(self, version, statement):
        (self.parent / "CONTEXT.src.md").write_text(
            f'# Parent — Local Context Source\n'
            f'<!-- ctx:node id="parent-id" name="Parent" version="{version}" -->\n\n'
            '## Local Rules\n\n### Guidance\n\n'
            f'- **Policy:** {statement}\n'
            '  Why: This is reviewed upstream guidance.\n'
            '  <!-- ctx:rule id="P-1" -->\n\n'
            '## Local Topics\n\n'
            '### Resource guide\n\n'
            'When reviewing this Parent guide:\n\n'
            'Optional:\n'
            '- Resource: `docs/guide.md`\n'
            '  <!-- ctx:resource id="RESOURCE-GUIDE" -->\n'
            '<!-- ctx:topic id="TOPIC-GUIDE" -->\n',
            encoding="utf-8",
        )

    def _child_source(self, parent_version):
        (self.child / "CONTEXT.src.md").write_text(
            '# Child — Local Context Source\n'
            '<!-- ctx:node id="child-id" name="Child" version="0.1.0" -->\n\n'
            '## Context Imports\n\n'
            f'- [Parent](../parent/) — `{parent_version}` — `relationship=parent`\n'
            f'  <!-- ctx:source id="parent-id" version="{parent_version}" -->\n',
            encoding="utf-8",
        )

    def _publish(self, root):
        compiled = Compiler(self.repo).compile(root)
        publish_outputs(compiled)
        return compiled

    def _command(self, args, *, decisions=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            if decisions is None:
                rc = cli_main(args)
            else:
                with mock.patch("builtins.input", side_effect=decisions):
                    rc = cli_main(args)
        return rc, output.getvalue()

    def _advance_parent(self):
        source = self.parent / "CONTEXT.src.md"
        source.write_text(
            source.read_text(encoding="utf-8").replace("Old guidance.", "New guidance."),
            encoding="utf-8",
        )

    def test_bump_pending_decline_then_accept_and_offline_rebuild(self):
        self._advance_parent()
        rc, out = self._command(["build", "--all", str(self.repo)])
        self.assertEqual(rc, 1, out)
        self.assertIn("pending propagation", out)
        self.assertEqual(parse_node(self.parent, self.repo).metadata.version, "0.3.10-draft")

        frozen = Compiler(self.repo).compile(self.child)
        self.assertEqual(frozen.source_packages[0].package_digest, self.original.package_digest)
        self.assertEqual(check_outputs(frozen), [])
        self.assertEqual(load_package(version_path(self.repo, self.original)).package_digest,
                         self.original.package_digest)

        rc, out = self._command(["propagate", "--status", "--all", str(self.repo)])
        self.assertEqual(rc, 1, out)
        self.assertIn("0.3.9-draft -> 0.3.10-draft", out)

        old_text = (self.child / "CONTEXT.src.md").read_bytes()
        rc, out = self._command(["propagate", "--all", str(self.repo)], decisions=["n"])
        self.assertEqual(rc, 0, out)
        self.assertIn("No Parent update applied", out)
        self.assertEqual((self.child / "CONTEXT.src.md").read_bytes(), old_text)
        self.assertEqual(Compiler(self.repo).compile(self.child).source_packages[0].package_digest,
                         self.original.package_digest)

        rc, out = self._command(["check", "--all", str(self.repo)])
        self.assertEqual(rc, 1, out)
        self.assertIn("pending propagation", out)
        self.assertNotIn("drift child:", out)

        rc, out = self._command(["propagate", "--all", str(self.repo)], decisions=["y"])
        self.assertEqual(rc, 0, out)
        self.assertIn("Parent: Parent 0.3.9-draft -> 0.3.10-draft", out)
        self.assertIn("Applied Parent update", out)
        accepted = parse_node(self.child, self.repo).sources[0]
        self.assertTrue(accepted.is_pinned)
        self.assertEqual(accepted.version, "0.3.10-draft")
        self.assertNotEqual(accepted.package_digest, self.original.package_digest)

        rc, out = self._command(["build", "--all", str(self.repo)])
        self.assertEqual(rc, 0, out)
        rc, out = self._command(["check", "--all", str(self.repo)])
        self.assertEqual(rc, 0, out)
        self.assertEqual(Compiler(self.repo).compile(self.child).inherited_rules[0].statement,
                         "New guidance.")
        self.assertEqual(load_package(version_path(self.repo, self.child_original)).package_digest,
                         self.child_original.package_digest)

        shutil.rmtree(self.parent)
        offline = Compiler(self.repo).compile(self.child)
        self.assertEqual(offline.inherited_rules[0].statement, "New guidance.")
        self.assertEqual(check_outputs(offline), [])

    def test_same_version_changed_in_place_is_not_silently_accepted(self):
        self._advance_parent()
        compiled = Compiler(self.repo).compile(self.child)
        self.assertEqual(compiled.source_packages[0].package_digest, self.original.package_digest)
        rc, out = self._command(["propagate", "--status", "--all", str(self.repo)])
        self.assertEqual(rc, 1, out)
        self.assertIn("package changed without a new accepted Child snapshot", out)
        rc, out = self._command(["propagate", "--all", str(self.repo)], decisions=["n"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(parse_node(self.child, self.repo).sources[0].version, "0.3.9-draft")

    def test_missing_history_fails_closed(self):
        self._advance_parent()
        shutil.rmtree(version_path(self.repo, self.original))
        with self.assertRaisesRegex(ContextCanonError, "accepted local Parent package"):
            Compiler(self.repo).compile(self.child)

    def test_resource_only_change_is_reviewed_without_manual_version_edit(self):
        self.guide.write_text("# Guide\nUpdated resource bytes.\n", encoding="utf-8")
        rc, out = self._command(["build", "--all", str(self.repo)])
        self.assertEqual(rc, 1, out)
        self.assertEqual(parse_node(self.parent, self.repo).metadata.version, "0.3.10-draft")
        frozen = Compiler(self.repo).compile(self.child)
        self.assertEqual(frozen.source_packages[0].package_digest, self.original.package_digest)
        diff, _ = review_parent_candidate(self.child, "parent-id")
        self.assertTrue(any(entry.category == "resource" for entry in diff.entries))
        rc, out = self._command(["propagate", "--all", str(self.repo)], decisions=["y"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(parse_node(self.child, self.repo).sources[0].version, "0.3.10-draft")
        rc, out = self._command(["build", "--all", str(self.repo)])
        self.assertEqual(rc, 0, out)
        rc, out = self._command(["check", "--all", str(self.repo)])
        self.assertEqual(rc, 0, out)
        self.assertNotEqual(
            compiled_package(Compiler(self.repo).compile(self.child)).package_digest,
            self.child_original.package_digest,
        )

    def test_version_only_update_is_normatively_current_without_forced_review(self):
        self._parent_source("0.3.10-draft", "Old guidance.")
        rc, out = self._command(["build", "--all", str(self.repo)])
        self.assertEqual(rc, 0, out)
        rc, out = self._command(["propagate", "--status", "--all", str(self.repo)])
        self.assertEqual(rc, 0, out)
        self.assertIn("non-normative", out)
        self.assertEqual(parse_node(self.child, self.repo).sources[0].version, "0.3.9-draft")
        rc, out = self._command(["check", "--all", str(self.repo)])
        self.assertEqual(rc, 0, out)

    def test_multigeneration_and_second_parent_preserve_other_binding(self):
        # A sibling Parent with a space in its path exercises Markdown locator
        # encoding and filesystem behavior without platform-specific
        # absolute path spelling.
        other = self.repo / "second parent"
        other.mkdir()
        (other / "CONTEXT.src.md").write_text(
            '# Other Parent\n'
            '<!-- ctx:node id="other-id" name="Other Parent" version="1.0.0" -->\n\n'
            '## Local Rules\n\n### Other guidance\n\n'
            '- **Other policy:** Independent rule.\n'
            '  Why: Second Parent must not change.\n'
            '  <!-- ctx:rule id="OTHER-1" -->\n',
            encoding="utf-8",
        )
        self._publish(other)
        child_source = self.child / "CONTEXT.src.md"
        child_source.write_text(
            child_source.read_text(encoding="utf-8")
            + '\n- [Other Parent](../second%20parent/) — `1.0.0` — `relationship=parent`\n'
              '  <!-- ctx:source id="other-id" version="1.0.0" -->\n',
            encoding="utf-8",
        )
        # Publish the expanded accepted Child before the upstream change.
        rc, out = self._command(["build", "--all", str(self.repo)])
        self.assertEqual(rc, 0, out)
        child_before = compiled_package(Compiler(self.repo).compile(self.child))
        other_before = next(ref for ref in child_before.sources if ref.id == "other-id")

        grand = self.repo / "grandchild"
        grand.mkdir()
        (grand / "CONTEXT.src.md").write_text(
            '# Grandchild\n'
            '<!-- ctx:node id="grand-id" name="Grandchild" version="0.1.0" -->\n\n'
            '## Context Imports\n\n'
            f'- [Child](../child/) — `{child_before.metadata.version}` — `relationship=parent`\n'
            f'  <!-- ctx:source id="child-id" version="{child_before.metadata.version}" -->\n',
            encoding="utf-8",
        )
        self._publish(grand)
        self._advance_parent()
        rc, out = self._command(["propagate", "--all", str(self.repo)], decisions=["y", "y"])
        self.assertEqual(rc, 0, out)
        self.assertIn('Applied Parent update to Child "Child"', out)
        self.assertIn('Applied Parent update to Child "Grandchild"', out)
        accepted_other = next(ref for ref in parse_node(self.child, self.repo).sources
                              if ref.id == "other-id")
        self.assertFalse(accepted_other.is_pinned)
        self.assertEqual(accepted_other.version, other_before.version)
        rc, out = self._command(["build", "--all", str(self.repo)])
        self.assertEqual(rc, 0, out)
        rc, out = self._command(["check", "--all", str(self.repo)])
        self.assertEqual(rc, 0, out)
        rules = {rule.id: rule.statement for rule in Compiler(self.repo).compile(grand).inherited_rules}
        self.assertEqual(rules["P-1"], "New guidance.")
        self.assertEqual(rules["OTHER-1"], "Independent rule.")

    def test_corrupted_historical_parent_package_fails_closed(self):
        self._advance_parent()
        old_file = version_path(self.repo, self.original) / "CONTEXT.md"
        old_file.write_bytes(old_file.read_bytes() + b"tampered")
        with self.assertRaisesRegex(ContextCanonError, "digest|mismatch|sha256|size"):
            Compiler(self.repo).compile(self.child)
        self.assertFalse(parse_node(self.child, self.repo).sources[0].is_pinned)

    def test_stale_review_receipt_cannot_authorize_acceptance(self):
        self._parent_source("0.3.10-draft", "New guidance.")
        review_parent_candidate(self.child, "parent-id")
        source = self.child / "CONTEXT.src.md"
        source.write_text(source.read_text(encoding="utf-8") + "\n<!-- changed -->\n",
                          encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "changed after Parent review"):
            accept_parent_candidate(self.child, "parent-id")
        self.assertEqual(parse_node(self.child, self.repo).sources[0].version, "0.3.9-draft")


if __name__ == "__main__":
    unittest.main()
