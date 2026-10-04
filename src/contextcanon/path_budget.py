from __future__ import annotations

import os
import sys
import warnings
from collections.abc import Iterable
from pathlib import Path, PurePath

from .parser import ContextCanonError


# Leave headroom below MAX_PATH (260) and the directory limit (248).
# Count UTF-16 units, as Win32 does, including surrogate pairs.
WINDOWS_PATH_BUDGET = 240


def _windows() -> bool:
    return sys.platform == "win32"


def _length(path: PurePath) -> int:
    return len(str(path).encode("utf-16-le", errors="surrogatepass")) // 2


def preflight_paths(
    root: PurePath,
    relatives: Iterable[str],
    *,
    action: str,
    node_root: PurePath | None = None,
) -> None:
    """Check the whole destination set before writing or deleting anything.

    Pure Windows paths also allow platform-independent regression coverage.
    This is a compatibility budget for downstream tools, not an OS probe.
    """
    if not _windows():
        return
    if isinstance(root, Path):
        root = root.resolve()
    paths = [root / relative for relative in relatives]
    if not paths:
        return
    longest = max(paths, key=lambda path: (_length(path), str(path)))
    length = _length(longest)
    if length < WINDOWS_PATH_BUDGET:
        return
    base = node_root or root
    if isinstance(base, Path):
        base = base.resolve()
    added = length - _length(base)
    relative = longest.relative_to(base)
    parts = relative.parts
    owned = 0
    if parts[:1] == (".context",):
        owned += sum(len(part) + 1 for part in parts[:3])
    for index in range(len(parts) - 2):
        if parts[index:index + 2] == ("CONTEXT", "references"):
            owned += sum(len(part) + 1 for part in parts[index:index + 3])
    contribution = (
        f"ContextCanon-owned store/package prefixes contribute at least {owned} characters. "
        + ("That exceeds the Node/project root contribution. " if owned > _length(base) else "")
    )
    message = (
        f"Windows path compatibility budget exceeded during {action}: "
        f"{length} characters (UTF-16 units; budget < {WINDOWS_PATH_BUDGET}).\n"
        f"Longest destination: {longest}\n"
        f"Node/project root: {_length(base)} characters; ContextCanon's destination layout "
        f"adds {added}, including the unchanged Resource/document path. "
        + contribution + "Do not rename project documents blindly.\n"
        "Long-path failures are tool-dependent: Git, IDE links and file APIs can fail "
        "at different layers; partial success does not prove this path is safe. "
        "For Git-related failures, use 'git config core.longpaths true'. Enable Windows "
        "long-path support where policy permits; each downstream application must support it. "
        "A shorter checkout location is a temporary workaround. After verifying the tools "
        "you use, explicitly opt in with CONTEXTCANON_ALLOW_LONG_PATHS=1 "
        '(PowerShell: $env:CONTEXTCANON_ALLOW_LONG_PATHS = "1"); this retains warnings.'
    )
    if os.environ.get("CONTEXTCANON_ALLOW_LONG_PATHS") == "1":
        warnings.warn(message, RuntimeWarning, stacklevel=2)
    else:
        raise ContextCanonError(message)
