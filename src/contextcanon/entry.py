from __future__ import annotations

import sys

from .cli import main as cli_main
from .onboarding_reset import run_journaled
from .parser import ContextCanonError


def _windows_permission_error(exc: PermissionError) -> str:
    return (
        "Windows denied a ContextCanon filesystem operation. "
        f"Original error: {exc}\n"
        "Repeated ContextCanon owner runs have shown that antivirus and other background scanners can hold "
        "project files/directories long enough to trigger WinError 5 during atomic publication. ContextCanon "
        "cannot identify the locking process automatically. If your security policy permits it, exclude the "
        "project directory from real-time scanning (JetBrains IDEs can configure Microsoft Defender via "
        "'Exclude Folders'), then rerun the same ContextCanon command. See docs/windows.md."
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        return run_journaled(args, cli_main)
    except ContextCanonError as exc:
        print(f"contextcanon: error: {exc}", file=sys.stderr)
        return 2
    except PermissionError as exc:
        if sys.platform == "win32" or getattr(exc, "winerror", None) == 5:
            print(f"contextcanon: error: {_windows_permission_error(exc)}", file=sys.stderr)
        else:
            print(f"contextcanon: error: filesystem permission denied: {exc}", file=sys.stderr)
        return 2
