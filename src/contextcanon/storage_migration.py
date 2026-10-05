"""Removable Phase-1 transition from consumer-local package directories.

Runtime readers do not depend on this module. Migration is explicit and
preview-first; it never fetches providers, rewrites pins or changes packages.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .compiler import discover_nodes
from .gitignore import ensure_candidate_gitignore
from .model import CompiledPackage
from .package import PACKAGE_MANIFEST_PATH, load_package
from .parser import ContextCanonError, find_repo_root
from .parser import parse_node
from .links import markdown_link_target
from .sources import _SOURCE_LINE_RE, _atomic_write_text
from .path_budget import preflight_paths
from .version_history import render_inventory
from .version_store import identity_token, install_version, library_root, package_key, package_location, version_path

MIGRATION_SCHEMA = "contextcanon/storage-migration/v1"
LINK_SCHEMA = "contextcanon/storage-migration-links/v1"


def _carrier_links(repo: Path, node: Path) -> tuple[bytes, bytes]:
    """Change only a pinned import's locator into its owned legacy wrapper.

    Real provider/discovery locations and all semantic pin fields stay intact.
    No broad replacement in prose, comments or arbitrary project documents.
    """
    source = node / "CONTEXT.src.md"
    before = source.read_bytes()
    parsed = parse_node(node, repo)
    replacements = {}
    for ref in (*parsed.parents, *parsed.sources):
        if not ref.is_pinned or getattr(ref, "has_transport", False):
            continue
        old = node / ".context/sources" / str(ref.package_digest)
        located = (node / ref.locator).resolve()
        if located not in {old.resolve(), (old / "CONTEXT.md").resolve()}:
            continue
        target = version_path(node, ref) / "CONTEXT.md"
        new = os.path.relpath(target, node).replace(os.sep, "/")
        replacements[ref.locator] = markdown_link_target(new)
    lines = before.decode("utf-8").splitlines(keepends=True)
    from .links import markdown_target_locator
    for index, line in enumerate(lines):
        match = _SOURCE_LINE_RE.match(line)
        if match is None:
            continue
        old = markdown_target_locator(match.group("path"))
        if old in replacements:
            start, end = match.span("path")
            lines[index] = line[:start] + replacements[old] + line[end:]
    return before, "".join(lines).encode("utf-8")


def _rebind_link_reviews(repo: Path, receipt: Path) -> None:
    raw = json.loads(receipt.read_text(encoding="utf-8"))
    source_rel = raw.get("source")
    if raw.get("schema") != LINK_SCHEMA or not isinstance(source_rel, str) or Path(source_rel).is_absolute() or ".." in Path(source_rel).parts:
        raise ContextCanonError(f"Invalid carrier-link migration receipt: {receipt}")
    if receipt.name != identity_token(source_rel) + ".links.json":
        raise ContextCanonError(f"Carrier-link ownership token mismatch: {receipt}")
    source = repo / source_rel
    if source.is_symlink() or hashlib.sha256(source.read_bytes()).hexdigest() != raw.get("after_sha256"):
        raise ContextCanonError(f"Carrier-link migration recovery found changed authoring: {source}")
    parsed = parse_node(source.parent, repo)
    if parsed.metadata.id != raw.get("node_id"):
        raise ContextCanonError(f"Carrier-link migration owner changed: {source}")
    # Frozen review decisions stay valid only for the exact mechanically moved
    # locator. Stale reviews are left stale, never promoted to valid state.
    for name in ("parent-reviews", "source-reviews"):
        from .version_store import scratch_root
        stores = (source.parent / ".context" / name, scratch_root(source.parent, name))
        for store in dict.fromkeys(stores):
            for path in store.glob("*.json"):
                record = json.loads(path.read_text(encoding="utf-8"))
                if record.get("consumer_node_id") == parsed.metadata.id and record.get("source_file_sha256") == raw.get("before_sha256"):
                    record["source_file_sha256"] = raw["after_sha256"]
                    _atomic_write_text(path, json.dumps(record, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
    receipt.unlink()


@dataclass(frozen=True)
class Relocation:
    source: Path
    destination: Path
    package: CompiledPackage
    remove: bool


def _paths(package: CompiledPackage) -> set[str]:
    return {PACKAGE_MANIFEST_PATH, *(file.path for file in package.files)}


def _owned_tree(root: Path, paths: set[str]) -> bool:
    if root.is_symlink():
        raise ContextCanonError(f"Migration refuses a symbolic-link package root: {root}")
    directories = {part.as_posix() for path in paths for part in Path(path).parents if str(part) != "."}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ContextCanonError(f"Migration refuses a symbolic link: {path}")
        rel = path.relative_to(root).as_posix()
        if path.is_file() and rel not in paths or path.is_dir() and rel not in directories:
            return False
    return True


def migration_plan(repo: Path) -> tuple[Relocation, ...]:
    rows = []
    for node in discover_nodes(repo):
        if (node / PACKAGE_MANIFEST_PATH).is_file():
            try:
                package = load_package(node)
            except ContextCanonError:
                # Broken generated output is repaired by normal build; it is
                # not an immutable package eligible for historical retention.
                package = None
            if package is not None:
                rows.append(Relocation(node, version_path(node, package), package, False))
        store = node / ".context" / "sources"
        if store.is_symlink():
            raise ContextCanonError(f"Migration refuses a symbolic-link legacy store: {store}")
        if not store.is_dir():
            continue
        for source in sorted(store.iterdir()):
            if not source.is_dir() or not re.fullmatch(r"[0-9a-f]{64}", source.name):
                continue
            package = load_package(source)
            if package.package_digest != source.name:
                raise ContextCanonError(f"Legacy directory does not match its complete package digest: {source}")
            owned = _owned_tree(source, _paths(package))
            rows.append(Relocation(source, version_path(node, package), package, owned))
    return tuple(rows)


def _remove_retired(repo: Path, receipt: Path) -> None:
    raw = json.loads(receipt.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != MIGRATION_SCHEMA:
        raise ContextCanonError(f"Invalid migration recovery receipt: {receipt}")
    original = raw.get("original")
    if not isinstance(original, str) or Path(original).is_absolute() or ".." in Path(original).parts:
        raise ContextCanonError(f"Invalid migration ownership in {receipt}")
    if receipt.stem != identity_token(original):
        raise ContextCanonError(f"Migration receipt token mismatch: {receipt}")
    trash = receipt.with_suffix("")
    if not trash.exists():
        receipt.unlink()
        return
    destination = package_location(library_root(repo), raw.get("package_key", ""))
    package = load_package(destination)
    paths = _paths(package)
    if not _owned_tree(trash, paths):
        raise ContextCanonError(f"Migration recovery found changed/unowned files: {trash}")
    hashes = {file.path: file.sha256 for file in package.files}
    hashes[PACKAGE_MANIFEST_PATH] = raw.get("manifest_sha256")
    # rmtree can be interrupted on Windows. Verify every remaining file
    # against the fully retained package before resuming that narrow deletion.
    for path in trash.rglob("*"):
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() != hashes[path.relative_to(trash).as_posix()]:
            raise ContextCanonError(f"Migration recovery found changed bytes: {path}")
    shutil.rmtree(trash)
    receipt.unlink()


def migrate_versions(path: Path, *, apply: bool = False) -> str:
    repo = find_repo_root(path.resolve())
    trash_store = repo / ".context" / "migration-trash"
    if trash_store.is_symlink():
        raise ContextCanonError(f"Migration recovery store is a symbolic link: {trash_store}")
    recovery = tuple(sorted(trash_store.glob("*.json"))) if trash_store.exists() else ()
    rows = migration_plan(repo)  # Verify all legacy inputs before mutations.
    link_changes = [(node, *_carrier_links(repo, node)) for node in discover_nodes(repo)]
    link_changes = [(node, before, after) for node, before, after in link_changes if before != after]
    lines = ["Node version migration — " + ("apply" if apply else "preview (no changes)"), ""]
    for row in rows:
        old = row.source.relative_to(repo).as_posix() or "."
        new = row.destination.relative_to(repo).as_posix()
        if row.remove:
            status = "relocate verified legacy package"
        elif row.source == repo or not (row.source.parent.name == "sources" and row.source.parent.parent.name == ".context"):
            status = "retain current publication; local outputs stay"
        else:
            status = "share exact package; keep old directory containing extra files"
        old_length = max(len(str(row.source / file.path).encode("utf-16-le")) // 2 for file in row.package.files)
        new_length = max(len(str(row.destination / file.path).encode("utf-16-le")) // 2 for file in row.package.files)
        lines.append(f"- {row.package.metadata.name} {row.package.metadata.version}: {old} -> {new} "
                     f"({status}; longest path {old_length} -> {new_length} UTF-16 units)")
    for node, _before, _after in link_changes:
        lines.append(f"- Update owned carrier links in {node.relative_to(repo)}/CONTEXT.src.md; exact pins stay unchanged.")
    if recovery:
        lines.append(f"- Resume cleanup of {len(recovery)} verified migration transaction(s).")
    if not apply:
        lines.extend(["", "Accepted pins and package bytes remain unchanged. "
                      "Onboarding Evidence/workspaces/reset journals are not migrated in Phase 1.",
                      "To apply: contextcanon versions migrate . --apply", ""])
        return "\n".join(lines)

    # Preflight every final/staged-retirement destination before changing any
    # accepted location. Package installation also checks its atomic staging.
    for row in rows:
        preflight_paths(row.destination, _paths(row.package), action="Node version migration", node_root=repo)
        if row.remove:
            token = identity_token(row.source.relative_to(repo).as_posix())
            preflight_paths(trash_store / token, _paths(row.package), action="legacy package retirement", node_root=repo)
    ensure_candidate_gitignore(repo)
    for receipt in recovery:
        raw = json.loads(receipt.read_text(encoding="utf-8"))
        if raw.get("schema") == LINK_SCHEMA:
            # If publication did not happen, ordinary planning retries it.
            source = repo / raw["source"]
            if hashlib.sha256(source.read_bytes()).hexdigest() == raw.get("before_sha256"):
                receipt.unlink()
            else:
                _rebind_link_reviews(repo, receipt)
        else:
            _remove_retired(repo, receipt)
    # Install and verify ALL shared versions before retiring any old wrapper.
    for row in rows:
        install_version(repo, row.source, row.package)
    for row in rows:
        destination = version_path(repo, row.package)
        if package_key(load_package(destination)) != package_key(row.package):
            raise ContextCanonError(f"Migrated package verification failed: {destination}")
    for node, before, after in link_changes:
        source = node / "CONTEXT.src.md"
        if source.read_bytes() != before:
            raise ContextCanonError(f"Authoring changed during migration: {source}")
        source_rel = source.relative_to(repo).as_posix()
        trash_store.mkdir(parents=True, exist_ok=True)
        receipt = trash_store / (identity_token(source_rel) + ".links.json")
        raw = {"schema": LINK_SCHEMA, "source": source_rel, "node_id": parse_node(node, repo).metadata.id,
               "before_sha256": hashlib.sha256(before).hexdigest(), "after_sha256": hashlib.sha256(after).hexdigest()}
        with receipt.open("x", encoding="utf-8") as handle:
            json.dump(raw, handle, sort_keys=True)
        _atomic_write_text(source, after.decode("utf-8"))
        _rebind_link_reviews(repo, receipt)
    for row in rows:
        if not row.remove:
            continue
        # Revalidate after staging: do not delete an input edited meanwhile.
        if package_key(load_package(row.source)) != package_key(row.package) or not _owned_tree(row.source, _paths(row.package)):
            raise ContextCanonError(f"Legacy package changed during migration: {row.source}")
        original = row.source.relative_to(repo).as_posix()
        token = identity_token(original)
        trash_store.mkdir(parents=True, exist_ok=True)
        receipt = trash_store / f"{token}.json"
        raw = {"schema": MIGRATION_SCHEMA, "original": original, "package_key": package_key(row.package),
               "manifest_sha256": hashlib.sha256((row.source / PACKAGE_MANIFEST_PATH).read_bytes()).hexdigest()}
        with receipt.open("x", encoding="utf-8") as handle:
            json.dump(raw, handle, sort_keys=True)
        trash = trash_store / token
        if trash.exists():
            raise ContextCanonError(f"Unowned migration retirement destination: {trash}")
        os.replace(row.source, trash)
        _remove_retired(repo, receipt)
        try:
            row.source.parent.rmdir()
        except OSError:
            pass
    store = library_root(repo)
    if store.exists():
        (store / "README.md").write_text(render_inventory(repo, relative_to=store), encoding="utf-8")
    try:
        trash_store.rmdir()
    except OSError:
        pass
    lines.extend(["", "Verified versions are shared. Exact accepted pins are unchanged; only owned carrier locators may be moved.",
                  "Next: contextcanon build --all .", "Then: contextcanon check --all .", ""])
    return "\n".join(lines)
