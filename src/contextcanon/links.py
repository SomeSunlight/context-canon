from __future__ import annotations

import re
from collections.abc import Iterator
from urllib.parse import quote, unquote

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "data:", "ssh://", "git://")


def _is_external_target(target: str) -> bool:
    return target.startswith(_EXTERNAL_PREFIXES)


def markdown_link_target(target: str) -> str:
    """Render one semantic/local path as a portable Markdown link destination.

    Callers pass the raw filesystem/ContextCanon locator, never an already
    percent-encoded presentation string. External URLs and pure anchors are
    left unchanged. Path separators and Windows drive colons stay readable;
    spaces plus Markdown/URI-sensitive path characters are percent-encoded.
    """

    value = target.replace("\\", "/")
    if not value or value.startswith("#") or _is_external_target(value):
        return value
    return quote(value, safe="/:-._~@")


def markdown_target_locator(target: str) -> str:
    """Decode one Markdown link destination back to its semantic/local locator.

    External URLs and pure anchors are not filesystem paths and remain
    untouched. Local targets are decoded exactly once.
    """

    value = target.strip()
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1].strip()
    if not value or value.startswith("#") or _is_external_target(value):
        return value
    return unquote(value)


def local_markdown_targets(text: str) -> Iterator[str]:
    """Yield decoded local link targets outside fenced code blocks.

    External URLs, mailto/data/ssh/git links, anchors, and empty links are
    ignored. Anchors on local paths are stripped before percent-decoding so an
    encoded percent-23 remains a literal # in the filesystem name.
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
            if not target or target.startswith("#") or _is_external_target(target):
                continue
            target = target.split("#", 1)[0]
            if target:
                yield markdown_target_locator(target)
