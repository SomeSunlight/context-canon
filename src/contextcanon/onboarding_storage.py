"""Owned, repository-root onboarding locators; identities remain complete.

Evidence bytes and review schemas do not depend on these directory names.
Migration is deliberately separate from normal runtime resolution.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from .parser import ContextCanonError, find_repo_root
from .version_store import TOKEN_LENGTHS

SCOPE_MARKER = ".scope.json"
RUN_MARKER = ".run.json"
SCOPE_SCHEMA = "contextcanon/onboarding-scope/v1"
RUN_SCHEMA = "contextcanon/onboarding-run/v1"


def _json(path: Path) -> dict:
    if path.is_symlink():
        raise ContextCanonError(f"Unsafe onboarding metadata: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ContextCanonError(f"Invalid onboarding metadata: {path}") from exc
    if not isinstance(value, dict):
        raise ContextCanonError(f"Invalid onboarding metadata: {path}")
    return value


def _normal_path(path: Path) -> None:
    # Check lexical ancestors before resolve(), which would hide a symlink.
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ContextCanonError(f"Onboarding storage is a symbolic link: {candidate}")


def _write_marker(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
    except FileExistsError:
        if _json(path) != value:
            raise ContextCanonError(f"Onboarding ownership changed: {path}")


def _scope(project: Path) -> tuple[Path, dict, str]:
    project = project.resolve()
    repository = find_repo_root(project)
    relative = project.relative_to(repository).as_posix()
    value = {"schema": SCOPE_SCHEMA, "project_path": relative}
    key = hashlib.sha256(relative.encode("utf-8")).hexdigest()
    return repository, value, key


def scope_root(project: Path, *, create: bool = False, legacy: bool = True) -> Path:
    repository, expected, key = _scope(project)
    old = project.resolve() / ".context" / "onboarding"
    # Existing local runs stay usable until an explicit migration. A central
    # root can contain other scopes, so its existence alone is not a legacy run.
    if legacy and old.exists() and (
        (old / "inventory-state.json").is_file()
        or (old / "inventory-acceptance.json").is_file()
        or any(p.is_dir() and (p / "manifest.json").is_file() for p in old.iterdir())
    ):
        _normal_path(old)
        return old
    base = repository / ".context" / "onboarding"
    _normal_path(base)
    free = None
    for length in TOKEN_LENGTHS:
        candidate = base / key[:length]
        _normal_path(candidate)
        if not candidate.exists():
            free = free or candidate
            continue
        marker = candidate / SCOPE_MARKER
        value = _json(marker)
        other = value.get("project_path")
        if set(value) != {"schema", "project_path"} or value.get("schema") != SCOPE_SCHEMA or not isinstance(other, str):
            raise ContextCanonError(f"Unowned onboarding scope: {candidate}")
        if not hashlib.sha256(other.encode("utf-8")).hexdigest().startswith(candidate.name):
            raise ContextCanonError(f"Onboarding scope token does not match its identity: {candidate}")
        if value == expected:
            return candidate
    if free is None:
        raise ContextCanonError("No free onboarding scope locator")
    if create:
        _write_marker(free / SCOPE_MARKER, expected)
    return free


def run_path(project: Path, evidence_digest: str, *, central: bool = False) -> Path:
    if not re.fullmatch(r"[0-9a-f]{64}", evidence_digest):
        raise ContextCanonError("Invalid onboarding Evidence identity")
    scope = scope_root(project, create=True, legacy=not central)
    if not (scope / SCOPE_MARKER).is_file():
        return scope / evidence_digest
    free = None
    for length in TOKEN_LENGTHS:
        candidate = scope / evidence_digest[:length]
        _normal_path(candidate)
        if not candidate.exists():
            free = free or candidate
            continue
        value = _json(candidate / RUN_MARKER)
        digest = value.get("evidence_digest")
        if value.get("schema") != RUN_SCHEMA or not isinstance(digest, str) or not digest.startswith(candidate.name):
            raise ContextCanonError(f"Invalid onboarding run identity: {candidate}")
        if digest == evidence_digest:
            project_from_run(candidate)
            return candidate
    if free is None:
        raise ContextCanonError("No free onboarding run locator")
    return free


def run_metadata(project: Path, evidence_digest: str) -> dict:
    _, scope, _ = _scope(project)
    return {"schema": RUN_SCHEMA, "project_path": scope["project_path"], "evidence_digest": evidence_digest}


def project_from_run(snapshot: Path) -> Path | None:
    _normal_path(snapshot)
    marker = snapshot / RUN_MARKER
    if not marker.exists():
        return None
    value = _json(marker)
    if set(value) != {"schema", "project_path", "evidence_digest"} or value["schema"] != RUN_SCHEMA:
        raise ContextCanonError(f"Invalid onboarding run ownership: {marker}")
    relative = value["project_path"]
    if not isinstance(relative, str) or (relative != "." and (
        PurePosixPath(relative).is_absolute() or "\\" in relative or ":" in relative
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    )):
        raise ContextCanonError(f"Unsafe onboarding project scope: {relative!r}")
    repository = find_repo_root(snapshot)
    project = repository / relative
    _normal_path(project)
    scope = scope_root(project, legacy=False)
    digest = value["evidence_digest"]
    if snapshot.parent != scope or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest) or not digest.startswith(snapshot.name):
        raise ContextCanonError(f"Onboarding locator does not match ownership: {snapshot}")
    manifest = _json(snapshot / "manifest.json")
    if manifest.get("evidence_digest") != digest:
        raise ContextCanonError(f"Onboarding run does not match frozen Evidence: {snapshot}")
    return project.resolve()


def default_workspace(project: Path) -> Path:
    project = project.resolve()
    repository, _, _ = _scope(project)
    old = project / "contextcanon-onboarding"
    if project == repository or old.exists():
        return old
    return repository / ("contextcanon-onboarding-" + scope_root(project).name)


def provenance_path(snapshot: Path, package) -> Path:
    from .version_store import package_key
    return snapshot / "catalog-provenance" / (package_key(package) + ".json")


def binding_from_row(row: dict):
    from .model import PackageDependency
    fields = ("id", "name", "version", "normalized_digest", "package_digest")
    if not all(isinstance(row.get(field), str) and row[field] for field in fields):
        raise ContextCanonError("Incomplete frozen onboarding package binding")
    return PackageDependency(*(row[field] for field in fields))


def package_files(root: Path, package) -> dict[str, bytes]:
    from .package import PACKAGE_MANIFEST_PATH
    return {rel: (root / rel).read_bytes() for rel in (PACKAGE_MANIFEST_PATH, *(f.path for f in package.files))}


def freeze_package(snapshot: Path, root: Path, package, provenance: dict) -> Path:
    from .onboarding import project_root_from_snapshot
    from .version_store import install_version
    destination = install_version(project_root_from_snapshot(snapshot), root, package)
    provenance = {**provenance, "node_id": package.metadata.id, "normalized_digest": package.normalized_digest}
    path = provenance_path(snapshot, package)
    # Provenance belongs to a review, not to the shared package. An existing
    # freeze is authoritative even if the provider's branch has since moved.
    if path.exists():
        value = _json(path)
        if value.get("package_digest") != package.package_digest or value.get("node_id") != package.metadata.id or value.get("normalized_digest") != package.normalized_digest:
            raise ContextCanonError(f"Frozen onboarding provenance changed: {path}")
    else:
        _write_marker(path, provenance)
    return destination


def enclosing_parent(snapshot: Path):
    """Return (exact package, exact files, authoring locator), frozen once/run."""
    from .compiler import Compiler
    from .onboarding import find_enclosing_context_root, project_root_from_snapshot
    from .package import artifact_files, compiled_package, load_package
    from .version_store import library_root, package_key, store_package, version_path
    project = project_root_from_snapshot(snapshot)
    repository = find_repo_root(project)
    record = snapshot / "enclosing-parent.json"
    if record.exists():
        value = _json(record)
        if value == {"schema": "contextcanon/onboarding-enclosing-parent/v1", "binding": None}:
            return None
        binding = binding_from_row(value.get("binding", {}))
        node_path = value.get("node_path")
        if not isinstance(node_path, str) or PurePosixPath(node_path).is_absolute() or ".." in PurePosixPath(node_path).parts or "\\" in node_path or ":" in node_path:
            raise ContextCanonError("Unsafe frozen enclosing Parent locator")
        root = version_path(project, binding)
        package = load_package(root)
        if package_key(package) != package_key(binding):
            raise ContextCanonError("Frozen enclosing Parent identity changed")
        return package, package_files(root, package), repository / node_path
    parent = find_enclosing_context_root(project)
    if parent is None:
        _write_marker(record, {"schema": "contextcanon/onboarding-enclosing-parent/v1", "binding": None})
        return None
    compiled = Compiler(repository).compile(parent)
    package = compiled_package(compiled)
    files = artifact_files(compiled)
    store_package(library_root(project), package, files, action="onboarding frozen enclosing Parent", node_root=project)
    value = {"schema": "contextcanon/onboarding-enclosing-parent/v1", "node_path": parent.relative_to(repository).as_posix(),
             "binding": {"id": package.metadata.id, "name": package.metadata.name, "version": package.metadata.version,
                         "normalized_digest": package.normalized_digest, "package_digest": package.package_digest}}
    _write_marker(record, value)
    return package, files, parent
