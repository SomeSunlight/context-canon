from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .authoring import add_rule, add_topic
from .compiler import Compiler, discover_nodes
from .diff import diff_compiled, render_diff
from .git_transport import fetch_git_candidate, load_candidate_provenance
from .onboarding import prepare_onboarding_evidence
from .onboarding_instruction import build_onboarding_instruction
from .onboarding_placement import load_onboarding_placement_proposal
from .onboarding_placement_audit import render_placement_source_audit
from .onboarding_placement_review import create_or_load_placement_review, load_placement_review
from .onboarding_reusable_contexts import load_accepted_reusable_contexts, refresh_reusable_contexts
from .onboarding_placement_publish import (
    build_placement_publication_preview,
    publish_placement_review,
    render_placement_followups,
    render_placement_publication_preview,
)
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
    load_structure_markdown,
)
from .onboarding_structure_instruction import build_onboarding_structure_instruction
from .onboarding_structure_materialize import (
    materialize_structure_skeletons,
    preview_structure_materialization,
    render_structure_materialization_preview,
)
from .onboarding_workspace import open_onboarding_workspace, remember_run_inputs, update_workspace_checkpoint, write_utf8
from .onboarding_reset import add_reset_parser, handle_reset_args
from .outputs import check_outputs, write_outputs
from .parser import ContextCanonError, find_repo_root
from .sources import adopt_source_package, accept_parent_candidate, accept_source_candidate, review_parent_candidate, review_source_candidate


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


def _snapshot_cli(snapshot: Path) -> str:
    try:
        return snapshot.resolve().relative_to(find_repo_root(snapshot)).as_posix()
    except ValueError:
        return str(snapshot)


def _catalog_labels(packages) -> tuple[str, ...]:
    return tuple(
        f"{package.metadata.id} · {package.metadata.name} · {package.metadata.version} · {package.package_digest}"
        for package in packages
    )


