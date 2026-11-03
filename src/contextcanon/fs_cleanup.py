"""Best-effort cleanup of tool-owned directory skeletons.

Removing empty directories is not an integrity operation. On Windows an
antivirus/indexer may temporarily hold a directory open after its files have
been removed. Never delete files here, never traverse reparse points, and
never treat nonempty broken packages as disposable.
"""
from __future__ import annotations

import errno
import stat
import time
from pathlib import Path


RETRY_DELAYS = (0.0, 0.05, 0.15, 0.35)


def _real_directory(path: Path) -> bool:
    """Reject symlinks and Windows junctions/reparse points."""
    try:
        metadata = path.lstat()
    except OSError:
        return False
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(metadata, "st_file_attributes", 0)
    return stat.S_ISDIR(metadata.st_mode) and not (attributes & reparse)


def is_fileless_directory(path: Path) -> bool:
    """True only for a real directory containing recursively *only* real dirs.

    A regular file, symlink, junction, or unreadable entry is NOT an orphaned
    skeleton. This predicate is read-only and must not be used for file cleanup.
    """
    if not _real_directory(path):
        return False
    pending = [path]
    while pending:
        current = pending.pop()
        try:
            entries = tuple(current.iterdir())
        except OSError:
            return False
        for entry in entries:
            if not _real_directory(entry):
                return False
            pending.append(entry)
    return True


def remove_empty_directory(path: Path, *, delays=RETRY_DELAYS) -> bool:
    """Attempt rmdir with bounded retry; never delete content or follow links.

    False means the directory still exists or is not eligible. On the next
    build its removal will be retried. Avoid retrying ENOTEMPTY: it is data,
    not a transient Windows lock.
    """
    attempts = tuple(delays)
    if not attempts:
        raise ValueError("at least one attempt is required")
    for index, delay in enumerate(attempts):
        if index and delay:
            time.sleep(delay)
        if not _real_directory(path):
            return not path.exists() and not path.is_symlink()
        try:
            path.rmdir()
            return True
        except OSError as exc:
            if exc.errno in (errno.ENOTEMPTY, errno.EEXIST):
                return False
    return False


def prune_empty_owned_directories(owned_root: Path) -> None:
    """Best-effort prune under an explicit ContextCanon-owned root.

    The root itself is retained. All removals are rmdir, so any directory
    containing files survives. Traversal never enters symbolic links or
    junctions, and failure to clean up cannot block publication.
    """
    if not _real_directory(owned_root):
        return
    stack = [owned_root]
    descendants: list[Path] = []
    while stack:
        directory = stack.pop()
        try:
            children = tuple(directory.iterdir())
        except OSError:
            continue
        for child in children:
            if _real_directory(child):
                descendants.append(child)
                stack.append(child)
    for directory in sorted(descendants, key=lambda p: (len(p.parts), str(p)), reverse=True):
        remove_empty_directory(directory)


def prune_context_directories(repo_root: Path, node_roots: list[Path]) -> None:
    """A build can opportunistically repair leftovers across the repository."""
    roots = {repo_root / ".context"}
    for node in node_roots:
        roots.add(node / ".context")
        roots.add(node / "CONTEXT")
    for root in sorted(roots, key=str):
        prune_empty_owned_directories(root)
