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
from contextcanon.onboarding_structure import STRUCTURE_PROPOSAL_SCHEMA, create_or_load_structure_markdown
from contextcanon.onboarding_structure_materialize import (
    materialize_structure_skeletons,
    preview_structure_materialization,
    render_structure_materialization_preview,
)
from contextcanon.onboarding_workspace import open_onboarding_workspace
from contextcanon.outputs import write_outputs
from contextcanon.compiler import Compiler
from contextcanon.parser import ContextCanonError, parse_node


ROOT_ID = "aea56adf-2a26-43f0-b712-3bbeab7a3097"


class StructureMaterializationTests(unittest.TestCase):
    def make_project(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text(
            "# AI Workstation\nBootstrap Windows and Linux.\nGoose and Open WebUI are containerized applications.\n",
            encoding="utf-8",
        )
        (repo / "CONTEXT.src.md").write_text(
            "# ai-workstation — Local Context Source\n"
            f'<!-- ctx:node id="{ROOT_ID}" version="0.1.0" -->\n\n'
            "## Overview\n\nExisting accepted root.\n",
            encoding="utf-8",
        )
        for path in ("bootstrap/windows", "bootstrap/linux", "bin", "compose/goose", "compose/open-webui"):
            (repo / path).mkdir(parents=True, exist_ok=True)
        prepared = prepare_onboarding_evidence(repo)
        entry = next(item for item in prepared.included if item.path == "README.md")
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        raw = {
            "schema": STRUCTURE_PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "nodes": [],
            "knowledge_bodies": [],
            "source_reuses": [],
        }
        specs = [
            ("N-001", "AI Workstation", None, "."),
            ("N-002", "Bootstrap", "N-001", "bootstrap"),
            ("N-003", "Windows and WSL bootstrap", "N-002", "bootstrap/windows"),
            ("N-004", "Linux bootstrap", "N-002", "bootstrap/linux"),
            ("N-005", "aiw operator interface", "N-001", "bin"),
            ("N-006", "Containerized application runtimes", "N-001", "compose"),
            ("N-007", "Goose", "N-006", "compose/goose"),
            ("N-008", "Open WebUI", "N-006", "compose/open-webui"),
        ]
        for key, name, parent, path in specs:
            raw["nodes"].append(
                {
                    "key": key,
                    "name": name,
                    "parent_key": parent,
                    "suggested_path": path,
                    "lifecycle": "current",
                    "purpose": f"Start {name} work here.",
                    "rationale": "Evidence supports this accepted work area.",
                    "confidence": "high",
                    "evidence": [
                        {
                            "path": "README.md",
                            "sha256": entry.sha256,
                            "start_line": 1,
                            "end_line": 3,
                        }
                    ],
                }
            )
        workspace.structure_proposal_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        create_or_load_structure_markdown(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        return repo, prepared, workspace

    def test_preview_protects_existing_root_and_finds_seven_missing_nodes(self):
        repo, prepared, workspace = self.make_project()
        root_before = (repo / "CONTEXT.src.md").read_bytes()

        preview = preview_structure_materialization(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )

        self.assertEqual(len(preview.items), 8)
        self.assertEqual(preview.items[0].status, "existing")
        self.assertEqual(preview.items[0].existing_node_id, ROOT_ID)
        self.assertEqual(sum(item.status == "create" for item in preview.items), 7)
        self.assertTrue(next(item for item in preview.items if item.path == "compose/goose").directory_exists)
        self.assertIn("No project files were changed", render_structure_materialization_preview(preview))
        self.assertEqual((repo / "CONTEXT.src.md").read_bytes(), root_before)

    def test_materialize_creates_only_missing_skeletons_and_is_idempotent(self):
        repo, prepared, workspace = self.make_project()
        root_before = (repo / "CONTEXT.src.md").read_bytes()
        preview = preview_structure_materialization(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )

        created = materialize_structure_skeletons(preview)
        self.assertEqual(len(created), 7)
        self.assertEqual((repo / "CONTEXT.src.md").read_bytes(), root_before)
        self.assertTrue((repo / "bootstrap" / "CONTEXT.src.md").is_file())
        self.assertTrue((repo / "compose" / "goose" / "CONTEXT.md").is_file())
        self.assertTrue((repo / "compose" / "open-webui" / ".context" / "package.json").is_file())
        child_ids = {parse_node(path.parent, repo).metadata.id for path in created}
        self.assertEqual(len(child_ids), 7)
        self.assertNotIn(ROOT_ID, child_ids)

        second = preview_structure_materialization(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        self.assertTrue(all(item.status == "existing" for item in second.items))
        self.assertEqual(materialize_structure_skeletons(second), ())

    def test_preview_refuses_project_owned_context_output_collision(self):
        repo, prepared, workspace = self.make_project()
        (repo / "bootstrap" / "CONTEXT.md").write_text("project-owned\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "project-owned path already exists: CONTEXT.md"):
            preview_structure_materialization(
                prepared.snapshot_root,
                workspace.structure_proposal_path,
                workspace.structure_path,
            )
        self.assertFalse((repo / "bootstrap" / "CONTEXT.src.md").exists())

    def test_preview_recovers_missing_root_source_from_generated_contextcanon_state(self):
        repo, prepared, workspace = self.make_project()
        write_outputs(Compiler(repo).compile(repo))
        context_dir = repo / "CONTEXT"
        context_dir.mkdir(exist_ok=True)
        (context_dir / "README.md").write_text(
            "# Generated Context package resources\n\n> [!CAUTION]\n> **GENERATED DIRECTORY — DO NOT EDIT THESE FILES.**\n",
            encoding="utf-8",
        )
        (repo / "CONTEXT.src.md").unlink()
        (repo / "CONTEXT.md").unlink()

        preview = preview_structure_materialization(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        root = next(item for item in preview.items if item.path == ".")
        self.assertEqual(root.status, "recover")
        self.assertEqual(root.existing_node_id, ROOT_ID)
        self.assertIn("recover missing `CONTEXT.src.md`", render_structure_materialization_preview(preview))

        created = materialize_structure_skeletons(preview)
        self.assertEqual(len(created), 8)
        recovered = parse_node(repo, repo)
        self.assertEqual(recovered.metadata.id, ROOT_ID)
        self.assertEqual(recovered.metadata.version, "0.1.0")

    def test_root_recovery_still_refuses_foreign_context_directory(self):
        repo, prepared, workspace = self.make_project()
        write_outputs(Compiler(repo).compile(repo))
        (repo / "CONTEXT.src.md").unlink()
        (repo / "CONTEXT.md").unlink()
        context_dir = repo / "CONTEXT"
        context_dir.mkdir(exist_ok=True)
        (context_dir / "foreign.txt").write_text("project-owned\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "project-owned path already exists: CONTEXT"):
            preview_structure_materialization(
                prepared.snapshot_root,
                workspace.structure_proposal_path,
                workspace.structure_path,
            )

    def test_cli_preview_then_materialize_uses_standard_workspace(self):
        repo, prepared, workspace = self.make_project()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(["onboard", "structure-preview", str(prepared.snapshot_root)])
        self.assertEqual(result, 0)
        self.assertTrue(workspace.structure_preview_path.is_file())
        self.assertIn("Existing protected Nodes: 1", stdout.getvalue())
        self.assertIn("Missing Node skeletons: 7", stdout.getvalue())

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(["onboard", "structure-materialize", str(prepared.snapshot_root)])
        self.assertEqual(result, 0)
        self.assertIn("Materialized Node skeletons: 7", stdout.getvalue())
        self.assertTrue((repo / "compose" / "goose" / "CONTEXT.src.md").is_file())


if __name__ == "__main__":
    unittest.main()
