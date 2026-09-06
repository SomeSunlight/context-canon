from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from contextcanon.compiler import Compiler
from contextcanon.package import artifact_files, compiled_package
from contextcanon.parser import ContextCanonError
from contextcanon.sources import review_parent_candidate


class MultiParentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / ".git").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _node(self, rel: str, node_id: str, name: str, rule_id: str, statement: str) -> Path:
        root = self.repo / rel
        root.mkdir(parents=True, exist_ok=True)
        (root / "CONTEXT.src.md").write_text(
            f'''# {name} — Local Context Source
<!-- ctx:node id="{node_id}" version="1.0.0" -->

## Local Rules

### General

- **{rule_id}:** {statement}
  Why: regression
  <!-- ctx:rule id="{rule_id}" -->
''',
            encoding="utf-8",
        )
        return root

    def _install(self, child: Path, compiled) -> None:
        package = compiled_package(compiled)
        target = child / ".context" / "sources" / package.package_digest
        for rel, content in artifact_files(compiled).items():
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)

    def test_two_parents_compose_without_order_precedence(self) -> None:
        a = self._node("a", "node-a", "Parent A", "A-1", "Rule from A")
        b = self._node("b", "node-b", "Parent B", "B-1", "Rule from B")
        compiled_a = Compiler(self.repo).compile(a)
        compiled_b = Compiler(self.repo).compile(b)
        child = self._node("child", "node-child", "Child", "C-1", "Local rule")
        self._install(child, compiled_a)
        self._install(child, compiled_b)

        refs = []
        for rel, compiled in (("../b", compiled_b), ("../a", compiled_a)):
            refs.append(
                f'- [{compiled.metadata.name}]({rel}) — `{compiled.metadata.version}`\n'
                f'  <!-- ctx:parent id="{compiled.metadata.id}" version="{compiled.metadata.version}" '
                f'normalized-digest="{compiled.normalized_digest}" package-digest="{compiled.package_digest}" -->'
            )
        source = (child / "CONTEXT.src.md").read_text(encoding="utf-8")
        source = source.replace("\n## Local Rules", "\n## Parent Context Node\n\n" + "\n".join(refs) + "\n\n## Local Rules")
        (child / "CONTEXT.src.md").write_text(source, encoding="utf-8")

        compiled = Compiler(self.repo).compile(child)
        self.assertEqual([p.metadata.id for p in compiled.parent_packages], ["node-a", "node-b"])
        self.assertEqual({rule.id for rule in compiled.inherited_rules}, {"A-1", "B-1"})
        self.assertIn("**Parent Context Nodes:**", compiled.official_markdown)
        self.assertEqual([p.id for p in compiled_package(compiled).parents], ["node-a", "node-b"])

        # Reversing authoring order cannot create semantic precedence.
        reversed_source = source.replace("\n".join(refs), "\n".join(reversed(refs)))
        (child / "CONTEXT.src.md").write_text(reversed_source, encoding="utf-8")
        reversed_compiled = Compiler(self.repo).compile(child)
        self.assertEqual(reversed_compiled.normalized_digest, compiled.normalized_digest)

        with self.assertRaisesRegex(ContextCanonError, "multiple semantic Parents"):
            review_parent_candidate(child)


if __name__ == "__main__":
    unittest.main()
