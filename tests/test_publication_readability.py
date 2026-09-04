from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contextcanon.compiler import Compiler
from contextcanon.outputs import check_outputs, write_outputs
from contextcanon.parser import ContextCanonError, parse_node


class PublicationReadabilityTests(unittest.TestCase):
    def _repo(self) -> Path:
        repo = Path(tempfile.mkdtemp())
        (repo / ".git").mkdir()
        return repo

    def test_canonical_local_headings_parse_and_legacy_aliases_remain_compatible(self):
        repo = self._repo()
        source = repo / "CONTEXT.src.md"
        source.write_text(
            """# Example — Local Context Source
<!-- ctx:node id="example" version="1.0.0" -->

## Local Overview

Local orientation.

## Local State

- Current state.

## Local Plan

- Future plan.

## Local Rules

### General

- **Stay local:** This rule is authored here.
  Why: The heading must not imply an override.
  <!-- ctx:rule id="RULE-1" -->

## Local Topics

### Details

When details matter:

Required:
- Resource: `detail.md`
<!-- ctx:topic id="TOPIC-1" -->
""",
            encoding="utf-8",
        )
        (repo / "detail.md").write_text("# Detail\n", encoding="utf-8")
        parsed = parse_node(repo, repo)
        self.assertEqual(parsed.overview, "Local orientation.")
        self.assertEqual(len(parsed.rules), 1)
        self.assertEqual(len(parsed.topics), 1)

        legacy = source.read_text(encoding="utf-8")
        for canonical, old in (
            ("## Local Overview", "## Overview"),
            ("## Local State", "## State"),
            ("## Local Plan", "## Plan"),
            ("## Local Rules", "## Rules"),
            ("## Local Topics", "## Topics"),
        ):
            legacy = legacy.replace(canonical, old)
        source.write_text(legacy, encoding="utf-8")
        self.assertEqual(parse_node(repo, repo).overview, "Local orientation.")

        source.write_text(legacy + "\n## Local Rules\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "ambiguous duplicate section aliases"):
            parse_node(repo, repo)

    def test_generated_node_readme_is_owned_only_by_marker(self):
        repo = self._repo()
        (repo / "CONTEXT.src.md").write_text(
            """# Example — Local Context Source
<!-- ctx:node id="example" version="1.0.0" -->

## Local Overview

A small Node.
""",
            encoding="utf-8",
        )
        compiled = Compiler(repo).compile(repo)
        self.assertIn("missing README.md", check_outputs(compiled))
        write_outputs(compiled)
        readme = (repo / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("<!-- contextcanon:generated-node-readme -->\n"))
        self.assertIn("CONTEXT.md", readme)
        self.assertIn("CONTEXT.src.md", readme)
        self.assertEqual(check_outputs(Compiler(repo).compile(repo)), [])

        foreign = "# Project-owned README\n\nKeep me.\n"
        (repo / "README.md").write_text(foreign, encoding="utf-8")
        compiled = Compiler(repo).compile(repo)
        self.assertNotIn("README.md", "\n".join(check_outputs(compiled)))
        write_outputs(compiled)
        self.assertEqual((repo / "README.md").read_text(encoding="utf-8"), foreign)

    def test_official_local_headings_are_explicit(self):
        repo = self._repo()
        (repo / "CONTEXT.src.md").write_text(
            """# Example — Local Context Source
<!-- ctx:node id="example" version="1.0.0" -->

## Local Overview

Orientation.

## Local State

- State.

## Local Plan

- Plan.

## Local Rules

### General

- **Rule:** Statement.
  Why: Rationale.
  <!-- ctx:rule id="RULE-1" -->
""",
            encoding="utf-8",
        )
        official = Compiler(repo).compile(repo).official_markdown
        self.assertIn("## Local Overview", official)
        self.assertIn("## Local State", official)
        self.assertIn("## Local Plan", official)
        self.assertIn("## Local Rules", official)
        self.assertNotIn("\n## Rules\n", official)


if __name__ == "__main__":
    unittest.main()
