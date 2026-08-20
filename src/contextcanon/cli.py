from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import Compiler, discover_nodes
from .outputs import check_outputs, write_outputs
from .parser import ContextCanonError, find_repo_root


def _targets(path: Path, all_nodes: bool) -> tuple[Path, list[Path]]:
    path = path.resolve()
    if all_nodes:
        repo_root = path if (path / ".git").exists() else find_repo_root(path)
        return repo_root, discover_nodes(repo_root)
    node_root = path
    repo_root = find_repo_root(node_root)
    return repo_root, [node_root]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="contextcanon", description="Deterministic ContextCanon walking-skeleton compiler")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "check"):
        command = sub.add_parser(name)
        command.add_argument("path", nargs="?", default=".", help="Node root, or repository root with --all")
        command.add_argument("--all", action="store_true", help="discover and process every Node in the repository")
    args = parser.parse_args(argv)

    try:
        repo_root, node_roots = _targets(Path(args.path), args.all)
        if not node_roots:
            raise ContextCanonError(f"No Context Nodes found under {repo_root}")
        compiler = Compiler(repo_root)
        failed = False
        for node_root in node_roots:
            compiled = compiler.compile(node_root)
            label = node_root.relative_to(repo_root).as_posix() or "."
            if args.command == "build":
                changed = write_outputs(compiled)
                suffix = f" ({', '.join(changed)})" if changed else " (no changes)"
                print(f"built {label}{suffix}")
            else:
                drift = check_outputs(compiled)
                if drift:
                    failed = True
                    print(f"drift {label}:")
                    for item in drift:
                        print(f"  - {item}")
                else:
                    print(f"ok {label}")
        return 1 if failed else 0
    except ContextCanonError as exc:
        print(f"contextcanon: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
