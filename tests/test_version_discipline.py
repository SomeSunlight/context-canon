from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.outputs import write_outputs
from contextcanon.parser import ContextCanonError, parse_node
from contextcanon.sources import install_source_package, review_source_candidate
from contextcanon.versioning import minimum_patch_bump


def node_text(version: str, statement: str) -> str:
    return (
        '# Demo — Local Context Source\n'
        f'<!-- ctx:node id="demo" name="Demo" version="{version}" -->\n\n'
        '## Local Rules\n\n### General\n\n'
        f'- **Rule:** {statement}\n  Why: Test.\n  <!-- ctx:rule id="R1" -->\n'
    )


def make_repo(version: str = "1.2.3-draft") -> Path:
    root = Path(tempfile.mkdtemp())
    (root / ".git").mkdir()
    (root / "CONTEXT.src.md").write_text(node_text(version, "Before."), encoding="utf-8")
    write_outputs(Compiler(root).compile(root))
    return root


class VersionDisciplineTests(unittest.TestCase):
    def test_minimum_patch_bump_preserves_suffix(self):
        self.assertEqual(minimum_patch_bump("0.2.0-draft"), "0.2.1-draft")
        self.assertEqual(minimum_patch_bump("1.9.9"), "1.9.10")
        self.assertIsNone(minimum_patch_bump("summer-preview"))

    def test_build_auto_bumps_reused_semver_and_advises_higher_version(self):
        root = make_repo()
        (root / "CONTEXT.src.md").write_text(node_text("1.2.3-draft", "After."), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = main(["build", str(root)])
        self.assertEqual(rc, 0)
        self.assertEqual(parse_node(root).metadata.version, "1.2.4-draft")
        self.assertIn("Auto-bumped Context Node version: 1.2.3-draft -> 1.2.4-draft", out.getvalue())
        self.assertIn("consider a higher minor or major version", out.getvalue())
        self.assertEqual(main(["check", str(root)]), 0)

    def test_build_preserves_human_selected_higher_version(self):
        root = make_repo()
        (root / "CONTEXT.src.md").write_text(node_text("2.0.0", "After."), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = main(["build", str(root)])
        self.assertEqual(rc, 0)
        self.assertEqual(parse_node(root).metadata.version, "2.0.0")
        self.assertNotIn("Auto-bumped", out.getvalue())

    def test_non_semver_reuse_requires_manual_version_change(self):
        root = make_repo("summer-preview")
        (root / "CONTEXT.src.md").write_text(node_text("summer-preview", "After."), encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = main(["build", str(root)])
        self.assertEqual(rc, 2)
        self.assertIn("cannot be patch-bumped safely", err.getvalue())

    def test_source_review_rejects_changed_package_with_reused_version(self):
        consumer = Path(tempfile.mkdtemp())
        provider_before = Path(tempfile.mkdtemp())
        provider_after = Path(tempfile.mkdtemp())
        (consumer / ".git").mkdir()
        for root, statement in ((provider_before, "Before."), (provider_after, "After.")):
            (root / ".git").mkdir()
            (root / "CONTEXT.src.md").write_text(node_text("1.0.0", statement), encoding="utf-8")
            write_outputs(Compiler(root).compile(root))

        before = Compiler(provider_before).compile(provider_before)
        consumer_text = (
            '# Consumer\n<!-- ctx:node id="consumer" name="Consumer" version="0.1.0" -->\n\n'
            '## Sources\n\n'
            '- [Demo](provider) — `1.0.0`\n'
            f'  <!-- ctx:source id="demo" version="1.0.0" normalized-digest="{before.normalized_digest}" package-digest="{before.package_digest}" -->\n'
        )
        (consumer / "CONTEXT.src.md").write_text(consumer_text, encoding="utf-8")
        install_source_package(consumer, provider_before)
        with self.assertRaisesRegex(ContextCanonError, "reused version"):
            review_source_candidate(consumer, "demo", provider_after)


if __name__ == "__main__":
    unittest.main()
