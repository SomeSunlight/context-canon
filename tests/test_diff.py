from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.diff import diff_compiled
from contextcanon.parser import ContextCanonError


FOUNDATION = '''# Demo Foundation — Local Context Source
<!-- ctx:node id="node-foundation" version="1.0.0" -->

## Rules

### Policy

- **Keep behavior stable:** Preserve the original behavior.
  Why: Consumers rely on this contract.
  <!-- ctx:rule id="F-001" -->
'''

PROJECT = '''# Demo Project — Local Context Source
<!-- ctx:node id="node-project" version="1.0.0" -->

## Sources

- [Demo Foundation](nodes/foundation/) — `1.0.0`
  <!-- ctx:source id="node-foundation" version="1.0.0" -->

## Topics

### Guidance

When changing exported output:

Required:
- Resource: `docs/guide.md`
<!-- ctx:topic id="P-GUIDE" -->
'''

REMOVE = '''

## Changes

### Remove

- `Demo Foundation / F-001` — Keep behavior stable
  Why: This project deliberately replaces that inherited contract.
  <!-- ctx:change op="remove" source-id="node-foundation" rule-id="F-001" -->
'''


class ContextDiffTests(unittest.TestCase):
    def make_repo(
        self,
        *,
        project: str = PROJECT,
        foundation: str = FOUNDATION,
        guide: str = "# Guide\n\nOriginal guidance.\n",
    ) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "docs").mkdir()
        (root / "docs/guide.md").write_text(guide, encoding="utf-8")
        (root / "CONTEXT.src.md").write_text(project, encoding="utf-8")
        source = root / "nodes/foundation"
        source.mkdir(parents=True)
        (source / "CONTEXT.src.md").write_text(foundation, encoding="utf-8")
        return root

    def compile(self, root: Path):
        return Compiler(root).compile(root)

    def test_identical_compiled_context_has_empty_diff(self):
        before_root = self.make_repo()
        after_root = self.make_repo()

        result = diff_compiled(self.compile(before_root), self.compile(after_root))

        self.assertTrue(result.is_empty)
        self.assertEqual(result.entries, ())
        self.assertEqual(result.to_json(), result.to_json())
        payload = json.loads(result.to_json())
        self.assertEqual(payload["schema"], "contextcanon/diff/v0")
        self.assertFalse(payload["changed"])

    def test_detects_node_source_rule_topic_and_resource_changes(self):
        before_root = self.make_repo()
        changed_foundation = FOUNDATION.replace(
            "Preserve the original behavior.",
            "Preserve the revised behavior.",
        )
        changed_project = PROJECT.replace(
            'version="1.0.0"',
            'version="1.1.0"',
            1,
        ).replace(
            "When changing exported output:",
            "When changing exported output or archive layout:",
        )
        after_root = self.make_repo(
            project=changed_project,
            foundation=changed_foundation,
            guide="# Guide\n\nRevised guidance.\n",
        )

        result = diff_compiled(self.compile(before_root), self.compile(after_root))
        entries = {(entry.category, entry.identity): entry for entry in result.entries}

        self.assertFalse(result.is_empty)
        self.assertIn(("node", "node-project"), entries)
        self.assertEqual(entries[("node", "node-project")].changed_fields, ("version",))

        self.assertIn(("source", "node-foundation"), entries)
        self.assertIn("package_digest", entries[("source", "node-foundation")].changed_fields)

        rule_key = "node-foundation#F-001"
        self.assertIn(("rule", rule_key), entries)
        self.assertIn("statement", entries[("rule", rule_key)].changed_fields)

        topic_key = "node-project#P-GUIDE"
        self.assertIn(("topic", topic_key), entries)
        self.assertIn("condition", entries[("topic", topic_key)].changed_fields)

        resource_key = "CONTEXT/references/docs/guide.md"
        self.assertIn(("resource", resource_key), entries)
        self.assertIn("sha256", entries[("resource", resource_key)].changed_fields)

    def test_active_rule_to_removed_rule_is_one_state_transition(self):
        before_root = self.make_repo()
        after_root = self.make_repo(project=PROJECT + REMOVE)

        result = diff_compiled(self.compile(before_root), self.compile(after_root))
        rule_entries = [entry for entry in result.entries if entry.category == "rule"]
        change_entries = [entry for entry in result.entries if entry.category == "change"]

        self.assertEqual(len(rule_entries), 1)
        rule = rule_entries[0]
        self.assertEqual(rule.change, "modified")
        self.assertEqual(rule.identity, "node-foundation#F-001")
        self.assertEqual(rule.before["status"], "active")
        self.assertEqual(rule.after["status"], "removed")
        self.assertIn("status", rule.changed_fields)

        self.assertEqual(len(change_entries), 1)
        self.assertEqual(change_entries[0].change, "added")
        self.assertEqual(change_entries[0].identity, "node-foundation#F-001")

    def test_different_node_ids_fail_clearly(self):
        before_root = self.make_repo()
        after_root = self.make_repo(project=PROJECT.replace("node-project", "other-project", 1))

        with self.assertRaisesRegex(ContextCanonError, "Cannot diff different Context Nodes"):
            diff_compiled(self.compile(before_root), self.compile(after_root))

    def test_json_cli_is_deterministic_and_uses_diff_exit_codes(self):
        before_root = self.make_repo()
        after_root = self.make_repo(guide="# Guide\n\nChanged.\n")

        first = io.StringIO()
        with contextlib.redirect_stdout(first):
            changed_code = main(["diff", str(before_root), str(after_root), "--json"])
        second = io.StringIO()
        with contextlib.redirect_stdout(second):
            repeated_code = main(["diff", str(before_root), str(after_root), "--json"])

        self.assertEqual(changed_code, 1)
        self.assertEqual(repeated_code, 1)
        self.assertEqual(first.getvalue(), second.getvalue())
        payload = json.loads(first.getvalue())
        self.assertTrue(payload["changed"])
        self.assertEqual(payload["entries"][0]["category"], "resource")

        same = io.StringIO()
        with contextlib.redirect_stdout(same):
            same_code = main(["diff", str(before_root), str(before_root), "--json"])
        self.assertEqual(same_code, 0)
        self.assertFalse(json.loads(same.getvalue())["changed"])


if __name__ == "__main__":
    unittest.main()
