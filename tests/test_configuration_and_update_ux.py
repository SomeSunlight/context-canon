from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main as cli_main
from contextcanon.compiler import Compiler
from contextcanon.config import configured_source, load_project_config, upsert_git_source, upsert_local_mapping
from contextcanon.git_transport import fetch_git_candidate
from contextcanon.outputs import check_outputs, write_outputs
from contextcanon.package import artifact_files
from contextcanon.parser import parse_node
from contextcanon.sources import accept_parent_candidate, review_parent_candidate


def write_node(root: Path, node_id: str, name: str, version: str, statement: str) -> object:
    root.mkdir(parents=True, exist_ok=True)
    (root / "CONTEXT.src.md").write_text(
        f'''# {name} — Local Context Source\n<!-- ctx:node id="{node_id}" name="{name}" version="{version}" -->\n\n## Local Rules\n\n### General\n\n- **Policy:** {statement}\n  Why: Test policy.\n  <!-- ctx:rule id="RULE-1" -->\n''',
        encoding="utf-8",
    )
    compiled = Compiler(root if (root / ".git").exists() else root.parent).compile(root)
    write_outputs(compiled)
    return Compiler(root if (root / ".git").exists() else root.parent).compile(root)


def install_package(child: Path, compiled) -> None:
    destination = child / ".context" / "sources" / compiled.package_digest
    for rel, content in artifact_files(compiled).items():
        path = destination / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def parent_source(child_id: str, child_name: str, parent_path: str, parent) -> str:
    return f'''# {child_name} — Local Context Source\n<!-- ctx:node id="{child_id}" name="{child_name}" version="0.1.0" -->\n\n## Parent Context Node\n\n- [{parent.metadata.name}]({parent_path}) — `{parent.metadata.version}`\n  <!-- ctx:parent id="{parent.metadata.id}" version="{parent.metadata.version}" normalized-digest="{parent.normalized_digest}" package-digest="{parent.package_digest}" -->\n'''


