from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path

from contextcanon.compiler import Compiler
from contextcanon.onboarding_reusable_contexts import (
    ASSIGNMENTS_END,
    ASSIGNMENTS_START,
    CATALOG_END,
    CATALOG_START,
    _catalog_locations,
    load_accepted_reusable_contexts,
    refresh_reusable_contexts,
    render_reusable_contexts,
)
from contextcanon.onboarding_structure import HumanStructureNode, HumanStructurePlan
from contextcanon.outputs import write_outputs
from contextcanon.onboarding_placement_instruction import _render_accepted_reusable_contexts
from contextcanon.parser import ContextCanonError, parse_node


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
            '<!-- ctx:node id="workflow-node" name="Development Workflow" version="0.2.0-draft" -->\n\n'
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


    def _git_catalog(self, root: Path) -> tuple[Path, Path]:
        catalog = root / "catalog-git"
        node = catalog / "development-workflow"
        node.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(catalog)], check=True)
        subprocess.run(["git", "-C", str(catalog), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(catalog), "config", "user.name", "Test"], check=True)
        (node / "CONTEXT.src.md").write_text(
            "# Development Workflow — Local Context Source\n"
            '<!-- ctx:node id="workflow-node" name="Development Workflow" version="0.2.0-draft" -->\n\n'
            "## Local Rules\n\n"
            "### Development\n\n"
            "- **Review before merge:** Keep changes reviewable.\n"
            "  Why: Humans should explicitly accept important changes.\n"
            '  <!-- ctx:rule id="WF-001" -->\n',
            encoding="utf-8",
        )
        write_outputs(Compiler(catalog).compile(node))
        subprocess.run(["git", "-C", str(catalog), "add", "."], check=True)
        subprocess.run(["git", "-C", str(catalog), "commit", "-qm", "workflow 0.2.0"], check=True)
        return catalog, node

    def _accept_workflow(self, workspace_file: Path, snapshot: Path, structure: HumanStructurePlan, catalog: Path):
        refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
        text = workspace_file.read_text(encoding="utf-8")
        text = text.replace(
            CATALOG_START + "\n" + CATALOG_END,
            CATALOG_START + f"\n- `{catalog}`\n" + CATALOG_END,
        )
        text = text.replace("Decision: `pending`", "Decision: `accept`")
        assignment = (
            "AI Workstation (.) ← Development Workflow (0.2.0-draft) [Parent]\n"
            "Why: Shared development workflow applies to the whole project.\n"
        )
        text = text.replace(
            ASSIGNMENTS_START + "\n```text\n```\n" + ASSIGNMENTS_END,
            ASSIGNMENTS_START + "\n```text\n" + assignment + "```\n" + ASSIGNMENTS_END,
        )
        workspace_file.write_text(text, encoding="utf-8")
        return refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)[0]

    def _advance_workflow(self, catalog: Path, node: Path) -> None:
        source = node / "CONTEXT.src.md"
        text = source.read_text(encoding="utf-8").replace(
            'version="0.2.0-draft"',
            'version="0.3.0-draft"',
        )
        source.write_text(text, encoding="utf-8")
        write_outputs(Compiler(catalog).compile(node))
        subprocess.run(["git", "-C", str(catalog), "add", "."], check=True)
        subprocess.run(["git", "-C", str(catalog), "commit", "-qm", "workflow 0.3.0"], check=True)

    def test_sparse_human_gate_discovers_catalog_and_persists_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-07-reusable-contexts.md"
            structure = self._structure()
            catalog = self._catalog(root)

            first, created = refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertTrue(created)
            self.assertFalse(first.is_complete)
            text = workspace_file.read_text(encoding="utf-8")
            self.assertIn("# STEP 07 — Reusable Contexts", text)
            self.assertNotIn("workflow-node", text)

            text = text.replace(
                CATALOG_START + "\n" + CATALOG_END,
                CATALOG_START + f"\n- `{catalog}`\n" + CATALOG_END,
            )
            text = text.replace("Decision: `pending`", "Decision: `accept`")
            assignment = (
                "AI Workstation (.) ← Development Workflow (0.2.0-draft) [Parent]\n"
                "Why: Shared development workflow applies to the whole project.\n"
            )
            text = text.replace(
                ASSIGNMENTS_START + "\n```text\n```\n" + ASSIGNMENTS_END,
                ASSIGNMENTS_START + "\n```text\n" + assignment + "```\n" + ASSIGNMENTS_END,
            )
            workspace_file.write_text(text, encoding="utf-8")

            second, created = refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertFalse(created)
            self.assertTrue(second.is_complete)
            canonical_after_accept = workspace_file.read_text(encoding="utf-8")
            self.assertIn(
                "AI Workstation (.) ← Development Workflow (0.2.0-draft) [Parent]\n"
                "Why: Shared development workflow applies to the whole project.",
                canonical_after_accept,
            )
            self.assertEqual(second.owner_source_specs, ("N-001=workflow-node",))
            self.assertEqual(
                second.owner_source_whys["N-001=workflow-node"],
                "Shared development workflow applies to the whole project.",
            )
            accepted = load_accepted_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertEqual(len(accepted.catalog_packages), 1)
            state = json.loads((snapshot / "reusable-contexts.json").read_text(encoding="utf-8"))
            self.assertEqual(state["assignments"][0]["source_node_id"], "workflow-node")

    def test_accept_allows_dirty_nested_worktree_outside_package_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-07-reusable-contexts.md"
            structure = self._structure()
            catalog, node = self._git_catalog(root)

            active_subtree = node / "active-subtree"
            active_subtree.mkdir()
            (active_subtree / "working.md").write_text(
                "# Uncommitted child project work\n",
                encoding="utf-8",
            )
            status = subprocess.run(
                ["git", "-C", str(catalog), "status", "--porcelain", "--", str(active_subtree)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            self.assertTrue(status)

            accepted = self._accept_workflow(workspace_file, snapshot, structure, catalog)

            self.assertTrue(accepted.is_complete)
            self.assertEqual(accepted.catalog_packages[0].metadata.id, "workflow-node")
            self.assertTrue((accepted.catalog_roots[0] / ".context/package.json").is_file())

    def test_accept_rejects_dirty_exact_package_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-07-reusable-contexts.md"
            structure = self._structure()
            catalog, node = self._git_catalog(root)

            with (node / ".context" / "package.json").open("a", encoding="utf-8") as handle:
                handle.write("\n")

            with self.assertRaisesRegex(ContextCanonError, "uncommitted package artifact changes"):
                self._accept_workflow(workspace_file, snapshot, structure, catalog)

    def test_accepted_catalog_is_frozen_before_provider_advances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-07-reusable-contexts.md"
            structure = self._structure()
            catalog, node = self._git_catalog(root)

            accepted = self._accept_workflow(workspace_file, snapshot, structure, catalog)
            old_digest = accepted.catalog_packages[0].package_digest
            frozen_root = snapshot / "reusable-context-packages" / old_digest
            self.assertEqual(accepted.catalog_roots, (frozen_root,))
            self.assertTrue((frozen_root / ".context/package.json").is_file())

            self._advance_workflow(catalog, node)
            loaded = load_accepted_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            rerun, created = refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)

            self.assertFalse(created)
            self.assertEqual(loaded.catalog_packages[0].metadata.version, "0.2.0-draft")
            self.assertEqual(loaded.catalog_packages[0].package_digest, old_digest)
            self.assertEqual(loaded.catalog_roots, (frozen_root.resolve(),))
            self.assertEqual(rerun.catalog_packages[0].package_digest, old_digest)
            self.assertEqual(rerun.catalog_roots, (frozen_root,))

    def test_legacy_accepted_catalog_recovers_exact_package_from_git_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-07-reusable-contexts.md"
            structure = self._structure()
            catalog, node = self._git_catalog(root)

            accepted = self._accept_workflow(workspace_file, snapshot, structure, catalog)
            old_digest = accepted.catalog_packages[0].package_digest
            shutil.rmtree(snapshot / "reusable-context-packages")
            self._advance_workflow(catalog, node)

            loaded = load_accepted_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)

            frozen_root = snapshot / "reusable-context-packages" / old_digest
            self.assertEqual(loaded.catalog_packages[0].metadata.version, "0.2.0-draft")
            self.assertEqual(loaded.catalog_packages[0].package_digest, old_digest)
            self.assertEqual(loaded.catalog_roots, (frozen_root.resolve(),))
            provenance = json.loads(
                (frozen_root / ".context/onboarding-provenance.json").read_text(encoding="utf-8")
            )
            self.assertEqual(provenance["package_digest"], old_digest)
            self.assertEqual(provenance["node_path"], "development-workflow")
            self.assertRegex(provenance["ref"], r"^[0-9a-f]{40}$")

    def test_legacy_markdown_assignment_remains_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-07-reusable-contexts.md"
            structure = self._structure()
            catalog = self._catalog(root)

            refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            text = workspace_file.read_text(encoding="utf-8")
            text = text.replace(
                CATALOG_START + "\n" + CATALOG_END,
                CATALOG_START + f"\n- `{catalog}`\n" + CATALOG_END,
            )
            legacy = (
                "- **AI Workstation** (`.`) ← **Development Workflow** (`0.2.0-draft`)\n"
                "  Why: Legacy authored syntax remains valid.\n"
            )
            text = text.replace("contextcanon/onboarding-reusable-contexts/v1", "contextcanon/onboarding-reusable-contexts/v0")
            text = text.replace(
                ASSIGNMENTS_START + "\n```text\n```\n" + ASSIGNMENTS_END,
                ASSIGNMENTS_START + "\n" + legacy + ASSIGNMENTS_END,
            )
            workspace_file.write_text(text, encoding="utf-8")

            plan, _ = refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertEqual(plan.owner_source_specs, ("N-001=workflow-node",))
            canonical = workspace_file.read_text(encoding="utf-8")
            self.assertIn("AI Workstation (.) ← Development Workflow (0.2.0-draft) [Parent]", canonical)
            self.assertNotIn("- **AI Workstation**", canonical)

    def test_reference_assignment_persists_explicit_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-07-reusable-contexts.md"
            structure = self._structure()
            catalog = self._catalog(root)

            refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            text = workspace_file.read_text(encoding="utf-8")
            text = text.replace(
                CATALOG_START + "\n" + CATALOG_END,
                CATALOG_START + f"\n- `{catalog}`\n" + CATALOG_END,
            )
            text = text.replace("Decision: `pending`", "Decision: `accept`")
            assignment = (
                "AI Workstation (.) ← Development Workflow (0.2.0-draft) [Reference]\n"
                "Why: Useful background, but its workflow rules do not govern this project.\n"
            )
            text = text.replace(
                ASSIGNMENTS_START + "\n```text\n```\n" + ASSIGNMENTS_END,
                ASSIGNMENTS_START + "\n```text\n" + assignment + "```\n" + ASSIGNMENTS_END,
            )
            workspace_file.write_text(text, encoding="utf-8")

            accepted, _ = refresh_reusable_contexts(
                workspace_file, snapshot, "a" * 64, structure
            )

            self.assertEqual(accepted.assignments[0].relationship, "reference")
            self.assertEqual(
                accepted.owner_source_relationships["N-001=workflow-node"],
                "reference",
            )
            state = json.loads(
                (snapshot / "reusable-contexts.json").read_text(encoding="utf-8")
            )
            self.assertEqual(state["assignments"][0]["relationship"], "reference")
            self.assertIn(
                "Development Workflow (0.2.0-draft) [Reference]",
                workspace_file.read_text(encoding="utf-8"),
            )

    def test_legacy_accepted_state_keeps_exact_digest_and_defaults_to_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            path = root / "STEP-07-reusable-contexts.md"
            structure = self._structure()
            catalog = self._catalog(root)
            accepted = self._accept_workflow(path, snapshot, structure, catalog)
            text = path.read_text(encoding="utf-8").replace(
                "contextcanon/onboarding-reusable-contexts/v1", "contextcanon/onboarding-reusable-contexts/v0"
            ).replace(" [Parent]", "")
            path.write_text(text, encoding="utf-8")
            state_path = snapshot / "reusable-contexts.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["schema"] = "contextcanon/onboarding-reusable-contexts-state/v0"
            for assignment in state["assignments"]:
                assignment.pop("relationship")
            payload = {key: value for key, value in state.items()
                       if key not in {"review_digest", "human_file_sha256", "frozen_catalog_packages"}}
            state["review_digest"] = hashlib.sha256(json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")).hexdigest()
            state["human_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            state_path.write_text(json.dumps(state), encoding="utf-8")
            loaded = load_accepted_reusable_contexts(path, snapshot, "a" * 64, structure)
            self.assertEqual(loaded.assignments[0].relationship, "parent")
            self.assertEqual(loaded.review_digest, state["review_digest"])
            self.assertEqual(loaded.catalog_packages[0].package_digest, accepted.catalog_packages[0].package_digest)

    def test_catalog_locations_accept_plain_windows_path_and_common_wrappers(self) -> None:
        windows_path = r"C:\Users\u239230\PycharmProjects\context-canon\nodes\library"
        variants = (
            windows_path,
            f"- {windows_path}",
            f'"{windows_path}"',
            f"- `{windows_path}`",
        )
        for value in variants:
            with self.subTest(value=value):
                text = f"{CATALOG_START}\n{value}\n{CATALOG_END}\n"
                self.assertEqual(_catalog_locations(text), (windows_path,))

    def test_step05_marks_editable_areas_visibly_and_canonicalizes_plain_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-07-reusable-contexts.md"
            structure = self._structure()
            catalog = self._catalog(root)

            refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            text = workspace_file.read_text(encoding="utf-8")
            self.assertIn("> ✏️ **EDIT HERE — Catalog locations start below.**", text)
            self.assertIn("> **END EDITABLE Catalog locations.**", text)
            self.assertIn("> ✏️ **EDIT HERE — reusable-Context Assignments and Decision start below.**", text)
            self.assertIn("> **END EDITABLE reusable-Context Assignments.**", text)
            self.assertIn("Edit only", text)
            self.assertIn(r"Example path: `C:\Users\you\PycharmProjects\context-canon\nodes\library`", text)

            text = text.replace(
                CATALOG_START + "\n" + CATALOG_END,
                CATALOG_START + f"\n{catalog}\n" + CATALOG_END,
            )
            workspace_file.write_text(text, encoding="utf-8")
            plan, created = refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertFalse(created)
            self.assertEqual(plan.catalog_locations, (str(catalog),))
            canonical = workspace_file.read_text(encoding="utf-8")
            self.assertIn(f"- `{catalog}`", canonical)
            self.assertIn("Assignment syntax:", canonical)
            self.assertNotIn("## Copy-ready Assignment lines — generated", canonical)
            self.assertNotIn("Example first line using entries from this project", canonical)
            self.assertIn("- Copy: AI Workstation (.)", canonical)
            self.assertIn(
                "- Copy: Development Workflow (0.2.0-draft) — exact package",
                canonical,
            )
            self.assertIn("raw Markdown text", canonical)
            self.assertIn("up to but not including", canonical)


    def test_assignment_help_scales_linearly_without_cartesian_product(self) -> None:
        nodes = tuple(
            HumanStructureNode(
                f"N-{index:03d}",
                f"Project Node {index}",
                "." if index == 0 else f"area-{index}",
                "current",
                None if index == 0 else "N-000",
                f"N-{index:03d}",
            )
            for index in range(20)
        )
        structure = HumanStructurePlan(
            evidence_digest="a" * 64,
            proposal_digest="b" * 64,
            nodes=nodes,
            fixed_markdown=(),
            structure_digest="c" * 64,
        )
        packages = tuple(
            SimpleNamespace(
                metadata=SimpleNamespace(name=f"Reusable Node {index}", version=f"1.0.{index}"),
                package_digest=f"{index + 1:064x}",
            )
            for index in range(40)
        )

        rendered = render_reusable_contexts("a" * 64, structure, "pending", ("catalog",), packages, ())
        assignment_like = [line for line in rendered.splitlines() if line.startswith("- **") and " ← " in line]

        self.assertEqual(len(assignment_like), 0)  # generated choice lists never look like authored Assignments
        self.assertIn("Project Node 19", rendered)
        self.assertIn("Reusable Node 39", rendered)
        self.assertNotIn("Copy-ready Assignment lines", rendered)
        self.assertLess(len(rendered.splitlines()), 140)
        self.assertIn("copy everything after `Copy:`", rendered)


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
            relationship="parent",
            why="Shared development workflow applies to the whole project.",
        )
        rendered = "\n".join(_render_accepted_reusable_contexts((assignment,)))
        self.assertIn("already accepted", rendered)
        self.assertIn("AI Workstation", rendered)
        self.assertIn("Development Workflow", rendered)
        self.assertIn("[Parent]", rendered)
        self.assertIn("semantic Children", rendered)
        self.assertIn("Why: Shared development workflow applies to the whole project.", rendered)
        self.assertIn("must not reclassify", rendered)

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
                '<!-- ctx:node id="shared" name="Shared" version="1.0.0" -->\n',
                encoding="utf-8",
            )
            (consumer / "CONTEXT.src.md").write_text(
                "# Consumer — Local Context Source\n"
                '<!-- ctx:node id="consumer" name="Consumer" version="1.0.0" -->\n\n'
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
