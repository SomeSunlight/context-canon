from __future__ import annotations

import re
import shutil
import warnings
from pathlib import Path

from .model import CompiledPackage
from .package import load_package
from .parser import ContextCanonError
from .version_store import package_key, scratch_root, store_package


STORES = ("candidates", "parent-candidates")
TOKEN_LENGTHS = (16, 24, 32, 40, 48, 56, 64)


def _digest(digest: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ContextCanonError(f"Invalid candidate package digest: {digest!r}")


def candidate_path(node_root: Path, store_name: str, digest: str, *, node_id: str | None = None,
                   normalized_digest: str | None = None) -> Path:
    """Read both old local scratch and new isolated working-tree scratch."""
    _digest(digest)
    if store_name not in STORES:
        raise ValueError(f"Not a candidate store: {store_name}")
    matches = []
    legacy = node_root / ".context" / store_name
    central = scratch_root(node_root, store_name)
    for store in dict.fromkeys((legacy, central)):
        if not store.is_dir():
            continue
        for path in sorted(store.iterdir()):
            if not path.is_dir() or not (path / ".context/package.json").is_file():
                continue
            package = load_package(path)
            if package.package_digest != digest:
                continue
            if node_id is not None and package.metadata.id != node_id:
                continue
            if normalized_digest is not None and package.normalized_digest != normalized_digest:
                continue
            if store == central and not package_key(package).startswith(path.name):
                raise ContextCanonError(f"Candidate token does not match its full identity: {path}")
            matches.append(path)
    if len(matches) > 1 and len({package_key(load_package(path)) for path in matches}) > 1:
        raise ContextCanonError(f"Ambiguous candidate bytes {digest}; select complete Node identity")
    return matches[0] if matches else central / digest[:16]


def store_candidate(node_root: Path, store_name: str, package: CompiledPackage,
                    files: dict[str, bytes]) -> Path:
    if store_name not in STORES:
        raise ValueError(f"Not a candidate store: {store_name}")
    store = scratch_root(node_root, store_name, create=True)
    return store_package(store, package, files, action=f"{store_name} candidate publication",
                         node_root=node_root, lengths=TOKEN_LENGTHS)


def cleanup_accepted_candidate(
    node_root: Path,
    candidate_root: Path,
    digest: str,
    receipt_path: Path,
    provenance_path: Path | None = None,
) -> None:
    """Called only after durable package installation and atomic pin publication.

    Explicit user-supplied packages and accepted sources are never removed.
    Cleanup failure must not turn a completed acceptance into a failed one.
    """
    _digest(digest)
    node_root = node_root.resolve()
    candidate_root = candidate_root.resolve()
    managed = any(
        candidate_root.parent in (node_root / ".context" / name, scratch_root(node_root, name))
        for name in STORES
    ) and len(candidate_root.name) in TOKEN_LENGTHS
    try:
        if managed and candidate_root.exists():
            if load_package(candidate_root).package_digest != digest:
                raise ContextCanonError(f"Refusing cleanup of a different candidate: {candidate_root}")
            shutil.rmtree(candidate_root)
            if provenance_path is not None:
                provenance_path.unlink(missing_ok=True)
        receipt_path.unlink(missing_ok=True)
    except (OSError, ContextCanonError) as exc:
        warnings.warn(f"Package accepted, but candidate scratch cleanup needs a retry: {exc}", RuntimeWarning)
