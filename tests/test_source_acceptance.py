from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.package import artifact_files
from contextcanon.parser import ContextCanonError
from contextcanon.sources import accept_source_candidate, review_source_candidate


PROVIDER_TEMPLATE = '''# Shared Python Development — Local Context Source
<!-- ctx:node id="node-python" version="{version}" -->

## Rules

### Python

{rule}
'''

RULE_TEMPLATE = '''- **Use explicit Python:** {statement}
  Why: Consumers need predictable implementation behavior.
  <!-- ctx:rule id="PY-001" -->
'''

CONSUMER_TEMPLATE = '''# Demo Consumer — Local Context Source
<!-- ctx:node id="node-consumer" version="0.1.0" -->

## Sources

- [Shared Python Development](https://example.invalid/shared-python) — `{version}`
  <!-- ctx:source id="node-python" version="{version}" normalized-digest="{normalized}" package-digest="{package}" -->

## Changes

### Override

- `Shared Python Development / PY-001` — Use explicit Python
  New rule: Keep explicit Python and preserve the consumer command contract.
  Why: The consumer narrows the generic Python rule.
  <!-- ctx:change op="override" source-id="node-python" rule-id="PY-001" -->
'''


class SourceAcceptanceTests(unittest.TestCase):
    def make_provider(self, version: str, statement: str | None):
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        rule = "" if statement is None else RULE_TEMPLATE.format(statement=statement)
        (root / "CONTEXT.src.md").write_text(
            PROVIDER_TEMPLATE.format(version=version, rule=rule),
            encoding="utf-8",
        )
        compiled = Compiler(root).compile(root)
        artifact = Path(tempfile.mkdtemp())
        for rel, content in artifact_files(compiled).items():
            path = artifact / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return root, compiled, artifact

    def make_consumer(self, accepted) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(
            CONSUMER_TEMPLATE.format(
                version=accepted.metadata.version,
                normalized=accepted.normalized_digest,
                package=accepted.package_digest,
            ),
            encoding="utf-8",
        )
        self.install_package(root, accepted)
        return root

    def install_package(self, consumer: Path, compiled) -> None:
        destination = consumer / ".context" / "sources" / compiled.package_digest
        for rel, content in artifact_files(compiled).items():
            path = destination / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def test_review_then_accept_updates_pin_store_and_offline_build(self):
        provider1, v1, _ = self.make_provider("1.0.0", "Prefer explicit Python v1.")
        provider2, v2, candidate = self.make_provider("2.0.0", "Prefer explicit Python v2.")
        consumer = self.make_consumer(v1)

        shutil.rmtree(provider1)
        shutil.rmtree(provider2)

        diff, receipt = review_source_candidate(consumer, "node-python", candidate)
        self.assertTrue(receipt.is_file())
        self.assertFalse(diff.is_empty)
        self.assertEqual(diff.before_version, "1.0.0")
        self.assertEqual(diff.after_version, "2.0.0")
        rule_entries = [entry for entry in diff.entries if entry.category == "rule"]
        self.assertEqual(len(rule_entries), 1)
        self.assertEqual(rule_entries[0].identity, "node-python#PY-001")
        self.assertIn("statement", rule_entries[0].changed_fields)

        accepted = accept_source_candidate(consumer, "node-python", candidate)
        self.assertEqual(accepted.package_digest, v2.package_digest)
        self.assertTrue((consumer / ".context/sources" / v2.package_digest / ".context/package.json").is_file())

        source_text = (consumer / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("— `2.0.0`", source_text)
        self.assertIn(f'version="2.0.0"', source_text)
        self.assertIn(f'normalized-digest="{v2.normalized_digest}"', source_text)
        self.assertIn(f'package-digest="{v2.package_digest}"', source_text)

        compiled = Compiler(consumer).compile(consumer)
        self.assertEqual(compiled.source_packages[0].metadata.version, "2.0.0")
        self.assertEqual(compiled.source_packages[0].package_digest, v2.package_digest)
        inherited = compiled.inherited_rules[0]
        self.assertEqual(inherited.origin_node_id, "node-python")
        self.assertEqual(inherited.statement, "Keep explicit Python and preserve the consumer command contract.")

    def test_accept_requires_matching_review_receipt(self):
        _, v1, _ = self.make_provider("1.0.0", "Prefer explicit Python v1.")
        _, _, candidate = self.make_provider("2.0.0", "Prefer explicit Python v2.")
        consumer = self.make_consumer(v1)

        with self.assertRaisesRegex(ContextCanonError, "run 'contextcanon source review' first"):
            accept_source_candidate(consumer, "node-python", candidate)

    def test_source_change_after_review_invalidates_receipt(self):
        _, v1, _ = self.make_provider("1.0.0", "Prefer explicit Python v1.")
        _, _, candidate = self.make_provider("2.0.0", "Prefer explicit Python v2.")
        consumer = self.make_consumer(v1)
        review_source_candidate(consumer, "node-python", candidate)

        source_path = consumer / "CONTEXT.src.md"
        source_path.write_text(source_path.read_text(encoding="utf-8") + "\n<!-- reviewed source changed -->\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "changed after Source review"):
            accept_source_candidate(consumer, "node-python", candidate)

    def test_review_rejects_candidate_that_makes_local_change_dangling(self):
        _, v1, _ = self.make_provider("1.0.0", "Prefer explicit Python v1.")
        _, _, candidate = self.make_provider("2.0.0", None)
        consumer = self.make_consumer(v1)

        with self.assertRaisesRegex(ContextCanonError, "targets missing inherited Rule"):
            review_source_candidate(consumer, "node-python", candidate)

    def test_failed_atomic_pin_replace_preserves_old_source_and_old_build(self):
        _, v1, _ = self.make_provider("1.0.0", "Prefer explicit Python v1.")
        _, v2, candidate = self.make_provider("2.0.0", "Prefer explicit Python v2.")
        consumer = self.make_consumer(v1)
        review_source_candidate(consumer, "node-python", candidate)

        # Preinstall the candidate so the simulated os.replace failure below
        # exercises only publication of the canonical Source pin. A failed pin
        # swap may leave an unreferenced immutable package, but must never
        # damage or partially update CONTEXT.src.md.
        self.install_package(consumer, v2)
        source_path = consumer / "CONTEXT.src.md"
        original = source_path.read_bytes()

        with patch("contextcanon.sources.os.replace", side_effect=OSError("simulated replace failure")):
            with self.assertRaisesRegex(ContextCanonError, "Could not atomically write"):
                accept_source_candidate(consumer, "node-python", candidate)

        self.assertEqual(source_path.read_bytes(), original)
        self.assertEqual(list(consumer.glob(".CONTEXT.src.md.*.tmp")), [])

        compiled = Compiler(consumer).compile(consumer)
        self.assertEqual(compiled.source_packages[0].metadata.version, "1.0.0")
        self.assertEqual(compiled.source_packages[0].package_digest, v1.package_digest)
        self.assertTrue((consumer / ".context/sources" / v2.package_digest).is_dir())


if __name__ == "__main__":
    unittest.main()
