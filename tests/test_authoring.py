from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.parser import parse_node


class AuthoringTests(unittest.TestCase):
    def make_node(self) -> Path:
        root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        (root / "CONTEXT.src.md").write_text(
            "# Example — Local Context Source\n"
            '<!-- ctx:node id="example-node" version="0.1.0" -->\n',
            encoding="utf-8",
        )
        return root

    def test_author_rule_allocates_identity_and_writes_normal_source(self):
        root = self.make_node()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([
                "author", "rule", str(root),
                "--group", "Security",
                "--title", "Keep secrets out of Git",
                "--statement", "Credentials stay outside version control.",
                "--why", "Version control is not a secret store.",
            ])
        self.assertEqual(result, 0)
        parsed = parse_node(root)
        self.assertEqual(len(parsed.rules), 1)
        rule = parsed.rules[0]
        self.assertTrue(rule.id.startswith("RULE-"))
        self.assertEqual(rule.group, "Security")
        text = (root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn(f'<!-- ctx:rule id="{rule.id}" -->', text)
        self.assertIn("Next: contextcanon build", stdout.getvalue())

    def test_author_topic_allocates_identity_and_preserves_typed_targets(self):
        root = self.make_node()
        (root / "docs").mkdir()
        (root / "docs" / "logging.md").write_text("# Logging\n", encoding="utf-8")
        result = main([
            "author", "topic", str(root),
            "--title", "Logging",
            "--condition", "When changing logging or diagnostics:",
            "--required-resource", "docs/logging.md",
            "--optional-node", "../operations",
        ])
        self.assertEqual(result, 0)
        parsed = parse_node(root)
        self.assertEqual(len(parsed.topics), 1)
        topic = parsed.topics[0]
        self.assertTrue(topic.id.startswith("TOPIC-"))
        self.assertEqual(topic.condition, "When changing logging or diagnostics:")
        self.assertEqual([(target.intent, target.kind, target.locator) for target in topic.targets], [
            ("required", "resource", "docs/logging.md"),
            ("optional", "context-node", "../operations"),
        ])

    def test_author_topic_requires_a_target_without_mutating_source(self):
        root = self.make_node()
        source = root / "CONTEXT.src.md"
        before = source.read_bytes()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main([
                "author", "topic", str(root),
                "--title", "Empty",
                "--condition", "When nothing is linked:",
            ])
        self.assertEqual(result, 2)
        self.assertEqual(source.read_bytes(), before)
        self.assertIn("Topic needs at least one", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
