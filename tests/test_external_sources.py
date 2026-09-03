from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.package import artifact_files
from contextcanon.parser import ContextCanonError, parse_node


SOURCE = '''# Shared Python Development — Local Context Source
<!-- ctx:node id="node-python" version="1.2.0" -->

## Rules

### Python

- **Use explicit Python:** Prefer explicit, deterministic Python over hidden magic.
  Why: Consumers need predictable implementation behavior.
  <!-- ctx:rule id="PY-001" -->

## Topics

### Python guide

When changing Python implementation details:

Required:
- Resource: `guide.md`
<!-- ctx:topic id="PY-GUIDE" -->
'''

CONSUMER_TEMPLATE = '''# Demo Consumer — Local Context Source
<!-- ctx:node id="node-consumer" version="0.1.0" -->

## Sources

- [Shared Python Development](https://example.invalid/shared-python) — `1.2.0`
  <!-- ctx:source id="node-python" version="1.2.0" normalized-digest="{normalized}" package-digest="{package}" -->

## Changes

### Override

- `Shared Python Development / PY-001` — Use explicit Python
  New rule: Prefer explicit, deterministic Python and keep this consumer's command surface small.
  Why: The consumer has a narrower operational contract.
  <!-- ctx:change op="override" source-id="node-python" rule-id="PY-001" -->
'''


class ExternalSourceTests(unittest.TestCase):
    def make_provider(self):
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(SOURCE, encoding="utf-8")
        (root / "guide.md").write_text("# Python Guide\n\nKeep implementation explicit.\n", encoding="utf-8")
        return root, Compiler(root).compile(root)

    def make_consumer(self, normalized: str, package: str) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(
            CONSUMER_TEMPLATE.format(normalized=normalized, package=package),
            encoding="utf-8",
        )
        return root

    def install_accepted_package(self, consumer: Path, compiled) -> Path:
        destination = consumer / ".context" / "sources" / compiled.package_digest
        for rel, content in artifact_files(compiled).items():
            path = destination / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return destination

    def test_pinned_source_composes_offline_without_dereferencing_locator(self):
        provider_root, source = self.make_provider()
        consumer = self.make_consumer(source.normalized_digest, source.package_digest)
        self.install_accepted_package(consumer, source)

        shutil.rmtree(provider_root)
        compiled = Compiler(consumer).compile(consumer)

        self.assertEqual(len(compiled.source_packages), 1)
        accepted = compiled.source_packages[0]
        self.assertEqual(accepted.metadata.id, "node-python")
        self.assertEqual(accepted.normalized_digest, source.normalized_digest)
        self.assertEqual(accepted.package_digest, source.package_digest)
        self.assertEqual(compiled.parsed.sources[0].locator, "https://example.invalid/shared-python")

        self.assertEqual([rule.id for rule in compiled.inherited_rules], ["PY-001"])
        inherited = compiled.inherited_rules[0]
        self.assertEqual(inherited.origin_node_id, "node-python")
        self.assertIn("keep this consumer's command surface small", inherited.statement)
        self.assertEqual([mod.node_id for mod in inherited.modifications], ["node-consumer"])

        self.assertEqual([topic.id for topic in compiled.inherited_topics], ["PY-GUIDE"])
        self.assertIn("CONTEXT/references/node-python/guide.md", compiled.resources)
        self.assertEqual(compiled.resources["CONTEXT/references/node-python/guide.md"], b"# Python Guide\n\nKeep implementation explicit.\n")
        self.assertIn("Rules from Shared Python Development", compiled.official_markdown)
        self.assertIn("Topics from Shared Python Development", compiled.official_markdown)
        self.assertIn(source.normalized_digest, compiled.package_manifest)
        self.assertIn(source.package_digest, compiled.package_manifest)
        self.assertIn(source.package_digest, compiled.machine_yaml)

    def test_pinned_source_missing_from_store_fails_without_fetching(self):
        _, source = self.make_provider()
        consumer = self.make_consumer(source.normalized_digest, source.package_digest)

        with self.assertRaisesRegex(ContextCanonError, "build does not fetch Source packages"):
            Compiler(consumer).compile(consumer)

    def test_pinned_source_normalized_digest_must_match_accepted_package(self):
        _, source = self.make_provider()
        consumer = self.make_consumer("0" * 64, source.package_digest)
        self.install_accepted_package(consumer, source)

        with self.assertRaisesRegex(ContextCanonError, "normalized digest mismatch"):
            Compiler(consumer).compile(consumer)

    def test_source_pin_requires_both_digests(self):
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        text = '''# Invalid Consumer — Local Context Source
<!-- ctx:node id="node-consumer" version="0.1.0" -->

## Sources

- [Shared Python Development](https://example.invalid/shared-python) — `1.2.0`
  <!-- ctx:source id="node-python" version="1.2.0" normalized-digest="''' + ("0" * 64) + '''" -->
'''
        (root / "CONTEXT.src.md").write_text(text, encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "needs both normalized-digest and package-digest"):
            parse_node(root, root)


if __name__ == "__main__":
    unittest.main()
