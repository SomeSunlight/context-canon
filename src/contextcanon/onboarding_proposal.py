from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .onboarding import EVIDENCE_SCHEMA
from .parser import ContextCanonError


PROPOSAL_SCHEMA = "contextcanon/onboarding-proposal/v0"
PROPOSAL_KINDS = {
    "local-rule",
    "existing-source",
    "candidate-reusable-node",
    "topic-resource",
    "state-planning",
    "ordinary-documentation",
    "unresolved-question",
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
_ITEM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_TOP_LEVEL_KEYS = {"schema", "evidence_digest", "items"}
_ITEM_KEYS = {"id", "kind", "title", "rationale", "confidence", "evidence", "payload"}
_EVIDENCE_REF_KEYS = {"path", "sha256", "start_line", "end_line"}

_PAYLOAD_FIELDS: dict[str, tuple[set[str], set[str]]] = {
    "local-rule": (
        {"group", "statement", "why"},
        {"group", "statement", "why"},
    ),
    "existing-source": (
        {"source_node_id", "source_name", "reason"},
        {"source_node_id", "source_name", "reason"},
    ),
    "candidate-reusable-node": (
        {"suggested_name", "scope", "why_reusable"},
        {"suggested_name", "scope", "why_reusable"},
    ),
    "topic-resource": (
        {"condition", "resource_paths"},
        {"condition", "resource_paths"},
    ),
    "state-planning": (
        {"destination", "summary"},
        {"destination", "summary"},
    ),
    "ordinary-documentation": (
        {"document_paths", "reason"},
        {"document_paths", "reason"},
    ),
    "unresolved-question": (
        {"question", "why_unresolved"},
        {"question", "why_unresolved"},
    ),
}


@dataclass(frozen=True)
class SnapshotEvidence:
    path: str
    sha256: str
    size: int
    reason: str
    line_count: int


@dataclass(frozen=True)
class EvidenceSnapshot:
    root: Path
    evidence_digest: str
    entries: tuple[SnapshotEvidence, ...]

    @property
    def by_path(self) -> dict[str, SnapshotEvidence]:
        return {entry.path: entry for entry in self.entries}


@dataclass(frozen=True)
class EvidenceReference:
    path: str
    sha256: str
    start_line: int
    end_line: int

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }


@dataclass(frozen=True)
class ProposalItem:
    id: str
    kind: str
    title: str
    rationale: str
    confidence: str
    evidence: tuple[EvidenceReference, ...]
    payload: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "evidence": [reference.to_dict() for reference in self.evidence],
            "payload": self.payload,
        }


@dataclass(frozen=True)
class OnboardingProposal:
    evidence_digest: str
    items: tuple[ProposalItem, ...]
    proposal_digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": PROPOSAL_SCHEMA,
            "evidence_digest": self.evidence_digest,
            "items": [item.to_dict() for item in self.items],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _error(message: str) -> ContextCanonError:
    return ContextCanonError(f"Invalid onboarding proposal: {message}")


def _expect_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _error(f"{label} must be a JSON object")
    return value


