from __future__ import annotations

import os
import re
import shutil
import tempfile
import warnings
from pathlib import Path

from .model import CompiledPackage
from .package import load_package
from .parser import ContextCanonError
from .path_budget import preflight_paths


STORES = ("candidates", "parent-candidates")
TOKEN_LENGTHS = (16, 24, 32, 40, 48, 56, 64)


def _digest(digest: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ContextCanonError(f"Invalid candidate package digest: {digest!r}")


def candidate_path(node_root: Path, store_name: str, digest: str) -> Path:
    """Find exact existing bytes, or the first free collision-safe prefix.

    Full digests remain authoritative. Historical full-digest directories are
    still read; a prefix collision never reuses or overwrites another package.
    """
    _digest(digest)
    if store_name not in STORES:
        raise ValueError(f"Not a candidate store: {store_name}")
    store = node_root / ".context" / store_name
    legacy = store / digest
    if legacy.exists():
        if load_package(legacy).package_digest != digest:
            raise ContextCanonError(f"Candidate full-digest path contains different content: {legacy}")
        return legacy
    first_free = None
    for size in TOKEN_LENGTHS:
        path = store / digest[:size]
        if not path.exists():
            if first_free is None:
                first_free = path
            continue
        existing = load_package(path)
        if existing.package_digest == digest:
            return path
        if not existing.package_digest.startswith(path.name):
            raise ContextCanonError(f"Candidate token does not match its full package digest: {path}")
    if first_free is None:
        raise ContextCanonError(f"No free candidate path for {digest}")
    return first_free


def store_candidate(
    node_root: Path,
    store_name: str,
    package: CompiledPackage,
    files: dict[str, bytes],
) -> Path:
    destination = candidate_path(node_root, store_name, package.package_digest)
    if destination.exists():
        return destination
    action = f"{store_name} candidate materialization"
    preflight_paths(destination, files, action=action, node_root=node_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # A short random sibling also leaves room for atomic staging.
    staging = Path(tempfile.mkdtemp(prefix=".tmp-", dir=destination.parent))
    try:
        preflight_paths(staging, files, action=f"{action} (staging)", node_root=node_root)
        for relative, content in files.items():
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        staged = load_package(staging)
        if (
            staged.metadata.id != package.metadata.id
            or staged.normalized_digest != package.normalized_digest
            or staged.package_digest != package.package_digest
        ):
            raise ContextCanonError("Candidate identity changed while staging")
        # Never replace an occupied token, including one published concurrently.
        if destination.exists():
            if load_package(destination).package_digest != package.package_digest:
                raise ContextCanonError(f"Candidate token became occupied; retry: {destination}")
        else:
            os.rename(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination


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
        candidate_root.parent == node_root / ".context" / name
        for name in STORES
    ) and len(candidate_root.name) in TOKEN_LENGTHS and digest.startswith(candidate_root.name)
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
