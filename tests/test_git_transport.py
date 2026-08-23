from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.git_transport import fetch_git_candidate
from contextcanon.outputs import write_outputs
from contextcanon.package import artifact_files
from contextcanon.parser import ContextCanonError, parse_node
from contextcanon.sources import accept_source_candidate, review_source_candidate


PROVIDER_TEMPLATE = '''# Shared Python Development — Local Context Source
<!-- ctx:node id="node-python" version="{version}" -->

## Rules

### Python

- **Use explicit Python:** {statement}
  Why: Consumers need stable Python guidance.
  <!-- ctx:rule id="PY-001" -->
'''

CONSUMER_TEMPLATE = '''# Demo Consumer — Local Context Source
<!-- ctx:node id="node-consumer" version="0.1.0" -->

## Sources

- [Shared Python Development]({locator}) — `{version}`
  <!-- ctx:source id="node-python" version="{version}" normalized-digest="{normalized}" package-digest="{package}" transport="git" ref="main" node-path="nodes/library/python-development" -->
'''


class GitTransportTests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def make_provider(self):
        root = Path(tempfile.mkdtemp())
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.email", "contextcanon@example.invalid")
        self.git(root, "config", "user.name", "ContextCanon Tests")

        node = root / "nodes/library/python-development"
        node.mkdir(parents=True)
        source = node / "CONTEXT.src.md"
        source.write_text(
            PROVIDER_TEMPLATE.format(version="1.0.0", statement="Prefer explicit Python v1."),
            encoding="utf-8",
        )
        compiler1 = Compiler(root)
        v1 = compiler1.compile(node)
        write_outputs(v1)
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "Publish Python context v1")

        source.write_text(
            PROVIDER_TEMPLATE.format(version="2.0.0", statement="Prefer explicit Python v2."),
            encoding="utf-8",
        )
        compiler2 = Compiler(root)
        v2 = compiler2.compile(node)
        write_outputs(v2)
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "Publish Python context v2")
        return root, v1, v2

    def make_consumer(self, provider: Path, accepted) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(
            CONSUMER_TEMPLATE.format(
                locator=provider.as_posix(),
                version=accepted.metadata.version,
                normalized=accepted.normalized_digest,
                package=accepted.package_digest,
            ),
            encoding="utf-8",
        )
        accepted_root = root / ".context/sources" / accepted.package_digest
        for rel, content in artifact_files(accepted).items():
            path = accepted_root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return root

    def test_git_fetch_is_candidate_only_until_reviewed_accept(self):
        provider, v1, v2 = self.make_provider()
        consumer = self.make_consumer(provider, v1)

        before = Compiler(consumer).compile(consumer)
        self.assertEqual(before.source_packages[0].metadata.version, "1.0.0")
        self.assertEqual(before.source_packages[0].package_digest, v1.package_digest)
        self.assertEqual(before.inherited_rules[0].statement, "Prefer explicit Python v1.")

        candidate, candidate_root = fetch_git_candidate(consumer, "node-python")
        self.assertEqual(candidate.metadata.version, "2.0.0")
        self.assertEqual(candidate.package_digest, v2.package_digest)
        self.assertEqual(
            candidate_root,
            consumer / ".context/candidates" / v2.package_digest,
        )
        self.assertTrue((candidate_root / ".context/package.json").is_file())

        still_before = Compiler(consumer).compile(consumer)
        self.assertEqual(still_before.source_packages[0].metadata.version, "1.0.0")
        self.assertEqual(still_before.inherited_rules[0].statement, "Prefer explicit Python v1.")

        diff, receipt = review_source_candidate(consumer, "node-python", candidate_root)
        self.assertFalse(diff.is_empty)
        self.assertTrue(receipt.is_file())
        accept_source_candidate(consumer, "node-python", candidate_root)

        text = (consumer / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("— `2.0.0`", text)
        self.assertIn(f'package-digest="{v2.package_digest}"', text)
        self.assertIn('transport="git"', text)
        self.assertIn('ref="main"', text)
        self.assertIn('node-path="nodes/library/python-development"', text)

        after = Compiler(consumer).compile(consumer)
        self.assertEqual(after.source_packages[0].metadata.version, "2.0.0")
        self.assertEqual(after.source_packages[0].package_digest, v2.package_digest)
        self.assertEqual(after.inherited_rules[0].statement, "Prefer explicit Python v2.")

    def test_git_fetch_rejects_missing_node_path(self):
        provider, v1, _ = self.make_provider()
        consumer = self.make_consumer(provider, v1)
        path = consumer / "CONTEXT.src.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                'node-path="nodes/library/python-development"',
                'node-path="nodes/library/missing"',
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ContextCanonError, "node-path does not exist"):
            fetch_git_candidate(consumer, "node-python")

    def test_git_fetch_rejects_unknown_ref(self):
        provider, v1, _ = self.make_provider()
        consumer = self.make_consumer(provider, v1)
        path = consumer / "CONTEXT.src.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace('ref="main"', 'ref="does-not-exist"'),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ContextCanonError, "Git Source fetch failed"):
            fetch_git_candidate(consumer, "node-python")

    def test_transport_metadata_is_all_or_nothing_and_node_path_is_safe(self):
        provider, v1, _ = self.make_provider()
        consumer = self.make_consumer(provider, v1)
        path = consumer / "CONTEXT.src.md"

        incomplete = path.read_text(encoding="utf-8").replace(' ref="main"', "")
        path.write_text(incomplete, encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "transport metadata is incomplete"):
            parse_node(consumer, consumer)

        path.write_text(
            CONSUMER_TEMPLATE.format(
                locator=provider.as_posix(),
                version=v1.metadata.version,
                normalized=v1.normalized_digest,
                package=v1.package_digest,
            ).replace(
                'node-path="nodes/library/python-development"',
                'node-path="../python-development"',
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "invalid Git Source node-path"):
            parse_node(consumer, consumer)


if __name__ == "__main__":
    unittest.main()
