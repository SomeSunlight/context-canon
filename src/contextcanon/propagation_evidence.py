"""Human-readable, read-only evidence for guided Parent propagation.

The immutable package and ContextDiff remain the authority. This module only
renders labels and verified old/new Resource bytes already available locally.
"""
from __future__ import annotations

import difflib
import hashlib
from itertools import islice
from pathlib import Path

from .diff import ContextDiff
from .model import CompiledPackage

_MAX_TEXT_BYTES = 128_000
_MAX_DIFF_LINES = 40
_COMPACT_DIFF_LINES = 18


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


def _diff_lines(old: bytes | None, new: bytes | None, old_name: str, new_name: str, *, max_lines: int):
    if old is None or new is None:
        return ["Exact content comparison unavailable; inspect the indicated snapshots."]
    if old == new:
        return ["Document bytes are identical; only the location or package metadata changed."]
    if len(old) > _MAX_TEXT_BYTES or len(new) > _MAX_TEXT_BYTES:
        return ["File too large for inline diff; press d to inspect source/snapshot paths."]
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
    ), max_lines + 1))
    truncated = len(delta) > max_lines
    return [
        *delta[:max_lines],
        *(["... diff shortened; press d for more lines and exact paths."] if truncated else []),
    ]


def describe_resource_effect(
    parent_diff: ContextDiff,
    child_diff: ContextDiff,
    old_package: CompiledPackage,
    new_package: CompiledPackage,
) -> str | None:
    """Explain one unchanged-through-inheritance Resource effect in plain language.

    Never claim that a particular document changed this Child unless its
    Resource identity, action and fingerprints match the effective Child diff.
    """
    parent_resources = [entry for entry in parent_diff.entries if entry.category == "resource"]
    child_resources = [entry for entry in child_diff.entries if entry.category == "resource"]
    if len(parent_resources) != 1 or len(child_resources) != 1:
        return None
    parent_entry, child_entry = parent_resources[0], child_resources[0]
    if any(entry.category in {"rule", "topic", "change"} for entry in child_diff.entries):
        return None
    if any(entry.category in {"rule", "topic", "change"} for entry in parent_diff.entries):
        return None
    if (
        parent_entry.identity != child_entry.identity
        or parent_entry.change != child_entry.change
        or (parent_entry.before or {}).get("sha256") != (child_entry.before or {}).get("sha256")
        or (parent_entry.after or {}).get("sha256") != (child_entry.after or {}).get("sha256")
    ):
        return None

    old_info = parent_entry.before or {}
    new_info = parent_entry.after or {}
    fallback = (
        parent_entry.identity if "#" not in parent_entry.identity
        and parent_entry.identity.startswith("CONTEXT/") else None
    )
    old_path = old_info.get("path") or (fallback if parent_entry.before else None)
    new_path = new_info.get("path") or (fallback if parent_entry.after else None)
    old_origin, _ = _resource_details(old_package, old_path, parent_entry.identity)
    new_origin, _ = _resource_details(new_package, new_path, parent_entry.identity)
    origin = new_origin or old_origin
    name = origin.repo_path if origin else (new_path or old_path)
    if not name:
        return None

    if parent_entry.change == "modified":
        action = (
            "use the updated document" if old_info.get("sha256") != new_info.get("sha256")
            else "use the updated document metadata for"
        )
    elif parent_entry.change == "added":
        action = "gain the new document"
    elif parent_entry.change == "removed":
        action = "no longer inherit the document"
    elif parent_entry.change == "moved":
        action = "use the moved document"
    else:
        return None
    return f'{action} "{name}"'


