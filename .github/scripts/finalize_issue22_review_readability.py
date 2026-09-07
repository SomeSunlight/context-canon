from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True, text=True)


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path}: {old!r}; found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        path.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


def checkpoint_plan() -> None:
    plan = ROOT / "PLAN.md"
    marker = "Owner-test review-readability follow-up under #22"
    append_once(
        plan,
        marker,
        """
Owner-test review-readability follow-up under #22: keep immutable digests visible, but make the human meaning of a Source/Parent review primary. Review output should summarize semantic/content changes before technical fingerprints, and legacy-to-central discovery migration must state explicitly that migration alone does not change the accepted Source.
""",
    )
    run("git", "add", "PLAN.md")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode != 0:
        run("git", "commit", "-m", "Checkpoint Issue #22 review readability")


def update_diff_renderer() -> None:
    path = ROOT / "src/contextcanon/diff.py"
    text = path.read_text(encoding="utf-8")
    start = text.index("def render_diff(diff: ContextDiff) -> str:\n")
    end = text.index("\ndef _diff_maps(", start)
    replacement = r'''_CATEGORY_NOUNS = {
    "node": ("node metadata item", "node metadata items"),
    "parent": ("parent", "parents"),
    "source": ("source", "sources"),
    "change": ("local change", "local changes"),
    "rule": ("rule", "rules"),
    "topic": ("topic", "topics"),
    "resource": ("resource", "resources"),
}


def _transition(before: str, after: str) -> str:
    return f"unchanged ({before})" if before == after else f"{before} -> {after}"


def _summary_parts(diff: ContextDiff) -> list[str]:
    counts: dict[tuple[str, DiffChange], int] = {}
    for entry in diff.entries:
        key = (entry.category, entry.change)
        counts[key] = counts.get(key, 0) + 1

    action = {"added": "added", "removed": "removed", "modified": "changed"}
    parts: list[str] = []
    for category in sorted(_CATEGORY_ORDER, key=_CATEGORY_ORDER.get):
        singular, plural = _CATEGORY_NOUNS[category]
        for change in ("added", "removed", "modified"):
            count = counts.get((category, change), 0)
            if count:
                noun = singular if count == 1 else plural
                parts.append(f"{count} {noun} {action[change]}")
    return parts


def render_diff(diff: ContextDiff) -> str:
    summary = ", ".join(_summary_parts(diff))
    if not summary:
        summary = (
            "package presentation changed; semantic and Resource content unchanged"
            if not diff.is_empty
            else "no compiled context changes"
        )

    lines = [
        f"ContextCanon diff: {diff.before_name} ({diff.node_id})",
        f"  Version: {_transition(diff.before_version, diff.after_version)}",
        f"  Summary: {summary}",
    ]

    if diff.entries:
        current_category = None
        symbol = {"added": "+", "removed": "-", "modified": "~"}
        for entry in diff.entries:
            if entry.category != current_category:
                current_category = entry.category
                lines.extend(["", current_category.title() + "s:"])
            detail = ""
            if entry.change == "modified" and entry.changed_fields:
                detail = " [" + ", ".join(entry.changed_fields) + "]"
            lines.append(f"  {symbol[entry.change]} {entry.identity}{detail}")
    elif diff.is_empty:
        lines.extend(["", "No compiled context changes."])
    else:
        lines.extend(["", "Package presentation changed without semantic or Resource content changes."])

    lines.extend(
        [
            "",
            "Technical details:",
            f"  Normalized digest: {_transition(diff.before_normalized_digest, diff.after_normalized_digest)}",
            f"  Package digest: {_transition(diff.before_package_digest, diff.after_package_digest)}",
        ]
    )
    return "\n".join(lines) + "\n"
'''
    path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


def update_cli_copy() -> None:
    path = ROOT / "src/contextcanon/cli.py"
    replace_once(
        path,
        'print(f"fetched candidate {candidate.metadata.name} {candidate.metadata.version} ({candidate.package_digest})")',
        'print(f"Fetched candidate: {candidate.metadata.name} {candidate.metadata.version} ({candidate.package_digest})")',
    )
    replace_once(path, 'print(f"Candidate Git commit: {provenance[\'commit\']}")', 'print(f"  Git commit: {provenance[\'commit\']}")')
    replace_once(path, 'print(f"Candidate local repository: {provenance[\'location\']}")', 'print(f"  Local repository: {provenance[\'location\']}")')
    replace_once(path, 'print(f"Candidate package: {label}")', 'print(f"  Cached package: {label}")')
    replace_once(
        path,
        'print(f"Migrated legacy Source discovery to {migrated}")',
        'print(f"Migrated legacy Source discovery to central configuration: {migrated}")\n                        print("  This migration only changes where future Source candidates are discovered.")\n                        print("  It does not change the accepted Source; acceptance happens only after this review.")',
    )


