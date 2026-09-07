from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.parser import ContextCanonError, parse_node


class ExplicitNodeNameTests(unittest.TestCase):
    def make_repo(self, h1: str, name: str, *, include_name: bool = True) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        name_attr = f' name="{name}"' if include_name else ""
        (root / "CONTEXT.src.md").write_text(
            f'# {h1}\n<!-- ctx:node id="node-demo"{name_attr} version="0.1.0" -->\n',
            encoding="utf-8",
        )
        return root

    def test_canonical_name_comes_from_explicit_machine_metadata(self):
        repo = self.make_repo("A presentation title with no special suffix", "Canonical Demo")
        self.assertEqual(parse_node(repo).metadata.name, "Canonical Demo")

    def test_changing_h1_does_not_change_normalized_semantics(self):
        repo = self.make_repo("First presentation", "Canonical Demo")
        first = Compiler(repo).compile(repo)
        source = repo / "CONTEXT.src.md"
        source.write_text(source.read_text(encoding="utf-8").replace("# First presentation", "# Entirely different presentation"), encoding="utf-8")
        second = Compiler(repo).compile(repo)
        self.assertEqual(first.metadata.name, second.metadata.name)
        self.assertEqual(first.normalized_digest, second.normalized_digest)

    def test_changing_explicit_name_changes_canonical_semantics(self):
        repo = self.make_repo("Presentation stays fixed", "Canonical Demo")
        first = Compiler(repo).compile(repo)
        source = repo / "CONTEXT.src.md"
        source.write_text(source.read_text(encoding="utf-8").replace('name="Canonical Demo"', 'name="Renamed Demo"'), encoding="utf-8")
        second = Compiler(repo).compile(repo)
        self.assertEqual(second.metadata.name, "Renamed Demo")
        self.assertNotEqual(first.normalized_digest, second.normalized_digest)

    def test_missing_explicit_name_fails_clearly(self):
        repo = self.make_repo("Presentation", "unused", include_name=False)
        with self.assertRaisesRegex(ContextCanonError, "ctx:node id/name/version"):
            parse_node(repo)


if __name__ == "__main__":
    unittest.main()