def _expect_exact_keys(value: dict[str, Any], allowed: set[str], required: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise _error(f"{label} has unknown field(s): {', '.join(unknown)}")
    if missing:
        raise _error(f"{label} is missing field(s): {', '.join(missing)}")


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(f"{label} must be a non-empty string")
    return value


def _safe_relative_path(value: object, label: str) -> str:
    path = _nonempty_string(value, label)
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != path:
        raise _error(f"{label} must be a normalized repository-relative POSIX path")
    return path


def _canonical_digest(value: dict[str, object]) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContextCanonError(f"Missing {label}: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"{label} is not valid UTF-8: {path}") from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContextCanonError(f"Invalid JSON in {label} {path}: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ContextCanonError(f"{label} must contain a JSON object: {path}")
    return parsed


def load_evidence_snapshot(snapshot_root: Path) -> EvidenceSnapshot:
    root = snapshot_root.resolve()
    manifest_path = root / "manifest.json"
    manifest = _read_json(manifest_path, "onboarding evidence manifest")

    expected_top = {"schema", "selection", "included", "excluded", "evidence_digest"}
    if set(manifest) != expected_top:
        unknown = sorted(set(manifest) - expected_top)
        missing = sorted(expected_top - set(manifest))
        detail = []
        if unknown:
            detail.append(f"unknown fields: {', '.join(unknown)}")
        if missing:
            detail.append(f"missing fields: {', '.join(missing)}")
        raise ContextCanonError(f"Invalid onboarding evidence manifest ({'; '.join(detail)})")
    if manifest["schema"] != EVIDENCE_SCHEMA:
        raise ContextCanonError(f"Unsupported onboarding evidence schema: {manifest['schema']!r}")

    digest = manifest["evidence_digest"]
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise ContextCanonError("Invalid onboarding evidence digest")
    payload = {key: manifest[key] for key in ("schema", "selection", "included", "excluded")}
    if _canonical_digest(payload) != digest:
        raise ContextCanonError("Onboarding evidence manifest digest does not match its payload")

    included = manifest["included"]
    if not isinstance(included, list):
        raise ContextCanonError("Onboarding evidence manifest included must be a list")

    entries: list[SnapshotEvidence] = []
    expected_paths: set[str] = set()
    previous_path: str | None = None
    for index, raw_entry in enumerate(included):
        if not isinstance(raw_entry, dict):
            raise ContextCanonError(f"Onboarding evidence included[{index}] must be an object")
        expected_keys = {"path", "reason", "sha256", "size", "snapshot"}
        if set(raw_entry) != expected_keys:
            raise ContextCanonError(f"Onboarding evidence included[{index}] has invalid fields")
        path = _safe_relative_path(raw_entry["path"], f"evidence included[{index}].path")
        if previous_path is not None and path <= previous_path:
            raise ContextCanonError("Onboarding evidence included paths must be unique and sorted")
        previous_path = path
        reason = _nonempty_string(raw_entry["reason"], f"evidence included[{index}].reason")
        sha256 = raw_entry["sha256"]
        if not isinstance(sha256, str) or not _SHA256_RE.fullmatch(sha256):
            raise ContextCanonError(f"Invalid SHA-256 for onboarding evidence {path}")
        size = raw_entry["size"]
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise ContextCanonError(f"Invalid size for onboarding evidence {path}")
        expected_snapshot = f"evidence/{path}"
        if raw_entry["snapshot"] != expected_snapshot:
            raise ContextCanonError(f"Invalid snapshot path for onboarding evidence {path}")

        evidence_file = root.joinpath(*PurePosixPath(expected_snapshot).parts)
        if evidence_file.is_symlink() or not evidence_file.is_file():
            raise ContextCanonError(f"Missing or unsafe onboarding evidence file: {path}")
        data = evidence_file.read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != sha256:
            raise ContextCanonError(f"Onboarding evidence file does not match manifest: {path}")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContextCanonError(f"Onboarding evidence file is not valid UTF-8: {path}") from exc
        entries.append(SnapshotEvidence(path, sha256, size, reason, len(text.splitlines())))
        expected_paths.add(path)

    evidence_root = root / "evidence"
    actual_paths: set[str] = set()
    if evidence_root.exists():
        for candidate in evidence_root.rglob("*"):
            if candidate.is_symlink():
                raise ContextCanonError(f"Onboarding evidence snapshot contains symlink: {candidate}")
            if candidate.is_file():
                actual_paths.add(candidate.relative_to(evidence_root).as_posix())
    if actual_paths != expected_paths:
        raise ContextCanonError("Onboarding evidence snapshot file set does not match manifest")

    excluded = manifest["excluded"]
    if not isinstance(excluded, list):
        raise ContextCanonError("Onboarding evidence manifest excluded must be a list")
    previous_excluded: str | None = None
    for index, raw_entry in enumerate(excluded):
        if not isinstance(raw_entry, dict) or set(raw_entry) != {"path", "reason"}:
            raise ContextCanonError(f"Onboarding evidence excluded[{index}] has invalid fields")
        path = _safe_relative_path(raw_entry["path"], f"evidence excluded[{index}].path")
        _nonempty_string(raw_entry["reason"], f"evidence excluded[{index}].reason")
        if previous_excluded is not None and path <= previous_excluded:
            raise ContextCanonError("Onboarding evidence excluded paths must be unique and sorted")
        previous_excluded = path

    return EvidenceSnapshot(root=root, evidence_digest=digest, entries=tuple(entries))


def _parse_reference(raw: object, item_id: str, index: int, snapshot: EvidenceSnapshot) -> EvidenceReference:
    reference = _expect_object(raw, f"item {item_id} evidence[{index}]")
    _expect_exact_keys(reference, _EVIDENCE_REF_KEYS, _EVIDENCE_REF_KEYS, f"item {item_id} evidence[{index}]")
    path = _safe_relative_path(reference["path"], f"item {item_id} evidence[{index}].path")
    entry = snapshot.by_path.get(path)
    if entry is None:
        raise _error(f"item {item_id} references evidence not present in snapshot: {path}")
    sha256 = reference["sha256"]
    if sha256 != entry.sha256:
        raise _error(f"item {item_id} evidence hash does not match snapshot: {path}")
    start = reference["start_line"]
    end = reference["end_line"]
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        raise _error(f"item {item_id} evidence start_line must be a positive integer")
    if not isinstance(end, int) or isinstance(end, bool) or end < start:
        raise _error(f"item {item_id} evidence end_line must be >= start_line")
    if end > entry.line_count:
        raise _error(
            f"item {item_id} evidence range {start}-{end} exceeds {path} line count {entry.line_count}"
        )
    return EvidenceReference(path=path, sha256=entry.sha256, start_line=start, end_line=end)


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise _error(f"{label} must be a non-empty list")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_safe_relative_path(item, f"{label}[{index}]"))
    if len(set(result)) != len(result):
        raise _error(f"{label} contains duplicate paths")
    return result


def _validate_payload(kind: str, raw: object, item_id: str, snapshot: EvidenceSnapshot) -> dict[str, object]:
    payload = _expect_object(raw, f"item {item_id} payload")
    allowed, required = _PAYLOAD_FIELDS[kind]
    _expect_exact_keys(payload, allowed, required, f"item {item_id} payload")

    normalized: dict[str, object] = {}
    if kind == "local-rule":
        normalized = {
            "group": _nonempty_string(payload["group"], f"item {item_id} payload.group"),
            "statement": _nonempty_string(payload["statement"], f"item {item_id} payload.statement"),
            "why": _nonempty_string(payload["why"], f"item {item_id} payload.why"),
        }
    elif kind == "existing-source":
        normalized = {
            "source_node_id": _nonempty_string(
                payload["source_node_id"], f"item {item_id} payload.source_node_id"
            ),
            "source_name": _nonempty_string(payload["source_name"], f"item {item_id} payload.source_name"),
            "reason": _nonempty_string(payload["reason"], f"item {item_id} payload.reason"),
        }
    elif kind == "candidate-reusable-node":
        normalized = {
            "suggested_name": _nonempty_string(
                payload["suggested_name"], f"item {item_id} payload.suggested_name"
            ),
            "scope": _nonempty_string(payload["scope"], f"item {item_id} payload.scope"),
            "why_reusable": _nonempty_string(
                payload["why_reusable"], f"item {item_id} payload.why_reusable"
            ),
        }
    elif kind == "topic-resource":
        paths = _string_list(payload["resource_paths"], f"item {item_id} payload.resource_paths")
        missing = sorted(set(paths) - set(snapshot.by_path))
        if missing:
            raise _error(f"item {item_id} topic resource path is not in evidence snapshot: {missing[0]}")
        normalized = {
            "condition": _nonempty_string(payload["condition"], f"item {item_id} payload.condition"),
            "resource_paths": paths,
        }
    elif kind == "state-planning":
        destination = payload["destination"]
        if destination not in {"state", "plan"}:
            raise _error(f"item {item_id} payload.destination must be 'state' or 'plan'")
        normalized = {
            "destination": destination,
            "summary": _nonempty_string(payload["summary"], f"item {item_id} payload.summary"),
        }
    elif kind == "ordinary-documentation":
        paths = _string_list(payload["document_paths"], f"item {item_id} payload.document_paths")
        missing = sorted(set(paths) - set(snapshot.by_path))
        if missing:
            raise _error(f"item {item_id} ordinary document path is not in evidence snapshot: {missing[0]}")
        normalized = {
            "document_paths": paths,
            "reason": _nonempty_string(payload["reason"], f"item {item_id} payload.reason"),
        }
    elif kind == "unresolved-question":
        normalized = {
            "question": _nonempty_string(payload["question"], f"item {item_id} payload.question"),
            "why_unresolved": _nonempty_string(
                payload["why_unresolved"], f"item {item_id} payload.why_unresolved"
            ),
        }
    else:  # guarded by caller; defensive against future edits
        raise _error(f"unsupported item kind: {kind}")
    return normalized


def load_onboarding_proposal(proposal_path: Path, snapshot_root: Path) -> OnboardingProposal:
    snapshot = load_evidence_snapshot(snapshot_root)
    raw = _read_json(proposal_path.resolve(), "onboarding proposal")
    _expect_exact_keys(raw, _TOP_LEVEL_KEYS, _TOP_LEVEL_KEYS, "proposal")
    if raw["schema"] != PROPOSAL_SCHEMA:
        raise _error(f"unsupported schema {raw['schema']!r}")
    if raw["evidence_digest"] != snapshot.evidence_digest:
        raise _error("evidence_digest does not match the supplied evidence snapshot")
    raw_items = raw["items"]
    if not isinstance(raw_items, list):
        raise _error("items must be a list")

    items: list[ProposalItem] = []
    ids: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        item = _expect_object(raw_item, f"items[{index}]")
        _expect_exact_keys(item, _ITEM_KEYS, _ITEM_KEYS, f"items[{index}]")
        item_id = _nonempty_string(item["id"], f"items[{index}].id")
        if not _ITEM_ID_RE.fullmatch(item_id):
            raise _error(f"item id has invalid format: {item_id!r}")
        if item_id in ids:
            raise _error(f"duplicate item id: {item_id}")
        ids.add(item_id)
        kind = item["kind"]
        if kind not in PROPOSAL_KINDS:
            raise _error(f"item {item_id} has unsupported kind: {kind!r}")
        title = _nonempty_string(item["title"], f"item {item_id} title")
        rationale = _nonempty_string(item["rationale"], f"item {item_id} rationale")
        confidence = item["confidence"]
        if confidence not in CONFIDENCE_LEVELS:
            raise _error(f"item {item_id} confidence must be high, medium, or low")
        raw_evidence = item["evidence"]
        if not isinstance(raw_evidence, list) or not raw_evidence:
            raise _error(f"item {item_id} evidence must be a non-empty list")
        references = tuple(
            _parse_reference(reference, item_id, ref_index, snapshot)
            for ref_index, reference in enumerate(raw_evidence)
        )
        payload = _validate_payload(kind, item["payload"], item_id, snapshot)
        items.append(
            ProposalItem(
                id=item_id,
                kind=kind,
                title=title,
                rationale=rationale,
                confidence=confidence,
                evidence=references,
                payload=payload,
            )
        )

    normalized = {
        "schema": PROPOSAL_SCHEMA,
        "evidence_digest": snapshot.evidence_digest,
        "items": [item.to_dict() for item in items],
    }
    digest = _canonical_digest(normalized)
    return OnboardingProposal(snapshot.evidence_digest, tuple(items), digest)
