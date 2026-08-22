from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .diff import ContextDiff, DiffEntry
from .model import CompiledPackage
from .parser import ContextCanonError

_CATEGORY_ORDER = {
    "node": 0,
    "source": 1,
    "change": 2,
    "rule": 3,
    "topic": 4,
    "resource": 5,
}


def diff_packages(before: CompiledPackage, after: CompiledPackage) -> ContextDiff:
    """Compare two immutable versions of the same stable Context Node."""

    if before.metadata.id != after.metadata.id:
        raise ContextCanonError(
            "Cannot diff different Context Nodes: "
            f"{before.metadata.name} ({before.metadata.id}) != "
            f"{after.metadata.name} ({after.metadata.id})"
        )

    entries: list[DiffEntry] = []
    entries.extend(_diff_maps("node", _node_snapshot(before), _node_snapshot(after)))
    entries.extend(_diff_maps("source", _source_snapshot(before), _source_snapshot(after)))
    entries.extend(_diff_maps("change", _change_snapshot(before), _change_snapshot(after)))
    entries.extend(_diff_maps("rule", _rule_snapshot(before), _rule_snapshot(after)))
    entries.extend(_diff_maps("topic", _topic_snapshot(before), _topic_snapshot(after)))
    entries.extend(_diff_maps("resource", _resource_snapshot(before), _resource_snapshot(after)))
    entries.sort(key=lambda entry: (_CATEGORY_ORDER[entry.category], entry.identity, entry.change))

    return ContextDiff(
        node_id=before.metadata.id,
        before_name=before.metadata.name,
        after_name=after.metadata.name,
        before_version=before.metadata.version,
        after_version=after.metadata.version,
        before_normalized_digest=before.normalized_digest,
        after_normalized_digest=after.normalized_digest,
        before_package_digest=before.package_digest,
        after_package_digest=after.package_digest,
        entries=tuple(entries),
    )


def _diff_maps(
    category: str,
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> list[DiffEntry]:
    result: list[DiffEntry] = []
    for identity in sorted(set(before) | set(after)):
        old = before.get(identity)
        new = after.get(identity)
        if old is None:
            result.append(DiffEntry(category, "added", identity, None, new))
        elif new is None:
            result.append(DiffEntry(category, "removed", identity, old, None))
        elif old != new:
            changed_fields = tuple(
                sorted(key for key in set(old) | set(new) if old.get(key) != new.get(key))
            )
            result.append(DiffEntry(category, "modified", identity, old, new, changed_fields))
    return result


def _node_snapshot(package: CompiledPackage) -> dict[str, dict[str, Any]]:
    return {
        package.metadata.id: {
            "name": package.metadata.name,
            "version": package.metadata.version,
        }
    }


def _source_snapshot(package: CompiledPackage) -> dict[str, dict[str, Any]]:
    return {
        source.id: {
            "version": source.version,
            "normalized_digest": source.normalized_digest,
            "package_digest": source.package_digest,
        }
        for source in package.sources
    }


def _change_snapshot(package: CompiledPackage) -> dict[str, dict[str, Any]]:
    return {
        f"{change.target_node_id}#{change.target_rule_id}": {
            "kind": change.kind,
            "target_node_name": change.target_node_name,
            "statement": change.statement,
            "why": change.why,
        }
        for change in package.changes
    }


def _rule_snapshot(package: CompiledPackage) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for rule in package.rules:
        identity = f"{rule.origin_node_id}#{rule.id}"
        result[identity] = {"status": "active", **asdict(rule)}

    removals: dict[str, list[dict[str, Any]]] = {}
    origin_names: dict[str, str] = {}
    for removal in package.removed_rules:
        identity = f"{removal.origin_node_id}#{removal.rule_id}"
        origin_names[identity] = removal.origin_node_name
        removals.setdefault(identity, []).append(
            {
                "removed_by_node_id": removal.removed_by_node_id,
                "removed_by_node_name": removal.removed_by_node_name,
                "why": removal.why,
            }
        )
    for identity, provenance in removals.items():
        provenance.sort(
            key=lambda item: (
                item["removed_by_node_id"],
                item["removed_by_node_name"],
                item["why"],
            )
        )
        result[identity] = {
            "status": "removed",
            "origin_node_name": origin_names[identity],
            "removals": provenance,
        }
    return result


def _topic_snapshot(package: CompiledPackage) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for topic in package.topics:
        item = asdict(topic)
        item["targets"] = sorted(
            item["targets"],
            key=lambda target: (target["intent"], target["kind"], target["locator"]),
        )
        result[f"{topic.origin_node_id}#{topic.id}"] = item
    return result


def _resource_snapshot(package: CompiledPackage) -> dict[str, dict[str, Any]]:
    return {
        file.path: {
            "sha256": file.sha256,
            "size": file.size,
        }
        for file in package.files
        if file.path.startswith("CONTEXT/")
    }
