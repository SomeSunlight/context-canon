from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import CONTEXT_FOLDER_README, Compiler
from contextcanon.outputs import check_outputs, write_outputs


SOURCE_WITH_RESOURCE = '''# Demo Node — Local Context Source
<!-- ctx:node id="demo-node" version="0.1.0" -->

## Topics

### Guide

When deeper guidance is useful:

Required:
- Resource: `guide.md`
<!-- ctx:topic id="GUIDE" -->
'''

SOURCE_WITHOUT_RESOURCE = '''# Demo Node — Local Context Source
<!-- ctx:node id="demo-node" version="0.1.0" -->
'''


class ContextFolderOrientationTests(unittest.TestCase):
    def make_repo(self, *, with_resource: bool) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(
            SOURCE_WITH_RESOURCE if with_resource else SOURCE_WITHOUT_RESOURCE,
            encoding="utf-8",
        )
        if with_resource:
            (root / "guide.md").write_text("# Guide\n\nRead this only when needed.\n", encoding="utf-8")
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
        self.assertIn("CONTEXT/references/demo-node/guide.md", compiled.resources)

    def test_resource_link_to_generated_context_is_independent_of_previous_build(self):
        root = self.make_repo(with_resource=True)
        (root / "guide.md").write_text(
            "# Guide\n\nSee [Project Context](CONTEXT.md).\n",
            encoding="utf-8",
        )

        # Reproduce the real ai-workstation compiler-0.4 shape: a stale generated
        # Official Context exists and its resource tree even contains a copied
        # CONTEXT.src.md. Neither may influence the new package identity.
        (root / "CONTEXT.md").write_text("stale generated context\n", encoding="utf-8")
        legacy = root / "CONTEXT" / "references"
        legacy.mkdir(parents=True)
        (legacy / "CONTEXT.src.md").write_bytes((root / "CONTEXT.src.md").read_bytes())

        first = Compiler(root).compile(root)
        bridge = "CONTEXT/references/demo-node/CONTEXT.md"
        self.assertIn(bridge, first.resources)
        self.assertIn("Official Context bridge", first.resources[bridge].decode("utf-8"))
        self.assertIn("../../../CONTEXT.md", first.resources[bridge].decode("utf-8"))
        self.assertNotIn(b"stale generated context", first.resources[bridge])
        self.assertNotIn("CONTEXT/references/demo-node/CONTEXT.src.md", first.resources)

        write_outputs(first)
        self.assertFalse((legacy / "CONTEXT.src.md").exists())

        second = Compiler(root).compile(root)
        self.assertEqual(first.package_digest, second.package_digest)
        self.assertEqual(first.resources, second.resources)
        self.assertEqual(check_outputs(second), [])

    def test_resource_free_node_stays_without_context_directory_material(self):
        root = self.make_repo(with_resource=False)
        compiled = Compiler(root).compile(root)

        self.assertEqual(compiled.resources, {})


if __name__ == "__main__":
    unittest.main()
