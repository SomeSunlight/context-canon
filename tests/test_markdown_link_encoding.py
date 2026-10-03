from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from contextcanon.compiler import Compiler
from contextcanon.links import local_markdown_targets, markdown_link_target, markdown_target_locator
from contextcanon.onboarding_placement_instruction import _render_contract
from contextcanon.onboarding_placement_publish import _render_parent_body
from contextcanon.onboarding_placement_review import _node_entry_link
from contextcanon.onboarding_placement_split_review import _finding_node_link
from contextcanon.parser import parse_node
from contextcanon.sources import normalize_source_relationships


class MarkdownLinkEncodingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / ".git").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_node(self, root: Path, node_id: str, name: str, extra: str = "") -> None:
        root.mkdir(parents=True, exist_ok=True)
        text = (
            f"# {name} — Local Context Source\n"
            f'<!-- ctx:node id="{node_id}" name="{name}" version="1.0.0" -->\n\n'
            + extra.rstrip()
            + ("\n" if extra else "")
        )
        (root / "CONTEXT.src.md").write_text(text, encoding="utf-8")

    def test_local_markdown_target_roundtrip_encodes_sensitive_path_characters(self) -> None:
        raw = "01 F1/docs/spec #1% (draft).md"
        encoded = "01%20F1/docs/spec%20%231%25%20%28draft%29.md"
        self.assertEqual(markdown_link_target(raw), encoded)
        self.assertEqual(markdown_target_locator(encoded), raw)
        self.assertEqual(markdown_link_target("safe/path.md"), "safe/path.md")
        self.assertEqual(markdown_link_target("https://example.org/a%20b"), "https://example.org/a%20b")
        self.assertEqual(list(local_markdown_targets(f"[local]({encoded})")), [raw])
        contract = "\n".join(_render_contract("0" * 64, "1" * 64))
        self.assertIn("percent-encode the link destination as a URI path", contract)

    def test_context_import_with_special_directory_name_normalizes_and_still_resolves(self) -> None:
        parent_root = self.repo / "01 F1 #100%(draft)"
        self._write_node(
            parent_root,
            "parent",
            "Parent P",
            """## Local Rules

### General

- **Parent rule:** Applies.
  Why: Regression.
  <!-- ctx:rule id="P-1" -->""",
        )
        child_root = self.repo / "02 F2"
        self._write_node(
            child_root,
            "child",
            "Child",
            """## Context Imports

- [Parent P](../01 F1 #100%(draft)/) — `1.0.0` — `relationship=parent`
  <!-- ctx:source id="parent" version="1.0.0" -->""",
        )

        before = Compiler(self.repo).compile(child_root)
        self.assertEqual([rule.id for rule in before.inherited_rules], ["P-1"])
        self.assertEqual(parse_node(child_root, self.repo).sources[0].locator, "../01 F1 #100%(draft)/")

        self.assertTrue(normalize_source_relationships(child_root))
        normalized = (child_root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("../01%20F1%20%23100%25%28draft%29/", normalized)
        self.assertEqual(parse_node(child_root, self.repo).sources[0].locator, "../01 F1 #100%(draft)/")
        self.assertEqual([rule.id for rule in Compiler(self.repo).compile(child_root).inherited_rules], ["P-1"])
        self.assertFalse(normalize_source_relationships(child_root))

    def test_official_context_encodes_resource_and_context_node_links_while_closure_decodes(self) -> None:
        target_root = self.repo / "01 F1 #100%(draft)"
        self._write_node(target_root, "target", "Target Node")

        docs = self.repo / "docs"
        docs.mkdir()
        guide = docs / "guide file #1%.md"
        detail = docs / "detail #2%(draft).txt"
        guide.write_text("# Guide\n\n[Detail](detail%20%232%25%28draft%29.txt)\n", encoding="utf-8")
        detail.write_text("detail\n", encoding="utf-8")

        self._write_node(
            self.repo,
            "root",
            "Root",
            """## Local Topics

### Special paths

When special-path material is needed:

Required:
- Resource: `docs/guide file #1%.md`
  <!-- ctx:resource id="RESOURCE-SPECIAL" -->
- Context Node: `01 F1 #100%(draft)`
<!-- ctx:topic id="TOPIC-SPECIAL" -->""",
        )

        compiled = Compiler(self.repo).compile(self.repo)
        self.assertIn("CONTEXT/references/root/docs/guide file #1%.md", compiled.resources)
        self.assertIn("CONTEXT/references/root/docs/detail #2%(draft).txt", compiled.resources)
        self.assertIn(
            "(CONTEXT/references/root/docs/guide%20file%20%231%25.md)",
            compiled.official_markdown,
        )
        self.assertIn(
            "(01%20F1%20%23100%25%28draft%29/CONTEXT.md)",
            compiled.official_markdown,
        )

    def test_onboarding_node_links_and_parent_publication_encode_presentation_only(self) -> None:
        node_path = "01 F1 #100%(draft)"
        self.assertEqual(_node_entry_link(node_path), "../01%20F1%20%23100%25%28draft%29/CONTEXT.md")
        self.assertEqual(_finding_node_link(node_path), "../../01%20F1%20%23100%25%28draft%29/CONTEXT.md")

        parent_root = self.repo / node_path
        self._write_node(parent_root, "parent", "Parent P")
        compiled_parent = Compiler(self.repo).compile(parent_root)
        child_root = self.repo / "02 F2"
        child_root.mkdir()
        parent = SimpleNamespace(key="N-001", name="Parent P")
        body, locator = _render_parent_body(parent, compiled_parent, child_root, parent_root)
        self.assertEqual(locator, "../01 F1 #100%(draft)")
        self.assertIn("](../01%20F1%20%23100%25%28draft%29)", body)


if __name__ == "__main__":
    unittest.main()
