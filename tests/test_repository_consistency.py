from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.links import local_markdown_targets


def broken_local_markdown_links(root: Path) -> list[str]:
    broken: list[str] = []
    for markdown in sorted(root.rglob("*.md")):
        relative = markdown.relative_to(root)
        if any(part in {".git", ".context"} for part in relative.parts):
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

    def test_repository_local_markdown_links_resolve(self):
        root = Path(__file__).resolve().parents[1]
        broken = broken_local_markdown_links(root)
        self.assertEqual(broken, [], "\n".join(broken))


if __name__ == "__main__":
    unittest.main()
