from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import Compiler, discover_nodes
from .diff import diff_compiled, render_diff
from .git_transport import fetch_git_candidate
from .onboarding import prepare_onboarding_evidence
from .onboarding_instruction import build_onboarding_instruction
from .onboarding_placement import load_onboarding_placement_proposal
from .onboarding_placement_review import create_or_load_placement_review
from .onboarding_placement_instruction import build_onboarding_placement_instruction
from .onboarding_proposal import load_onboarding_proposal
from .onboarding_review import (
    accept_onboarding_review,
    create_or_load_onboarding_review,
    parse_source_locator_arguments,
    render_onboarding_review,
)
from .onboarding_structure import (
    create_or_load_structure_markdown,
    load_onboarding_structure_proposal,
)
from .onboarding_structure_instruction import build_onboarding_structure_instruction
from .onboarding_structure_materialize import (
    materialize_structure_skeletons,
    preview_structure_materialization,
    render_structure_materialization_preview,
)
from .onboarding_workspace import open_onboarding_workspace, write_utf8
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


def _workspace_path(value: str | None) -> Path | None:
    return Path(value) if value is not None else None


def _add_workspace(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace",
        metavar="PATH",
        help="visible human onboarding workspace (default: <project>/contextcanon-onboarding)",
    )


def _add_structure_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--structure-proposal",
        metavar="PATH",
        help="validated structure proposal (default: <workspace>/structure-proposal.json)",
    )
    parser.add_argument(
        "--structure",
        metavar="PATH",
        help="human-edited structure Markdown (default: <workspace>/structure.md)",
    )


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

    onboard_structure_instruction = onboard_sub.add_parser(
        "structure-instruction",
        help="write the framework-owned coarse structure-discovery instruction for one exact evidence snapshot",
    )
    onboard_structure_instruction.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_structure_instruction.add_argument(
        "--catalog-package",
        action="append",
        default=[],
        metavar="PATH",
        help="verified immutable reusable Source package offered to the structure reviewer; may be repeated",
    )
    _add_workspace(onboard_structure_instruction)
    onboard_structure_instruction.add_argument(
        "--stdout",
        action="store_true",
        help="emit the instruction to stdout instead of creating/updating the visible onboarding workspace",
    )

    onboard_structure_validate = onboard_sub.add_parser(
        "structure-validate",
        help="validate a coarse onboarding structure proposal against one exact evidence snapshot",
    )
    onboard_structure_validate.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_structure_validate.add_argument(
        "proposal",
        nargs="?",
        help="JSON onboarding structure proposal (default: <workspace>/structure-proposal.json)",
    )
    _add_workspace(onboard_structure_validate)

    onboard_structure_review = onboard_sub.add_parser(
        "structure-review",
        help="create or validate the human-editable Markdown structure review for one validated structure proposal",
    )
    onboard_structure_review.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_structure_review.add_argument(
        "proposal",
        nargs="?",
        help="validated JSON onboarding structure proposal (default: <workspace>/structure-proposal.json)",
    )
    onboard_structure_review.add_argument(
        "structure",
        nargs="?",
        help="human-editable structure Markdown file (default: <workspace>/structure.md)",
    )
    _add_workspace(onboard_structure_review)

    onboard_structure_preview = onboard_sub.add_parser(
        "structure-preview",
        help="preview existing protected Nodes and missing Node skeletons from the edited structure",
    )
    onboard_structure_preview.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    _add_workspace(onboard_structure_preview)
    onboard_structure_preview.add_argument("--project", metavar="PATH", help="target Git repository root (default: infer from snapshot)")

    onboard_structure_materialize = onboard_sub.add_parser(
        "structure-materialize",
        help="explicitly create only missing Context Node skeletons from the edited structure",
    )
    onboard_structure_materialize.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    _add_workspace(onboard_structure_materialize)
    onboard_structure_materialize.add_argument("--project", metavar="PATH", help="target Git repository root (default: infer from snapshot)")

    onboard_placement_instruction = onboard_sub.add_parser(
        "placement-instruction",
        help="write the framework-owned second-pass content-placement instruction bound to the edited structure",
    )
    onboard_placement_instruction.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    _add_workspace(onboard_placement_instruction)
    _add_structure_inputs(onboard_placement_instruction)
    onboard_placement_instruction.add_argument(
        "--catalog-package",
        action="append",
        default=[],
        metavar="PATH",
        help="verified immutable reusable Source package offered to the placement reviewer; may be repeated",
    )
    onboard_placement_instruction.add_argument(
        "--stdout",
        action="store_true",
        help="emit the instruction to stdout instead of writing <workspace>/placement-instruction.md",
    )

    onboard_placement_validate = onboard_sub.add_parser(
        "placement-validate",
        help="validate one content-placement proposal against frozen Evidence, edited structure, and exact Source catalog",
    )
    onboard_placement_validate.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_placement_validate.add_argument(
        "proposal",
        nargs="?",
        help="placement proposal JSON (default: <workspace>/placement-proposal.json)",
    )
    _add_workspace(onboard_placement_validate)
    _add_structure_inputs(onboard_placement_validate)
    onboard_placement_validate.add_argument(
        "--catalog-package",
        action="append",
        default=[],
        metavar="PATH",
        help="same exact immutable Source package catalog shown to the placement reviewer; may be repeated",
    )

    onboard_placement_review = onboard_sub.add_parser(
        "placement-review",
        help="write an evidence-rich Markdown review of a validated content-placement proposal",
    )
    onboard_placement_review.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_placement_review.add_argument(
        "proposal",
        nargs="?",
        help="placement proposal JSON (default: <workspace>/placement-proposal.json)",
    )
    _add_workspace(onboard_placement_review)
    _add_structure_inputs(onboard_placement_review)
    onboard_placement_review.add_argument(
        "--catalog-package",
        action="append",
        default=[],
        metavar="PATH",
        help="same exact immutable Source package catalog shown to the placement reviewer; may be repeated",
    )
    onboard_placement_review.add_argument(
        "--review",
        metavar="PATH",
        help="human-editable placement Markdown (default: <workspace>/placement.md)",
    )
    onboard_placement_review.add_argument(
        "--owner-source",
        action="append",
        default=[],
        metavar="TARGET_NODE_KEY=SOURCE_NODE_ID",
        help="explicitly select one exact catalog Source as owner design input when creating a new review; may be repeated",
    )

    onboard_instruction = onboard_sub.add_parser(
        "instruction",
        help="render the legacy framework-owned semantic instruction for one exact evidence snapshot",
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
        help="validate a legacy semantic onboarding proposal against one exact evidence snapshot",
    )
    onboard_validate.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_validate.add_argument("proposal", help="JSON onboarding proposal to validate")

    onboard_review = onboard_sub.add_parser(
        "review",
        help="create or inspect the human decision file for one validated legacy onboarding proposal",
    )
    onboard_review.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_review.add_argument("proposal", help="validated JSON onboarding proposal")
    onboard_review.add_argument("review", help="human-editable onboarding review JSON file")
    onboard_review.add_argument("--node-name", help="canonical Node name; required only when creating a new review file")
    onboard_review.add_argument("--node-id", help="stable Node ID; defaults to a fresh UUID when the review is created")
    onboard_review.add_argument(
        "--node-version",
        default="0.1.0",
        help="initial canonical Node version when creating the review (default: 0.1.0)",
    )

    onboard_accept = onboard_sub.add_parser(
        "accept",
        help="explicitly publish a fully reviewed legacy proposal as the first canonical Context Node",
    )
    onboard_accept.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_accept.add_argument("proposal", help="validated JSON onboarding proposal")
    onboard_accept.add_argument("review", help="completed onboarding review JSON file")
    onboard_accept.add_argument("--project", default=".", help="target Git repository root (default: current directory)")
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
            snapshot = Path(args.snapshot) if hasattr(args, "snapshot") else None

            if args.onboard_command == "prepare":
                prepared = prepare_onboarding_evidence(Path(args.project), explicit_paths=args.include)
                label = prepared.snapshot_root.relative_to(prepared.project_root).as_posix()
                print(f"prepared onboarding evidence {prepared.evidence_digest}")
                print(f"Evidence snapshot: {label}")
                print(f"Included files: {len(prepared.included)}")
                print(f"Excluded candidates: {len(prepared.excluded)}")
                return 0

            if args.onboard_command == "structure-instruction":
                instruction = build_onboarding_structure_instruction(
                    snapshot,
                    catalog_package_roots=(Path(path) for path in args.catalog_package),
                )
                if args.stdout:
                    if args.workspace is not None:
                        raise ContextCanonError("--workspace cannot be combined with --stdout")
                    print(instruction.text, end="")
                    print(f"contextcanon onboarding structure instruction digest: {instruction.instruction_digest}", file=sys.stderr)
                    return 0
                workspace = open_onboarding_workspace(snapshot, _workspace_path(args.workspace), create=True)
                write_utf8(workspace.structure_instruction_path, instruction.text)
                print(f"wrote onboarding structure instruction {workspace.structure_instruction_path}")
                print(f"Instruction digest: {instruction.instruction_digest}")
                print(f"Evidence snapshot: {instruction.evidence_digest}")
                print(f"Expected LLM output: {workspace.structure_proposal_path}")
                return 0

            if args.onboard_command == "structure-validate":
                if args.proposal is None:
                    workspace = open_onboarding_workspace(snapshot, _workspace_path(args.workspace), create=False)
                    proposal_path = workspace.structure_proposal_path
                else:
                    proposal_path = Path(args.proposal)
                proposal = load_onboarding_structure_proposal(proposal_path, snapshot)
                print(f"validated onboarding structure proposal {proposal.proposal_digest}")
                print(f"Proposal file: {proposal_path}")
                print(f"Evidence snapshot: {proposal.evidence_digest}")
                print(f"Proposed Nodes: {len(proposal.nodes)}")
                print(f"Knowledge bodies: {len(proposal.knowledge_bodies)}")
                print(f"Source reuses: {len(proposal.source_reuses)}")
                return 0

            if args.onboard_command == "structure-review":
                workspace = None
                if args.proposal is None or args.structure is None:
                    workspace = open_onboarding_workspace(snapshot, _workspace_path(args.workspace), create=False)
                proposal_path = Path(args.proposal) if args.proposal is not None else workspace.structure_proposal_path
                structure_path = Path(args.structure) if args.structure is not None else workspace.structure_path
                plan, proposal, _, created = create_or_load_structure_markdown(snapshot, proposal_path, structure_path)
                verb = "created" if created else "loaded"
                print(f"{verb} onboarding structure {plan.structure_digest}")
                print(f"Structure file: {structure_path}")
                print(f"Structure proposal: {proposal.proposal_digest}")
                print(f"Nodes in edited tree: {len(plan.nodes)}")
                return 0

            if args.onboard_command in {"structure-preview", "structure-materialize"}:
                workspace = open_onboarding_workspace(snapshot, _workspace_path(args.workspace), create=False)
                project = Path(args.project) if args.project is not None else None
                preview = preview_structure_materialization(
                    snapshot,
                    workspace.structure_proposal_path,
                    workspace.structure_path,
                    project_root=project,
                )
                text = render_structure_materialization_preview(preview)
                write_utf8(workspace.structure_preview_path, text)
                print(f"wrote structure materialization preview {workspace.structure_preview_path}")
                existing = sum(item.status == "existing" for item in preview.items)
                missing = sum(item.status == "create" for item in preview.items)
                print(f"Structure digest: {preview.structure_digest}")
                print(f"Existing protected Nodes: {existing}")
                print(f"Missing Node skeletons: {missing}")
                if args.onboard_command == "structure-preview":
                    return 0
                created = materialize_structure_skeletons(preview)
                print(f"Materialized Node skeletons: {len(created)}")
                for path in created:
                    print(f"  - {path}")
                return 0

            if args.onboard_command in {"placement-instruction", "placement-validate", "placement-review"}:
                workspace = open_onboarding_workspace(snapshot, _workspace_path(args.workspace), create=False)
                structure_proposal_path = (
                    Path(args.structure_proposal) if args.structure_proposal is not None else workspace.structure_proposal_path
                )
                structure_path = Path(args.structure) if args.structure is not None else workspace.structure_path
                catalog = tuple(Path(path) for path in args.catalog_package)

                if args.onboard_command == "placement-instruction":
                    instruction = build_onboarding_placement_instruction(
                        snapshot,
                        structure_proposal_path,
                        structure_path,
                        catalog_package_roots=catalog,
                    )
                    if args.stdout:
                        if args.workspace is not None:
                            raise ContextCanonError("--workspace cannot be combined with --stdout")
                        print(instruction.text, end="")
                        print(f"contextcanon onboarding placement instruction digest: {instruction.instruction_digest}", file=sys.stderr)
                        return 0
                    write_utf8(workspace.placement_instruction_path, instruction.text)
                    print(f"wrote onboarding placement instruction {workspace.placement_instruction_path}")
                    print(f"Instruction digest: {instruction.instruction_digest}")
                    print(f"Evidence snapshot: {instruction.evidence_digest}")
                    print(f"Structure digest: {instruction.structure_digest}")
                    print(f"Expected LLM output: {workspace.placement_proposal_path}")
                    return 0

                proposal_path = Path(args.proposal) if args.proposal is not None else workspace.placement_proposal_path
                proposal = load_onboarding_placement_proposal(
                    proposal_path,
                    snapshot,
                    structure_proposal_path,
                    structure_path,
                    catalog_package_roots=catalog,
                )
                if args.onboard_command == "placement-validate":
                    print(f"validated onboarding placement proposal {proposal.proposal_digest}")
                    print(f"Proposal file: {proposal_path}")
                    print(f"Evidence snapshot: {proposal.evidence_digest}")
                    print(f"Structure digest: {proposal.structure_digest}")
                    print(f"Placement items: {len(proposal.items)}")
                    print(f"Source reuses: {len(proposal.source_reuses)}")
                    return 0

                review_path = Path(args.review) if args.review is not None else workspace.placement_path
                review, created = create_or_load_placement_review(
                    review_path,
                    proposal,
                    snapshot,
                    owner_source_specs=args.owner_source,
                )
                verb = "created" if created else "loaded"
                print(f"{verb} onboarding placement review {review.review_digest}")
                print(f"Review file: {review_path}")
                print(f"Items: {len(review.items)} · Sources: {len(review.sources)} · complete: {review.is_complete}")
                return 0

            if args.onboard_command == "instruction":
                instruction = build_onboarding_instruction(
                    snapshot,
                    catalog_package_roots=(Path(path) for path in args.catalog_package),
                )
                print(instruction.text, end="")
                print(f"contextcanon onboarding instruction digest: {instruction.instruction_digest}", file=sys.stderr)
                return 0

            if args.onboard_command == "validate":
                proposal = load_onboarding_proposal(Path(args.proposal), snapshot)
                print(f"validated onboarding proposal {proposal.proposal_digest}")
                print(f"Evidence snapshot: {proposal.evidence_digest}")
                print(f"Proposal items: {len(proposal.items)}")
                return 0

            if args.onboard_command == "review":
                review, proposal, evidence_snapshot, created = create_or_load_onboarding_review(
                    snapshot,
                    Path(args.proposal),
                    Path(args.review),
                    node_name=args.node_name,
                    node_id=args.node_id,
                    node_version=args.node_version,
                )
                verb = "created" if created else "loaded"
                print(f"{verb} onboarding review {review.review_digest}")
                print(f"Review file: {Path(args.review)}")
                print(render_onboarding_review(review, proposal, evidence_snapshot), end="")
                return 0

            acceptance = accept_onboarding_review(
                snapshot,
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
                print(f"fetched candidate {candidate.metadata.name} {candidate.metadata.version} ({candidate.package_digest})")
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
            print(f"accepted {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")
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
