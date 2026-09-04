from __future__ import annotations

import sys

from .cli import main as cli_main
from .onboarding_reset import run_journaled
from .parser import ContextCanonError


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        return run_journaled(args, cli_main)
    except ContextCanonError as exc:
        print(f"contextcanon: error: {exc}", file=sys.stderr)
        return 2
