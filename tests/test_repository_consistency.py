from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.links import local_markdown_targets


def _is_compiler_owned_markdown(relative: Path) -> bool:
    return relative.name == "CONTEXT.md" or "CONTEXT" in relative.parts


def broken_local_markdown_links(root: Path) -> list[str]:
    """Check authored repository Markdown links, not stale compiler projections.

    Review-ready ContextCanon changes may intentionally carry generated drift until
    the final merge gate. Generated CONTEXT.md/CONTEXT/ integrity is therefore
    owned by `contextcanon check --all .`; this independent repository test keeps
    authored documentation links useful without turning known generated drift into
    an earlier hard gate.
    """

    broken: list[str] = []
    for markdown in sorted(root.rglob("*.md")):
        relative = markdown.relative_to(root)
        if any(part in {".git", ".context"} for part in relative.parts):
            continue
        if _is_compiler_owned_markdown(relative):
            continue
        text = markdown.read_text(encoding="utf-8")
        for target in local_markdown_targets(text):
            target = unquote(target)
            resolved = (markdown.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                broken.append(f"{relative}: link escapes repository: {target}")
                continue
            if not resolved.exists():
                broken.append(f"{relative}: missing local link target: {target}")
    return broken


class RepositoryConsistencyTests(unittest.TestCase):
    def test_link_checker_ignores_code_fences_and_detects_real_broken_links(self):
        root = Path(tempfile.mkdtemp())
        (root / "ok.md").write_text("# OK\n", encoding="utf-8")
        (root / "README.md").write_text(
            "[works](ok.md)\n```markdown\n[example](not-real.md)\n```\n[broken](missing.md)\n",
            encoding="utf-8",
        )
        self.assertEqual(
            broken_local_markdown_links(root),
            ["README.md: missing local link target: missing.md"],
        )

    def test_link_checker_leaves_generated_markdown_to_drift_check(self):
        root = Path(tempfile.mkdtemp())
        (root / "CONTEXT.md").write_text("[stale generated link](missing.md)\n", encoding="utf-8")
        (root / "CONTEXT").mkdir()
        (root / "CONTEXT" / "README.md").write_text("[stale copy](missing.md)\n", encoding="utf-8")
        (root / "README.md").write_text("# Authored and valid\n", encoding="utf-8")
        self.assertEqual(broken_local_markdown_links(root), [])

    def test_repository_local_markdown_links_resolve(self):
        root = Path(__file__).resolve().parents[1]
        broken = broken_local_markdown_links(root)
        self.assertEqual(broken, [], "\n".join(broken))


if __name__ == "__main__":
    unittest.main()