def render_resource_evidence(
    diff: ContextDiff,
    old_package: CompiledPackage,
    new_package: CompiledPackage,
    old_package_root: Path,
    new_resource_bytes: dict[str, bytes],
    repo_root: Path,
    first_seen: dict[tuple[str, str, str, str], int],
    review_number: int,
    *,
    verbose: bool = False,
) -> str:
    """Show exact Resource identity by human name and old/new file evidence.

    `first_seen` is ephemeral presentation state for one propagation command;
    it does not alter receipts, versions, or accepted Parent pins.
    """
    resources = [entry for entry in diff.entries if entry.category == "resource"]
    if not resources:
        return ""

    lines = ["Changed Resources:"]
    for entry in resources:
        old_info, new_info = entry.before or {}, entry.after or {}
        # Older path-identified Resources store the path as identity rather than
        # under the "path" key; preserve readable evidence for those packages.
        fallback = entry.identity if "#" not in entry.identity and entry.identity.startswith("CONTEXT/") else None
        old_path = old_info.get("path") or (fallback if entry.before else None)
        new_path = new_info.get("path") or (fallback if entry.after else None)
        old_origin, old_uses = _resource_details(old_package, old_path, entry.identity)
        new_origin, new_uses = _resource_details(new_package, new_path, entry.identity)
        origin = new_origin or old_origin
        uses = new_uses or old_uses
        repo_path = origin.repo_path if origin else None
        label = repo_path or new_path or old_path or "(original document path unavailable)"
        from_node, topic = uses[0] if uses else (None, None)
        origin_name = from_node or (f"Node {origin.node_id}" if origin else "origin not recorded")
        if entry.change == "moved":
            kind = "moved (same content)" if old_info.get("sha256") == new_info.get("sha256") else "moved and edited"
        elif entry.change == "modified":
            kind = "content changed" if old_info.get("sha256") != new_info.get("sha256") else "metadata changed"
        elif entry.change == "added":
            kind = "added"
        else:
            kind = "removed"
        lines.append(f"  {label} — {kind}")
        lines.append("    " + (
            f"Topic: {topic} · Origin: {origin_name}" if topic else f"Origin: {origin_name}"
        ))
        if old_path and new_path and old_path != new_path:
            old_source = old_origin.repo_path if old_origin else old_path
            lines.append(f"    Moved from: {old_source}")
        fingerprint = (entry.identity, entry.change, old_info.get("sha256", ""), new_info.get("sha256", ""))
        earlier = first_seen.setdefault(fingerprint, review_number)
        if earlier != review_number:
            lines.append(
                f"    Same upstream change as review {earlier}; "
                "this Child did not edit the document."
            )
        if earlier == review_number or verbose:
            old_file = old_package_root / old_path if old_path else None
            old_data, old_error = (
                _existing_bytes(old_file, old_info.get("sha256")) if old_file else (None, "not in old package")
            )
            new_data = new_resource_bytes.get(new_path) if new_path else None
            if new_data is not None and hashlib.sha256(new_data).hexdigest() != new_info.get("sha256"):
                new_data = None
                lines.append("    New Resource bytes differ from the reviewed candidate; no diff shown.")
            lines.extend(
                "    " + row for row in (
                    [f"Old bytes unavailable: {old_error}"] if old_error else
                    _diff_lines(
                        old_data, new_data, "accepted Parent", "new Parent",
                        max_lines=_MAX_DIFF_LINES if verbose else _COMPACT_DIFF_LINES,
                    )
                )
            )

        if not verbose:
            continue

        if old_path:
            old_file = old_package_root / old_path
            try:
                old_location = old_file.relative_to(repo_root).as_posix()
            except ValueError:
                old_location = str(old_file)
            lines.append(f"  Old accepted snapshot: {old_location}")
        if repo_path and new_path:
            authored = repo_root / repo_path
            try:
                locally_verified = (
                    authored.is_file()
                    and not authored.is_symlink()
                    and hashlib.sha256(authored.read_bytes()).hexdigest() == new_info.get("sha256")
                )
            except OSError:
                locally_verified = False
            if locally_verified:
                lines.append(f"  New authored source: {repo_path} (verified in this checkout)")
            else:
                lines.append(
                    f"  Authored origin recorded in package: {repo_path} "
                    "(not verified as the new bytes in this checkout; may be external)"
                )
                lines.append(f"  New candidate package locator: {new_path}")
        elif new_path:
            lines.append(f"  New candidate package locator: {new_path} (authored origin path unavailable)")
        if old_info.get("sha256") != new_info.get("sha256"):
            lines.append("  Evidence: Resource content fingerprint changed.")
        elif old_path != new_path:
            lines.append("  Evidence: Resource location changed; content fingerprint unchanged.")
        else:
            lines.append("  Evidence: package Resource metadata changed.")

    if verbose:
        lines.append("  These paths and fingerprints document the exact immutable comparison.")
    return "\n".join(lines)
