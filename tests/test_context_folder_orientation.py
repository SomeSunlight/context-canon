from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import CONTEXT_FOLDER_README, Compiler


class ContextFolderOrientationTests(unittest.TestCase):
    def make_repo(self, *, with_resource: bool) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        source = '''# Demo Node — Local Context Source
<!-- ctx:node id="demo-node" version="1.0.0" -->
'''
        if with_resource:
            (root / "guide.md").write_text("# Guide\n\nRead this only when needed.\n", encoding="utf-8")
            source += '''
## Topics

### Guide

When the guide is needed:

Required:
- Resource: `guide.md`
<!-- ctx:topic id="DEMO-GUIDE" -->
'''
        (root / "CONTEXT.src.md").write_text(source, encoding="utf-8")
        return root

    def test_resource_package_gets_generated_context_readme(self):
        root = self.make_repo(with_resource=True)
        compiled = Compiler(root).compile(root)

        self.assertEqual(compiled.resources["CONTEXT/README.md"], CONTEXT_FOLDER_README.encode("utf-8"))
        readme = compiled.resources["CONTEXT/README.md"].decode("utf-8")
        self.assertIn("GENERATED DIRECTORY", readme)
        self.assertIn("not another maintenance surface", readme)
        self.assertIn("self-contained", readme)
        self.assertIn("../CONTEXT.md", readme)
        self.assertIn("CONTEXT/references/guide.md", compiled.resources)

    def test_resource_free_node_stays_without_context_directory_material(self):
        root = self.make_repo(with_resource=False)
        compiled = Compiler(root).compile(root)

        self.assertEqual(compiled.resources, {})


if __name__ == "__main__":
    unittest.main()
