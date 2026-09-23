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

    def test_source_code_defaults_to_lookup_and_custom_rule_can_override_it(self):
        repo = self.make_repo()
        (repo / "src").mkdir()
        (repo / "src/main.py").write_text("print('hello')\n", encoding="utf-8")

        default_csv = repo / "default.csv"
        default = refresh_inventory(repo, default_csv)
        self.assertEqual((default.rows[0].kind, default.rows[0].handling), ("source-code", "lookup"))

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
        self.assertEqual({row.path: row.handling for row in selection.rows}["src/main.py"], "lookup")
        self.assertFalse((prepared.snapshot_root / "evidence/src/main.py").exists())

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
        self.assertEqual(by_path["README.md"].status, "present")
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
        self.assertEqual(by_path["src/hello.py"].handling, "lookup")
        self.assertEqual(by_path["assets/reference.pdf"].handling, "ignore")
        self.assertEqual(by_path["unknown.weird"].handling, "undecided")
        self.assertNotIn("generated/example.txt", by_path)

    def test_minimal_speedyboarding_csv_is_valid_when_it_accounts_for_live_scope(self):
        repo = self.make_repo()
        (repo / "product.md").write_text("# Product\n", encoding="utf-8")
        (repo / "src").mkdir()
        (repo / "src/main.py").write_text("print('hello')\n", encoding="utf-8")
        csv_path = repo / "speedy.csv"
        csv_path.write_text(
            "path,kind,handling,description\n"
            "product.md,document,source,Product definition\n"
            "src/main.py,source-code,lookup,\n",
            encoding="utf-8",
        )

        prepared, _ = prepare_from_inventory(repo, csv_path)
        self.assertEqual([entry.path for entry in prepared.included], ["product.md"])


if __name__ == "__main__":
    unittest.main()
