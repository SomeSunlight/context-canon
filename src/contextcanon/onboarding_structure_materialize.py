from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .compiler import Compiler
from .onboarding_structure import (
    HumanStructureNode,
    HumanStructurePlan,
    load_onboarding_structure_proposal,
    load_structure_markdown,
)
from .onboarding_workspace import write_utf8
from .outputs import write_outputs
from .parser import ContextCanonError, find_repo_root, parse_node


@dataclass(frozen=True)
class StructureMaterializationItem:
    key: str
    name: str
    path: str
    lifecycle: str
    status: str
    existing_node_id: str | None
    existing_node_name: str | None
    directory_exists: bool


@dataclass(frozen=True)
class StructureMaterializationPreview:
    project_root: Path
    structure_digest: str
    items: tuple[StructureMaterializationItem, ...]


_COLLISION_NAMES = ("CONTEXT.md", "CONTEXT")


def _node_root(project_root: Path, path: str) -> Path:
    if path == ".":
        return project_root
    return project_root / Path(*PurePosixPath(path).parts)


def _preflight_new_node(root: Path) -> None:
    source = root / "CONTEXT.src.md"
    if source.exists() or source.is_symlink():
        raise ContextCanonError(f"Structure materialization expected a missing Node but found {source}")
    for name in _COLLISION_NAMES:
        target = root / name
        if target.exists() or target.is_symlink():
            raise ContextCanonError(
                f"Refusing to materialize Context Node at {root}: project-owned path already exists: {name}"
            )
    machine = root / ".context"
    if machine.exists() or machine.is_symlink():
        raise ContextCanonError(
            f"Refusing to materialize Context Node at {root}: pre-existing .context path would be ambiguous"
        )


def preview_structure_materialization(
    snapshot_root: Path,
    proposal_path: Path,
    structure_path: Path,
    *,
    project_root: Path | None = None,
) -> StructureMaterializationPreview:
    proposal = load_onboarding_structure_proposal(proposal_path, snapshot_root)
    plan = load_structure_markdown(structure_path, proposal)
    project = (project_root or find_repo_root(snapshot_root)).resolve()
    if not (project / ".git").exists():
        raise ContextCanonError(f"Structure materialization project root is not a Git repository: {project}")

    items: list[StructureMaterializationItem] = []
    for node in plan.nodes:
        root = _node_root(project, node.path)
        source = root / "CONTEXT.src.md"
        if source.is_file():
            parsed = parse_node(root, project)
            items.append(
                StructureMaterializationItem(
                    key=node.key,
                    name=node.name,
                    path=node.path,
                    lifecycle=node.lifecycle,
                    status="existing",
                    existing_node_id=parsed.metadata.id,
                    existing_node_name=parsed.metadata.name,
                    directory_exists=True,
                )
            )
            continue
        _preflight_new_node(root)
        items.append(
            StructureMaterializationItem(
                key=node.key,
                name=node.name,
                path=node.path,
                lifecycle=node.lifecycle,
                status="create",
                existing_node_id=None,
                existing_node_name=None,
                directory_exists=root.exists(),
            )
        )

    roots = [item for item in items if item.path == "."]
    if len(roots) != 1 or roots[0].status != "existing":
        raise ContextCanonError(
            "Structure-first continuation requires the already-onboarded project root to remain an existing Context Node"
        )

    return StructureMaterializationPreview(project, plan.structure_digest, tuple(items))


def render_structure_materialization_preview(preview: StructureMaterializationPreview) -> str:
    lines = [
        "# ContextCanon structure materialization preview",
        "",
        f"Structure digest: `{preview.structure_digest}`",
        "",
        "No project files were changed by this preview.",
        "",
        "## Nodes",
        "",
    ]
    for item in preview.items:
        if item.status == "existing":
            label = f"existing Node `{item.existing_node_id}`"
            if item.existing_node_name != item.name:
                label += f"; canonical name `{item.existing_node_name}` is preserved while structure label is `{item.name}`"
            lines.append(f"- **{item.name}** (`{item.path}`) — {label}")
        else:
            state = "existing directory" if item.directory_exists else "new directory"
            reserved = "; reserved" if item.lifecycle == "reserved" else ""
            lines.append(
                f"- **{item.name}** (`{item.path}`) — create Context Node in {state}; fresh stable UUID allocated once at materialization{reserved}"
            )
    lines.extend(
        [
            "",
            "Materialization creates only missing `CONTEXT.src.md` skeletons and their deterministic compiler output. Existing Nodes and ordinary project files are not rewritten. Individual project knowledge is distributed only by the later reviewed placement pass.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_skeleton(node: HumanStructureNode, node_id: str) -> str:
    state = (
        "This area is intentionally reserved by the project owner; implementation details are not yet decided."
        if node.lifecycle == "reserved"
        else "This Node skeleton reserves the accepted onboarding landing point before detailed project knowledge is distributed."
    )
    return (
        f"# {node.name} — Local Context Source\n"
        f'<!-- ctx:node id="{node_id}" version="0.1.0-draft" -->\n\n'
        "## Overview\n\n"
        f"{state}\n\n"
        "The later placement pass will add only the Rules, Topics, Sources, or mappings reviewed for this area.\n"
    )


def _remove_created_output(node_root: Path, rel: str) -> None:
    path = node_root / Path(*PurePosixPath(rel).parts)
    if path.is_file() or path.is_symlink():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        return
    parent = path.parent
    while parent != node_root:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def materialize_structure_skeletons(preview: StructureMaterializationPreview) -> tuple[Path, ...]:
    project = preview.project_root
    created_sources: list[Path] = []
    created_outputs: list[tuple[Path, str]] = []
    try:
        for item in preview.items:
            if item.status != "create":
                continue
            root = _node_root(project, item.path)
            _preflight_new_node(root)
            root.mkdir(parents=True, exist_ok=True)
            source = root / "CONTEXT.src.md"
            node = HumanStructureNode(
                key=item.key,
                name=item.name,
                path=item.path,
                lifecycle=item.lifecycle,
                parent_key=None,
                proposal_key=None,
            )
            write_utf8(source, _render_skeleton(node, str(uuid.uuid4())))
            created_sources.append(source)

        compiler = Compiler(project)
        for source in created_sources:
            root = source.parent
            compiled = compiler.compile(root)
            for rel in write_outputs(compiled):
                created_outputs.append((root, rel))
        return tuple(created_sources)
    except BaseException:
        for root, rel in reversed(created_outputs):
            _remove_created_output(root, rel)
        for source in reversed(created_sources):
            source.unlink(missing_ok=True)
            parent = source.parent
            while parent != project:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
        raise
