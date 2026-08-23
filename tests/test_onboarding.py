from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.onboarding import MAX_EVIDENCE_FILE_BYTES, prepare_onboarding_evidence
from contextcanon.parser import ContextCanonError


class OnboardingEvidenceTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        return root

    def test_prepare_needs_no_context_node_and_is_deterministic(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (repo / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
        (repo / "docs").mkdir()
        (repo / "docs/architecture.md").write_text("# Architecture\n", encoding="utf-8")
        (repo / "src").mkdir()
        (repo / "src/main.py").write_text("print('not automatic evidence')\n", encoding="utf-8")

        first = prepare_onboarding_evidence(repo)
        second = prepare_onboarding_evidence(repo)

        self.assertFalse((repo / "CONTEXT.src.md").exists())
        self.assertEqual(first.evidence_digest, second.evidence_digest)
        self.assertEqual(first.snapshot_root, second.snapshot_root)
        self.assertEqual(first.excluded, second.excluded)
        self.assertEqual(
            [(entry.path, entry.reason) for entry in first.included],
            [
                ("README.md", "root-document"),
                ("docs/architecture.md", "documentation"),
                ("pyproject.toml", "project-manifest"),
            ],
        )
        self.assertFalse((first.snapshot_root / "evidence/src/main.py").exists())
        self.assertEqual(
            (first.snapshot_root / "evidence/docs/architecture.md").read_bytes(),
            (repo / "docs/architecture.md").read_bytes(),
        )

        manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "contextcanon/onboarding-evidence/v0")
        self.assertEqual(manifest["evidence_digest"], first.evidence_digest)
        self.assertEqual(
            manifest["selection"]["repository_listing"],
            "git ls-files --cached --others --exclude-standard",
        )

    def test_gitignore_limits_automatic_inventory_but_explicit_include_can_add_safe_file(self):
        repo = self.make_repo()
        (repo / ".gitignore").write_text("docs/ignored.md\n", encoding="utf-8")
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (repo / "docs").mkdir()
        (repo / "docs/ignored.md").write_text("# Deliberately ignored\n", encoding="utf-8")

        automatic = prepare_onboarding_evidence(repo)
        self.assertEqual([entry.path for entry in automatic.included], ["README.md"])

        explicit = prepare_onboarding_evidence(repo, explicit_paths=["docs/ignored.md"])
        self.assertEqual(
            [(entry.path, entry.reason) for entry in explicit.included],
            [("README.md", "root-document"), ("docs/ignored.md", "explicit")],
        )
        self.assertNotEqual(automatic.evidence_digest, explicit.evidence_digest)

    def test_safe_defaults_include_agent_instructions_ci_and_common_manifests(self):
        repo = self.make_repo()
        (repo / "AGENTS.md").write_text("Read project instructions.\n", encoding="utf-8")
        (repo / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
        workflow = repo / ".github/workflows/test.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("name: test\n", encoding="utf-8")
        instruction = repo / ".github/instructions/python.md"
        instruction.parent.mkdir(parents=True)
        instruction.write_text("# Python\n", encoding="utf-8")

        prepared = prepare_onboarding_evidence(repo)
        self.assertEqual(
            [(entry.path, entry.reason) for entry in prepared.included],
            [
                (".github/instructions/python.md", "agent-instruction"),
                (".github/workflows/test.yml", "ci-workflow"),
                ("AGENTS.md", "agent-instruction"),
                ("package.json", "project-manifest"),
            ],
        )

    def test_sensitive_candidate_is_recorded_as_excluded_without_copying_it(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (repo / "docs").mkdir()
        (repo / "docs/secrets.md").write_text("token = do-not-copy\n", encoding="utf-8")

        prepared = prepare_onboarding_evidence(repo)

        self.assertEqual([entry.path for entry in prepared.included], ["README.md"])
        self.assertEqual(
            [(entry.path, entry.reason) for entry in prepared.excluded],
            [("docs/secrets.md", "sensitive-path")],
        )
        self.assertFalse((prepared.snapshot_root / "evidence/docs/secrets.md").exists())

    def test_large_and_non_utf8_candidates_are_excluded(self):
        repo = self.make_repo()
        (repo / "README.md").write_bytes(b"x" * (MAX_EVIDENCE_FILE_BYTES + 1))
        (repo / "docs").mkdir()
        (repo / "docs/binary.md").write_bytes(b"\xff\xfe\x00")

        prepared = prepare_onboarding_evidence(repo)

        self.assertEqual(prepared.included, ())
        self.assertEqual(
            [(entry.path, entry.reason) for entry in prepared.excluded],
            [("README.md", "too-large"), ("docs/binary.md", "non-utf8")],
        )

    def test_explicit_include_rejects_sensitive_escape_directory_and_oversize(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (repo / ".env").write_text("SECRET=value\n", encoding="utf-8")
        (repo / "large.txt").write_bytes(b"x" * (MAX_EVIDENCE_FILE_BYTES + 1))
        (repo / "folder").mkdir()

        with self.assertRaisesRegex(ContextCanonError, r"blocked \(sensitive-path\)"):
            prepare_onboarding_evidence(repo, explicit_paths=[".env"])
        with self.assertRaisesRegex(ContextCanonError, "escapes repository"):
            prepare_onboarding_evidence(repo, explicit_paths=["../outside.md"])
        with self.assertRaisesRegex(ContextCanonError, "regular file"):
            prepare_onboarding_evidence(repo, explicit_paths=["folder"])
        with self.assertRaisesRegex(ContextCanonError, "exceeds"):
            prepare_onboarding_evidence(repo, explicit_paths=["large.txt"])

    def test_selected_content_change_creates_new_snapshot_and_keeps_old_one(self):
        repo = self.make_repo()
        readme = repo / "README.md"
        readme.write_text("v1\n", encoding="utf-8")
        before = prepare_onboarding_evidence(repo)

        readme.write_text("v2\n", encoding="utf-8")
        after = prepare_onboarding_evidence(repo)

        self.assertNotEqual(before.evidence_digest, after.evidence_digest)
        self.assertTrue(before.snapshot_root.exists())
        self.assertTrue(after.snapshot_root.exists())
        self.assertEqual((before.snapshot_root / "evidence/README.md").read_text(encoding="utf-8"), "v1\n")
        self.assertEqual((after.snapshot_root / "evidence/README.md").read_text(encoding="utf-8"), "v2\n")

    def test_existing_snapshot_corruption_is_rejected(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        prepared = prepare_onboarding_evidence(repo)
        (prepared.snapshot_root / "evidence/README.md").write_text("corrupt\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "modified file"):
            prepare_onboarding_evidence(repo)

    def test_cli_prepare_reports_content_addressed_snapshot(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")

        self.assertEqual(main(["onboard", "prepare", str(repo)]), 0)
        snapshots = [path for path in (repo / ".context/onboarding").iterdir() if path.is_dir()]
        self.assertEqual(len(snapshots), 1)
        self.assertTrue((snapshots[0] / "manifest.json").is_file())

    def test_prepare_requires_repository_root(self):
        repo = self.make_repo()
        child = repo / "child"
        child.mkdir()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "must target the Git repository root"):
            prepare_onboarding_evidence(child)


if __name__ == "__main__":
    unittest.main()
