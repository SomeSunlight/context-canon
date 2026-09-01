from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .model import CompiledPackage
from .onboarding_instruction import _load_catalog
from .onboarding_proposal import EvidenceReference, EvidenceSnapshot, load_evidence_snapshot
from .onboarding_structure import HumanStructurePlan, load_onboarding_structure_proposal, load_structure_markdown
from .parser import ContextCanonError


PLACEMENT_PROPOSAL_SCHEMA = "contextcanon/onboarding-placement-proposal/v1"
PLACEMENT_KINDS = {
    "overview",
    "rule",
    "topic-resource",
    "ordinary-documentation",
    "state",
    "plan",
    "authority-mapping",
    "unresolved",
}
PLACEMENT_ACTIONS = {"keep", "promote", "reference", "map"}
WORDING_ORIGINS = {"exact", "lightly-edited", "synthesized"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}


@dataclass(frozen=True)
class PlacementItem:
    id: str
    title: str
    kind: str
    action: str
    destination_node_key: str | None
    rationale: str
    confidence: str
    evidence: tuple[EvidenceReference, ...]
    payload: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "kind": self.kind,
            "action": self.action,
            "destination_node_key": self.destination_node_key,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "evidence": [reference.to_dict() for reference in self.evidence],
            "payload": self.payload,
        }


@dataclass(frozen=True)
class PlacementSourceReuse:
    id: str
    target_node_key: str
    source_node_id: str
    source_name: str
    source_version: str
    source_normalized_digest: str
    source_package_digest: str
    reason: str
    confidence: str
    evidence: tuple[EvidenceReference, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "target_node_key": self.target_node_key,
            "source_node_id": self.source_node_id,
            "source_name": self.source_name,
            "source_version": self.source_version,
            "source_normalized_digest": self.source_normalized_digest,
            "source_package_digest": self.source_package_digest,
            "reason": self.reason,
            "confidence": self.confidence,
            "evidence": [reference.to_dict() for reference in self.evidence],
        }


@dataclass(frozen=True)
class PlacementSourceEdit:
    id: str
    path: str
    sha256: str
    start_line: int
    end_line: int
    linked_item_ids: tuple[str, ...]
    replacement: str
    rationale: str
    confidence: str

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "path": self.path,
            "sha256": self.sha256,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "linked_item_ids": list(self.linked_item_ids),
            "replacement": self.replacement,
            "rationale": self.rationale,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class OnboardingPlacementProposal:
    evidence_digest: str
    structure_digest: str
    items: tuple[PlacementItem, ...]
    source_edits: tuple[PlacementSourceEdit, ...]
    source_reuses: tuple[PlacementSourceReuse, ...]
    proposal_digest: str
    structure: HumanStructurePlan
    catalog_packages: tuple[CompiledPackage, ...]


def _error(message: str) -> ContextCanonError:
    return ContextCanonError(f"Invalid onboarding placement: {message}")


