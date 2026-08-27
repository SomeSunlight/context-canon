from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import Compiler, discover_nodes
from .diff import diff_compiled, render_diff
from .git_transport import fetch_git_candidate
from .onboarding import prepare_onboarding_evidence
from .onboarding_instruction import build_onboarding_instruction
from .onboarding_proposal import load_onboarding_proposal
from .onboarding_review import (
    accept_onboarding_review,
    create_or_load_onboarding_review,
    parse_source_locator_arguments,
    render_onboarding_review,
)
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

    onboard_parser = sub.add_parser("onboard", help="prepare, review, and accept project onboarding state")
    onboard_sub = onboard_parser.add_subparsers(dest="onboard_command", required=True)
    onboard_prepare = onboard_sub.add_parser(
        "prepare",
        help="create a deterministic content-addressed evidence snapshot from a Git repository",
    )
    onboard_prepare.add_argument("project", nargs="?", default=".", help="Git repository root (default: current directory)")
    onboard_prepare.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="PATH",
        help="explicitly include one additional safe UTF-8 repository-relative file; may be repeated",
    )

    onboard_instruction = onboard_sub.add_parser(
        "instruction",
        help="render the framework-owned semantic instruction for one exact evidence snapshot",
    )
    onboard_instruction.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_instruction.add_argument(
        "--catalog-package",
        action="append",
        default=[],
        metavar="PATH",
        help="verified immutable reusable Source package offered to the semantic reviewer; may be repeated",
    )

    onboard_validate = onboard_sub.add_parser(
        "validate",
        help="validate a semantic onboarding proposal against one exact evidence snapshot",
    )
    onboard_validate.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_validate.add_argument("proposal", help="JSON onboarding proposal to validate")

    onboard_review = onboard_sub.add_parser(
        "review",
        help="create or inspect the human decision file for one validated onboarding proposal",
    )
    onboard_review.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_review.add_argument("proposal", help="validated JSON onboarding proposal")
    onboard_review.add_argument("review", help="human-editable onboarding review JSON file")
    onboard_review.add_argument(
        "--node-name",
        help="canonical Node name; required only when creating a new review file",
    )
    onboard_review.add_argument(
        "--node-id",
        help="stable Node ID; defaults to a fresh UUID when the review is created",
    )
    onboard_review.add_argument(
        "--node-version",
        default="0.1.0",
        help="initial canonical Node version when creating the review (default: 0.1.0)",
    )

    onboard_accept = onboard_sub.add_parser(
        "accept",
        help="explicitly publish a fully reviewed proposal as the first canonical Context Node",
    )
    onboard_accept.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_accept.add_argument("proposal", help="validated JSON onboarding proposal")
    onboard_accept.add_argument("review", help="completed onboarding review JSON file")
    onboard_accept.add_argument(
        "--project",
        default=".",
        help="target Git repository root (default: current directory)",
    )
    onboard_accept.add_argument(
        "--catalog-package",
        action="append",
        default=[],
        metavar="PATH",
        help="exact immutable Source package for an accepted existing-source finding; may be repeated",
    )
    onboard_accept.add_argument(
        "--source-locator",
        action="append",
        default=[],
        metavar="ITEM_ID=LOCATOR",
        help="visible Source provenance/update locator for an accepted existing-source finding; may be repeated",
    )

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

        if args.command == "onboard":
            if args.onboard_command == "prepare":
                prepared = prepare_onboarding_evidence(
                    Path(args.project),
                    explicit_paths=args.include,
                )
                label = prepared.snapshot_root.relative_to(prepared.project_root).as_posix()
                print(f"prepared onboarding evidence {prepared.evidence_digest}")
                print(f"Evidence snapshot: {label}")
                print(f"Included files: {len(prepared.included)}")
                print(f"Excluded candidates: {len(prepared.excluded)}")
                return 0

            if args.onboard_command == "instruction":
                instruction = build_onboarding_instruction(
                    Path(args.snapshot),
                    catalog_package_roots=(Path(path) for path in args.catalog_package),
                )
                print(instruction.text, end="")
                print(
                    f"contextcanon onboarding instruction digest: {instruction.instruction_digest}",
                    file=sys.stderr,
                )
                return 0

            if args.onboard_command == "validate":
                proposal = load_onboarding_proposal(Path(args.proposal), Path(args.snapshot))
                print(f"validated onboarding proposal {proposal.proposal_digest}")
                print(f"Evidence snapshot: {proposal.evidence_digest}")
                print(f"Proposal items: {len(proposal.items)}")
                return 0

            if args.onboard_command == "review":
                review, proposal, snapshot, created = create_or_load_onboarding_review(
                    Path(args.snapshot),
                    Path(args.proposal),
                    Path(args.review),
                    node_name=args.node_name,
                    node_id=args.node_id,
                    node_version=args.node_version,
                )
                verb = "created" if created else "loaded"
                print(f"{verb} onboarding review {review.review_digest}")
                print(f"Review file: {Path(args.review)}")
                print(render_onboarding_review(review, proposal, snapshot), end="")
                return 0

            acceptance = accept_onboarding_review(
                Path(args.snapshot),
                Path(args.proposal),
                Path(args.review),
                Path(args.project),
                catalog_package_roots=(Path(path) for path in args.catalog_package),
                source_locators=parse_source_locator_arguments(args.source_locator),
            )
            print(f"accepted onboarding review {acceptance.acceptance_path.parent.name}")
            print(f"Canonical source: {acceptance.source_path}")
            print(f"Normalized digest: {acceptance.normalized_digest}")
            print(f"Package digest: {acceptance.package_digest}")
            print(f"Acceptance record: {acceptance.acceptance_path}")
            return 0

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