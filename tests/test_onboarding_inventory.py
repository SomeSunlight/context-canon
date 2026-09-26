from __future__ import annotations

import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main as cli_main
from contextcanon.onboarding_structure_instruction import build_onboarding_structure_instruction
from contextcanon.onboarding_proposal import load_evidence_snapshot
from contextcanon.onboarding_inventory import (
    INVENTORY_COLUMNS,
    prepare_from_inventory,
    refresh_inventory,
)
from contextcanon.parser import ContextCanonError


class OnboardingInventoryTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        return root

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream))

    def write_csv(self, path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=INVENTORY_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def describe_sources(self, path: Path) -> None:
        rows = self.read_csv(path)
        for row in rows:
            if row["handling"] in {"source", "interpret"} and not row["description"]:
                row["description"] = f"Reviewed purpose of {row['path']}"
        self.write_csv(path, rows)

    def test_inventory_scopes_multiple_directories_and_applies_readable_defaults(self):
        repo = self.make_repo()
        (repo / "Jira").mkdir()
        (repo / "Jira/feature-template.md").write_text("# Feature template\n", encoding="utf-8")
        (repo / "P1/F1").mkdir(parents=True)
        (repo / "P1/parameters.csv").write_text("name,default\nanswer,42\n", encoding="utf-8")
        (repo / "P1/F1/prestudy.md").write_text("# Prestudy\nMaybe A, maybe B.\n", encoding="utf-8")
        (repo / "src").mkdir()
        (repo / "src/main.py").write_text("print('hello')\n", encoding="utf-8")

        csv_path = repo / "inventory.csv"
        result = refresh_inventory(repo, csv_path, directories=["Jira", "P1"])
        rows = {row.path: row for row in result.rows}

        self.assertEqual(set(rows), {"Jira/feature-template.md", "P1/F1/prestudy.md", "P1/parameters.csv"})
        self.assertEqual((rows["Jira/feature-template.md"].kind, rows["Jira/feature-template.md"].handling), ("document", "source"))
        self.assertEqual((rows["P1/parameters.csv"].kind, rows["P1/parameters.csv"].handling), ("structured-data", "source"))
        self.assertEqual((rows["P1/F1/prestudy.md"].kind, rows["P1/F1/prestudy.md"].handling), ("raw-record", "interpret"))
        self.assertEqual(rows["P1/parameters.csv"].description, "Structured parameter data.")

    def test_onboard_init_creates_plan_and_inventory_guide_before_inventory(self):
        repo = self.make_repo()

        result = cli_main(["onboard", "init", str(repo)])

        self.assertEqual(result, 0)
        workspace = repo / "contextcanon-onboarding"
        self.assertTrue((workspace / "README.md").is_file())
        self.assertTrue((workspace / "PLAN.md").is_file())
        self.assertTrue((workspace / "STEP-02-inventory-guide.md").is_file())
        self.assertFalse((workspace / "STEP-02-inventory.csv").exists())
        guide = (workspace / "STEP-02-inventory-guide.md").read_text(encoding="utf-8")
        self.assertIn("Do not hand-edit", guide)
        self.assertIn("unchanged", guide)
        self.assertIn("same basename", guide)

    def test_embedded_git_directory_entry_is_visible_but_safe_and_must_remain_ignored(self):
        repo = self.make_repo()
        nested = repo / "P1" / "F1"
        nested.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(nested)], check=True)
        (nested / "README.md").write_text("# Nested\n", encoding="utf-8")

        listed = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "--cached", "--others", "--exclude-standard"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.splitlines()
        self.assertIn("P1/F1/", listed)

        csv_path = repo / "inventory.csv"
        refreshed = refresh_inventory(repo, csv_path)
        row = {item.path: item for item in refreshed.rows}["P1/F1"]

        self.assertEqual((row.kind, row.handling), ("other", "ignore"))
        self.assertEqual(row.rule, "git-directory-entry")
        self.assertIn("embedded repository", row.hint)
        self.assertEqual(row.sha256, "")

        rows = self.read_csv(csv_path)
        rows[0]["handling"] = "source"
        rows[0]["description"] = "Nested project."
        self.write_csv(csv_path, rows)
        with self.assertRaisesRegex(ContextCanonError, "not a regular file.*embedded Git repository"):
            prepare_from_inventory(repo, csv_path)

    def test_inventory_hash_error_names_operation_and_relative_path(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        csv_path = repo / "inventory.csv"
        from unittest.mock import patch

        with patch("contextcanon.onboarding_inventory.Path.open", side_effect=PermissionError(13, "Permission denied")):
            with self.assertRaisesRegex(ContextCanonError, "while hashing 'README.md'"):
                refresh_inventory(repo, csv_path)

    def test_onboard_init_manages_gitignore_for_transient_workspace_but_keeps_inventory_state_visible(self):
        repo = self.make_repo()
        (repo / ".gitignore").write_text("existing-temp/\n", encoding="utf-8")

        self.assertEqual(cli_main(["onboard", "init", str(repo)]), 0)
        self.assertEqual(cli_main(["onboard", "init", str(repo)]), 0)

        text = (repo / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("existing-temp/", text)
        self.assertEqual(text.count("# >>> ContextCanon onboarding (managed)"), 1)
        self.assertIn("/contextcanon-onboarding/", text)
        self.assertIn("/.context/onboarding/*", text)
        self.assertIn("!/.context/onboarding/inventory-state.json", text)
        self.assertIn("!/.context/onboarding/inventory-acceptance.json", text)

        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        workspace = repo / "contextcanon-onboarding"
        refresh_inventory(repo, workspace / "STEP-02-inventory.csv")
        self.describe_sources(workspace / "STEP-02-inventory.csv")
        prepared, _ = prepare_from_inventory(repo, workspace / "STEP-02-inventory.csv")

        ignored_workspace = subprocess.run(
            ["git", "-C", str(repo), "check-ignore", "contextcanon-onboarding/PLAN.md"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(ignored_workspace.returncode, 0)
        ignored_snapshot = subprocess.run(
            ["git", "-C", str(repo), "check-ignore", f".context/onboarding/{prepared.evidence_digest}/manifest.json"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(ignored_snapshot.returncode, 0)
        for durable in (
            ".context/onboarding/inventory-state.json",
            ".context/onboarding/inventory-acceptance.json",
        ):
            visible = subprocess.run(
                ["git", "-C", str(repo), "check-ignore", durable],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(visible.returncode, 0, durable)

    def test_inventory_can_be_reconstructed_after_workspace_and_snapshot_are_removed(self):
        repo = self.make_repo()
        (repo / "docs").mkdir()
        (repo / "docs/product.md").write_text("# Product\n", encoding="utf-8")
        (repo / "docs/data.foo").write_text("opaque but deliberately ignored\n", encoding="utf-8")
        (repo / "outside.md").write_text("# Outside\n", encoding="utf-8")

        self.assertEqual(cli_main(["onboard", "init", str(repo)]), 0)
        csv_path = repo / "contextcanon-onboarding" / "STEP-02-inventory.csv"
        refresh_inventory(
            repo,
            csv_path,
            directories=["docs"],
            rule_specs=["docs/*.foo=other:ignore"],
        )
        rows = self.read_csv(csv_path)
        product = next(row for row in rows if row["path"] == "docs/product.md")
        product["description"] = "Owner-reviewed product definition."
        product["note"] = "Keep for later onboarding refreshes."
        self.write_csv(csv_path, rows)
        prepared, _ = prepare_from_inventory(repo, csv_path)

        shutil.rmtree(repo / "contextcanon-onboarding")
        for child in (repo / ".context" / "onboarding").iterdir():
            if child.name not in {"inventory-state.json", "inventory-acceptance.json"}:
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()

        self.assertEqual(cli_main(["onboard", "init", str(repo)]), 0)
        restored_csv = repo / "contextcanon-onboarding" / "STEP-02-inventory.csv"
        restored = refresh_inventory(repo, restored_csv)
        by_path = {row.path: row for row in restored.rows}

        self.assertEqual(restored.directories, ("docs",))
        self.assertEqual([(rule.pattern, rule.kind, rule.handling) for rule in restored.rules], [("docs/*.foo", "other", "ignore")])
        self.assertEqual(set(by_path), {"docs/data.foo", "docs/product.md"})
        self.assertEqual(by_path["docs/product.md"].description, "Owner-reviewed product definition.")
        self.assertEqual(by_path["docs/product.md"].note, "Keep for later onboarding refreshes.")
        self.assertEqual(by_path["docs/product.md"].status, "unchanged")
        self.assertEqual(by_path["docs/data.foo"].handling, "ignore")
        self.assertFalse((repo / ".context" / "onboarding" / prepared.evidence_digest).exists())

    def test_opaque_document_uses_same_stem_markdown_as_transcription(self):
        repo = self.make_repo()
        (repo / "architecture.pdf").write_bytes(b"%PDF placeholder\n")
        (repo / "architecture.md").write_text("# Architecture transcription\n", encoding="utf-8")

        refreshed = refresh_inventory(repo, repo / "inventory.csv")
        rows = {row.path: row for row in refreshed.rows}

        self.assertEqual((rows["architecture.pdf"].kind, rows["architecture.pdf"].handling), ("binary", "ignore"))
        self.assertEqual((rows["architecture.md"].kind, rows["architecture.md"].handling), ("transcription", "source"))
        self.assertIn("architecture.md", rows["architecture.pdf"].hint)
        self.assertIn("architecture.pdf", rows["architecture.md"].description)

    def test_opaque_document_without_transcription_explains_required_markdown_companion(self):
        repo = self.make_repo()
        (repo / "architecture.docx").write_bytes(b"placeholder")

        refreshed = refresh_inventory(repo, repo / "inventory.csv")
        row = refreshed.rows[0]

        self.assertEqual((row.kind, row.handling), ("binary", "ignore"))
        self.assertIn("architecture.md", row.hint)

    def test_legacy_present_status_is_accepted_as_unchanged(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        csv_path = repo / "inventory.csv"
        refresh_inventory(repo, csv_path)
        rows = self.read_csv(csv_path)
        rows[0]["status"] = "present"
        rows[0]["description"] = "Project overview."
        self.write_csv(csv_path, rows)

        _, selection = prepare_from_inventory(repo, csv_path)

        self.assertEqual(selection.rows[0].status, "unchanged")

    def test_source_code_is_omitted_by_default_and_custom_rule_can_opt_it_in(self):
        repo = self.make_repo()
        (repo / "src").mkdir()
        (repo / "src/main.py").write_text("print('hello')\n", encoding="utf-8")

        default_csv = repo / "default.csv"
        default = refresh_inventory(repo, default_csv)
        self.assertEqual(default.rows, ())
        self.assertEqual(default.omitted_source_code, 1)

        custom_csv = repo / "custom.csv"
        custom = refresh_inventory(
            repo,
            custom_csv,
            rule_specs=["src/*.py=source-code:source"],
        )
        custom_row = {row.path: row for row in custom.rows}["src/main.py"]
        self.assertEqual((custom_row.kind, custom_row.handling), ("source-code", "source"))
        self.assertEqual(custom_row.rule, "custom:src/*.py")

    def test_reviewed_inventory_drives_evidence_and_lookup_stays_out(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Hello Extended\n", encoding="utf-8")
        (repo / "data.csv").write_text("name,value\nanswer,42\n", encoding="utf-8")
        (repo / "src").mkdir()
        (repo / "src/main.py").write_text("print('hello')\n", encoding="utf-8")

        csv_path = repo / "inventory.csv"
        refresh_inventory(repo, csv_path)
        self.describe_sources(csv_path)

        prepared, selection = prepare_from_inventory(repo, csv_path)

        self.assertEqual(
            [(entry.path, entry.reason) for entry in prepared.included],
            [("README.md", "inventory-source"), ("data.csv", "inventory-source")],
        )
        self.assertNotIn("src/main.py", {row.path for row in selection.rows})
        self.assertFalse((prepared.snapshot_root / "evidence/src/main.py").exists())

    def test_reviewed_description_is_snapshot_bound_and_visible_to_semantic_llm(self):
        repo = self.make_repo()
        (repo / "parameters.csv").write_text("name,default\nanswer,42\n", encoding="utf-8")
        csv_path = repo / "inventory.csv"
        refresh_inventory(repo, csv_path)
        rows = self.read_csv(csv_path)
        row = next(item for item in rows if item["path"] == "parameters.csv")
        row["description"] = "Canonical P1 parameter catalog used by every sub-product."
        row["note"] = "Owner-confirmed during onboarding."
        self.write_csv(csv_path, rows)

        prepared, _ = prepare_from_inventory(repo, csv_path)
        snapshot = load_evidence_snapshot(prepared.snapshot_root)
        entry = snapshot.by_path["parameters.csv"]
        self.assertEqual(entry.kind, "structured-data")
        self.assertEqual(entry.handling, "source")
        self.assertEqual(entry.description, "Canonical P1 parameter catalog used by every sub-product.")
        self.assertEqual(entry.note, "Owner-confirmed during onboarding.")

        instruction = build_onboarding_structure_instruction(prepared.snapshot_root).text
        self.assertIn("kind `structured-data`", instruction)
        self.assertIn("handling `source`", instruction)
        self.assertIn("Owner-reviewed description: Canonical P1 parameter catalog used by every sub-product.", instruction)
        self.assertIn("Owner note: Owner-confirmed during onboarding.", instruction)

    def test_external_speedyboarding_csv_does_not_hide_sibling_project_files(self):
        repo = self.make_repo()
        (repo / "setup").mkdir()
        (repo / "setup/inventory.csv").write_text(
            "path,kind,handling,description\n"
            "product.md,document,source,Product definition\n",
            encoding="utf-8",
        )
        (repo / "product.md").write_text("# Product\n", encoding="utf-8")
        (repo / "setup/important.md").write_text("# Important\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "setup/important.md"):
            prepare_from_inventory(repo, repo / "setup/inventory.csv")

    def test_cli_copies_external_speedyboarding_csv_into_canonical_workspace(self):
        repo = self.make_repo()
        (repo / "product.md").write_text("# Product\n", encoding="utf-8")
        external = repo / "speedy.csv"
        external.write_text(
            "path,kind,handling,description\n"
            "product.md,document,source,Product definition\n",
            encoding="utf-8",
        )

        result = cli_main([
            "onboard", "prepare", str(repo),
            "--inventory", str(external),
        ])
        self.assertEqual(result, 0)
        canonical = repo / "contextcanon-onboarding" / "STEP-02-inventory.csv"
        self.assertEqual(canonical.read_bytes(), external.read_bytes())
        plan = (repo / "contextcanon-onboarding" / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("--inventory contextcanon-onboarding/STEP-02-inventory.csv", plan)

    def test_prepare_rejects_repository_file_added_after_inventory(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        csv_path = repo / "inventory.csv"
        refresh_inventory(repo, csv_path)
        self.describe_sources(csv_path)
        (repo / "new.md").write_text("# New\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "Inventory is stale"):
            prepare_from_inventory(repo, csv_path)

    def test_refresh_after_acceptance_surfaces_new_changed_and_missing_files_and_preserves_review(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (repo / "parameters.csv").write_text("name,default\na,1\n", encoding="utf-8")
        (repo / "notes.md").write_text("# Notes\n", encoding="utf-8")
        csv_path = repo / "inventory.csv"

        refresh_inventory(repo, csv_path)
        rows = self.read_csv(csv_path)
        for row in rows:
            if row["path"] == "parameters.csv":
                row["description"] = "Authoritative product parameter catalog."
                row["note"] = "Owner-reviewed."
            elif row["handling"] in {"source", "interpret"} and not row["description"]:
                row["description"] = f"Reviewed {row['path']}"
        self.write_csv(csv_path, rows)
        prepare_from_inventory(repo, csv_path)

        (repo / "parameters.csv").write_text("name,default\na,1\nb,2\n", encoding="utf-8")
        (repo / "notes.md").unlink()
        (repo / "feature.md").write_text("# Feature\n", encoding="utf-8")

        refreshed = refresh_inventory(repo, csv_path)
        by_path = {row.path: row for row in refreshed.rows}

        self.assertEqual(by_path["parameters.csv"].status, "changed")
        self.assertEqual(by_path["feature.md"].status, "new")
        self.assertEqual(by_path["notes.md"].status, "missing")
        self.assertEqual(by_path["README.md"].status, "unchanged")
        self.assertEqual(by_path["parameters.csv"].description, "Authoritative product parameter catalog.")
        self.assertEqual(by_path["parameters.csv"].note, "Owner-reviewed.")
        self.assertTrue(by_path["parameters.csv"].accepted_sha256)

    def test_missing_reviewed_file_must_be_restored_or_explicitly_ignored(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        csv_path = repo / "inventory.csv"
        refresh_inventory(repo, csv_path)
        self.describe_sources(csv_path)
        prepare_from_inventory(repo, csv_path)

        (repo / "README.md").unlink()
        refresh_inventory(repo, csv_path)
        with self.assertRaisesRegex(ContextCanonError, "file is missing"):
            prepare_from_inventory(repo, csv_path)

        rows = self.read_csv(csv_path)
        rows[0]["handling"] = "ignore"
        self.write_csv(csv_path, rows)
        prepared, _ = prepare_from_inventory(repo, csv_path)
        self.assertEqual(prepared.included, ())

    def test_shared_hello_world_extended_fixture_covers_core_inventory_cases(self):
        repo = self.make_repo()
        fixture = ROOT / "examples" / "onboarding" / "hello-world-extended"
        shutil.copytree(fixture, repo, dirs_exist_ok=True)

        csv_path = repo / "inventory.csv"
        refreshed = refresh_inventory(repo, csv_path)
        by_path = {row.path: row for row in refreshed.rows}

        self.assertEqual(by_path["P1/parameters.csv"].kind, "structured-data")
        self.assertEqual(by_path["P1/F1/prestudy.md"].handling, "interpret")
        self.assertEqual(by_path["P1/F1/meeting-notes.md"].handling, "interpret")
        self.assertNotIn("src/hello.py", by_path)
        self.assertEqual(refreshed.omitted_source_code, 1)
        self.assertEqual(by_path["assets/reference.pdf"].handling, "ignore")
        self.assertEqual(by_path["assets/reference.pdf"].kind, "binary")
        self.assertEqual(by_path["assets/reference.md"].kind, "transcription")
        self.assertEqual(by_path["assets/reference.md"].handling, "source")
        self.assertIn("assets/reference.md", by_path["assets/reference.pdf"].hint)
        self.assertEqual(by_path[".gitignore"].handling, "ignore")
        self.assertEqual(by_path[".gitignore"].kind, "configuration")
        self.assertEqual(by_path["unknown.weird"].handling, "undecided")
        self.assertNotIn("generated/example.txt", by_path)

    def test_minimal_speedyboarding_csv_may_omit_default_source_code(self):
        repo = self.make_repo()
        (repo / "product.md").write_text("# Product\n", encoding="utf-8")
        (repo / "src").mkdir()
        (repo / "src/main.py").write_text("print('hello')\n", encoding="utf-8")
        csv_path = repo / "speedy.csv"
        csv_path.write_text(
            "path,kind,handling,description\n"
            "product.md,document,source,Product definition\n",
            encoding="utf-8",
        )

        prepared, selection = prepare_from_inventory(repo, csv_path)
        self.assertEqual([entry.path for entry in prepared.included], ["product.md"])
        self.assertEqual([row.path for row in selection.rows], ["product.md"])


if __name__ == "__main__":
    unittest.main()
