from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler, discover_nodes
from contextcanon.outputs import check_outputs, write_outputs
from contextcanon.parser import ContextCanonError


GATEWAY = '''# Demo Gateway — Local Context Source
<!-- ctx:node id="node-gateway" version="0.1.0" adapters="agents,goose,copilot" -->

## Topics

### Development

When changing the demo implementation:

Required:
- Context Node: `nodes/internal/development`
<!-- ctx:topic id="GW-DEV" -->
'''

FOUNDATION = '''# Demo Foundation — Local Context Source
<!-- ctx:node id="node-foundation" version="0.1.0" -->

## Rules

### Style

- **Write clearly:** Use plain technical prose.
  Why: Context should be easy to interpret.
  <!-- ctx:rule id="F-001" -->

## Topics

### Authoring

When editing context:

Required:
- Resource: `../../../docs/authoring.md`
<!-- ctx:topic id="F-AUTH" -->
'''

DEVELOPMENT = '''# Demo Development — Local Context Source
<!-- ctx:node id="node-development" version="0.1.0" -->

## Sources

- [Demo Foundation](../../library/foundation/) — `0.1.0`
  <!-- ctx:source id="node-foundation" version="0.1.0" -->

## Rules

### Compiler

- **Stay deterministic:** Compute exact mechanics without an LLM.
  Why: Builds must be reproducible.
  <!-- ctx:rule id="D-001" -->

## Topics

### Architecture

When changing architecture:

Required:
- Resource: `../../../docs/architecture.md`
Optional:
- Resource: `../../../docs/authoring.md`
<!-- ctx:topic id="D-ARCH" -->
'''


class WalkingSkeletonTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "docs").mkdir()
        (root / "docs/authoring.md").write_text("# Authoring\n\n[Details](details.md)\n", encoding="utf-8")
        (root / "docs/details.md").write_text("# Details\n", encoding="utf-8")
        (root / "docs/architecture.md").write_text("# Architecture\n", encoding="utf-8")
        (root / "STATE.md").write_text("# State\n", encoding="utf-8")
        (root / "CONTEXT.src.md").write_text(GATEWAY, encoding="utf-8")
        foundation = root / "nodes/library/foundation"
        development = root / "nodes/internal/development"
        foundation.mkdir(parents=True)
        development.mkdir(parents=True)
        (foundation / "CONTEXT.src.md").write_text(FOUNDATION, encoding="utf-8")
        (development / "CONTEXT.src.md").write_text(DEVELOPMENT, encoding="utf-8")
        return root

    def test_discovers_three_node_roots(self):
        repo = self.make_repo()
        rel = [path.relative_to(repo).as_posix() or "." for path in discover_nodes(repo)]
        self.assertEqual(rel, [".", "nodes/internal/development", "nodes/library/foundation"])

    def test_compiles_sources_rules_topics_resources_and_digests(self):
        repo = self.make_repo()
        compiler = Compiler(repo)
        node = compiler.compile(repo / "nodes/internal/development")
        self.assertEqual([rule.id for rule in node.inherited_rules], ["F-001"])
        self.assertEqual([rule.id for rule in node.local_rules], ["D-001"])
        self.assertEqual([topic.id for topic in node.local_topics], ["D-ARCH"])
        self.assertEqual(
            list(node.resources),
            ["CONTEXT/references/docs/architecture.md", "CONTEXT/references/docs/authoring.md", "CONTEXT/references/docs/details.md"],
        )
        self.assertEqual(len(node.normalized_digest), 64)
        self.assertEqual(len(node.package_digest), 64)
        self.assertIn("How to use this context", node.official_markdown)
        self.assertIn("Apply all Rules below to every task in this Node.", node.official_markdown)
        self.assertIn("Rules from Demo Foundation", node.official_markdown)
        self.assertIn("`F-001` — Write clearly", node.official_markdown)
        self.assertIn("`D-001` — Stay deterministic", node.official_markdown)

    def test_build_then_check_is_clean_and_detects_drift(self):
        repo = self.make_repo()
        compiler = Compiler(repo)
        for node_root in discover_nodes(repo):
            write_outputs(compiler.compile(node_root))
        compiler2 = Compiler(repo)
        for node_root in discover_nodes(repo):
            compiled = compiler2.compile(node_root)
            self.assertEqual(check_outputs(compiled), [])
            self.assertEqual(write_outputs(compiled), [])
        (repo / "CONTEXT.md").write_text("drift\n", encoding="utf-8")
        compiler3 = Compiler(repo)
        self.assertIn("changed CONTEXT.md", check_outputs(compiler3.compile(repo)))

    def test_context_node_target_is_validated_without_materialization(self):
        repo = self.make_repo()
        node = Compiler(repo).compile(repo)
        self.assertEqual(node.resources, {})
        self.assertIn("Demo Development", node.official_markdown)
        self.assertFalse((repo / "CONTEXT").exists())

    def test_nonempty_changes_section_fails_clearly(self):
        repo = self.make_repo()
        path = repo / "nodes/library/foundation/CONTEXT.src.md"
        path.write_text(FOUNDATION + "\n## Changes\n\n### Remove\n- something\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "Changes is reserved"):
            Compiler(repo).compile(repo / "nodes/library/foundation")

    def test_source_id_mismatch_fails(self):
        repo = self.make_repo()
        path = repo / "nodes/internal/development/CONTEXT.src.md"
        path.write_text(DEVELOPMENT.replace('id="node-foundation"', 'id="wrong-id"'), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "expects Node ID"):
            Compiler(repo).compile(repo / "nodes/internal/development")

    def test_cli_build_all_and_check_all(self):
        repo = self.make_repo()
        self.assertEqual(main(["build", "--all", str(repo)]), 0)
        self.assertEqual(main(["check", "--all", str(repo)]), 0)
        self.assertTrue((repo / "AGENTS.md").is_file())
        self.assertTrue((repo / ".goosehints").is_file())
        copilot = repo / ".github/copilot-instructions.md"
        self.assertTrue(copilot.is_file())
        self.assertIn("[CONTEXT.md](../CONTEXT.md)", copilot.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
