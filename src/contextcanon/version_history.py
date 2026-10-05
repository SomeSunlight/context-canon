"""Published package retention and a regenerable, human-readable inventory."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .compiler import discover_nodes
from .links import markdown_link_target
from .model import CompiledNode, CompiledPackage
from .outputs import expected_outputs, write_outputs
from .package import PACKAGE_MANIFEST_PATH, artifact_files, compiled_package, load_package
from .parser import ContextCanonError, find_repo_root, parse_node
from .path_budget import preflight_paths
from .version_store import accepted_package_path, install_version, library_root, package_key, store_package


@dataclass(frozen=True)
class VersionEntry:
    path: Path
    package: CompiledPackage
    used_by: tuple[str, ...]


def version_inventory(repo_root: Path) -> tuple[VersionEntry, ...]:
    repo_root = find_repo_root(repo_root.resolve())
    store = library_root(repo_root)
    packages = []
    if store.is_dir():
        for path in sorted(store.iterdir()):
            if not path.is_dir() or path.name.startswith(".tmp-"):
                continue
            if path.is_symlink():
                raise ContextCanonError(f"Version library entry is a symbolic link: {path}")
            package = load_package(path)
            if not package_key(package).startswith(path.name):
                raise ContextCanonError(f"Version token does not match complete identity: {path}")
            packages.append((path, package))
    users: dict[str, list[str]] = {}
    for root in discover_nodes(repo_root):
        try:
            parsed = parse_node(root, repo_root)
        except ContextCanonError:
            # A local Node build must not fail after publication merely because
            # an unrelated sibling has unfinished authoring. check --all owns
            # that diagnostic; this inventory never authorizes history pruning.
            continue
        label = root.relative_to(repo_root).as_posix() or "."
        for ref in (*parsed.parents, *parsed.sources):
            if ref.is_pinned:
                relation = getattr(ref, "relationship", "parent").title()
                users.setdefault(package_key(ref), []).append(f"{label} [{relation}]")
        if (root / PACKAGE_MANIFEST_PATH).is_file():
            try:
                current = load_package(root)
            except ContextCanonError:
                # Drift/corruption is diagnosed by check. It is not a valid
                # current publication binding and never enters the library.
                continue
            users.setdefault(package_key(current), []).append(f"{label} [current publication]")
            for ref in (*current.parents, *current.sources):
                relation = (ref.relationship or "parent").title()
                users.setdefault(package_key(ref), []).append(f"{label} [published {relation}]")
    entries = [VersionEntry(path, package, tuple(sorted(set(users.get(package_key(package), [])))))
               for path, package in packages]
    return tuple(sorted(entries, key=lambda entry: (entry.package.metadata.name.casefold(),
                                                   entry.package.metadata.id, entry.package.metadata.version,
                                                   package_key(entry.package))))


def render_inventory(repo_root: Path, *, relative_to: Path | None = None) -> str:
    base = relative_to or repo_root
    lines = ["# Node versions", "", "> GENERATED INVENTORY — DO NOT EDIT.", "",
             "Complete immutable Node packages retained in this Git working tree. "
             "Current imports stay pinned until separately reviewed acceptance.", "",
             "| Node | Node ID | Version | Used by | Package |", "| --- | --- | --- | --- | --- |"]
    for entry in version_inventory(repo_root):
        rel = os.path.relpath(entry.path / "CONTEXT.md", base).replace(os.sep, "/")
        name = entry.package.metadata.name.replace("|", "\\|")
        users = "; ".join(entry.used_by).replace("|", "\\|") or "retained history"
        node_id = entry.package.metadata.id.replace("|", "\\|")
        lines.append(f"| {name} | {node_id} | {entry.package.metadata.version} | {users} | [inspect]({markdown_link_target(rel)}) |")
    lines.extend(["", "Full Node identity, semantic digest and exact package digest live in each "
                  "verified package manifest. Directory names are compact locators.", "",
                  "Incomplete authoring is diagnosed by check --all and omitted from this consumer inventory. "
                  "Retained history may still support reviews or onboarding recovery. "
                  "This view is not permission to delete an apparently unused version.", ""])
    return "\n".join(lines)


def publish_outputs(compiled: CompiledNode) -> list[str]:
    """Normal build keeps verified previous/current packages before replacement.

    Onboarding still uses write_outputs directly until its separate Phase 2.
    Retention never fetches and never changes accepted consumer pins.
    """
    root = compiled.parsed.root
    preflight_paths(root, expected_outputs(compiled), action="Official Context output publication")
    if (root / PACKAGE_MANIFEST_PATH).is_file():
        try:
            previous = load_package(root)
        except ContextCanonError:
            previous = None
        if previous is not None:
            install_version(root, root, previous)
    # Old accepted inputs remain readable, but publication gives its new
    # carrier links real shared targets even before explicit legacy cleanup.
    for ref, imported in [*zip(compiled.parsed.parents, compiled.parent_packages),
                          *zip(compiled.parsed.sources, compiled.source_packages)]:
        if ref.is_pinned:
            install_version(root, accepted_package_path(root, ref), imported)
    package = compiled_package(compiled)
    store_package(library_root(root), package, artifact_files(compiled),
                  action="published Node version retention", node_root=root)
    changed = write_outputs(compiled)
    store = library_root(root)
    inventory = store / "README.md"
    content = render_inventory(find_repo_root(root), relative_to=store)
    if not inventory.exists() or inventory.read_text(encoding="utf-8") != content:
        inventory.write_text(content, encoding="utf-8")
    return changed