class ConfigurationAndUpdateUXTests(unittest.TestCase):
    def test_cli_version_is_available(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as raised:
            cli_main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), "contextcanon 0.7.2")

    def test_central_yaml_can_switch_same_source_to_pure_local_discovery(self):
        project = Path(tempfile.mkdtemp())
        source_repo = Path(tempfile.mkdtemp())
        try:
            (project / ".git").mkdir()
            (source_repo / ".git").mkdir()
            source = write_node(source_repo, "source-id", "Shared", "1.0.0", "Old meaning.")
            consumer = project
            (consumer / "CONTEXT.src.md").write_text(
                f'''# Consumer — Local Context Source\n<!-- ctx:node id="consumer" name="Consumer" version="0.1.0" -->\n\n## Sources\n\n- [Shared](contextcanon.yaml) — `1.0.0`\n  <!-- ctx:source id="source-id" version="1.0.0" normalized-digest="{source.normalized_digest}" package-digest="{source.package_digest}" -->\n''',
                encoding="utf-8",
            )
            install_package(consumer, source)
            upsert_local_mapping(project, "source-id", source_repo, ".")
            config = load_project_config(project)
            self.assertEqual(config.repositories[config.sources["source-id"].repository].kind, "local")
            candidate, _ = fetch_git_candidate(consumer, "source-id")
            self.assertEqual(candidate.package_digest, source.package_digest)
        finally:
            shutil.rmtree(project, ignore_errors=True)
            shutil.rmtree(source_repo, ignore_errors=True)

    def test_explicit_ref_fetches_unmerged_git_candidate_without_rewriting_config(self):
        project = Path(tempfile.mkdtemp())
        provider = Path(tempfile.mkdtemp())
        try:
            (project / ".git").mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main", str(provider)], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.name", "Test"], check=True)
            main_package = write_node(provider, "source-id", "Shared", "1.0.0", "Main meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "main"], check=True)
            subprocess.run(["git", "-C", str(provider), "checkout", "-qb", "feature"], check=True)
            feature_package = write_node(provider, "source-id", "Shared", "1.1.0", "Feature meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "feature"], check=True)

            consumer = project
            (consumer / "CONTEXT.src.md").write_text(
                f'''# Consumer — Local Context Source\n<!-- ctx:node id="consumer" name="Consumer" version="0.1.0" -->\n\n## Sources\n\n- [Shared](contextcanon.yaml) — `1.0.0`\n  <!-- ctx:source id="source-id" version="1.0.0" normalized-digest="{main_package.normalized_digest}" package-digest="{main_package.package_digest}" -->\n''',
                encoding="utf-8",
            )
            install_package(consumer, main_package)
            upsert_git_source(project, "source-id", str(provider), "main", ".")
            candidate, _ = fetch_git_candidate(consumer, "source-id", discovery_ref="feature")
            self.assertEqual(candidate.package_digest, feature_package.package_digest)
            source_cfg, repo_cfg = configured_source(project, "source-id")
            self.assertEqual(repo_cfg.ref, "main")
        finally:
            shutil.rmtree(project, ignore_errors=True)
            shutil.rmtree(provider, ignore_errors=True)

    def test_guided_update_migrates_legacy_git_discovery_without_persisting_one_off_ref(self):
        project = Path(tempfile.mkdtemp())
        provider = Path(tempfile.mkdtemp())
        try:
            (project / ".git").mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main", str(provider)], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.name", "Test"], check=True)
            main_package = write_node(provider, "source-id", "Shared", "1.0.0", "Main meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "main"], check=True)
            main_head = subprocess.run(
                ["git", "-C", str(provider), "rev-parse", "HEAD"], check=True, text=True, capture_output=True
            ).stdout.strip()
            subprocess.run(["git", "-C", str(provider), "checkout", "-qb", "feature"], check=True)
            feature_package = write_node(provider, "source-id", "Shared", "1.1.0", "Feature meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "feature"], check=True)

            consumer = project
            (consumer / "CONTEXT.src.md").write_text(
                f'''# Consumer — Local Context Source\n<!-- ctx:node id="consumer" name="Consumer" version="0.1.0" -->\n\n## Sources\n\n- [Shared]({provider.as_posix()}) — `1.0.0`\n  <!-- ctx:source id="source-id" version="1.0.0" normalized-digest="{main_package.normalized_digest}" package-digest="{main_package.package_digest}" transport="git" ref="{main_head}" node-path="." -->\n''',
                encoding="utf-8",
            )
            install_package(consumer, main_package)

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cli_main(["source", "update", "Shared", "--node", str(consumer), "--ref", "feature", "--yes"])
            self.assertEqual(rc, 0, out.getvalue())
            self.assertIn("Discovery setup note:", out.getvalue())
            self.assertIn("Legacy Source lookup settings were moved to", out.getvalue())
            self.assertIn("This command is offering an update to Consumer; its Context has not changed yet.", out.getvalue())
            self.assertIn("That only changes where future candidates are found; it does not apply this Source update.", out.getvalue())
            self.assertIn("Current local Source:", out.getvalue())
            self.assertIn("New candidate found:", out.getvalue())
            self.assertIn("What changed in Source \"Shared\" since the version used here:", out.getvalue())
            self.assertIn("Local update offered for Node \"Consumer\":", out.getvalue())
            self.assertIn("Effective Context after existing local Overrides/Removes and other imports: 1 rule changed", out.getvalue())
            self.assertIn("Before choosing Y, check:", out.getvalue())
            self.assertNotIn("\nNodes:\n", out.getvalue())

            source_cfg, repo_cfg = configured_source(project, "source-id")
            self.assertEqual(repo_cfg.kind, "git")
            self.assertEqual(repo_cfg.location, provider.as_posix())
            self.assertIsNone(repo_cfg.ref)
            self.assertEqual(source_cfg.node_path, ".")
            accepted = Compiler(project).compile(project).source_packages[0]
            self.assertEqual(accepted.package_digest, feature_package.package_digest)
            self.assertIn('ref="', (consumer / "CONTEXT.src.md").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(project, ignore_errors=True)
            shutil.rmtree(provider, ignore_errors=True)

    def test_source_update_explains_downstream_parent_child_review_and_guided_command(self):
        project = Path(tempfile.mkdtemp())
        provider = Path(tempfile.mkdtemp())
        try:
            (project / ".git").mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main", str(provider)], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.name", "Test"], check=True)
            old_source = write_node(provider, "source-id", "Shared", "1.0.0", "Old meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "old"], check=True)
            subprocess.run(["git", "-C", str(provider), "checkout", "-qb", "feature"], check=True)
            write_node(provider, "source-id", "Shared", "1.1.0", "New meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "new"], check=True)

            (project / "CONTEXT.src.md").write_text(
                f'''# Consumer — Local Context Source\n<!-- ctx:node id="consumer" name="Consumer" version="0.1.0" -->\n\n## Sources\n\n- [Shared](contextcanon.yaml) — `1.0.0`\n  <!-- ctx:source id="source-id" version="1.0.0" normalized-digest="{old_source.normalized_digest}" package-digest="{old_source.package_digest}" -->\n''',
                encoding="utf-8",
            )
            install_package(project, old_source)
            upsert_git_source(project, "source-id", str(provider), "main", ".")
            current_consumer = Compiler(project).compile(project)
            write_outputs(current_consumer)

            child_root = project / "child"
            child_root.mkdir()
            (child_root / "CONTEXT.src.md").write_text(
                parent_source("child", "Child", "..", current_consumer),
                encoding="utf-8",
            )
            install_package(child_root, current_consumer)
            write_outputs(Compiler(project).compile(child_root))

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cli_main(["source", "update", "Shared", "--node", str(project), "--ref", "feature", "--yes"])
            self.assertEqual(rc, 0, out.getvalue())
            self.assertIn("What comes after this local update:", out.getvalue())
            self.assertIn("Consumer -> Child (child)", out.getvalue())
            self.assertIn("review that chain top-down in one guided run:", out.getvalue())
            self.assertIn("contextcanon propagate", out.getvalue())
            self.assertIn("asks separately before applying each changed Parent -> Child step", out.getvalue())
        finally:
            shutil.rmtree(project, ignore_errors=True)
            shutil.rmtree(provider, ignore_errors=True)

    def test_source_list_and_update_use_accepted_package_name_when_consumer_label_is_stale(self):
        project = Path(tempfile.mkdtemp())
        provider = Path(tempfile.mkdtemp())
        try:
            (project / ".git").mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main", str(provider)], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.name", "Test"], check=True)
            main_package = write_node(provider, "source-id", "Shared Canonical", "1.0.0", "Main meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "main"], check=True)
            main_head = subprocess.run(
                ["git", "-C", str(provider), "rev-parse", "HEAD"], check=True, text=True, capture_output=True
            ).stdout.strip()
            subprocess.run(["git", "-C", str(provider), "checkout", "-qb", "feature"], check=True)
            feature_package = write_node(provider, "source-id", "Shared Canonical", "1.1.0", "Feature meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "feature"], check=True)

            consumer = project
            source_text = (
                '# Consumer — Local Context Source\n'
                '<!-- ctx:node id="consumer" name="Consumer" version="0.1.0" -->\n\n'
                '## Sources\n\n'
                f'- [stale accidental label]({provider.as_posix()}) — `1.0.0`\n'
                f'  <!-- ctx:source id="source-id" version="1.0.0" normalized-digest="{main_package.normalized_digest}" package-digest="{main_package.package_digest}" transport="git" ref="{main_head}" node-path="." -->\n'
            )
            (consumer / "CONTEXT.src.md").write_text(source_text, encoding="utf-8")
            install_package(consumer, main_package)
            write_outputs(Compiler(project).compile(project))
            self.assertIn(
                "Source label mismatch for source-id: 'stale accidental label' != accepted package name 'Shared Canonical'",
                check_outputs(Compiler(project).compile(project)),
            )

            listed = io.StringIO()
            with contextlib.redirect_stdout(listed):
                rc = cli_main(["source", "list", "--node", str(consumer)])
            self.assertEqual(rc, 0, listed.getvalue())
            self.assertIn("Shared Canonical | source-id | using 1.0.0", listed.getvalue())
            self.assertIn("consumer display label is 'stale accidental label'", listed.getvalue())

            updated = io.StringIO()
            with contextlib.redirect_stdout(updated):
                rc = cli_main(["source", "update", "Shared Canonical", "--node", str(consumer), "--ref", "feature", "--yes"])
            self.assertEqual(rc, 0, updated.getvalue())
            self.assertEqual(Compiler(project).compile(project).source_packages[0].package_digest, feature_package.package_digest)
            self.assertIn("- [Shared Canonical]", (consumer / "CONTEXT.src.md").read_text(encoding="utf-8"))
            self.assertNotIn("stale accidental label", (consumer / "CONTEXT.src.md").read_text(encoding="utf-8"))
            write_outputs(Compiler(project).compile(project))
            self.assertEqual(check_outputs(Compiler(project).compile(project)), [])
        finally:
            shutil.rmtree(project, ignore_errors=True)
            shutil.rmtree(provider, ignore_errors=True)

    def test_check_reports_stale_parent_display_name(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            parent = write_node(repo, "root", "Canonical Parent", "1.0.0", "Meaning.")
            child_root = repo / "child"
            child_root.mkdir()
            source = parent_source("child", "Child", "..", parent).replace("[Canonical Parent]", "[stale parent label]")
            (child_root / "CONTEXT.src.md").write_text(source, encoding="utf-8")
            install_package(child_root, parent)
            compiled = Compiler(repo).compile(child_root)
            write_outputs(compiled)
            self.assertIn(
                "Parent label mismatch for root: 'stale parent label' != accepted package name 'Canonical Parent'",
                check_outputs(Compiler(repo).compile(child_root)),
            )
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_parent_propagate_updates_chain_top_down_in_one_command(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            parent = write_node(repo, "root", "Root", "1.0.0", "Initial meaning.")
            child_root = repo / "child"
            child_root.mkdir()
            (child_root / "CONTEXT.src.md").write_text(parent_source("child", "Child", "..", parent), encoding="utf-8")
            install_package(child_root, parent)
            child = Compiler(repo).compile(child_root)
            write_outputs(child)

            grand_root = child_root / "grand"
            grand_root.mkdir()
            (grand_root / "CONTEXT.src.md").write_text(parent_source("grand", "Grand", "..", child), encoding="utf-8")
            install_package(grand_root, child)
            write_outputs(Compiler(repo).compile(grand_root))

            write_node(repo, "root", "Root", "1.1.0", "Updated meaning.")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cli_main(["parent", "propagate", str(repo), "--yes"])
            self.assertEqual(rc, 0, out.getvalue())
            grand = Compiler(repo).compile(grand_root)
            self.assertEqual([rule.statement for rule in grand.inherited_rules], ["Updated meaning."])
            self.assertIn("Propagation review complete: applied 2 changed Parent/Child update(s).", out.getvalue())
        finally:
            shutil.rmtree(repo, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
