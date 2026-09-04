from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from contextcanon.compiler import Compiler
from contextcanon.onboarding_reusable_contexts import (
    ASSIGNMENTS_END,
    ASSIGNMENTS_START,
    CATALOG_END,
    CATALOG_START,
    load_accepted_reusable_contexts,
    refresh_reusable_contexts,
)
from contextcanon.onboarding_structure import HumanStructureNode, HumanStructurePlan
from contextcanon.outputs import write_outputs
from contextcanon.onboarding_placement_instruction import _render_accepted_reusable_contexts
from contextcanon.parser import parse_node


class ReusableContextsTests(unittest.TestCase):
    def _structure(self) -> HumanStructurePlan:
        return HumanStructurePlan(
            evidence_digest="a" * 64,
            proposal_digest="b" * 64,
            nodes=(
                HumanStructureNode("N-001", "AI Workstation", ".", "current", None, "N-001"),
                HumanStructureNode("N-002", "Bootstrap", "bootstrap", "current", "N-001", "N-002"),
            ),
            fixed_markdown=(),
            structure_digest="c" * 64,
        )

    def _catalog(self, root: Path) -> Path:
        node = root / "catalog" / "development-workflow"
        node.mkdir(parents=True)
        (root / "catalog" / ".git").mkdir()
        (node / "CONTEXT.src.md").write_text(
            "# Development Workflow — Local Context Source\n"
            '<!-- ctx:node id="workflow-node" version="0.2.0-draft" -->\n\n'
            "## Local Rules\n\n"
            "### Development\n\n"
            "- **Review before merge:** Keep changes reviewable.\n"
            "  Why: Humans should explicitly accept important changes.\n"
            '  <!-- ctx:rule id="WF-001" -->\n',
            encoding="utf-8",
        )
        compiled = Compiler(root / "catalog").compile(node)
        write_outputs(compiled)
        return root / "catalog"

    def test_sparse_human_gate_discovers_catalog_and_persists_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-05-reusable-contexts.md"
            structure = self._structure()
            catalog = self._catalog(root)

            first, created = refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertTrue(created)
            self.assertFalse(first.is_complete)
            text = workspace_file.read_text(encoding="utf-8")
            self.assertIn("# STEP 05 — Reusable Contexts", text)
            self.assertNotIn("workflow-node", text)

            text = text.replace(
                CATALOG_START + "\n" + CATALOG_END,
                CATALOG_START + f"\n- `{catalog}`\n" + CATALOG_END,
            )
            text = text.replace("Decision: `pending`", "Decision: `accept`")
            assignment = (
                "- **AI Workstation** (`.`) ← **Development Workflow** (`0.2.0-draft`)\n"
                "  Why: Shared development workflow applies to the whole project.\n"
            )
            text = text.replace(
                ASSIGNMENTS_START + "\n" + ASSIGNMENTS_END,
                ASSIGNMENTS_START + "\n" + assignment + ASSIGNMENTS_END,
            )
            workspace_file.write_text(text, encoding="utf-8")

            second, created = refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertFalse(created)
            self.assertTrue(second.is_complete)
            self.assertEqual(second.owner_source_specs, ("N-001=workflow-node",))
            self.assertEqual(
                second.owner_source_whys["N-001=workflow-node"],
                "Shared development workflow applies to the whole project.",
            )
            accepted = load_accepted_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertEqual(len(accepted.catalog_packages), 1)
            state = json.loads((snapshot / "reusable-contexts.json").read_text(encoding="utf-8"))
            self.assertEqual(state["assignments"][0]["source_node_id"], "workflow-node")

    def test_accepted_assignment_is_explicit_placement_reasoning_input(self) -> None:
        from contextcanon.onboarding_reusable_contexts import ReusableContextAssignment

        assignment = ReusableContextAssignment(
            target_node_key="N-001",
            target_name="AI Workstation",
            target_path=".",
            source_node_id="workflow-node",
            source_name="Development Workflow",
            source_version="0.2.0-draft",
            source_normalized_digest="1" * 64,
            source_package_digest="2" * 64,
            why="Shared development workflow applies to the whole project.",
        )
        rendered = "\n".join(_render_accepted_reusable_contexts((assignment,)))
        self.assertIn("already accepted", rendered)
        self.assertIn("AI Workstation", rendered)
        self.assertIn("Development Workflow", rendered)
        self.assertIn("semantic descendants", rendered)
        self.assertIn("Why: Shared development workflow applies to the whole project.", rendered)
        self.assertIn("Do not emit a `source_reuses` entry", rendered)

    def test_source_why_is_parsed_from_authored_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            source = root / "shared"
            consumer = root / "consumer"
            source.mkdir()
            consumer.mkdir()
            (source / "CONTEXT.src.md").write_text(
                "# Shared — Local Context Source\n"
                '<!-- ctx:node id="shared" version="1.0.0" -->\n',
                encoding="utf-8",
            )
            (consumer / "CONTEXT.src.md").write_text(
                "# Consumer — Local Context Source\n"
                '<!-- ctx:node id="consumer" version="1.0.0" -->\n\n'
                "## Sources\n\n"
                "- [Shared](../shared) — `1.0.0`\n"
                "  Why: Shared policy applies to every consumer here.\n"
                '  <!-- ctx:source id="shared" version="1.0.0" -->\n',
                encoding="utf-8",
            )
            parsed = parse_node(consumer, root)
            self.assertEqual(parsed.sources[0].why, "Shared policy applies to every consumer here.")
            compiled = Compiler(root).compile(consumer)
            self.assertEqual(compiled.imported_contexts[0].why, "Shared policy applies to every consumer here.")
            self.assertIn("Why: Shared policy applies to every consumer here.", compiled.official_markdown)
            manifest = json.loads(compiled.package_manifest)
            self.assertEqual(manifest["imports"][0]["why"], "Shared policy applies to every consumer here.")
