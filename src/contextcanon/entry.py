from __future__ import annotations

import sys

from .cli import main as cli_main
from .onboarding_reset import run_journaled
from .parser import ContextCanonError


_WINDOWS_LOCK_GUIDANCE = (
    "Repeated ContextCanon owner runs have shown that antivirus and other background scanners can hold "
    "project files/directories long enough to trigger WinError 5 during atomic file operations. ContextCanon "
    "cannot identify the locking process automatically. If your security policy permits it, exclude the "
    "project directory from real-time scanning (JetBrains IDEs can configure Microsoft Defender via "
    "'Exclude Folders'), then rerun the same ContextCanon command. See docs/windows.md."
)


def _looks_like_windows_lock(message: str) -> bool:
    lowered = message.lower()
    return (
        "winerror 5" in lowered
        or "access is denied" in lowered
        or "zugriff verweigert" in lowered
        or "temporary filesystem lock" in lowered
        or "transient windows access" in lowered
    )


def _windows_permission_error(exc: PermissionError) -> str:
    winerror = getattr(exc, "winerror", None)
    path = f" Path: {exc.filename}." if getattr(exc, "filename", None) else ""
    if winerror == 5:
        return (
            f"Windows filesystem operation failed with WinError 5 / access denied.{path} Original error: {exc}\n"
            f"{_WINDOWS_LOCK_GUIDANCE}"
        )
    errno = getattr(exc, "errno", None)
    code = f"errno {errno}" if errno is not None else "permission denied"
    return (
        f"Windows filesystem operation failed with permission denied ({code}).{path} Original error: {exc}\n"
        "This is not being classified as the known transient WinError 5/scanner-lock case. "
        "Check whether the reported path is the expected filesystem type and whether normal Windows ACLs allow the operation."
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        return run_journaled(args, cli_main)
    except ContextCanonError as exc:
        message = str(exc)
        if _looks_like_windows_lock(message):
            message = f"{message}\n{_WINDOWS_LOCK_GUIDANCE}"
        print(f"contextcanon: error: {message}", file=sys.stderr)
        return 2
    except PermissionError as exc:
        if sys.platform == "win32" or getattr(exc, "winerror", None) == 5:
            print(f"contextcanon: error: {_windows_permission_error(exc)}", file=sys.stderr)
        else:
            print(f"contextcanon: error: filesystem permission denied: {exc}", file=sys.stderr)
        return 2
