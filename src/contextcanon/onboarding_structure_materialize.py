from __future__ import annotations

import hashlib
import json
import re
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
    existing_node_version: str | None
    directory_exists: bool


@dataclass(frozen=True)
class StructureMaterializationPreview:
    project_root: Path
    structure_digest: str
    items: tuple[StructureMaterializationItem, ...]


@dataclass(frozen=True)
class _RecoveredNodeIdentity:
    id: str
    name: str
    version: str
    origin: str


def _node_root(project_root: Path, path: str) -> Path:
    if path == ".":
        return project_root
    return project_root / Path(*PurePosixPath(path).parts)


def _identity(value: object, origin: str) -> _RecoveredNodeIdentity | None:
    if not isinstance(value, dict):
        return None
    node_id = value.get("id")
    name = value.get("name")
    version = value.get("version")
    if not all(isinstance(item, str) and item.strip() and "\n" not in item and "\r" not in item for item in (node_id, name, version)):
        return None
    return _RecoveredNodeIdentity(node_id.strip(), name.strip(), version.strip(), origin)


def _json_object(path: Path) -> dict[str, object] | None:
    if path.is_symlink() or not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _yaml_generated_identity(path: Path) -> _RecoveredNodeIdentity | None:
    if path.is_symlink() or not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not text.startswith("# GENERATED ContextCanon machine state"):
        return None
    match = re.search(
        r'(?m)^node:\n  id: (?P<id>".*")\n  name: (?P<name>".*")\n  version: (?P<version>".*")$',
        text,
    )
    if match is None:
        return None
    try:
        value = {key: json.loads(match.group(key)) for key in ("id", "name", "version")}
    except json.JSONDecodeError:
        return None
    return _identity(value, ".context/context.yaml")


def _recover_node_identity(root: Path, *, include_acceptance: bool) -> _RecoveredNodeIdentity | None:
    candidates: list[_RecoveredNodeIdentity] = []
    manifest = _json_object(root / ".context" / "package.json")
    if manifest is not None and manifest.get("schema") == "contextcanon/package/v0":
        item = _identity(manifest.get("node"), ".context/package.json")
        if item is not None:
            candidates.append(item)
    yaml_identity = _yaml_generated_identity(root / ".context" / "context.yaml")
    if yaml_identity is not None:
        candidates.append(yaml_identity)
    if include_acceptance:
        accepted = root / ".context" / "onboarding" / "accepted"
        if accepted.is_dir() and not accepted.is_symlink():
            for path in sorted(accepted.glob("*/acceptance.json")):
                raw = _json_object(path)
                if raw is None or raw.get("schema") != "contextcanon/onboarding-acceptance/v0":
                    continue
                item = _identity(raw.get("node"), path.relative_to(root).as_posix())
                if item is not None:
                    candidates.append(item)
    if not candidates:
        return None
    node_ids = {item.id for item in candidates}
    if len(node_ids) != 1:
        origins = ", ".join(f"{item.origin}={item.id}" for item in candidates)
        raise ContextCanonError(f"Conflicting prior ContextCanon Node identities: {origins}")
    machine = [item for item in candidates if item.origin in {".context/package.json", ".context/context.yaml"}]
    if machine:
        metadata = {(item.name, item.version) for item in machine}
        if len(metadata) != 1:
            raise ContextCanonError("Conflicting generated ContextCanon Node name/version metadata")
        return machine[0]
    metadata = {(item.name, item.version) for item in candidates}
    if len(metadata) != 1:
        raise ContextCanonError("Prior ContextCanon acceptance records disagree on Node name/version")
    return candidates[0]


def _manifest_file_hash(root: Path, rel: str) -> str | None:
    manifest = _json_object(root / ".context" / "package.json")
    if manifest is None or manifest.get("schema") != "contextcanon/package/v0":
        return None
    files = manifest.get("files")
    if not isinstance(files, list):
        return None
    for item in files:
        if isinstance(item, dict) and item.get("path") == rel and isinstance(item.get("sha256"), str):
            return str(item["sha256"])
    return None


def _matches_generated_manifest(root: Path, rel: str) -> bool:
    path = root / Path(*PurePosixPath(rel).parts)
    if not path.exists() and not path.is_symlink():
        return True
    if path.is_symlink() or not path.is_file():
        return False
    expected = _manifest_file_hash(root, rel)
    return expected is not None and hashlib.sha256(path.read_bytes()).hexdigest() == expected


def _generated_context_namespace(root: Path) -> bool:
    context = root / "CONTEXT"
    if not context.exists() and not context.is_symlink():
        return True
    if context.is_symlink() or not context.is_dir():
        return False
    files = [path for path in context.rglob("*") if path.is_file() or path.is_symlink()]
    if not files:
        return True
    generated_readme = False
    readme = context / "README.md"
    if readme.is_file() and not readme.is_symlink():
        try:
            generated_readme = readme.read_text(encoding="utf-8").startswith("# Generated Context package resources\n")
        except (OSError, UnicodeDecodeError):
            generated_readme = False
    for path in files:
        if path.is_symlink():
            return False
        rel = path.relative_to(root).as_posix()
        if rel == "CONTEXT/README.md" and generated_readme:
            continue
        expected = _manifest_file_hash(root, rel)
        if expected is None or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            return False
    return True


