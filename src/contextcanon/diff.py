from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

from .model import CompiledNode
from .parser import ContextCanonError

DiffChange = Literal["added", "removed", "modified"]

_CATEGORY_ORDER = {
    "node": 0,
    "parent": 1,
    "source": 2,
    "change": 3,
    "rule": 4,
    "topic": 5,
    "resource": 6,
}


@dataclass(frozen=True)
class DiffEntry:
    category: str
    change: DiffChange
    identity: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    changed_fields: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "change": self.change,
            "identity": self.identity,
            "before": self.before,
            "after": self.after,
            "changed_fields": list(self.changed_fields),
        }


@dataclass(frozen=True)
class ContextDiff:
    node_id: str
    before_name: str
    after_name: str
    before_version: str
    after_version: str
    before_normalized_digest: str
    after_normalized_digest: str
    before_package_digest: str
    after_package_digest: str
    entries: tuple[DiffEntry, ...]

    @property
    def is_empty(self) -> bool:
        return (
            not self.entries
            and self.before_normalized_digest == self.after_normalized_digest
            and self.before_package_digest == self.after_package_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "contextcanon/diff/v0",
            "node_id": self.node_id,
            "before": {
                "name": self.before_name,
                "version": self.before_version,
                "normalized_digest": self.before_normalized_digest,
                "package_digest": self.before_package_digest,
            },
            "after": {
                "name": self.after_name,
                "version": self.after_version,
                "normalized_digest": self.after_normalized_digest,
                "package_digest": self.after_package_digest,
            },
            "changed": not self.is_empty,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def diff_compiled(before: CompiledNode, after: CompiledNode) -> ContextDiff:
    if before.metadata.id != after.metadata.id:
        raise ContextCanonError(
            "Cannot diff different Context Nodes: "
            f"{before.metadata.name} ({before.metadata.id}) != "
            f"{after.metadata.name} ({after.metadata.id})"
        )

    entries: list[DiffEntry] = []
    entries.extend(_diff_maps("node", _node_snapshot(before), _node_snapshot(after)))
    entries.extend(_diff_maps("parent", _parent_snapshot(before), _parent_snapshot(after)))
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


_CATEGORY_NOUNS = {
    "node": ("node metadata item", "node metadata items"),
    "parent": ("parent", "parents"),
    "source": ("source", "sources"),
    "change": ("local change", "local changes"),
    "rule": ("rule", "rules"),
    "topic": ("topic", "topics"),
    "resource": ("resource", "resources"),
}


def _transition(before: str, after: str) -> str:
    return f"unchanged ({before})" if before == after else f"{before} -> {after}"


def _summary_parts(diff: ContextDiff) -> list[str]:
    counts: dict[tuple[str, DiffChange], int] = {}
    for entry in diff.entries:
        key = (entry.category, entry.change)
        counts[key] = counts.get(key, 0) + 1

    action = {"added": "added", "removed": "removed", "modified": "changed"}
    parts: list[str] = []
    for category in sorted(_CATEGORY_ORDER, key=_CATEGORY_ORDER.get):
        singular, plural = _CATEGORY_NOUNS[category]
        for change in ("added", "removed", "modified"):
            count = counts.get((category, change), 0)
            if count:
                noun = singular if count == 1 else plural
                parts.append(f"{count} {noun} {action[change]}")
    return parts


def render_diff(diff: ContextDiff, *, include_technical: bool = True) -> str:
    summary = ", ".join(_summary_parts(diff))
    if not summary:
        summary = (
            "package presentation changed; semantic and Resource content unchanged"
            if not diff.is_empty
            else "no compiled context changes"
        )

    lines = [
        f"ContextCanon diff: {diff.before_name} ({diff.node_id})",
        f"  Version: {_transition(diff.before_version, diff.after_version)}",
        f"  Summary: {summary}",
    ]

    if diff.entries:
        current_category = None
        symbol = {"added": "+", "removed": "-", "modified": "~"}
        for entry in diff.entries:
            if entry.category != current_category:
                current_category = entry.category
                lines.extend(["", current_category.title() + "s:"])
            detail = ""
            if entry.change == "modified" and entry.changed_fields:
                detail = " [" + ", ".join(entry.changed_fields) + "]"
            lines.append(f"  {symbol[entry.change]} {entry.identity}{detail}")
    elif diff.is_empty:
        lines.extend(["", "No compiled context changes."])
    else:
        lines.extend(["", "Package presentation changed without semantic or Resource content changes."])

    if include_technical:
        lines.extend(["", *render_diff_technical(diff).rstrip("\n").split("\n")])
    return "\n".join(lines) + "\n"


def render_diff_technical(diff: ContextDiff) -> str:
    return "\n".join(
        [
            "Technical details:",
            f"  Normalized digest: {_transition(diff.before_normalized_digest, diff.after_normalized_digest)}",
            f"  Package digest: {_transition(diff.before_package_digest, diff.after_package_digest)}",
        ]
    ) + "\n"

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


def _node_snapshot(compiled: CompiledNode) -> dict[str, dict[str, Any]]:
    return {
        compiled.metadata.id: {
            "name": compiled.metadata.name,
            "version": compiled.metadata.version,
        }
    }


def _parent_snapshot(compiled: CompiledNode) -> dict[str, dict[str, Any]]:
    return {
        parent.metadata.id: {
            "version": parent.metadata.version,
            "normalized_digest": parent.normalized_digest,
            "package_digest": parent.package_digest,
        }
        for parent in compiled.parent_packages
    }

def _source_snapshot(compiled: CompiledNode) -> dict[str, dict[str, Any]]:
    return {
        source.metadata.id: {
            "version": source.metadata.version,
            "normalized_digest": source.normalized_digest,
            "package_digest": source.package_digest,
        }
        for source in compiled.source_packages
    }


def _change_snapshot(compiled: CompiledNode) -> dict[str, dict[str, Any]]:
    return {
        f"{change.target_node_id}#{change.target_rule_id}": {
            "kind": change.kind,
            "target_node_name": change.target_node_name,
            "statement": change.statement,
            "why": change.why,
        }
        for change in compiled.local_changes
    }


def _rule_snapshot(compiled: CompiledNode) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for rule in (*compiled.inherited_rules, *compiled.local_rules):
        identity = f"{rule.origin_node_id}#{rule.id}"
        result[identity] = {"status": "active", **asdict(rule)}

    removals: dict[str, list[dict[str, Any]]] = {}
    origin_names: dict[str, str] = {}
    for removal in compiled.removed_rules:
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


def _topic_snapshot(compiled: CompiledNode) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for topic in (*compiled.inherited_topics, *compiled.local_topics):
        item = asdict(topic)
        item["targets"] = sorted(
            item["targets"],
            key=lambda target: (target["intent"], target["kind"], target["locator"]),
        )
        result[f"{topic.origin_node_id}#{topic.id}"] = item
    return result


def _resource_snapshot(compiled: CompiledNode) -> dict[str, dict[str, Any]]:
    return {
        path: {
            "sha256": hashlib.sha256(content).hexdigest(),
            "size": len(content),
        }
        for path, content in compiled.resources.items()
    }
