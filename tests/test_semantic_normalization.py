from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.parser import ContextCanonError


SOURCE_A = '''# Source A — Local Context Source
<!-- ctx:node id="source-a" version="1.0.0" -->

## Rules

### A

- **Rule A:** Apply A.
  Why: Fixture A.
  <!-- ctx:rule id="A-001" -->
'''

SOURCE_B = '''# Source B — Local Context Source
<!-- ctx:node id="source-b" version="1.0.0" -->

## Rules

### B

- **Rule B:** Apply B.
  Why: Fixture B.
  <!-- ctx:rule id="B-001" -->
'''


def project(sources: str) -> str:
    return f'''# Project — Local Context Source
<!-- ctx:node id="project" version="1.0.0" -->

## Sources

{sources}
'''


SOURCE_LINE_A = '''- [Source A](nodes/a/) — `1.0.0`
  <!-- ctx:source id="source-a" version="1.0.0" -->'''
SOURCE_LINE_B = '''- [Source B](nodes/b/) — `1.0.0`
  <!-- ctx:source id="source-b" version="1.0.0" -->'''


class SemanticNormalizationTests(unittest.TestCase):
    def make_repo(self, source_block: str) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(project(source_block), encoding="utf-8")
        a = root / "nodes/a"
        b = root / "nodes/b"
        a.mkdir(parents=True)
        b.mkdir(parents=True)
        (a / "CONTEXT.src.md").write_text(SOURCE_A, encoding="utf-8")
        (b / "CONTEXT.src.md").write_text(SOURCE_B, encoding="utf-8")
        return root

    def test_source_order_does_not_change_normalized_semantics(self):
        first = self.make_repo(SOURCE_LINE_A + "\n\n" + SOURCE_LINE_B)
        second = self.make_repo(SOURCE_LINE_B + "\n\n" + SOURCE_LINE_A)

        first_node = Compiler(first).compile(first)
        second_node = Compiler(second).compile(second)

        self.assertEqual(first_node.normalized_digest, second_node.normalized_digest)
        self.assertEqual(
            {(rule.origin_node_id, rule.id) for rule in first_node.inherited_rules},
            {(rule.origin_node_id, rule.id) for rule in second_node.inherited_rules},
        )

    def test_duplicate_direct_source_id_fails(self):
        duplicate = SOURCE_LINE_A + "\n\n" + SOURCE_LINE_A.replace("nodes/a/", "nodes/a/")
        root = self.make_repo(duplicate)

        with self.assertRaisesRegex(ContextCanonError, "duplicate Source Node ID source-a"):
            Compiler(root).compile(root)


if __name__ == "__main__":
    unittest.main()