def _owner_specs_for_review(
    review_path: Path, explicit: tuple[str, ...], remembered: tuple[str, ...]
) -> tuple[str, ...]:
    if explicit:
        return explicit
    return remembered if not review_path.exists() else ()


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
        help="validated structure proposal (default: <workspace>/STEP-02b-structure-proposal.json)",
    )
    parser.add_argument(
        "--structure",
        metavar="PATH",
        help="human-edited structure Markdown (default: <workspace>/STEP-03-structure.md)",
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
    add_reset_parser(onboard_sub)

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
        help="JSON onboarding structure proposal (default: <workspace>/STEP-02b-structure-proposal.json)",
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
        help="validated JSON onboarding structure proposal (default: <workspace>/STEP-02b-structure-proposal.json)",
    )
    onboard_structure_review.add_argument(
        "structure",
        nargs="?",
        help="human-editable structure Markdown file (default: <workspace>/STEP-03-structure.md)",
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

    onboard_reusable_contexts = onboard_sub.add_parser(
        "reusable-contexts",
        help="create or validate the human reusable-Context Catalog and assignment gate",
    )
    onboard_reusable_contexts.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    _add_workspace(onboard_reusable_contexts)
    _add_structure_inputs(onboard_reusable_contexts)

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
        help="emit the instruction to stdout instead of writing <workspace>/STEP-06a-placement-instruction.md",
    )

    onboard_placement_validate = onboard_sub.add_parser(
        "placement-validate",
        help="validate one content-placement proposal against frozen Evidence, edited structure, and exact Source catalog",
    )
    onboard_placement_validate.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    onboard_placement_validate.add_argument(
        "proposal",
        nargs="?",
        help="placement proposal JSON (default: <workspace>/STEP-06b-placement-proposal.json)",
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
        help="placement proposal JSON (default: <workspace>/STEP-06b-placement-proposal.json)",
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
        help="human-editable placement Markdown (default: <workspace>/STEP-08-placement.md)",
    )
    onboard_placement_review.add_argument(
        "--owner-source",
        action="append",
        default=[],
        metavar="TARGET_NODE_KEY=SOURCE_NODE_ID",
        help="explicitly select one exact catalog Source as owner design input when creating a new review; may be repeated",
    )

    for command_name, command_help in (
        ("placement-preview", "preview exact reviewed placement publication without changing project files"),
        ("placement-publish", "explicitly publish one complete reviewed placement into existing Context Nodes"),
    ):
        command = onboard_sub.add_parser(command_name, help=command_help)
        command.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
        command.add_argument(
            "proposal", nargs="?", help="placement proposal JSON (default: <workspace>/STEP-06b-placement-proposal.json)"
        )
        _add_workspace(command)
        _add_structure_inputs(command)
        command.add_argument(
            "--catalog-package",
            action="append",
            default=[],
            metavar="PATH",
            help="same exact immutable Source catalog used for placement review; may be repeated",
        )
        command.add_argument(
            "--review", metavar="PATH", help="human-edited placement Markdown (default: <workspace>/STEP-08-placement.md)"
        )
        command.add_argument(
            "--project", metavar="PATH", help="target Git repository root (default: infer from snapshot)"
        )
        if command_name == "placement-publish":
            command.add_argument(
                "--acceptance",
                metavar="PATH",
                help="exact machine acceptance record (default: <snapshot>/placement-acceptance.json)",
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

    author_parser = sub.add_parser("author", help="write ordinary Rule/Topic authoring with stable IDs allocated by ContextCanon")
    author_sub = author_parser.add_subparsers(dest="author_command", required=True)
    author_rule = author_sub.add_parser("rule", help="add one Rule to CONTEXT.src.md and allocate its stable ID")
    author_rule.add_argument("path", nargs="?", default=".", help="Context Node root (default: current directory)")
    author_rule.add_argument("--group", default="General", help="Rule group heading (default: General)")
    author_rule.add_argument("--title", required=True, help="short human-facing Rule title")
    author_rule.add_argument("--statement", required=True, help="Rule statement")
    author_rule.add_argument("--why", required=True, help="Rule rationale")

    author_topic = author_sub.add_parser("topic", help="add one Topic to CONTEXT.src.md and allocate its stable ID")
    author_topic.add_argument("path", nargs="?", default=".", help="Context Node root (default: current directory)")
    author_topic.add_argument("--title", required=True, help="short human-facing Topic title")
    author_topic.add_argument("--condition", required=True, help="when this deeper context applies")
    author_topic.add_argument("--required-resource", action="append", default=[], metavar="PATH", help="required Resource target; may be repeated")
    author_topic.add_argument("--optional-resource", action="append", default=[], metavar="PATH", help="optional Resource target; may be repeated")
    author_topic.add_argument("--required-node", action="append", default=[], metavar="PATH", help="required Context Node navigation target; may be repeated")
    author_topic.add_argument("--optional-node", action="append", default=[], metavar="PATH", help="optional Context Node navigation target; may be repeated")

    parent_parser = sub.add_parser("parent", help="review and explicitly accept a newer semantic Parent snapshot")
    parent_sub = parent_parser.add_subparsers(dest="parent_command", required=True)
    parent_review = parent_sub.add_parser("review", help="compile the live Parent explicitly and review its immutable candidate snapshot")
    parent_review.add_argument("--node", default=".", help="child Context Node root (default: current directory)")
    parent_accept = parent_sub.add_parser("accept", help="accept exactly the most recently reviewed Parent snapshot")
    parent_accept.add_argument("--node", default=".", help="child Context Node root (default: current directory)")

    source_parser = sub.add_parser("source", help="fetch, review, and explicitly accept immutable Source packages")
    source_sub = source_parser.add_subparsers(dest="source_command", required=True)
    source_adopt = source_sub.add_parser("adopt", help="explicitly adopt one exact published Git package as a new Source")
    source_adopt.add_argument("package", help="local root of the exact published Source package Node")
    source_adopt.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")
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

            if args.onboard_command == "reset":
                result = handle_reset_args(args)
                print(f"reset onboarding from step {result['from_step']}")
                print(f"Journal records reversed: {result['journal_records_reversed']}")
                print(f"Project files restored/removed: {len(result['project_files_restored_or_removed'])}")
                print(f"Workspace files removed: {len(result['workspace_files_removed'])}")
                print("Frozen Evidence: preserved")
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
                update_workspace_checkpoint(
                    workspace, snapshot,
                    stage="structure instruction ready",
                    source_catalog=_catalog_labels(instruction.catalog_packages),
                    source_catalog_inputs=tuple(args.catalog_package),
                    next_action=(
                        "Give `STEP-02a-structure-instruction.md` and only the frozen `evidence/` tree to a strong reasoning LLM. "
                        "Save its single JSON result as `STEP-02b-structure-proposal.json`, then run "
                        f"`contextcanon onboard structure-validate {_snapshot_cli(snapshot)}`."
                    ),
                )
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
                if args.proposal is None:
                    update_workspace_checkpoint(
                        workspace, snapshot,
                        stage="structure proposal validated",
                        next_action=f"Run `contextcanon onboard structure-review {_snapshot_cli(snapshot)}` and edit `STEP-03-structure.md`.",
                    )
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
                if workspace is not None:
                    update_workspace_checkpoint(
                        workspace, snapshot,
                        stage="human structure validated",
                        structure_digest=plan.structure_digest,
                        next_action=f"Run `contextcanon onboard structure-preview {_snapshot_cli(snapshot)}`.",
                    )
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
                recovering = sum(item.status == "recover" for item in preview.items)
                missing = sum(item.status == "create" for item in preview.items)
                print(f"Structure digest: {preview.structure_digest}")
                print(f"Existing protected Nodes: {existing}")
                print(f"Root authoring recoveries: {recovering}")
                print(f"Missing Node skeletons: {missing}")
                if args.onboard_command == "structure-preview":
                    next_action = (
                        f"Run `contextcanon onboard structure-materialize {_snapshot_cli(snapshot)}` after reviewing `STEP-04-structure-preview.md`."
                        if missing or recovering else
                        f"Run `contextcanon onboard reusable-contexts {_snapshot_cli(snapshot)}`."
                    )
                    update_workspace_checkpoint(
                        workspace, snapshot, stage="structure previewed",
                        structure_digest=preview.structure_digest, next_action=next_action,
                    )
                    return 0
                created = materialize_structure_skeletons(preview)
                print(f"Materialized Node skeletons: {len(created)}")
                for path in created:
                    print(f"  - {path}")
                update_workspace_checkpoint(
                    workspace, snapshot, stage="structure materialized",
                    structure_digest=preview.structure_digest,
                    next_action=f"Run `contextcanon onboard reusable-contexts {_snapshot_cli(snapshot)}`.",
                )
                return 0

            if args.onboard_command == "reusable-contexts":
                workspace = open_onboarding_workspace(snapshot, _workspace_path(args.workspace), create=False)
                structure_proposal_path = (
                    Path(args.structure_proposal) if args.structure_proposal is not None else workspace.structure_proposal_path
                )
                structure_path = Path(args.structure) if args.structure is not None else workspace.structure_path
                structure_proposal = load_onboarding_structure_proposal(structure_proposal_path, snapshot)
                structure = load_structure_markdown(structure_path, structure_proposal)
                plan, created = refresh_reusable_contexts(
                    workspace.reusable_contexts_path,
                    snapshot,
                    structure_proposal.evidence_digest,
                    structure,
                )
                verb = "created" if created else "validated"
                print(f"{verb} reusable Context setup {plan.review_digest}")
                print(f"Review file: {workspace.reusable_contexts_path}")
                print(f"Catalog Nodes: {len(plan.catalog_packages)} · assignments: {len(plan.assignments)} · complete: {plan.is_complete}")
                # Keep the old machine run-input cache populated for scripting/backward compatibility,
                # but the human PLAN never asks the operator to reconstruct these values.
                remember_run_inputs(
                    snapshot,
                    catalog_inputs=plan.catalog_package_inputs,
                    owner_source_specs=plan.owner_source_specs,
                )
                stage = "reusable contexts accepted" if plan.is_complete else "reusable contexts review"
                next_action = (
                    f"Run `contextcanon onboard placement-instruction {_snapshot_cli(snapshot)}`."
                    if plan.is_complete else
                    f"Edit `{workspace.reusable_contexts_path.name}` (Catalog locations / sparse Assignments / Why), then rerun `contextcanon onboard reusable-contexts {_snapshot_cli(snapshot)}`."
                )
                update_workspace_checkpoint(
                    workspace, snapshot,
                    stage=stage,
                    structure_digest=structure.structure_digest,
                    next_action=next_action,
                )
                return 0

            if args.onboard_command in {
                "placement-instruction",
                "placement-validate",
                "placement-review",
                "placement-preview",
                "placement-publish",
            }:
                workspace = open_onboarding_workspace(snapshot, _workspace_path(args.workspace), create=False)
                structure_proposal_path = (
                    Path(args.structure_proposal) if args.structure_proposal is not None else workspace.structure_proposal_path
                )
                structure_path = Path(args.structure) if args.structure is not None else workspace.structure_path
                catalog = tuple(Path(path) for path in args.catalog_package)
                catalog_inputs = tuple(args.catalog_package)
                explicit_owner = tuple(args.owner_source) if hasattr(args, "owner_source") else ()
                owner_source_whys: dict[str, str] = {}
                preaccepted_owner_sources = False
                accepted_reusable_assignments = ()

                structure_proposal = load_onboarding_structure_proposal(structure_proposal_path, snapshot)
                structure = load_structure_markdown(structure_path, structure_proposal)
                remembered_catalog, remembered_owner = remember_run_inputs(
                    snapshot,
                    catalog_inputs=catalog_inputs,
                    owner_source_specs=explicit_owner,
                )
                if not catalog_inputs and workspace.reusable_contexts_path.is_file():
                    reusable = load_accepted_reusable_contexts(
                        workspace.reusable_contexts_path,
                        snapshot,
                        structure_proposal.evidence_digest,
                        structure,
                    )
                    catalog_inputs = reusable.catalog_package_inputs
                    catalog = tuple(Path(path) for path in catalog_inputs)
                    remembered_owner = reusable.owner_source_specs
                    owner_source_whys = reusable.owner_source_whys
                    accepted_reusable_assignments = reusable.assignments
                    preaccepted_owner_sources = True
                elif not catalog_inputs and remembered_catalog:
                    # Legacy/scripting compatibility for an onboarding started before STEP 05 existed.
                    catalog_inputs = remembered_catalog
                    catalog = tuple(Path(path) for path in catalog_inputs)

                if args.onboard_command == "placement-instruction":
                    instruction = build_onboarding_placement_instruction(
                        snapshot,
                        structure_proposal_path,
                        structure_path,
                        catalog_package_roots=catalog,
                        accepted_reusable_assignments=accepted_reusable_assignments,
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
                    update_workspace_checkpoint(
                        workspace, snapshot, stage="placement instruction ready",
                        structure_digest=instruction.structure_digest,
                        source_catalog=_catalog_labels(instruction.catalog_packages),
                        source_catalog_inputs=catalog_inputs,
                        next_action=(
                            "Give `STEP-06a-placement-instruction.md` and only the frozen `evidence/` tree to a strong reasoning LLM. "
                            "Save its single JSON result as `STEP-06b-placement-proposal.json`, then run "
                            f"`contextcanon onboard placement-validate {_snapshot_cli(snapshot)}`."
                        ),
                    )
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
                    print(f"Source edits: {len(proposal.source_edits)}")
                    print(f"Source reuses: {len(proposal.source_reuses)}")
                    update_workspace_checkpoint(
                        workspace, snapshot, stage="placement proposal validated",
                        structure_digest=proposal.structure_digest,
                        placement_proposal_digest=proposal.proposal_digest,
                        source_catalog=_catalog_labels(proposal.catalog_packages),
                        source_catalog_inputs=catalog_inputs,
                        next_action=(
                            f"Run `contextcanon onboard placement-review {_snapshot_cli(snapshot)}`. "
                            "Reusable Context relationships were already accepted in STEP 05; no Source IDs need to be typed here."
                        ),
                    )
                    return 0

                review_path = Path(args.review) if args.review is not None else workspace.placement_path
                if args.onboard_command == "placement-review":
                    owner_for_review = _owner_specs_for_review(review_path, explicit_owner, remembered_owner)
                    review, created = create_or_load_placement_review(
                        review_path,
                        proposal,
                        snapshot,
                        owner_source_specs=owner_for_review,
                        owner_source_whys=owner_source_whys,
                        preaccepted_owner_sources=preaccepted_owner_sources,
                    )
                    verb = "created" if created else "loaded"
                    write_utf8(
                        workspace.placement_audit_path,
                        render_placement_source_audit(proposal, review, snapshot, review_filename=review_path.name),
                    )
                    print(f"{verb} onboarding placement review {review.review_digest}")
                    print(f"Review file: {review_path}")
                    print(f"Source audit: {workspace.placement_audit_path}")
                    print(f"Items: {len(review.items)} · Source edits: {len(review.source_edits)} · Sources: {len(review.sources)} · complete: {review.is_complete}")
                    next_action = (
                        f"Review `{workspace.placement_audit_path.name}` for source-by-source semantic loss, then run `contextcanon onboard placement-preview {_snapshot_cli(snapshot)}` after checking the exact command in PLAN.md."
                        if review.is_complete else
                        f"Inspect `{workspace.placement_audit_path.name}` source-by-source, edit `{workspace.placement_path.name}` where needed, and set every item/Source-edit/Source Decision to `accept` or `reject`. "
                        f"Then rerun `contextcanon onboard placement-review {_snapshot_cli(snapshot)}`; it validates the edited human gate and regenerates the audit."
                    )
                    update_workspace_checkpoint(
                        workspace, snapshot, stage="human placement review",
                        structure_digest=proposal.structure_digest,
                        placement_proposal_digest=proposal.proposal_digest,
                        placement_review_digest=review.review_digest,
                        placement_review_complete=review.is_complete,
                        source_catalog=_catalog_labels(proposal.catalog_packages),
                        source_catalog_inputs=catalog_inputs,
                        owner_source_specs=explicit_owner or remembered_owner,
                        next_action=next_action,
                    )
                    return 0

                review = load_placement_review(review_path, proposal, snapshot)
                project = Path(args.project) if args.project is not None else None
                preview = build_placement_publication_preview(
                    proposal,
                    review,
                    snapshot,
                    catalog_package_roots=catalog,
                    project_root=project,
                )
                write_utf8(workspace.placement_preview_path, render_placement_publication_preview(preview))
                print(f"wrote placement publication preview {workspace.placement_preview_path}")
                print(f"Review: {preview.review_digest} · complete: {preview.review_complete}")
                print(f"Touched Context Nodes: {len(preview.nodes)} · follow-ups: {len(preview.followups)}")
                if args.onboard_command == "placement-preview":
                    next_action = (
                        f"Review `STEP-09-placement-preview.md`, then run `contextcanon onboard placement-publish {_snapshot_cli(snapshot)}`."
                        if preview.review_complete else
                        "Return to `STEP-08-placement.md`, resolve all pending decisions, and preview again."
                    )
                    update_workspace_checkpoint(
                        workspace, snapshot, stage="placement publication previewed",
                        structure_digest=preview.structure_digest,
                        placement_proposal_digest=preview.proposal_digest,
                        placement_review_digest=preview.review_digest,
                        placement_review_complete=preview.review_complete,
                        source_catalog=_catalog_labels(proposal.catalog_packages),
                        source_catalog_inputs=catalog_inputs,
                        next_action=next_action,
                    )
                    return 0

                acceptance_path = (
                    Path(args.acceptance) if args.acceptance is not None else snapshot / "placement-acceptance.json"
                )
                result = publish_placement_review(
                    preview,
                    review,
                    snapshot_root=snapshot,
                    catalog_package_roots=catalog,
                    acceptance_path=acceptance_path,
                )
                write_utf8(workspace.placement_followup_path, render_placement_followups(preview))
                print(f"published reviewed placement {result.review_digest}")
                print(f"Acceptance record: {result.acceptance_path}")
                print(f"Acceptance digest: {result.acceptance_digest}")
                print(f"Changed Context sources: {len(result.changed_sources)}")
                print(f"Follow-up: {workspace.placement_followup_path}")
                update_workspace_checkpoint(
                    workspace, snapshot, stage="placement published",
                    structure_digest=preview.structure_digest,
                    placement_proposal_digest=preview.proposal_digest,
                    placement_review_digest=preview.review_digest,
                    placement_review_complete=True,
                    acceptance_digest=result.acceptance_digest,
                    source_catalog=_catalog_labels(proposal.catalog_packages),
                    source_catalog_inputs=catalog_inputs,
                    next_action=(
                        "Review `STEP-10-placement-followup.md`. Accepted mutable-Markdown Source After transformations were published transactionally with canonical Context; "
                        "ordinary ContextCanon-native project growth now happens by editing the relevant Node sources directly, not by rerunning migration onboarding."
                    ),
                )
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

        if args.command == "author":
            node_root = _node_root(Path(args.path))
            if args.author_command == "rule":
                result = add_rule(
                    node_root,
                    group=args.group,
                    title=args.title,
                    statement=args.statement,
                    why=args.why,
                )
                print(f"added Rule {result.element_id} to {result.source_path}")
            else:
                result = add_topic(
                    node_root,
                    title=args.title,
                    condition=args.condition,
                    required_resources=tuple(args.required_resource),
                    optional_resources=tuple(args.optional_resource),
                    required_nodes=tuple(args.required_node),
                    optional_nodes=tuple(args.optional_node),
                )
                print(f"added Topic {result.element_id} to {result.source_path}")
            print(f"Next: contextcanon build {node_root}")
            print(f"Then: contextcanon check {node_root}")
            return 0

        if args.command == "parent":
            node_root = _node_root(Path(args.node))
            if args.parent_command == "review":
                result, receipt = review_parent_candidate(node_root)
                print(render_diff(result), end="")
                try:
                    label = receipt.relative_to(node_root).as_posix()
                except ValueError:
                    label = str(receipt)
                print(f"Parent review receipt: {label}")
                print("Accepted Parent pin is unchanged until 'contextcanon parent accept'.")
                return 0
            accepted = accept_parent_candidate(node_root)
            print(f"accepted Parent {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")
            print(f"Next: contextcanon build {node_root}")
            print(f"Then: contextcanon check {node_root}")
            return 0

        if args.command == "source":
            node_root = _node_root(Path(args.node))
            if args.source_command == "adopt":
                adopted, changed = adopt_source_package(node_root, Path(args.package))
                verb = "adopted" if changed else "already adopted"
                print(f"{verb} Source {adopted.metadata.name} {adopted.metadata.version} ({adopted.package_digest})")
                print(f"Next: contextcanon build {node_root}")
                print(f"Then: contextcanon check {node_root}")
                return 0
            if args.source_command == "fetch":
                candidate, location = fetch_git_candidate(node_root, args.source_id)
                try:
                    label = location.relative_to(node_root).as_posix()
                except ValueError:
                    label = str(location)
                print(f"fetched candidate {candidate.metadata.name} {candidate.metadata.version} ({candidate.package_digest})")
                provenance = load_candidate_provenance(node_root, candidate.package_digest)
                if provenance is not None:
                    print(f"Candidate Git commit: {provenance['candidate_ref']}")
                print(f"Candidate package: {label}")
                print("Accepted Source pin is unchanged until explicit review and accept.")
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