def _framework_machine_namespace(root: Path, *, allow_onboarding: bool) -> bool:
    machine = root / ".context"
    if not machine.exists() and not machine.is_symlink():
        return True
    if machine.is_symlink() or not machine.is_dir():
        return False
    allowed = {"context.yaml", "package.json", "sources"}
    if allow_onboarding:
        allowed.add("onboarding")
    for child in machine.iterdir():
        if child.name not in allowed or child.is_symlink():
            return False
    return True


def _preflight_new_node(
    root: Path,
    *,
    project_root: Path,
    recovery_identity: _RecoveredNodeIdentity | None = None,
) -> None:
    source = root / "CONTEXT.src.md"
    if source.exists() or source.is_symlink():
        raise ContextCanonError(f"Structure materialization expected a missing Node but found {source}")
    if recovery_identity is None:
        for name in ("CONTEXT.md", "CONTEXT"):
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
        return
    if not _matches_generated_manifest(root, "CONTEXT.md"):
        raise ContextCanonError(
            f"Refusing to recover Context Node at {root}: existing CONTEXT.md is not proven generated output"
        )
    if not _generated_context_namespace(root):
        raise ContextCanonError(
            f"Refusing to recover Context Node at {root}: project-owned path already exists: CONTEXT"
        )
    if not _framework_machine_namespace(
        root,
        allow_onboarding=root.resolve() == project_root.resolve(),
    ):
        raise ContextCanonError(
            f"Refusing to recover Context Node at {root}: .context contains non-ContextCanon-owned entries"
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
                    existing_node_version=parsed.metadata.version,
                    directory_exists=True,
                )
            )
            continue
        recovered = _recover_node_identity(root, include_acceptance=node.path == ".")
        if recovered is not None:
            _preflight_new_node(root, project_root=project, recovery_identity=recovered)
            items.append(
                StructureMaterializationItem(
                    key=node.key,
                    name=node.name,
                    path=node.path,
                    lifecycle=node.lifecycle,
                    status="recover",
                    existing_node_id=recovered.id,
                    existing_node_name=recovered.name,
                    existing_node_version=recovered.version,
                    directory_exists=True,
                )
            )
            continue
        if node.path == ".":
            raise ContextCanonError(
                "Structure-first continuation found no CONTEXT.src.md at the project root and no unambiguous prior ContextCanon root identity to recover"
            )
        _preflight_new_node(root, project_root=project)
        items.append(
            StructureMaterializationItem(
                key=node.key,
                name=node.name,
                path=node.path,
                lifecycle=node.lifecycle,
                status="create",
                existing_node_id=None,
                existing_node_name=None,
                existing_node_version=None,
                directory_exists=root.exists(),
            )
        )

    roots = [item for item in items if item.path == "."]
    if len(roots) != 1 or roots[0].status not in {"existing", "recover"}:
        raise ContextCanonError(
            "Structure-first continuation requires the project root to remain an existing or provably recoverable Context Node"
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
        elif item.status == "recover":
            lines.append(
                f"- **{item.name}** (`{item.path}`) — recover missing `CONTEXT.src.md` for proven existing Node `{item.existing_node_id}`; stable identity/name/version are preserved from ContextCanon machine/acceptance state"
            )
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


def _render_skeleton(
    node: HumanStructureNode,
    node_id: str,
    *,
    canonical_name: str | None = None,
    version: str = "0.1.0-draft",
) -> str:
    state = (
        "This area is intentionally reserved by the project owner; implementation details are not yet decided."
        if node.lifecycle == "reserved"
        else "This Node skeleton reserves the accepted onboarding landing point before detailed project knowledge is distributed."
    )
    return (
        f"# {canonical_name or node.name} — Local Context Source\n"
        f'<!-- ctx:node id="{node_id}" version="{version}" -->\n\n'
        "## Local Overview\n\n"
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
            if item.status not in {"create", "recover"}:
                continue
            root = _node_root(project, item.path)
            recovered = (
                _RecoveredNodeIdentity(
                    item.existing_node_id or "",
                    item.existing_node_name or item.name,
                    item.existing_node_version or "0.1.0",
                    "preview",
                )
                if item.status == "recover"
                else None
            )
            _preflight_new_node(root, project_root=project, recovery_identity=recovered)
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
            node_id = item.existing_node_id if item.status == "recover" else str(uuid.uuid4())
            assert node_id is not None
            write_utf8(
                source,
                _render_skeleton(
                    node,
                    node_id,
                    canonical_name=item.existing_node_name if item.status == "recover" else None,
                    version=item.existing_node_version or "0.1.0-draft",
                ),
            )
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
