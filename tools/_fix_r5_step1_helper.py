from pathlib import Path

helper = Path("tools/_block_r5_parent_step1.py")
text = helper.read_text(encoding="utf-8")
start_marker = "def write_tests() -> None:\n"
end_marker = "\ndef complete() -> None:\n"
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("R5 write_tests function boundary not found")

test_source = r'''from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.diff import diff_compiled
from contextcanon.package import artifact_files, load_package
from contextcanon.parser import ContextCanonError, parse_node


PARENT_SOURCE = """# Shared Parent — Local Context Source
<!-- ctx:node id="node-parent" version="1.0.0" -->

## Rules

### Parent policy

- **Carry parent policy:** Parent policy must reach accepted descendants.
  Why: The semantic hierarchy should carry durable higher-level context.
  <!-- ctx:rule id="PARENT-001" -->

## Topics

### Parent guide

When changing inherited parent behavior:

Required:
- Resource: `guide.md`
<!-- ctx:topic id="PARENT-GUIDE" -->
"""


def child_source(normalized: str, package: str, relation: str = "Parent") -> str:
    if relation == "Parent":
        return f"""# Child — Local Context Source
<!-- ctx:node id="node-child" version="0.1.0" -->

## Parent

- [Shared Parent](../parent) — `1.0.0`
  <!-- ctx:parent id="node-parent" version="1.0.0" normalized-digest="{normalized}" package-digest="{package}" -->
"""
    return f"""# Child — Local Context Source
<!-- ctx:node id="node-child" version="0.1.0" -->

## Sources

- [Shared Parent](../parent) — `1.0.0`
  <!-- ctx:source id="node-parent" version="1.0.0" normalized-digest="{normalized}" package-digest="{package}" -->
"""


class ParentRelationshipTests(unittest.TestCase):
    def make_parent(self):
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(PARENT_SOURCE, encoding="utf-8")
        (root / "guide.md").write_text("# Parent Guide\n\nExact inherited bytes.\n", encoding="utf-8")
        return root, Compiler(root).compile(root)

    def make_child(self, normalized: str, package: str, relation: str = "Parent") -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(child_source(normalized, package, relation), encoding="utf-8")
        return root

    def install(self, child: Path, compiled) -> None:
        destination = child / ".context" / "sources" / compiled.package_digest
        for rel, content in artifact_files(compiled).items():
            path = destination / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def package_roundtrip(self, compiled):
        root = Path(tempfile.mkdtemp())
        for rel, content in artifact_files(compiled).items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return load_package(root)

    def test_pinned_parent_composes_offline_and_remains_distinct_from_sources(self):
        provider, parent = self.make_parent()
        child = self.make_child(parent.normalized_digest, parent.package_digest)
        self.install(child, parent)

        shutil.rmtree(provider)
        compiled = Compiler(child).compile(child)

        self.assertIsNotNone(compiled.parsed.parent)
        self.assertIsNotNone(compiled.parent_package)
        self.assertEqual(compiled.parent_package.metadata.id, "node-parent")
        self.assertEqual(compiled.source_packages, [])
        self.assertEqual([rule.id for rule in compiled.inherited_rules], ["PARENT-001"])
        self.assertEqual([topic.id for topic in compiled.inherited_topics], ["PARENT-GUIDE"])
        self.assertEqual(
            compiled.resources["CONTEXT/references/node-parent/guide.md"],
            b"# Parent Guide\n\nExact inherited bytes.\n",
        )
        self.assertIn("**Parent:** Shared Parent", compiled.official_markdown)
        self.assertIn("parent:\n", compiled.machine_yaml)

        package = self.package_roundtrip(compiled)
        self.assertIsNotNone(package.parent)
        self.assertEqual(package.parent.id, "node-parent")
        self.assertEqual(package.sources, ())

    def test_parent_role_is_semantic_not_just_a_source_label(self):
        _, parent = self.make_parent()
        child_as_parent = self.make_child(parent.normalized_digest, parent.package_digest, "Parent")
        child_as_source = self.make_child(parent.normalized_digest, parent.package_digest, "Source")
        self.install(child_as_parent, parent)
        self.install(child_as_source, parent)

        compiled_parent = Compiler(child_as_parent).compile(child_as_parent)
        compiled_source = Compiler(child_as_source).compile(child_as_source)
        self.assertEqual(
            [rule.statement for rule in compiled_parent.inherited_rules],
            [rule.statement for rule in compiled_source.inherited_rules],
        )
        self.assertNotEqual(compiled_parent.normalized_digest, compiled_source.normalized_digest)

    def test_parent_requires_both_exact_digests(self):
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(
            """# Child — Local Context Source
<!-- ctx:node id="node-child" version="0.1.0" -->

## Parent

- [Shared Parent](../parent) — `1.0.0`
  <!-- ctx:parent id="node-parent" version="1.0.0" normalized-digest=""" + ("0" * 64) + """" -->
""",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "Parent must pin both"):
            parse_node(root, root)

    def test_same_node_cannot_be_parent_and_source(self):
        _, parent = self.make_parent()
        child = self.make_child(parent.normalized_digest, parent.package_digest)
        with (child / "CONTEXT.src.md").open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n## Sources\n\n- [Shared Parent](../parent) — `1.0.0`\n"
                f"  <!-- ctx:source id=\"node-parent\" version=\"1.0.0\" normalized-digest=\"{parent.normalized_digest}\" package-digest=\"{parent.package_digest}\" -->\n"
            )
        self.install(child, parent)
        with self.assertRaisesRegex(ContextCanonError, "both semantic Parent and ordinary Source"):
            Compiler(child).compile(child)

    def test_diff_reports_parent_as_parent(self):
        _, parent = self.make_parent()
        before_root = self.make_child(parent.normalized_digest, parent.package_digest, "Source")
        after_root = self.make_child(parent.normalized_digest, parent.package_digest, "Parent")
        self.install(before_root, parent)
        self.install(after_root, parent)
        before = Compiler(before_root).compile(before_root)
        after = Compiler(after_root).compile(after_root)
        diff = diff_compiled(before, after)
        categories = {(entry.category, entry.identity, entry.change) for entry in diff.entries}
        self.assertIn(("source", "node-parent", "removed"), categories)
        self.assertIn(("parent", "node-parent", "added"), categories)


if __name__ == "__main__":
    unittest.main()
'''

replacement = (
    "def write_tests() -> None:\n"
    "    test = " + repr(test_source) + "\n"
    "    Path(\"tests/test_parent_relationship.py\").write_text(test, encoding=\"utf-8\")\n"
)
text = text[:start] + replacement + text[end:]
helper.write_text(text, encoding="utf-8")
