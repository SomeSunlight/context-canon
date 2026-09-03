from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(rel: str, old: str, new: str, *, count: int = 1) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"{rel}: expected {count} occurrence(s), found {actual}: {old[:120]!r}")
    path.write_text(text.replace(old, new, count), encoding="utf-8")


# First-adoption staging has no project README, so its prospective generated
# doorplate appears in expected_outputs. At the real target, a project-owned
# README must win. Exclude only that target-owned path from collision/rollback;
# if the target has no README, the generated doorplate remains part of the
# transaction and is removed on rollback like every other generated output.
patch(
    "src/contextcanon/onboarding_review.py",
    """    output_paths = tuple(expected_outputs(staged_compiled))\n    _ensure_first_adoption_outputs_absent(project_root, output_paths)\n""",
    """    staged_output_paths = tuple(expected_outputs(staged_compiled))\n    target_readme = project_root / \"README.md\"\n    output_paths = tuple(\n        rel\n        for rel in staged_output_paths\n        if not (rel == \"README.md\" and (target_readme.exists() or target_readme.is_symlink()))\n    )\n    _ensure_first_adoption_outputs_absent(project_root, output_paths)\n""",
)
patch(
    "src/contextcanon/onboarding_review.py",
    '        lines.extend(["## Rules", ""])\n',
    '        lines.extend(["## Local Rules", ""])\n',
)
patch(
    "src/contextcanon/onboarding_review.py",
    '        lines.extend(["## Topics", ""])\n',
    '        lines.extend(["## Local Topics", ""])\n',
)

# Legacy-migration fixtures intentionally remove newly previewed Parent blocks.
# Accept both historical and canonical display headings when creating that
# synthetic pre-Parent state.
for rel in ("tests/test_ai_workstation_parent_migration.py", "tests/test_parent_migration.py"):
    patch(
        rel,
        '    r"\\n## Parent\\n\\n<!-- contextcanon-placement-parent:start -->\\n.*?\\n<!-- contextcanon-placement-parent:end -->\\n?(?=\\n## |\\Z)",\n',
        '    r"\\n## (?:Parent Context Node|Parent)\\n\\n<!-- contextcanon-placement-parent:start -->\\n.*?\\n<!-- contextcanon-placement-parent:end -->\\n?(?=\\n## |\\Z)",\n',
    )

# Readability assertions follow the canonical display vocabulary.
patch(
    "tests/test_onboarding_placement_publish.py",
    '        self.assertIn("## Parent", child.after)\n',
    '        self.assertIn("## Parent Context Node", child.after)\n',
)
patch(
    "tests/test_onboarding_placement_publish.py",
    '        self.assertIn("## State", root.after)\n',
    '        self.assertIn("## Local State", root.after)\n',
)
patch(
    "tests/test_onboarding_placement_publish.py",
    '        self.assertIn("## Plan", root.after)\n',
    '        self.assertIn("## Local Plan", root.after)\n',
)
patch(
    "tests/test_overview.py",
    '        self.assertIn("## Overview", with_overview.official_markdown)\n',
    '        self.assertIn("## Local Overview", with_overview.official_markdown)\n',
)
patch(
    "tests/test_state_plan.py",
    '        self.assertIn("## State\\n\\n- Current migration is active.", first.official_markdown)\n',
    '        self.assertIn("## Local State\\n\\n- Current migration is active.", first.official_markdown)\n',
)
patch(
    "tests/test_state_plan.py",
    '        self.assertIn("## Plan\\n\\n- Finish onboarding before feature work.", first.official_markdown)\n',
    '        self.assertIn("## Local Plan\\n\\n- Finish onboarding before feature work.", first.official_markdown)\n',
)

# Keep the final project checkpoint tidy: exactly one terminating newline, no
# extra blank line that would make git diff --check fail.
state_path = ROOT / "STATE.md"
state_path.write_text(state_path.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8")
