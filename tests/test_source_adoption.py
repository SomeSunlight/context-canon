from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.package import artifact_files
from contextcanon.parser import ContextCanonError, parse_node
from contextcanon.sources import adopt_source_package
from tests.test_git_transport import GitTransportTests


CONSUMER = '''# AI Workstation — Local Context Source
<!-- ctx:node id="node-consumer" version="0.1.0" -->

## Overview

Already-published onboarding meaning remains untouched.
'''


class SourceAdoptionTests(unittest.TestCase):
    def setUp(self):
        helper = GitTransportTests()
        self.provider, self.v1, self.v2 = helper.make_provider()
        subprocess.run(
            ["git", "remote", "add", "origin", "https://example.test/shared-context.git"],
            cwd=self.provider,
            check=True,
        )
        self.package_root = self.provider / "nodes/library/python-development"
        self.consumer = Path(tempfile.mkdtemp())
        (self.consumer / ".git").mkdir()
        (self.consumer / "CONTEXT.src.md").write_text(CONSUMER, encoding="utf-8")
        acceptance = self.consumer / ".context/onboarding/frozen/placement-acceptance.json"
        acceptance.parent.mkdir(parents=True)
        acceptance.write_text(
            json.dumps({"schema": "legacy-placement", "sources": []}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.acceptance = acceptance
        self.acceptance_before = acceptance.read_bytes()

    def test_explicit_first_adoption_preserves_placement_and_builds_offline(self):
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.provider, check=True, text=True, capture_output=True
        ).stdout.strip()
        adopted, changed = adopt_source_package(self.consumer, self.package_root)
        self.assertTrue(changed)
        self.assertEqual(adopted.package_digest, self.v2.package_digest)
        self.assertEqual(self.acceptance.read_bytes(), self.acceptance_before)

        parsed = parse_node(self.consumer, self.consumer)
        self.assertEqual(len(parsed.sources), 1)
        source = parsed.sources[0]
        self.assertEqual(source.id, "node-python")
        self.assertEqual(source.package_digest, self.v2.package_digest)
        self.assertEqual(source.transport, "git")
        self.assertEqual(source.transport_ref, head)
        self.assertEqual(source.node_path, "nodes/library/python-development")
        self.assertEqual(source.locator, "https://example.test/shared-context.git")
        self.assertTrue((self.consumer / ".context/sources" / self.v2.package_digest).is_dir())

        again, second_changed = adopt_source_package(self.consumer, self.package_root)
        self.assertFalse(second_changed)
        self.assertEqual(again.package_digest, self.v2.package_digest)
        self.assertEqual((self.consumer / "CONTEXT.src.md").read_text(encoding="utf-8").count("ctx:source"), 1)

        shutil.rmtree(self.provider)
        compiled = Compiler(self.consumer).compile(self.consumer)
        self.assertEqual(compiled.source_packages[0].package_digest, self.v2.package_digest)
        self.assertEqual(compiled.inherited_rules[0].statement, "Prefer explicit Python v2.")
        self.assertEqual(self.acceptance.read_bytes(), self.acceptance_before)

    def test_cli_adopt_is_a_single_explicit_operator_action(self):
        self.assertEqual(
            main(["source", "adopt", str(self.package_root), "--node", str(self.consumer)]),
            0,
        )
        compiled = Compiler(self.consumer).compile(self.consumer)
        self.assertEqual(compiled.source_packages[0].package_digest, self.v2.package_digest)

    def test_existing_source_identity_cannot_be_silently_replaced(self):
        adopt_source_package(self.consumer, self.package_root)
        old_package = Path(tempfile.mkdtemp())
        for rel, content in artifact_files(self.v1).items():
            target = old_package / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        before = (self.consumer / "CONTEXT.src.md").read_bytes()
        with self.assertRaisesRegex(ContextCanonError, "already exists with a different accepted package"):
            adopt_source_package(self.consumer, old_package)
        self.assertEqual((self.consumer / "CONTEXT.src.md").read_bytes(), before)

    def test_dirty_package_checkout_is_rejected_before_consumer_mutation(self):
        before = (self.consumer / "CONTEXT.src.md").read_bytes()
        (self.package_root / "CONTEXT.src.md").write_text(
            (self.package_root / "CONTEXT.src.md").read_text(encoding="utf-8") + "\n<!-- dirty -->\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "uncommitted changes"):
            adopt_source_package(self.consumer, self.package_root)
        self.assertEqual((self.consumer / "CONTEXT.src.md").read_bytes(), before)
        self.assertFalse((self.consumer / ".context/sources" / self.v2.package_digest).exists())

    def test_structural_conflict_is_rejected_before_install_or_authoring_change(self):
        source = self.consumer / "CONTEXT.src.md"
        source.write_text(
            CONSUMER
            + "\n## Rules\n\n### Local\n\n"
            + "- **Collision:** Local rule deliberately collides with the Source visible ID.\n"
            + "  Why: Exercise prospective composition validation.\n"
            + '  <!-- ctx:rule id="PY-001" -->\n',
            encoding="utf-8",
        )
        before = source.read_bytes()
        with self.assertRaisesRegex(ContextCanonError, "Visible Rule ID collision"):
            adopt_source_package(self.consumer, self.package_root)
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse((self.consumer / ".context/sources" / self.v2.package_digest).exists())


if __name__ == "__main__":
    unittest.main()
