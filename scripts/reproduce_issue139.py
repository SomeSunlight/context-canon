"""Reproduce #139 on a disposable *real* ContextCanon six-Node checkout.

Runs against the installed ContextCanon implementation, never edits the source
checkout, never approves anything without explicitly answering the prompt, and
prints quantitative post-change Git staging metrics. Linux/Windows require Git.
"""
from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

from contextcanon.cli import main as cli_main
from contextcanon.parser import parse_node

ROOT = Path(__file__).resolve().parents[1]


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.stdout


def command(*args: str, approve: bool = False) -> tuple[int, str, int]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        if approve:
            with mock.patch("builtins.input", return_value="y") as response:
                result = cli_main(list(args))
                prompts = response.call_count
        else:
            result = cli_main(list(args))
            prompts = 0
    return result, buffer.getvalue(), prompts


def require(ok: bool, message: str, output: str = "") -> None:
    if not ok:
        raise AssertionError(f"{message}\n{output[-5000:]}")


def exercise(checkout: Path) -> None:
    provider = checkout / "nodes" / "library" / "development-workflow"
    guide = provider / "docs" / "external-github-publication.md"
    require(guide.is_file(), f"Missing #137 optional Resource: {guide}")
    root_arg = str(checkout)
    parent_version = parse_node(provider, checkout).metadata.version
    before_imports = {
        rel: (checkout / rel / "CONTEXT.src.md").read_bytes()
        for rel in (
            "nodes/internal/framework-development",
            "nodes/library/github",
            "nodes/library/github-local",
        )
    }
    with guide.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n## Additional optional publication tip\n\n"
                     "Keep each publication report linked to its original issue.\n")

    status, out, _ = command("propagate", "--status", "--all", root_arg)
    require(status == 1 and "Pending normative Parent updates" in out,
            "Changed Resource was not reported as pending", out)
    for rel, expected in before_imports.items():
        require((checkout / rel / "CONTEXT.src.md").read_bytes() == expected,
                "Read-only status changed an accepted import")

    before_build, out, _ = command("build", "--all", root_arg)
    require(before_build == 1 and "pending propagation" in out,
            "Pre-review build failed to distinguish pending from success", out)
    bumped_version = parse_node(provider, checkout).metadata.version
    require(bumped_version != parent_version, "Parent version did not advance")
    for rel, expected in before_imports.items():
        require((checkout / rel / "CONTEXT.src.md").read_bytes() == expected,
                "Pre-review build silently accepted a Parent")

    propagated, out, prompts = command("propagate", "--all", root_arg, approve=True)
    require(propagated == 0 and prompts >= 3,
            "Interactive propagation failed or skipped explicit review decisions", out)
    changed_imports = sum(
        (checkout / rel / "CONTEXT.src.md").read_bytes() != expected
        for rel, expected in before_imports.items()
    )
    require(changed_imports == 3, "Not all three direct local consumers accepted the Parent")

    rebuilt, out, _ = command("build", "--all", root_arg)
    require(rebuilt == 0, "Post-review build failed", out)
    checked, out, _ = command("check", "--all", root_arg)
    require(checked == 0, "Post-review self-hosted check drifted", out)

    # Only the throwaway worktree is staged, for reproducible *physical* numbers.
    git(checkout, "add", "-A")
    numstat = git(checkout, "diff", "--cached", "--numstat")
    names = git(checkout, "diff", "--cached", "--name-status")
    rows = [row.split("\t", 2) for row in numstat.splitlines()]
    additions = sum(int(row[0]) for row in rows if row[0].isdigit())
    deletions = sum(int(row[1]) for row in rows if row[1].isdigit())
    history = [line.split("\t", 1)[1] for line in names.splitlines()
               if line.startswith("A\t.context/versions/")]
    package_count = sum(path.endswith("/.context/package.json") for path in history)
    require(package_count >= 3,
            "Expected at least three new immutable self-hosted package versions")

    print("Issue #139 actual accepted self-hosted graph, disposable worktree:")
    print(f"  Parent: {parent_version} -> {bumped_version}")
    print(f"  Read-only status: pending; pre-review build: pending (exit 1)")
    print(f"  Explicit prompted approvals: {prompts}; direct Child imports updated: {changed_imports}")
    print("  Post-review build + check --all: clean (six Nodes, four normative edges)")
    print(f"  Physical Git diff: {len(rows)} changed paths, +{additions}/-{deletions} lines")
    print(f"  New immutable historical packages: {package_count}; new historical files: {len(history)}")
    print("  Note: this is a Resource *edit*; PR #137 added a Resource. "
          "Compare by category, not as identical logical changes.")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="contextcanon-139-") as temporary:
        checkout = Path(temporary) / "checkout"
        git(ROOT, "worktree", "add", "--detach", str(checkout), "HEAD")
        try:
            exercise(checkout)
        finally:
            git(ROOT, "worktree", "remove", "--force", str(checkout))
    return 0


if __name__ == "__main__":
    sys.exit(main())
