from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_structure import (
    STRUCTURE_MARKDOWN_SCHEMA,
    STRUCTURE_PROPOSAL_SCHEMA,
    create_or_load_structure_markdown,
    load_onboarding_structure_proposal,
    load_structure_markdown,
)
from contextcanon.onboarding_structure_instruction import build_onboarding_structure_instruction
from contextcanon.onboarding_workspace import (
    DEFAULT_WORKSPACE_NAME,
    STRUCTURE_INSTRUCTION_NAME,
    STRUCTURE_PROPOSAL_NAME,
    STRUCTURE_REVIEW_NAME,
    WORKSPACE_MARKER,
    open_onboarding_workspace,
    write_utf8,
)
from contextcanon.parser import ContextCanonError


class OnboardingStructureTests(unittest.TestCase):
    def make_snapshot(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text(
            "# AI Workstation\n"
            "Install the Linux host reproducibly.\n"
            "Goose runs as an isolated container.\n"
            "Open WebUI is a separate application container.\n",
            encoding="utf-8",
        )
        prepared = prepare_onboarding_evidence(repo)
        entry = next(item for item in prepared.included if item.path == "README.md")
        return repo, prepared, entry

    def proposal_dict(self, prepared, entry):
        evidence = lambda start, end: [
            {
                "path": "README.md",
                "sha256": entry.sha256,
                "start_line": start,
                "end_line": end,
            }
        ]
        return {
            "schema": STRUCTURE_PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "nodes": [
                {
                    "key": "N-001",
                    "name": "AI Workstation",
                    "parent_key": None,
                    "suggested_path": ".",
                    "lifecycle": "current",
                    "purpose": "Orient all work on the workstation repository.",
                    "rationale": "The README presents one workstation project with separable runtime areas.",
                    "confidence": "high",
                    "evidence": evidence(1, 4),
                },
                {
                    "key": "N-002",
                    "name": "Host / WSL",
                    "parent_key": "N-001",
                    "suggested_path": "nodes/host-wsl",
                    "lifecycle": "current",
                    "purpose": "Start work on reproducible Linux host provisioning here.",
                    "rationale": "Host installation is a distinct project concern.",
                    "confidence": "high",
                    "evidence": evidence(2, 2),
                },
                {
                    "key": "N-003",
                    "name": "AI Tools",
                    "parent_key": "N-001",
                    "suggested_path": "nodes/ai-tools",
                    "lifecycle": "current",
                    "purpose": "Group independently managed AI application runtimes.",
                    "rationale": "The evidence describes multiple independent application containers.",
                    "confidence": "high",
                    "evidence": evidence(3, 4),
                },
                {
                    "key": "N-004",
                    "name": "Goose",
                    "parent_key": "N-003",
                    "suggested_path": "nodes/ai-tools/goose",
                    "lifecycle": "current",
                    "purpose": "Start Goose-specific runtime work here.",
                    "rationale": "Goose is an independently isolated container.",
                    "confidence": "high",
                    "evidence": evidence(3, 3),
                },
            ],
            "knowledge_bodies": [
                {
                    "key": "K-001",
                    "kind": "project-documentation",
                    "name": "Repository overview",
                    "suggested_node_key": "N-001",
                    "paths": ["README.md"],
                    "purpose": "Keep ordinary first-contact project documentation as documentation.",
                    "rationale": "The README should remain a familiar document rather than become a Context Node.",
                    "confidence": "high",
                    "evidence": evidence(1, 4),
                }
            ],
            "source_reuses": [],
        }

    def write_proposal(self, prepared, entry, path: Path | None = None):
        path = path or (Path(tempfile.mkdtemp()) / STRUCTURE_PROPOSAL_NAME)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.proposal_dict(prepared, entry), indent=2), encoding="utf-8")
        return path

    def test_structure_instruction_is_coarse_first_and_bound_to_same_evidence(self):
        _, prepared, _ = self.make_snapshot()
        first = build_onboarding_structure_instruction(prepared.snapshot_root)
        second = build_onboarding_structure_instruction(prepared.snapshot_root)

        self.assertEqual(first.text, second.text)
        self.assertEqual(first.instruction_digest, second.instruction_digest)
        self.assertEqual(first.evidence_digest, prepared.evidence_digest)
        self.assertIn("designing the shelves before placing the books", first.text)
        self.assertIn("primary hierarchy", first.text)
        self.assertIn("project's apparent mental model", first.text)
        self.assertIn("non-Node knowledge bodies", first.text)
        self.assertIn("authoritative-reference", first.text)
        self.assertIn("Markdown knowledge-body paths only", first.text)
        self.assertIn("Non-Markdown authorities such as PDF", first.text)
        self.assertIn("Individual Rules, Topics, state/planning items", first.text)
        self.assertIn('"schema": "contextcanon/onboarding-structure-proposal/v0"', first.text)

    def test_structure_proposal_validates_primary_hierarchy_and_exact_evidence(self):
        _, prepared, entry = self.make_snapshot()
        proposal_path = self.write_proposal(prepared, entry)

        first = load_onboarding_structure_proposal(proposal_path, prepared.snapshot_root)
        second = load_onboarding_structure_proposal(proposal_path, prepared.snapshot_root)

        self.assertEqual(first.proposal_digest, second.proposal_digest)
        self.assertEqual([node.key for node in first.nodes], ["N-001", "N-002", "N-003", "N-004"])
        self.assertEqual(first.nodes_by_key["N-004"].parent_key, "N-003")
        self.assertEqual(first.knowledge_bodies[0].kind, "project-documentation")

    def test_structure_proposal_rejects_child_path_outside_primary_parent(self):
        _, prepared, entry = self.make_snapshot()
        raw = self.proposal_dict(prepared, entry)
        raw["nodes"][3]["suggested_path"] = "nodes/goose"
        proposal_path = Path(tempfile.mkdtemp()) / "bad.json"
        proposal_path.write_text(json.dumps(raw), encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "must be nested under parent path"):
            load_onboarding_structure_proposal(proposal_path, prepared.snapshot_root)

    def test_structure_proposal_rejects_wrong_evidence_hash(self):
        _, prepared, entry = self.make_snapshot()
        raw = self.proposal_dict(prepared, entry)
        raw["nodes"][0]["evidence"][0]["sha256"] = "0" * 64
        proposal_path = Path(tempfile.mkdtemp()) / "bad.json"
        proposal_path.write_text(json.dumps(raw), encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "evidence hash does not match snapshot"):
            load_onboarding_structure_proposal(proposal_path, prepared.snapshot_root)

    def test_structure_markdown_is_editable_tree_with_evidence_details(self):
        _, prepared, entry = self.make_snapshot()
        proposal_path = self.write_proposal(prepared, entry)
        structure_path = Path(tempfile.mkdtemp()) / STRUCTURE_REVIEW_NAME

        plan, proposal, _, created = create_or_load_structure_markdown(
            prepared.snapshot_root,
            proposal_path,
            structure_path,
        )

        self.assertTrue(created)
        text = structure_path.read_text(encoding="utf-8")
        self.assertIn(f"schema: {STRUCTURE_MARKDOWN_SCHEMA}", text)
        self.assertIn("> ✏️ Edit the Node tree between the markers below.", text)
        self.assertIn("> End editable Node tree.", text)
        self.assertIn("- **AI Workstation** (`.`) <!-- cc:key=N-001 -->", text)
        self.assertIn("  - **AI Tools** (`nodes/ai-tools`) <!-- cc:key=N-003 -->", text)
        self.assertIn("    - **Goose** (`nodes/ai-tools/goose`) <!-- cc:key=N-004 -->", text)
        self.assertIn("## Fixed Markdown", text)
        self.assertIn("Ordinary project-documentation Markdown is mutable by default", text)
        self.assertIn("authoritative-reference", text)
        self.assertIn("imported-corpus", text)
        self.assertIn("<!-- contextcanon-fixed-markdown:start -->", text)
        self.assertIn("## Proposal details", text)
        self.assertIn("3: Goose runs as an isolated container.", text)
        self.assertEqual(plan.proposal_digest, proposal.proposal_digest)

        edited = text.replace(
            "    - **Goose** (`nodes/ai-tools/goose`) <!-- cc:key=N-004 -->",
            "    - **Goose** (`nodes/ai-tools/goose`) <!-- cc:key=N-004 -->\n"
            "    - **Hermes** (`nodes/ai-tools/hermes`) [reserved]",
        )
        structure_path.write_text(edited, encoding="utf-8")
        edited = edited.replace(
            "<!-- contextcanon-fixed-markdown:start -->\n<!-- contextcanon-fixed-markdown:end -->",
            "<!-- contextcanon-fixed-markdown:start -->\n- `README.md`\n<!-- contextcanon-fixed-markdown:end -->",
        )
        structure_path.write_text(edited, encoding="utf-8")
        changed = load_structure_markdown(structure_path, proposal)

        self.assertEqual(changed.fixed_markdown, ("README.md",))
        self.assertEqual(len(changed.nodes), 5)
        hermes = changed.nodes[-1]
        self.assertEqual(hermes.name, "Hermes")
        self.assertEqual(hermes.lifecycle, "reserved")
        self.assertEqual(hermes.parent_key, "N-003")
        self.assertTrue(hermes.key.startswith("H-"))
        self.assertNotEqual(changed.structure_digest, plan.structure_digest)

    def test_structure_markdown_rejects_stale_proposal_binding(self):
        _, prepared, entry = self.make_snapshot()
        proposal_path = self.write_proposal(prepared, entry)
        structure_path = Path(tempfile.mkdtemp()) / STRUCTURE_REVIEW_NAME
        _, proposal, _, _ = create_or_load_structure_markdown(
            prepared.snapshot_root,
            proposal_path,
            structure_path,
        )
        text = structure_path.read_text(encoding="utf-8")
        structure_path.write_text(text.replace(proposal.proposal_digest, "0" * 64), encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "proposal_digest does not match"):
            load_structure_markdown(structure_path, proposal)

    def test_visible_workspace_is_owned_and_utf8_without_shell_redirection(self):
        repo, prepared, _ = self.make_snapshot()
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)

        self.assertEqual(workspace.root, repo / DEFAULT_WORKSPACE_NAME)
        readme = workspace.readme_path.read_text(encoding="utf-8")
        self.assertIn(WORKSPACE_MARKER, readme)
        self.assertIn("Why frozen Evidence exists", readme)
        self.assertIn(STRUCTURE_INSTRUCTION_NAME, readme)
        self.assertIn(STRUCTURE_PROPOSAL_NAME, readme)
        self.assertIn(STRUCTURE_REVIEW_NAME, readme)

        text = "Grüezi – äöü – UTF-8\n"
        write_utf8(workspace.structure_instruction_path, text)
        raw = workspace.structure_instruction_path.read_bytes()
        self.assertEqual(raw, text.encode("utf-8"))
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))

    def test_workspace_refuses_existing_unowned_directory(self):
        repo, prepared, _ = self.make_snapshot()
        root = repo / DEFAULT_WORKSPACE_NAME
        root.mkdir()
        (root / "README.md").write_text("# Project-owned directory\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "Refusing to take over existing directory"):
            open_onboarding_workspace(prepared.snapshot_root, create=True)

    def test_cli_structure_commands_use_standard_workspace_without_redirects(self):
        repo, prepared, entry = self.make_snapshot()
        workspace_root = repo / DEFAULT_WORKSPACE_NAME

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = main(["onboard", "structure-instruction", str(prepared.snapshot_root)])
        self.assertEqual(result, 0)
        self.assertEqual(stderr.getvalue(), "")
        instruction_path = workspace_root / STRUCTURE_INSTRUCTION_NAME
        proposal_path = workspace_root / STRUCTURE_PROPOSAL_NAME
        structure_path = workspace_root / STRUCTURE_REVIEW_NAME
        self.assertTrue(instruction_path.exists())
        self.assertTrue(instruction_path.read_text(encoding="utf-8").startswith(
            "# ContextCanon Onboarding Structure Discovery Instruction\n"
        ))
        self.assertNotIn("# ContextCanon Onboarding Structure Discovery Instruction", stdout.getvalue())
        self.assertIn(str(proposal_path), stdout.getvalue())

        self.write_proposal(prepared, entry, proposal_path)

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(["onboard", "structure-validate", str(prepared.snapshot_root)])
        self.assertEqual(result, 0)
        self.assertIn("validated onboarding structure proposal", stdout.getvalue())
        self.assertIn(str(proposal_path), stdout.getvalue())
        self.assertIn("Proposed Nodes: 4", stdout.getvalue())

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(["onboard", "structure-review", str(prepared.snapshot_root)])
        self.assertEqual(result, 0)
        self.assertTrue(structure_path.exists())
        self.assertIn("created onboarding structure", stdout.getvalue())
        self.assertIn(str(structure_path), stdout.getvalue())
        self.assertIn("Nodes in edited tree: 4", stdout.getvalue())

    def test_cli_stdout_and_explicit_paths_remain_available(self):
        _, prepared, entry = self.make_snapshot()

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = main(["onboard", "structure-instruction", str(prepared.snapshot_root), "--stdout"])
        self.assertEqual(result, 0)
        self.assertTrue(stdout.getvalue().startswith("# ContextCanon Onboarding Structure Discovery Instruction\n"))
        self.assertIn("structure instruction digest", stderr.getvalue())

        proposal_path = self.write_proposal(prepared, entry)
        structure_path = Path(tempfile.mkdtemp()) / "custom-structure.md"

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(
                ["onboard", "structure-validate", str(prepared.snapshot_root), str(proposal_path)]
            )
        self.assertEqual(result, 0)

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(
                [
                    "onboard",
                    "structure-review",
                    str(prepared.snapshot_root),
                    str(proposal_path),
                    str(structure_path),
                ]
            )
        self.assertEqual(result, 0)
        self.assertTrue(structure_path.exists())


if __name__ == "__main__":
    unittest.main()