def _canonical_digest(value: dict[str, object]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        text = path.resolve().read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContextCanonError(f"Missing onboarding placement proposal: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"Onboarding placement proposal is not valid UTF-8: {path}") from exc
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContextCanonError(f"Invalid JSON in onboarding placement proposal {path}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise _error("proposal must be a JSON object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) == expected:
        return
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    detail: list[str] = []
    if missing:
        detail.append(f"missing fields: {', '.join(missing)}")
    if unknown:
        detail.append(f"unknown fields: {', '.join(unknown)}")
    raise _error(f"{label} has {'; '.join(detail)}")


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(f"{label} must be a non-empty string")
    return value.strip()


def _optional_string(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _string(value, label)


def _replacement(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise _error(f"{label} must be a string")
    if "\x00" in value:
        raise _error(f"{label} contains an unsupported NUL character")
    return value.replace("\r\n", "\n").replace("\r", "\n").strip("\n")


def _confidence(value: object, label: str) -> str:
    if value not in CONFIDENCE_LEVELS:
        raise _error(f"{label} must be high, medium, or low")
    return str(value)


def _reference(raw: object, label: str, snapshot: EvidenceSnapshot) -> EvidenceReference:
    if not isinstance(raw, dict):
        raise _error(f"{label} must be an object")
    _exact_keys(raw, {"path", "sha256", "start_line", "end_line"}, label)
    path = _string(raw["path"], f"{label}.path")
    entry = snapshot.by_path.get(path)
    if entry is None:
        raise _error(f"{label} references evidence not in snapshot: {path}")
    if raw["sha256"] != entry.sha256:
        raise _error(f"{label} evidence hash does not match snapshot: {path}")
    start = raw["start_line"]
    end = raw["end_line"]
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        raise _error(f"{label}.start_line must be a positive integer")
    if not isinstance(end, int) or isinstance(end, bool) or end < start or end > entry.line_count:
        raise _error(f"{label}.end_line is outside the frozen evidence range")
    return EvidenceReference(path, entry.sha256, start, end)


def _references(raw: object, label: str, snapshot: EvidenceSnapshot) -> tuple[EvidenceReference, ...]:
    if not isinstance(raw, list) or not raw:
        raise _error(f"{label} must be a non-empty list")
    return tuple(_reference(item, f"{label}[{index}]", snapshot) for index, item in enumerate(raw))


def _path_list(value: object, label: str, snapshot: EvidenceSnapshot) -> list[str]:
    if not isinstance(value, list) or not value:
        raise _error(f"{label} must be a non-empty list")
    result: list[str] = []
    for index, raw in enumerate(value):
        path = _string(raw, f"{label}[{index}]")
        if path not in snapshot.by_path:
            raise _error(f"{label}[{index}] is not present in frozen Evidence: {path}")
        result.append(path)
    if len(result) != len(set(result)):
        raise _error(f"{label} contains duplicate paths")
    return result


def _wording(value: object, label: str) -> str:
    if value not in WORDING_ORIGINS:
        raise _error(f"{label} must be exact, lightly-edited, or synthesized")
    return str(value)


def _parse_payload(kind: str, raw: object, label: str, snapshot: EvidenceSnapshot) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise _error(f"{label} must be an object")
    payload = dict(raw)
    if kind == "rule":
        _exact_keys(payload, {"statement", "why", "wording_origin"}, label)
        return {
            "statement": _string(payload["statement"], f"{label}.statement"),
            "why": _string(payload["why"], f"{label}.why"),
            "wording_origin": _wording(payload["wording_origin"], f"{label}.wording_origin"),
        }
    if kind == "topic-resource":
        _exact_keys(payload, {"condition", "resource_paths"}, label)
        return {
            "condition": _string(payload["condition"], f"{label}.condition"),
            "resource_paths": _path_list(payload["resource_paths"], f"{label}.resource_paths", snapshot),
        }
    if kind == "ordinary-documentation":
        _exact_keys(payload, {"document_paths", "reason"}, label)
        return {
            "document_paths": _path_list(payload["document_paths"], f"{label}.document_paths", snapshot),
            "reason": _string(payload["reason"], f"{label}.reason"),
        }
    if kind in {"overview", "state", "plan"}:
        _exact_keys(payload, {"text", "wording_origin"}, label)
        return {
            "text": _string(payload["text"], f"{label}.text"),
            "wording_origin": _wording(payload["wording_origin"], f"{label}.wording_origin"),
        }
    if kind == "authority-mapping":
        _exact_keys(payload, {"authority_paths", "mapping", "wording_origin"}, label)
        return {
            "authority_paths": _path_list(payload["authority_paths"], f"{label}.authority_paths", snapshot),
            "mapping": _string(payload["mapping"], f"{label}.mapping"),
            "wording_origin": _wording(payload["wording_origin"], f"{label}.wording_origin"),
        }
    if kind == "unresolved":
        _exact_keys(payload, {"question"}, label)
        return {"question": _string(payload["question"], f"{label}.question")}
    raise _error(f"unsupported placement kind {kind!r}")


def load_onboarding_placement_proposal(
    proposal_path: Path,
    snapshot_root: Path,
    structure_proposal_path: Path,
    structure_path: Path,
    *,
    catalog_package_roots: Iterable[Path] = (),
) -> OnboardingPlacementProposal:
    snapshot = load_evidence_snapshot(snapshot_root)
    structure_proposal = load_onboarding_structure_proposal(structure_proposal_path, snapshot_root)
    structure = load_structure_markdown(structure_path, structure_proposal)
    packages = _load_catalog(catalog_package_roots)
    package_by_id = {package.metadata.id: package for package in packages}
    node_keys = {node.key for node in structure.nodes}

    raw = _read_json(proposal_path)
    required_top = {"schema", "evidence_digest", "structure_digest", "items", "source_reuses"}
    allowed_top = required_top | {"source_edits"}
    unknown_top = sorted(set(raw) - allowed_top)
    missing_top = sorted(required_top - set(raw))
    if unknown_top or missing_top:
        detail = []
        if missing_top:
            detail.append(f"missing fields: {', '.join(missing_top)}")
        if unknown_top:
            detail.append(f"unknown fields: {', '.join(unknown_top)}")
        raise _error(f"proposal has {'; '.join(detail)}")
    if raw["schema"] != PLACEMENT_PROPOSAL_SCHEMA:
        raise _error(f"unsupported schema {raw['schema']!r}")
    if raw["evidence_digest"] != snapshot.evidence_digest:
        raise _error("evidence_digest does not match the supplied frozen Evidence")
    if raw["structure_digest"] != structure.structure_digest:
        raise _error("structure_digest does not match the edited structure")

    raw_items = raw["items"]
    if not isinstance(raw_items, list):
        raise _error("items must be a list")
    items: list[PlacementItem] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, dict):
            raise _error(f"items[{index}] must be an object")
        _exact_keys(
            raw_item,
            {"id", "title", "kind", "action", "destination_node_key", "rationale", "confidence", "evidence", "payload"},
            f"items[{index}]",
        )
        item_id = _string(raw_item["id"], f"items[{index}].id")
        if item_id in seen_ids:
            raise _error(f"duplicate item id {item_id}")
        seen_ids.add(item_id)
        kind = raw_item["kind"]
        action = raw_item["action"]
        if kind not in PLACEMENT_KINDS:
            raise _error(f"items[{index}].kind is unsupported: {kind!r}")
        if action not in PLACEMENT_ACTIONS:
            raise _error(f"items[{index}].action is unsupported: {action!r}")
        destination = _optional_string(raw_item["destination_node_key"], f"items[{index}].destination_node_key")
        if destination is not None and destination not in node_keys:
            raise _error(f"items[{index}] references unknown destination Node {destination}")
        if kind in {"overview", "rule", "topic-resource", "state", "plan", "authority-mapping"} and destination is None:
            raise _error(f"items[{index}] kind {kind} requires destination_node_key")
        allowed_actions = {
            "overview": {"promote"},
            "rule": {"promote"},
            "topic-resource": {"reference"},
            "ordinary-documentation": {"keep"},
            "state": {"promote"},
            "plan": {"promote"},
            "authority-mapping": {"map"},
            "unresolved": {"keep"},
        }
        if action not in allowed_actions[str(kind)]:
            expected = ", ".join(sorted(allowed_actions[str(kind)]))
            raise _error(f"items[{index}] kind {kind} must use action {expected}")
        payload = _parse_payload(str(kind), raw_item["payload"], f"items[{index}].payload", snapshot)
        if kind == "authority-mapping":
            fixed = set(structure.fixed_markdown)
            for path in payload["authority_paths"]:
                if path not in fixed:
                    raise _error(
                        f"items[{index}] authority path {path!r} is not marked fixed in the accepted structure"
                    )
        items.append(
            PlacementItem(
                id=item_id,
                title=_string(raw_item["title"], f"items[{index}].title"),
                kind=str(kind),
                action=str(action),
                destination_node_key=destination,
                rationale=_string(raw_item["rationale"], f"items[{index}].rationale"),
                confidence=_confidence(raw_item["confidence"], f"items[{index}].confidence"),
                evidence=_references(raw_item["evidence"], f"items[{index}].evidence", snapshot),
                payload=payload,
            )
        )

    raw_source_edits = raw.get("source_edits", [])
    if not isinstance(raw_source_edits, list):
        raise _error("source_edits must be a list")
    source_edits: list[PlacementSourceEdit] = []
    item_by_id = {item.id: item for item in items}
    occupied: dict[str, list[tuple[int, int, str]]] = {}
    fixed_markdown = set(structure.fixed_markdown)
    for index, raw_edit in enumerate(raw_source_edits):
        label = f"source_edits[{index}]"
        if not isinstance(raw_edit, dict):
            raise _error(f"{label} must be an object")
        _exact_keys(
            raw_edit,
            {"id", "path", "sha256", "start_line", "end_line", "linked_item_ids", "replacement", "rationale", "confidence"},
            label,
        )
        edit_id = _string(raw_edit["id"], f"{label}.id")
        if edit_id in seen_ids:
            raise _error(f"duplicate proposal id {edit_id}")
        seen_ids.add(edit_id)
        edit_path = _string(raw_edit["path"], f"{label}.path")
        entry = snapshot.by_path.get(edit_path)
        if entry is None:
            raise _error(f"{label}.path is not present in frozen Evidence: {edit_path}")
        if not edit_path.lower().endswith(".md"):
            raise _error(f"{label}.path must be mutable Markdown")
        if edit_path in fixed_markdown:
            raise _error(f"{label}.path is fixed Markdown and cannot receive a source edit")
        if raw_edit["sha256"] != entry.sha256:
            raise _error(f"{label}.sha256 does not match frozen Evidence: {edit_path}")
        start = raw_edit["start_line"]
        end = raw_edit["end_line"]
        if not isinstance(start, int) or isinstance(start, bool) or start < 1:
            raise _error(f"{label}.start_line must be a positive integer")
        if not isinstance(end, int) or isinstance(end, bool) or end < start or end > entry.line_count:
            raise _error(f"{label}.end_line is outside the frozen Evidence range")
        linked_raw = raw_edit["linked_item_ids"]
        if not isinstance(linked_raw, list) or not linked_raw:
            raise _error(f"{label}.linked_item_ids must be a non-empty list")
        linked = tuple(_string(value, f"{label}.linked_item_ids[{i}]") for i, value in enumerate(linked_raw))
        if len(linked) != len(set(linked)):
            raise _error(f"{label}.linked_item_ids contains duplicates")
        covered: set[int] = set()
        for linked_id in linked:
            linked_item = item_by_id.get(linked_id)
            if linked_item is None:
                raise _error(f"{label} references unknown placement item {linked_id}")
            if linked_item.action != "promote":
                raise _error(f"{label} may link only promoted placement items; {linked_id} uses {linked_item.action}")
            for reference in linked_item.evidence:
                if reference.path == edit_path:
                    covered.update(range(reference.start_line, reference.end_line + 1))
        if not set(range(start, end + 1)).issubset(covered):
            raise _error(f"{label} range is not fully covered by Evidence of its linked promoted items")
        for other_start, other_end, other_id in occupied.setdefault(edit_path, []):
            if not (end < other_start or start > other_end):
                raise _error(f"{label} overlaps source edit {other_id} in {edit_path}")
        occupied[edit_path].append((start, end, edit_id))
        source_edits.append(
            PlacementSourceEdit(
                id=edit_id,
                path=edit_path,
                sha256=entry.sha256,
                start_line=start,
                end_line=end,
                linked_item_ids=linked,
                replacement=_replacement(raw_edit["replacement"], f"{label}.replacement"),
                rationale=_string(raw_edit["rationale"], f"{label}.rationale"),
                confidence=_confidence(raw_edit["confidence"], f"{label}.confidence"),
            )
        )

    raw_reuses = raw["source_reuses"]
    if not isinstance(raw_reuses, list):
        raise _error("source_reuses must be a list")
    reuses: list[PlacementSourceReuse] = []
    for index, raw_reuse in enumerate(raw_reuses):
        if not isinstance(raw_reuse, dict):
            raise _error(f"source_reuses[{index}] must be an object")
        _exact_keys(
            raw_reuse,
            {"id", "target_node_key", "source_node_id", "source_name", "source_version", "source_normalized_digest", "source_package_digest", "reason", "confidence", "evidence"},
            f"source_reuses[{index}]",
        )
        reuse_id = _string(raw_reuse["id"], f"source_reuses[{index}].id")
        if reuse_id in seen_ids:
            raise _error(f"duplicate proposal id {reuse_id}")
        seen_ids.add(reuse_id)
        target = _string(raw_reuse["target_node_key"], f"source_reuses[{index}].target_node_key")
        if target not in node_keys:
            raise _error(f"source_reuses[{index}] references unknown target Node {target}")
        source_id = _string(raw_reuse["source_node_id"], f"source_reuses[{index}].source_node_id")
        package = package_by_id.get(source_id)
        if package is None:
            raise _error(f"source_reuses[{index}] names Source {source_id} not supplied in the verified catalog")
        expected = {
            "source_name": package.metadata.name,
            "source_version": package.metadata.version,
            "source_normalized_digest": package.normalized_digest,
            "source_package_digest": package.package_digest,
        }
        for field, value in expected.items():
            if raw_reuse[field] != value:
                raise _error(f"source_reuses[{index}].{field} does not match supplied immutable package")
        reuses.append(
            PlacementSourceReuse(
                id=reuse_id,
                target_node_key=target,
                source_node_id=source_id,
                source_name=package.metadata.name,
                source_version=package.metadata.version,
                source_normalized_digest=package.normalized_digest,
                source_package_digest=package.package_digest,
                reason=_string(raw_reuse["reason"], f"source_reuses[{index}].reason"),
                confidence=_confidence(raw_reuse["confidence"], f"source_reuses[{index}].confidence"),
                evidence=_references(raw_reuse["evidence"], f"source_reuses[{index}].evidence", snapshot),
            )
        )

    normalized = {
        "schema": PLACEMENT_PROPOSAL_SCHEMA,
        "evidence_digest": snapshot.evidence_digest,
        "structure_digest": structure.structure_digest,
        "items": [item.to_dict() for item in items],
        "source_edits": [edit.to_dict() for edit in source_edits],
        "source_reuses": [reuse.to_dict() for reuse in reuses],
    }
    return OnboardingPlacementProposal(
        evidence_digest=snapshot.evidence_digest,
        structure_digest=structure.structure_digest,
        items=tuple(items),
        source_edits=tuple(source_edits),
        source_reuses=tuple(reuses),
        proposal_digest=_canonical_digest(normalized),
        structure=structure,
        catalog_packages=packages,
    )


def _evidence_excerpt(reference: EvidenceReference, snapshot: EvidenceSnapshot) -> list[str]:
    evidence_file = snapshot.root / "evidence" / reference.path
    text = evidence_file.read_text(encoding="utf-8").splitlines()
    lines = [f"- `{reference.path}` lines {reference.start_line}-{reference.end_line} · `{reference.sha256}`", "  ```text"]
    for number, content in enumerate(text[reference.start_line - 1 : reference.end_line], start=reference.start_line):
        lines.append(f"  {number:>5}: {content}")
    lines.append("  ```")
    return lines


def render_placement_review(proposal: OnboardingPlacementProposal, snapshot_root: Path) -> str:
    snapshot = load_evidence_snapshot(snapshot_root)
    node_by_key = {node.key: node for node in proposal.structure.nodes}
    lines = [
        "# ContextCanon onboarding placement review",
        "",
        f"Evidence: `{proposal.evidence_digest}`",
        f"Accepted structure: `{proposal.structure_digest}`",
        f"Placement proposal: `{proposal.proposal_digest}`",
        "",
        "This is a review artifact only. No source document or Context Node is changed by rendering it.",
        "",
    ]
    for item in proposal.items:
        destination = node_by_key.get(item.destination_node_key) if item.destination_node_key else None
        destination_text = f"{destination.name} (`{destination.path}`)" if destination else "none / stays outside Node authoring"
        lines.extend(
            [
                f"## {item.id} — {item.title}",
                "",
                f"Kind: `{item.kind}` · action: `{item.action}` · confidence: `{item.confidence}`",
                "",
                f"Destination: {destination_text}",
                "",
                item.rationale,
                "",
                "Proposed payload:",
                "```json",
                json.dumps(item.payload, ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
        wording = item.payload.get("wording_origin")
        if wording is not None:
            lines.extend([f"Wording origin: **{wording}**", ""])
        lines.append("Evidence:")
        for reference in item.evidence:
            lines.extend(_evidence_excerpt(reference, snapshot))
        lines.append("")

    if proposal.source_reuses:
        lines.extend(["# Proposed reusable Source matches", ""])
        for reuse in proposal.source_reuses:
            target = node_by_key[reuse.target_node_key]
            lines.extend(
                [
                    f"## {reuse.id} — reuse {reuse.source_name}",
                    "",
                    f"Target: {target.name} (`{target.path}`)",
                    f"Package: `{reuse.source_version}` · `{reuse.source_package_digest}`",
                    "",
                    reuse.reason,
                    "",
                    "Evidence:",
                ]
            )
            for reference in reuse.evidence:
                lines.extend(_evidence_excerpt(reference, snapshot))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
