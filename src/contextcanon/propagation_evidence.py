"""Human-readable, read-only evidence for guided Parent propagation.

The immutable package and ContextDiff remain the authority. This module only
renders labels and verified old/new Resource bytes already available locally.
"""
from __future__ import annotations

import difflib
import hashlib
from itertools import islice
from pathlib import Path

from .diff import ContextDiff, DiffEntry
from .model import CompiledPackage

_MAX_TEXT_BYTES = 128_000
_MAX_DIFF_LINES = 40


def _resource_details(package: CompiledPackage, path: str | None, identity: str):
    origin = next((item for item in package.resource_origins if item.path == path), None)
    node_id, _, resource_id = identity.partition("#")
    uses = []
    for topic in package.topics:
        if topic.origin_node_id != node_id:
            continue
        for target in topic.targets:
            if target.kind == "resource" and (
                (resource_id and target.resource_id == resource_id)
                or (not resource_id and target.locator == identity)
            ):
                uses.append((topic.origin_node_name, topic.title))
    return origin, sorted(set(uses))


def _existing_bytes(path: Path, expected_sha: str | None):
    if not expected_sha:
        return None, "no immutable content fingerprint available"
    if path.is_symlink() or not path.is_file():
        return None, "snapshot file is missing or is a symbolic link"
    try:
        data = path.read_bytes()
    except OSError as exc:
        return None, f"cannot read immutable snapshot: {exc}"
    if hashlib.sha256(data).hexdigest() != expected_sha:
        return None, "snapshot bytes differ from the reviewed fingerprint"
    return data, None


def _diff_lines(old: bytes | None, new: bytes | None, old_name: str, new_name: str):
    if old is None or new is None:
        return ["Exact content comparison unavailable; inspect the indicated snapshots."]
    if old == new:
        return ["Document bytes are identical; only the location or package metadata changed."]
    if len(old) > _MAX_TEXT_BYTES or len(new) > _MAX_TEXT_BYTES:
        return ["File too large for inline diff; inspect the two paths below."]
    if b"\x00" in old or b"\x00" in new:
        return ["Binary content changed; a text diff is not applicable."]
    try:
        old_text = old.decode("utf-8")
        new_text = new.decode("utf-8")
    except UnicodeDecodeError:
        return ["Non-UTF-8 content changed; a text diff is not applicable."]
    delta = list(islice(difflib.unified_diff(
        old_text.splitlines(), new_text.splitlines(),
        fromfile=old_name, tofile=new_name, lineterm="",
    ), _MAX_DIFF_LINES + 1))
    truncated = len(delta) > _MAX_DIFF_LINES
    return [
        *delta[:_MAX_DIFF_LINES],
        *(["... diff truncated; inspect the complete old/new files below."] if truncated else []),
    ]


def render_resource_evidence(
    diff: ContextDiff,
    old_package: CompiledPackage,
    new_package: CompiledPackage,
    old_package_root: Path,
    new_resource_bytes: dict[str, bytes],
    repo_root: Path,
    first_seen: dict[tuple[str, str, str, str], int],
    review_number: int,
) -> str:
    """Show exact Resource identity by human name and old/new file evidence.

    `first_seen` is ephemeral presentation state for one propagation command;
    it does not alter receipts, versions, or accepted Parent pins.
    """
    resources = [entry for entry in diff.entries if entry.category == "resource"]
    if not resources:
        return ""

    lines = ["Changed document evidence (before approving this Child):"]
    for entry in resources:
        old_info, new_info = entry.before or {}, entry.after or {}
        old_path, new_path = old_info.get("path"), new_info.get("path")
        old_origin, old_uses = _resource_details(old_package, old_path, entry.identity)
        new_origin, new_uses = _resource_details(new_package, new_path, entry.identity)
        origin = new_origin or old_origin
        uses = new_uses or old_uses
        repo_path = origin.repo_path if origin else None
        label = repo_path or new_path or old_path or "(original document path unavailable)"
        from_node, topic = uses[0] if uses else (None, None)
        origin_name = from_node or (f"Node {origin.node_id}" if origin else "origin not recorded")
        lines.append(f"  Document: {label}")
        lines.append(f"  Origin: {origin_name}" + (f" · Topic: {topic}" if topic else ""))
        lines.append(f"  Change: {entry.change}" + (
            f" (stored path: {old_path} -> {new_path})" if old_path and new_path and old_path != new_path else
            " (document bytes or metadata)" if entry.change == "modified" else ""
        ))
        fingerprint = (entry.identity, entry.change, old_info.get("sha256", ""), new_info.get("sha256", ""))
        earlier = first_seen.setdefault(fingerprint, review_number)
        if earlier != review_number:
            lines.append(
                f"  Same upstream Resource change as review {earlier}; "
                "this is inherited again, not another edit made in this Child."
            )
        else:
            old_file = old_package_root / old_path if old_path else None
            old_data, old_error = (
                _existing_bytes(old_file, old_info.get("sha256")) if old_file else (None, "not in old package")
            )
            new_data = new_resource_bytes.get(new_path) if new_path else None
            if new_data is not None and hashlib.sha256(new_data).hexdigest() != new_info.get("sha256"):
                new_data = None
                lines.append("  New Resource bytes differ from the reviewed candidate; no diff shown.")
            lines.extend(
                "    " + row for row in (
                    [f"Old bytes unavailable: {old_error}"] if old_error else
                    _diff_lines(old_data, new_data, "accepted Parent", "new Parent")
                )
            )

        if old_path:
            old_file = old_package_root / old_path
            try:
                old_location = old_file.relative_to(repo_root).as_posix()
            except ValueError:
                old_location = str(old_file)
            lines.append(f"  Old accepted snapshot: {old_location}")
        if repo_path and new_path:
            lines.append(f"  New authored source: {repo_path} (compare with old accepted snapshot)")
        elif new_path:
            lines.append(f"  New package file: {new_path} (authored origin path unavailable)")
        if old_info.get("sha256") != new_info.get("sha256"):
            lines.append("  Evidence: Resource content fingerprint changed.")
        elif old_path != new_path:
            lines.append("  Evidence: Resource location changed; content fingerprint unchanged.")
        else:
            lines.append("  Evidence: package Resource metadata changed.")

    lines.append("  Each Child still requires its own explicit Parent acceptance; no policy changed.")
    return "\n".join(lines)