def update_tests() -> None:
    path = ROOT / "tests/test_diff.py"
    text = path.read_text(encoding="utf-8")
    marker = "    def test_render_diff_prioritizes_human_summary_before_technical_details(self):"
    if marker not in text:
        insert = r"""
    def test_render_diff_prioritizes_human_summary_before_technical_details(self):
        before_root = self.make_repo()
        added_local_rule = '''

## Local Rules

### Review UX

- **Explain the review:** Put semantic meaning before fingerprints.
  Why: Humans review meaning first.
  <!-- ctx:rule id="P-REVIEW" -->
'''
        after_root = self.make_repo(
            project=PROJECT + added_local_rule,
            guide="# Guide\n\nChanged guidance.\n",
        )

        rendered = render_diff(diff_compiled(self.compile(before_root), self.compile(after_root)))

        self.assertIn("Version: unchanged (1.0.0)", rendered)
        self.assertIn("1 rule added", rendered)
        self.assertIn("1 resource changed", rendered)
        self.assertLess(rendered.index("Summary:"), rendered.index("Rules:"))
        self.assertLess(rendered.index("Resources:"), rendered.index("Technical details:"))
        self.assertIn("Normalized digest:", rendered)
        self.assertIn("Package digest:", rendered)

"""
        needle = '\n\nif __name__ == "__main__":\n'
        if needle not in text:
            raise RuntimeError("Could not locate test_diff.py insertion point")
        text = text.replace(needle, "\n" + insert + needle, 1)
        path.write_text(text, encoding="utf-8")

    path = ROOT / "tests/test_configuration_and_update_ux.py"
    text = path.read_text(encoding="utf-8")
    old = '            self.assertIn("Migrated legacy Source discovery", out.getvalue())\n'
    if 'This migration only changes where future Source candidates are discovered.' not in text:
        if old not in text:
            raise RuntimeError("Could not locate legacy migration assertion")
        new = old + (
            '            self.assertIn("This migration only changes where future Source candidates are discovered.", out.getvalue())\n'
            '            self.assertIn("It does not change the accepted Source; acceptance happens only after this review.", out.getvalue())\n'
            '            self.assertIn("Fetched candidate: Shared", out.getvalue())\n'
        )
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


def finish_docs() -> None:
    append_once(
        ROOT / "PLAN.md",
        "Issue #22 review-readability implementation checkpoint",
        """
Issue #22 review-readability implementation checkpoint: Source/Parent review output now presents version and a compact semantic/content change summary before category details, while normalized/package digests remain available under a clearly separated Technical details section. Guided legacy discovery migration explains that only candidate discovery changes until the reviewed Source is explicitly accepted. Full deterministic tests, self-build/check, and diff hygiene must remain green on the final product head.
""",
    )
    append_once(
        ROOT / "STATE.md",
        "Latest Source-update review readability",
        """
## Latest Source-update review readability

The real `ai-workstation` owner test confirmed that guided Source update, one-off `--ref`, and automatic `contextcanon.yaml` migration work correctly. The same run exposed a readability issue: immutable digests appeared before the semantic change meaning. PR #18 now presents a compact human summary and Rules/Resources first, moves fingerprints into a `Technical details` section, and states explicitly that legacy discovery migration alone does not change the accepted Source. Immutable identity and explicit human acceptance remain unchanged.
""",
    )


def main() -> None:
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")

    checkpoint_plan()
    update_diff_renderer()
    update_cli_copy()
    update_tests()
    finish_docs()

    run(sys.executable, "-m", "pip", "install", "-e", ".", "pytest")
    run(sys.executable, "-m", "compileall", "-q", "src", "tests")
    run(sys.executable, "-m", "pytest", "-q")
    run("contextcanon", "build", "--all", ".")
    run("contextcanon", "check", "--all", ".")
    run("git", "diff", "--check")

    run("git", "rm", "-f", ".github/scripts/finalize_issue22_review_readability.py", ".github/workflows/issue22-review-readability-finalizer.yml")
    run("git", "add", "-A")
    run("git", "commit", "-m", "Make Context review output human-first (#22)")
    run("git", "push", "origin", "HEAD:agent/issues-14-15-multi-parent")


if __name__ == "__main__":
    main()
