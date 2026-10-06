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


def ensure_onboarding_store_gitignore(project: Path) -> Path:
    """Repository-wide rules outlive a reset of any individual project scope."""
    path = find_repo_root(project.resolve()) / ".gitignore"
    start = "# >>> ContextCanon shared onboarding scratch (managed)"
    end = "# <<< ContextCanon shared onboarding scratch (managed)"
    before = path.read_text(encoding="utf-8") if path.exists() else ""
    block = "\n".join((start, "/contextcanon-onboarding-*/", "/.context/handoffs/", "/.context/onboarding-migrations/", "/.context/onboarding/**",
                       "!/.context/onboarding/", "!/.context/onboarding/inventory-state.json",
                       "!/.context/onboarding/inventory-acceptance.json", "!/.context/onboarding/*/",
                       "!/.context/onboarding/*/.scope.json",
                       "!/.context/onboarding/*/.active.json",
                       "!/.context/onboarding/*/inventory-state.json",
                       "!/.context/onboarding/*/inventory-acceptance.json", end))
    first, last = before.find(start), before.find(end)
    if (first >= 0) != (last >= 0) or (first >= 0 and last < first):
        raise ContextCanonError(f"Incomplete shared onboarding ignore block: {path}")
    after = (before[:first] + block + before[last + len(end):]) if first >= 0 else before.rstrip("\n") + ("\n\n" if before.strip() else "") + block + "\n"
    if after != before:
        path.write_text(after, encoding="utf-8")
    return path
