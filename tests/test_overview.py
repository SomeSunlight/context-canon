from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contextcanon.compiler import Compiler


WITHOUT_OVERVIEW = '''# Demo — Local Context Source
<!-- ctx:node id="demo-node" version="0.1.0" -->
'''

WITH_OVERVIEW = '''# Demo — Local Context Source
<!-- ctx:node id="demo-node" version="0.1.0" -->

## Overview

A compact orientation belongs in the official entry without becoming inherited governance.

- It may use ordinary Markdown.
- Deeper task-specific material still belongs behind Topics.
'''


class OverviewTests(unittest.TestCase):
    def make_repo(self, source: str) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(source, encoding="utf-8")
        return root

    def test_overview_changes_package_presentation_not_normalized_semantics(self):
        repo = self.make_repo(WITHOUT_OVERVIEW)
        baseline = Compiler(repo).compile(repo)

        (repo / "CONTEXT.src.md").write_text(WITH_OVERVIEW, encoding="utf-8")
        with_overview = Compiler(repo).compile(repo)

        self.assertIn("## Local Overview", with_overview.official_markdown)
        self.assertIn("A compact orientation belongs", with_overview.official_markdown)
        self.assertIn("- It may use ordinary Markdown.", with_overview.official_markdown)
        self.assertEqual(baseline.normalized_digest, with_overview.normalized_digest)
        self.assertNotEqual(baseline.package_digest, with_overview.package_digest)


if __name__ == "__main__":
    unittest.main()
