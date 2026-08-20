from __future__ import annotations

import re
from collections.abc import Iterator

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def local_markdown_targets(text: str) -> Iterator[str]:
    """Yield local link targets outside fenced code blocks.

    External URLs, mailto links, anchors, and empty links are ignored. Anchors on
    local paths are stripped because materialization operates on files.
    """
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK_RE.finditer(line):
            target = match.group(1).strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            if target:
                yield target
