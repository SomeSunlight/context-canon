from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import Compiler, discover_nodes
from .diff import diff_compiled, render_diff
from .git_transport import fetch_git_candidate
from .outputs import check_outputs, write_outputs
from .parser import ContextCanonError, find_repo_root
from .sources import accept_source_candidate, review_source_candidate


def _node_root(path: Path) -> Path:
    path = path.resolve()
    if path.is_file() and path.name in {"CONTEXT.src.md", "CONTEXT.md"}:
        return path.parent
    return path


def _targets(path: Path, all_nodes: bool) -> tuple[Path, list[Path]]:
    path = _node_root(path)
    if all_nodes:
        repo_root = path if (path / ".git").exists() else find_repo_root(path)
        return repo_root, discover_nodes(repo_root)
    node_root = path
    repo_root = find_repo_root(node_root)
    return repo_root, [node_root]


def _compile_one(path: Path):
    node_root = _node_root(path)
    repo_root = find_repo_root(node_root)
    return Compiler(repo_root).compile(node_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="contextcanon", description="Deterministic ContextCanon compiler")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "check"):
        command = sub.add_parser(name)
        command.add_argument("path", nargs="?", default=".", help="Node root, or repository root with --all")
        command.add_argument("--all", action="store_true", help="discover and process every Node in the repository")

    diff_parser = sub.add_parser("diff", help="compare two compiled versions of the same Context Node")
    diff_parser.add_argument("before", help="Node root for the earlier repository snapshot")
    diff_parser.add_argument("after", help="Node root for the later repository snapshot")
    diff_parser.add_argument("--json", action="store_true", help="emit deterministic machine-readable JSON")

    source_parser = sub.add_parser("source", help="fetch, review, and explicitly accept immutable Source packages")
    source_sub = source_parser.add_subparsers(dest="source_command", required=True)

    source_fetch = source_sub.add_parser("fetch", help="fetch a Source candidate through its declared transport")
    source_fetch.add_argument("source_id", help="stable Node ID of the Source in CONTEXT.src.md")
    source_fetch.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")

    source_review = source_sub.add_parser("review", help="diff and structurally validate a Source candidate")
    source_review.add_argument("source_id", help="stable Node ID of the Source in CONTEXT.src.md")
    source_review.add_argument("candidate", help="local root of the candidate immutable package")
    source_review.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")

    source_accept = source_sub.add_parser("accept", help="accept exactly a previously reviewed Source candidate")
    source_accept.add_argument("source_id", help="stable Node ID of the Source in CONTEXT.src.md")
    source_accept.add_argument("candidate", help="local root of the reviewed immutable package")
    source_accept.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")

    args = parser.parse_args(argv)

    try:
        if args.command == "diff":
            before = _compile_one(Path(args.before))
            after = _compile_one(Path(args.after))
            result = diff_compiled(before, after)
            print(result.to_json() if args.json else render_diff(result), end="")
            return 1 if not result.is_empty else 0

        if args.command == "source":
            node_root = _node_root(Path(args.node))
            if args.source_command == "fetch":
                candidate, location = fetch_git_candidate(node_root, args.source_id)
                try:
                    label = location.relative_to(node_root).as_posix()
                except ValueError:
                    label = str(location)
                print(
                    f"fetched candidate {candidate.metadata.name} {candidate.metadata.version} "
                    f"({candidate.package_digest})"
                )
                print(f"Candidate package: {label}")
                return 0

            candidate = Path(args.candidate).resolve()
            if args.source_command == "review":
                result, receipt = review_source_candidate(node_root, args.source_id, candidate)
                print(render_diff(result), end="")
                try:
                    label = receipt.relative_to(node_root).as_posix()
                except ValueError:
                    label = str(receipt)
                print(f"Review receipt: {label}")
                return 0

            accepted = accept_source_candidate(node_root, args.source_id, candidate)
            print(
                f"accepted {accepted.metadata.name} {accepted.metadata.version} "
                f"({accepted.package_digest})"
            )
            return 0

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
