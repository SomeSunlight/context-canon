from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from contextcanon.compiler import Compiler
from contextcanon.diff import diff_compiled
from contextcanon.outputs import write_outputs
from contextcanon.package import artifact_files, compiled_package, export_digest, load_package, load_package_files
from contextcanon.package_diff import diff_packages
from contextcanon.parser import ContextCanonError, parse_node
from contextcanon.resources import move_resource, reconcile_resource, register_resources


class ResourceNotesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def node(self, name: str = "Demo", targets: str | None = None) -> Path:
        root = self.repo / name
        root.mkdir()
        (root / "example.jsonc").write_text("// payload\n{}\n", encoding="utf-8")
        targets = targets if targets is not None else (
            '- Resource: `example.jsonc`\n'
            '  Why: Version 6 - VALID\n'
            '  <!-- ctx:resource id="RESOURCE-EXAMPLE" -->\n'
        )
        (root / "CONTEXT.src.md").write_text(
            f'# {name}\n<!-- ctx:node id="node-{name}" name="{name}" version="1.0.0" -->\n\n'
            '## Local Topics\n\n### Samples\n\nWhen comparing payload shapes:\n\n'
            f'Required:\n{targets}<!-- ctx:topic id="SAMPLES" -->\n',
            encoding="utf-8",
        )
        return root

    def test_why_before_or_after_identity_and_legacy_path_only(self) -> None:
        targets = (
            '- Resource: `example.jsonc`\n  Why: Version 6 - VALID\n'
            '- Resource: `example.jsonc`\n  Why: OBSOLETE\n'
            '  <!-- ctx:resource id="RESOURCE-EXAMPLE" -->\n'
            '- Resource: `example.jsonc`\n'
            '  <!-- ctx:resource id="RESOURCE-EXAMPLE" -->\n  Why: Comparison only (legacy)\n'
            'Optional:\n- Resource: `example.jsonc`\n'
        )
        root = self.node(targets=targets)
        parsed = parse_node(root)
        self.assertEqual([t.why for t in parsed.topics[0].targets],
                         ["Version 6 - VALID", "OBSOLETE", "Comparison only (legacy)", None])
        self.assertEqual([t.resource_id for t in parsed.topics[0].targets],
                         [None, "RESOURCE-EXAMPLE", "RESOURCE-EXAMPLE", None])
        compiled = Compiler(self.repo).compile(root)
        self.assertIn("\n  Why: OBSOLETE\n", compiled.official_markdown)
        self.assertEqual([t.intent for t in compiled.local_topics[0].targets],
                         ["required", "required", "required", "optional"])
        machine_targets = yaml.safe_load(compiled.machine_yaml)["targets"]
        self.assertEqual([t.get("why") for t in machine_targets],
                         ["Version 6 - VALID", "OBSOLETE", "Comparison only (legacy)", None])

    def test_rejects_misplaced_empty_duplicate_and_trailing_explanations(self) -> None:
        root = self.node()
        for targets in (
            '  Why: Orphan\n- Resource: `example.jsonc`\n',
            '- Resource: `example.jsonc`\nWhy: Not indented\n',
            '- Resource: `example.jsonc`\n  Why: \n',
            '- Resource: `example.jsonc`\n  Why: A\n  Why: B\n',
            '- Resource: `example.jsonc`\nOptional:\n  Why: Wrong group\n',
            '- Resource: `example.jsonc` (OBSOLETE)\n',
            '- Resource: `example.jsonc` free text\n',
            '- Context Node: `../other`\n  Why: Resource only\n',
        ):
            with self.subTest(targets=targets):
                source = (root / "CONTEXT.src.md").read_text(encoding="utf-8")
                source = source[:source.index("Required:")] + f'Required:\n{targets}<!-- ctx:topic id="SAMPLES" -->\n'
                with self.assertRaises(ContextCanonError):
                    parse_node(root, source_text=source)

    def test_package_roundtrip_and_why_only_review(self) -> None:
        root = self.node()
        before = Compiler(self.repo).compile(root)
        before_package = load_package_files(artifact_files(before))
        self.assertEqual(before_package.topics[0].targets[0].why, "Version 6 - VALID")
        source = root / "CONTEXT.src.md"
        source.write_text(source.read_text(encoding="utf-8").replace("Version 6 - VALID", "OBSOLETE"), encoding="utf-8")
        after = Compiler(self.repo).compile(root)
        after_package = load_package_files(artifact_files(after))
        self.assertNotEqual(before.normalized_digest, after.normalized_digest)
        self.assertNotEqual(export_digest(before_package), export_digest(after_package))
        self.assertEqual(before.resources, after.resources)
        for result in (diff_compiled(before, after), diff_packages(before_package, after_package)):
            self.assertEqual([(e.category, e.change) for e in result.entries], [("topic", "modified")])
            self.assertEqual(result.entries[0].after["targets"][0]["why"], "OBSOLETE")

    def test_package_rejects_invalid_or_tampered_why(self) -> None:
        compiled = Compiler(self.repo).compile(self.node())
        original = artifact_files(compiled)
        for why in (42, "", "  ", "one\ntwo", "one\n", "Changed without a matching digest"):
            with self.subTest(why=why):
                files = dict(original)
                manifest = json.loads(files[".context/package.json"])
                manifest["topics"][0]["targets"][0]["why"] = why
                files[".context/package.json"] = json.dumps(manifest).encode("utf-8")
                with self.assertRaises(ContextCanonError):
                    load_package_files(files)

    def test_reordering_explanations_keeps_canonical_identity(self) -> None:
        first = '- Resource: `example.jsonc`\n  Why: Current format\n'
        second = '- Resource: `example.jsonc`\n  Why: Historical comparison\n'
        root = self.node(targets=first + second)
        before = Compiler(self.repo).compile(root)
        source = root / "CONTEXT.src.md"
        source.write_text(source.read_text(encoding="utf-8").replace(first + second, second + first), encoding="utf-8")
        after = Compiler(self.repo).compile(root)
        self.assertEqual(before.normalized_digest, after.normalized_digest)
        self.assertNotEqual(before.package_digest, after.package_digest)
        self.assertEqual(diff_compiled(before, after).entries, ())
        self.assertEqual(diff_packages(compiled_package(before), compiled_package(after)).entries, ())

    def test_register_move_and_reconcile_preserve_why_and_identity(self) -> None:
        for identified in (False, True):
            with self.subTest(identified=identified):
                targets = '- Resource: `example.jsonc`\n  Why: OBSOLETE\n'
                if identified:
                    targets += '  <!-- ctx:resource id="RESOURCE-EXAMPLE" -->\n'
                root = self.node(str(identified), targets)
                result = register_resources(root)
                self.assertEqual(result.added, 0 if identified else 1)
                target = parse_node(root).topics[0].targets[0]
                identity = target.resource_id
                self.assertIsNotNone(identity)
                self.assertEqual(target.why, "OBSOLETE")
                write_outputs(Compiler(self.repo).compile(root))
                move_resource(self.repo, root / "example.jsonc", root / "moved.jsonc")
                target = parse_node(root).topics[0].targets[0]
                self.assertEqual((target.locator, target.resource_id, target.why), ("moved.jsonc", identity, "OBSOLETE"))
                write_outputs(Compiler(self.repo).compile(root))
                (root / "moved.jsonc").rename(root / "external.jsonc")
                reconcile_resource(self.repo, root / "moved.jsonc", root / "external.jsonc")
                target = parse_node(root).topics[0].targets[0]
                self.assertEqual((target.locator, target.resource_id, target.why), ("external.jsonc", identity, "OBSOLETE"))

    def test_offline_parent_and_reference_keep_explanations(self) -> None:
        provider = self.node("Provider")
        package = compiled_package(Compiler(self.repo).compile(provider))
        files = artifact_files(Compiler(self.repo).compile(provider))
        consumers = []
        for relationship in ("parent", "reference"):
            root = self.repo / relationship
            root.mkdir()
            (root / "CONTEXT.src.md").write_text(
                f'# Consumer\n<!-- ctx:node id="node-{relationship}" name="Consumer" version="1.0.0" -->\n\n'
                '## Context Imports\n\n'
                f'- [Provider](../Provider/) — `1.0.0` — `relationship={relationship}`\n'
                f'  <!-- ctx:source id="node-Provider" version="1.0.0" normalized-digest="{package.normalized_digest}" '
                f'package-digest="{package.package_digest}" -->\n', encoding="utf-8")
            store = root / ".context" / "sources" / package.package_digest
            for path, content in files.items():
                destination = store / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
            self.assertEqual(load_package(store).topics[0].targets[0].why, "Version 6 - VALID")
            consumers.append((root, relationship))
        shutil.rmtree(provider)
        for root, relationship in consumers:
            with self.subTest(relationship=relationship):
                compiled = Compiler(self.repo).compile(root)
                self.assertIn("Why: Version 6 - VALID", compiled.official_markdown)
                self.assertEqual(len(compiled.inherited_topics), 1 if relationship == "parent" else 0)
                self.assertEqual(len(compiled_package(compiled).topics), 1 if relationship == "parent" else 0)


if __name__ == "__main__":
    unittest.main()
