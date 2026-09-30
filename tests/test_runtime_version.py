from __future__ import annotations

import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

from contextcanon.version import display_version, git_provenance, release_version


ROOT = Path(__file__).resolve().parents[1]


class RuntimeVersionTests(unittest.TestCase):
    def make_project(self, *, git: bool) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "pyproject.toml").write_text(
            '[project]\nname = "contextcanon"\nversion = "1.2.3"\n',
            encoding="utf-8",
        )
        (root / "tracked.txt").write_text("clean\n", encoding="utf-8")
        if git:
            subprocess.run(["git", "init", "-q", "-b", "feature/version-test", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "initial"], check=True)
        self.addCleanup(shutil.rmtree, root, True)
        return root

    def test_checkout_uses_pyproject_as_release_version_source(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        self.assertEqual(release_version(ROOT), project["version"])

    def test_non_git_source_tree_reports_plain_release_version(self):
        root = self.make_project(git=False)
        self.assertEqual(release_version(root), "1.2.3")
        self.assertIsNone(git_provenance(root))
        self.assertEqual(display_version(root), "1.2.3")

    def test_git_checkout_reports_branch_commit_and_dirty_state(self):
        root = self.make_project(git=True)
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short=7", "HEAD"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        self.assertEqual(git_provenance(root), f"feature/version-test@{commit}")
        self.assertEqual(display_version(root), f"1.2.3 (feature/version-test@{commit})")

        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        self.assertEqual(git_provenance(root), f"feature/version-test@{commit}, dirty")
        self.assertEqual(display_version(root), f"1.2.3 (feature/version-test@{commit}, dirty)")


if __name__ == "__main__":
    unittest.main()
