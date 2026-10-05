"""Working-tree storage for complete, verified immutable Node versions.

Directory tokens are locators. The full Node/semantic/exact-byte binding in
each package manifest is authoritative; no allocation index is required.
Migration of old directories deliberately lives outside this runtime module.
"""
from __future__ import annotations

import hashlib
import errno
import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path

from .model import CompiledPackage, PackageDependency, SourceRef, ParentRef
from .package import PACKAGE_MANIFEST_PATH, load_package
from .parser import ContextCanonError, find_repo_root, parse_node
from .path_budget import preflight_paths

TOKEN_LENGTHS = (16, 24, 32, 40, 48, 56, 64)


def identity_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def package_key(package: CompiledPackage | PackageDependency | SourceRef | ParentRef) -> str:
    node_id = package.metadata.id if hasattr(package, "metadata") else package.id
    # CONTEXT.md need not render the Node ID or every semantic field. Thus two
    # different Nodes can genuinely have identical human package bytes. An
    # exact-byte digest alone is NOT a complete shared-store key.
    payload = [node_id, package.normalized_digest, package.package_digest]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()


def library_root(node_root: Path) -> Path:
    return find_repo_root(node_root) / ".context" / "versions"


def package_location(store: Path, key: str, *, lengths=TOKEN_LENGTHS) -> Path:
    if not re.fullmatch(r"[0-9a-f]{64}", key):
        raise ContextCanonError(f"Invalid package storage identity: {key!r}")
    first_free = None
    for length in lengths:
        path = store / key[:length]
        if not path.exists():
            if first_free is None:
                first_free = path
            continue
        if path.is_symlink():
            raise ContextCanonError(f"Package store entry is a symbolic link: {path}")
        existing_key = package_key(load_package(path))
        if existing_key == key:
            return path
        if not existing_key.startswith(path.name):
            raise ContextCanonError(f"Package token does not match its complete identity: {path}")
    if first_free is None:
        raise ContextCanonError(f"No free package location for {key}")
    return first_free


def version_path(node_root: Path, package: CompiledPackage | PackageDependency | SourceRef | ParentRef) -> Path:
    return package_location(library_root(node_root), package_key(package))


def accepted_package_path(node_root: Path, dependency: PackageDependency | SourceRef | ParentRef) -> Path:
    central = version_path(node_root, dependency)
    if central.exists():
        return central
    legacy = node_root / ".context" / "sources" / str(dependency.package_digest)
    return legacy if legacy.exists() else central


def _matches(path: Path, package: CompiledPackage) -> bool:
    if not path.exists():
        return False
    existing = load_package(path)
    if package_key(existing) != package_key(package):
        raise ContextCanonError(f"Immutable package store contains a different version: {path}")
    return True


def publish_directory(temporary: Path, destination: Path, package: CompiledPackage) -> None:
    # Retry only the final atomic publication on transient Windows locks.
    delays = (0.05, 0.10, 0.20, 0.40, 0.80)
    for attempt in range(len(delays) + 1):
        try:
            os.replace(temporary, destination)
            return
        except OSError as exc:
            if not isinstance(exc, (PermissionError, FileExistsError)) and exc.errno not in {errno.EACCES, errno.EPERM, errno.EEXIST, errno.ENOTEMPTY}:
                raise
            if _matches(destination, package):
                return
            if attempt == len(delays):
                raise ContextCanonError(
                    f"Could not publish immutable package {package.metadata.name} {package.metadata.version} "
                    f"to {destination} after retrying a temporary filesystem lock: {exc}"
                ) from exc
            time.sleep(delays[attempt])


def store_package(store: Path, package: CompiledPackage, files: dict[str, bytes], *,
                  action: str, node_root: Path, lengths=TOKEN_LENGTHS, destination: Path | None = None) -> Path:
    destination = destination or package_location(store, package_key(package), lengths=lengths)
    preflight_paths(destination, files, action=action, node_root=node_root)
    if _matches(destination, package):
        return destination
    store.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".tmp-", dir=store))
    try:
        preflight_paths(temporary, files, action=action + " staging", node_root=node_root)
        for rel, content in files.items():
            path = temporary / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        if not _matches(temporary, package):
            raise ContextCanonError("Staged package identity changed")
        publish_directory(temporary, destination, package)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return destination


def install_version(node_root: Path, package_root: Path, package: CompiledPackage) -> Path:
    files = {rel: (package_root / rel).read_bytes()
             for rel in (PACKAGE_MANIFEST_PATH, *(file.path for file in package.files))}
    return store_package(library_root(node_root), package, files,
                         action="accepted immutable package installation", node_root=node_root)


def scratch_root(node_root: Path, name: str, *, create: bool = False) -> Path:
    if name not in {"candidates", "parent-candidates", "source-reviews", "parent-reviews"}:
        raise ValueError(f"Unknown review store: {name}")
    repo = find_repo_root(node_root)
    source = node_root / "CONTEXT.src.md"
    owner = parse_node(node_root, repo).metadata.id if source.is_file() else node_root.relative_to(repo).as_posix()
    node_path = node_root.relative_to(repo).as_posix()
    expected_scope = {"owner": owner, "node_path": node_path}
    root = repo / ".context" / name / identity_token(owner + ":" + node_path)
    marker = root / ".scope.json"
    if root.is_symlink():
        raise ContextCanonError(f"Review scope is a symbolic link: {root}")
    if marker.exists():
        try:
            recorded = json.loads(marker.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise ContextCanonError(f"Invalid review scope {marker}: {exc}") from exc
        if recorded != expected_scope:
            raise ContextCanonError(f"Review scope token collision: {root}")
    elif root.exists() and any(root.iterdir()):
        raise ContextCanonError(f"Unowned review scope: {root}")
    elif create:
        root.mkdir(parents=True, exist_ok=True)
        try:
            with marker.open("x", encoding="utf-8") as handle:
                json.dump(expected_scope, handle, ensure_ascii=False)
        except FileExistsError:
            return scratch_root(node_root, name)
    return root


def review_path(node_root: Path, name: str, identity: str, *, match_field: str, match_value: str, extra_match: dict[str, str] | None = None) -> Path:
    store = scratch_root(node_root, name)
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    first_free = None
    for length in TOKEN_LENGTHS:
        path = store / (key[:length] + ".json")
        if not path.exists():
            if first_free is None:
                first_free = path
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise ContextCanonError(f"Invalid review record {path}: {exc}") from exc
        value = record
        for field in match_field.split("."):
            value = value.get(field) if isinstance(value, dict) else None
        if value == match_value and all(record.get(field) == expected for field, expected in (extra_match or {}).items()):
            return path
    if first_free is None:
        raise ContextCanonError(f"No free review location for {identity}")
    return first_free
