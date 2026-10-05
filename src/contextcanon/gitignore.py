from __future__ import annotations

from pathlib import Path

from .parser import ContextCanonError, find_repo_root


TRANSIENT_STORE_RULES = tuple(f"**/.context/{name}/" for name in (
    "candidates", "parent-candidates", "source-reviews", "parent-reviews", "migration-trash",
))
START = "# >>> ContextCanon candidate scratch (managed)"
END = "# <<< ContextCanon candidate scratch (managed)"


def ensure_candidate_gitignore(node_root: Path) -> Path:
    """Keep local review scratch out of normal staging, also for existing Nodes."""
    path = find_repo_root(node_root.resolve()) / ".gitignore"
    try:
        before = path.read_text(encoding="utf-8") if path.exists() else ""
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"Project .gitignore is not valid UTF-8: {path}") from exc
    block = "\n".join((START, *TRANSIENT_STORE_RULES, END))
    start, end = before.find(START), before.find(END)
    if (start >= 0) != (end >= 0) or (start >= 0 and end < start):
        raise ContextCanonError(f"Incomplete ContextCanon candidate scratch ignore block: {path}")
    if start >= 0:
        after = before[:start] + block + before[end + len(END):]
    else:
        after = before.rstrip("\n") + ("\n\n" if before.strip() else "") + block + "\n"
    if after != before:
        path.write_text(after, encoding="utf-8")
    return path
