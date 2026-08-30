from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .model import CompiledPackage
from .onboarding_placement import (
    PLACEMENT_ACTIONS,
    PLACEMENT_KINDS,
    WORDING_ORIGINS,
    OnboardingPlacementProposal,
    PlacementItem,
)
from .onboarding_proposal import EvidenceReference, EvidenceSnapshot, load_evidence_snapshot
from .parser import ContextCanonError


PLACEMENT_REVIEW_SCHEMA = "contextcanon/onboarding-placement-review/v1"
REVIEW_DECISIONS = {"pending", "accept", "reject"}

_HEADER_RE = re.compile(
    r"<!-- contextcanon-placement-review\s+"
    r"schema: (?P<schema>\S+)\s+"
    r"evidence_digest: (?P<evidence>[0-9a-f]{64})\s+"
    r"structure_digest: (?P<structure>[0-9a-f]{64})\s+"
    r"proposal_digest: (?P<proposal>[0-9a-f]{64})\s+-->"
)
_ITEM_HEADING_RE = re.compile(r"^## (?P<id>[^ ]+) — (?P<title>.+)$")
_ITEM_COMMENT_RE = re.compile(
    r'^<!-- cc:placement-item id="(?P<id>[^"]+)" authoring-id="(?P<authoring>[^"]+)" -->$'
)
_SOURCE_HEADING_RE = re.compile(r"^## Source (?P<id>[^ ]+) — (?P<title>.+)$")
_SOURCE_COMMENT_RE = re.compile(
    r'^<!-- cc:placement-source id="(?P<id>[^"]+)" origin="(?P<origin>[^"]+)" '
    r'source-id="(?P<source_id>[^"]+)" version="(?P<version>[^"]+)" '
    r'normalized-digest="(?P<normalized>[0-9a-f]{64})" package-digest="(?P<package>[0-9a-f]{64})" -->$'
)
_DESTINATION_RE = re.compile(r"^Destination: `(?P<key>[^`]+)`(?:\s+—.*)?$")
_SIMPLE_VALUE_RE = re.compile(r"^(?P<label>Decision|Kind|Action|Wording|Origin): `(?P<value>[^`]+)`$")
_PATH_RE = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class PlacementReviewItem:
    proposal_id: str
    authoring_id: str
    title: str
    decision: str
    destination_node_key: str | None
    kind: str
    action: str
    payload: dict[str, object]
    review_note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "authoring_id": self.authoring_id,
            "title": self.title,
            "decision": self.decision,
            "destination_node_key": self.destination_node_key,
            "kind": self.kind,
            "action": self.action,
            "payload": self.payload,
            "review_note": self.review_note,
        }


@dataclass(frozen=True)
class PlacementReviewSource:
    review_id: str
    origin: str
    target_node_key: str
    decision: str
    source_node_id: str
    source_name: str
    source_version: str
    source_normalized_digest: str
    source_package_digest: str
    review_note: str
    proposal_id: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "review_id": self.review_id,
            "origin": self.origin,
            "target_node_key": self.target_node_key,
            "decision": self.decision,
            "source_node_id": self.source_node_id,
            "source_name": self.source_name,
            "source_version": self.source_version,
            "source_normalized_digest": self.source_normalized_digest,
            "source_package_digest": self.source_package_digest,
            "review_note": self.review_note,
            "proposal_id": self.proposal_id,
        }


@dataclass(frozen=True)
class OnboardingPlacementReview:
    evidence_digest: str
    structure_digest: str
    proposal_digest: str
    items: tuple[PlacementReviewItem, ...]
    sources: tuple[PlacementReviewSource, ...]
    review_digest: str

    @property
    def is_complete(self) -> bool:
        return all(item.decision != "pending" for item in self.items) and all(
            source.decision != "pending" for source in self.sources
        )


def _error(message: str) -> ContextCanonError:
    return ContextCanonError(f"Invalid onboarding placement review: {message}")


def _digest(value: dict[str, object]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _one_line(value: object) -> str:
    return " ".join(str(value).splitlines()).strip()


def _fresh_authoring_id() -> str:
    return "ONB-" + uuid.uuid4().hex[:12].upper()


def _evidence_excerpt(reference: EvidenceReference, snapshot: EvidenceSnapshot) -> list[str]:
    evidence_file = snapshot.root / "evidence" / reference.path
    text = evidence_file.read_text(encoding="utf-8").splitlines()
    lines = [f"- `{reference.path}` lines {reference.start_line}-{reference.end_line} · `{reference.sha256}`", "  ```text"]
    for number, content in enumerate(text[reference.start_line - 1 : reference.end_line], start=reference.start_line):
        lines.append(f"  {number:>5}: {content}")
    lines.append("  ```")
    return lines


def _render_payload(kind: str, payload: dict[str, object]) -> list[str]:
    lines = ["### Maintained meaning", ""]
    if kind == "rule":
        lines.append(f"Statement: {_one_line(payload['statement'])}")
        lines.append(f"Why: {_one_line(payload['why'])}")
        lines.append(f"Wording: `{payload['wording_origin']}`")
    elif kind in {"overview", "state", "plan"}:
        lines.append(f"Text: {_one_line(payload['text'])}")
        lines.append(f"Wording: `{payload['wording_origin']}`")
    elif kind == "topic-resource":
        lines.append(f"Condition: {_one_line(payload['condition'])}")
        paths = ", ".join(f"`{path}`" for path in payload["resource_paths"])
        lines.append(f"Resources: {paths}")
    elif kind == "ordinary-documentation":
        paths = ", ".join(f"`{path}`" for path in payload["document_paths"])
        lines.append(f"Documents: {paths}")
        lines.append(f"Reason: {_one_line(payload['reason'])}")
    elif kind == "authority-mapping":
        paths = ", ".join(f"`{path}`" for path in payload["authority_paths"])
        lines.append(f"Authorities: {paths}")
        lines.append(f"Mapping: {_one_line(payload['mapping'])}")
        lines.append(f"Wording: `{payload['wording_origin']}`")
    elif kind == "unresolved":
        lines.append(f"Question: {_one_line(payload['question'])}")
    else:
        raise _error(f"unsupported kind {kind!r}")
    return lines


def _render_item(
    item: PlacementItem,
    review_item: PlacementReviewItem,
    proposal: OnboardingPlacementProposal,
    snapshot: EvidenceSnapshot,
) -> list[str]:
    nodes = {node.key: node for node in proposal.structure.nodes}
    destination = nodes.get(review_item.destination_node_key) if review_item.destination_node_key else None
    destination_text = (
        f"`{destination.key}` — **{destination.name}** (`{destination.path}`)" if destination else "none / outside Node authoring"
    )
    lines = [
        f"## {review_item.proposal_id} — {review_item.title}",
        f'<!-- cc:placement-item id="{review_item.proposal_id}" authoring-id="{review_item.authoring_id}" -->',
        "",
        f"Destination: {destination_text}",
        f"Decision: `{review_item.decision}`",
        f"Kind: `{review_item.kind}`",
        f"Action: `{review_item.action}`",
        f"Review note: {review_item.review_note or '-'}",
        "",
    ]
    lines.extend(_render_payload(review_item.kind, review_item.payload))
    lines.extend(
        [
            "",
            "### Proposal rationale",
            "",
            item.rationale,
            "",
            f"Original confidence: `{item.confidence}`",
            "",
            "### Evidence",
            "",
        ]
    )
    for reference in item.evidence:
        lines.extend(_evidence_excerpt(reference, snapshot))
    lines.append("")
    return lines


def _package_by_id(proposal: OnboardingPlacementProposal) -> dict[str, CompiledPackage]:
    return {package.metadata.id: package for package in proposal.catalog_packages}


def _initial_sources(
    proposal: OnboardingPlacementProposal,
    owner_source_specs: Iterable[str],
) -> tuple[PlacementReviewSource, ...]:
    result: list[PlacementReviewSource] = []
    seen: set[tuple[str, str]] = set()
    for reuse in proposal.source_reuses:
        pair = (reuse.target_node_key, reuse.source_node_id)
        seen.add(pair)
        result.append(
            PlacementReviewSource(
                review_id=reuse.id,
                origin="evidence-derived",
                target_node_key=reuse.target_node_key,
                decision="pending",
                source_node_id=reuse.source_node_id,
                source_name=reuse.source_name,
                source_version=reuse.source_version,
                source_normalized_digest=reuse.source_normalized_digest,
                source_package_digest=reuse.source_package_digest,
                review_note="",
                proposal_id=reuse.id,
            )
        )

    packages = _package_by_id(proposal)
    node_keys = {node.key for node in proposal.structure.nodes}
    for spec in owner_source_specs:
        if "=" not in spec:
            raise _error("--owner-source must be TARGET_NODE_KEY=SOURCE_NODE_ID")
        target, source_id = (part.strip() for part in spec.split("=", 1))
        if target not in node_keys:
            raise _error(f"owner-selected Source references unknown target Node {target}")
        package = packages.get(source_id)
        if package is None:
            raise _error(f"owner-selected Source {source_id} was not supplied in the exact catalog")
        pair = (target, source_id)
        if pair in seen:
            continue
        seen.add(pair)
        result.append(
            PlacementReviewSource(
                review_id="O-" + uuid.uuid4().hex[:10].upper(),
                origin="owner-selected",
                target_node_key=target,
                decision="pending",
                source_node_id=source_id,
                source_name=package.metadata.name,
                source_version=package.metadata.version,
                source_normalized_digest=package.normalized_digest,
                source_package_digest=package.package_digest,
                review_note="",
                proposal_id=None,
            )
        )
    return tuple(result)


def render_placement_review(
    proposal: OnboardingPlacementProposal,
    snapshot_root: Path,
    *,
    owner_source_specs: Iterable[str] = (),
) -> str:
    snapshot = load_evidence_snapshot(snapshot_root)
    review_items = tuple(
        PlacementReviewItem(
            proposal_id=item.id,
            authoring_id=_fresh_authoring_id(),
            title=item.title,
            decision="pending",
            destination_node_key=item.destination_node_key,
            kind=item.kind,
            action=item.action,
            payload=dict(item.payload),
            review_note="",
        )
        for item in proposal.items
    )
    sources = _initial_sources(proposal, owner_source_specs)
    lines = [
        "# ContextCanon onboarding placement review",
        "",
        "Edit this file directly. **Destination comes first** because future ownership is the primary review decision. Change `Decision`, destination, kind/action, title, or maintained wording where necessary. Evidence and proposal rationale below each item are review support, not a second decision file.",
        "",
        "Decisions are `pending`, `accept`, or `reject`. ContextCanon never publishes a pending review.",
        "",
        "<!-- contextcanon-placement-review",
        f"schema: {PLACEMENT_REVIEW_SCHEMA}",
        f"evidence_digest: {proposal.evidence_digest}",
        f"structure_digest: {proposal.structure_digest}",
        f"proposal_digest: {proposal.proposal_digest}",
        "-->",
        "",
        "# Placement findings",
        "",
    ]
    by_id = {item.id: item for item in proposal.items}
    for review_item in review_items:
        lines.extend(_render_item(by_id[review_item.proposal_id], review_item, proposal, snapshot))

    lines.extend(["# Reusable Sources", ""])
    if not sources:
        lines.append("No reusable Source is currently proposed or owner-selected.")
        lines.append("")
    else:
        nodes = {node.key: node for node in proposal.structure.nodes}
        by_reuse = {reuse.id: reuse for reuse in proposal.source_reuses}
        for source in sources:
            target = nodes[source.target_node_key]
            lines.extend(
                [
                    f"## Source {source.review_id} — {source.source_name}",
                    f'<!-- cc:placement-source id="{source.review_id}" origin="{source.origin}" source-id="{source.source_node_id}" version="{source.source_version}" normalized-digest="{source.source_normalized_digest}" package-digest="{source.source_package_digest}" -->',
                    "",
                    f"Destination: `{target.key}` — **{target.name}** (`{target.path}`)",
                    f"Decision: `{source.decision}`",
                    f"Origin: `{source.origin}`",
                    f"Review note: {source.review_note or '-'}",
                    "",
                    f"Exact package: `{source.source_version}` · `{source.source_package_digest}`",
                    "",
                ]
            )
            if source.proposal_id is not None:
                reuse = by_reuse[source.proposal_id]
                lines.extend(["Proposal rationale:", "", reuse.reason, "", "Evidence:", ""])
                for reference in reuse.evidence:
                    lines.extend(_evidence_excerpt(reference, snapshot))
                lines.append("")
            else:
                lines.extend(
                    [
                        "This Source was selected explicitly by the project owner from the supplied exact catalog. It is design input, not a claim derived from frozen project Evidence.",
                        "",
                    ]
                )
    return "\n".join(lines).rstrip() + "\n"


def _section_blocks(lines: list[str], prefix: str) -> list[tuple[int, int]]:
    starts = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    result: list[tuple[int, int]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(lines)
        result.append((start, end))
    return result


def _find_line(block: list[str], prefix: str, label: str) -> str:
    matches = [line[len(prefix) :] for line in block if line.startswith(prefix)]
    if len(matches) != 1:
        raise _error(f"{label} must appear exactly once")
    return matches[0].strip()


def _simple_value(block: list[str], label: str) -> str:
    line = next((line for line in block if line.startswith(label + ":")), None)
    if line is None:
        raise _error(f"missing {label}")
    match = _SIMPLE_VALUE_RE.match(line)
    if match is None or match.group("label") != label:
        raise _error(f"{label} must use backtick value syntax")
    return match.group("value")


def _destination(block: list[str], *, allow_none: bool) -> str | None:
    line = next((line for line in block if line.startswith("Destination:")), None)
    if line is None:
        raise _error("missing Destination")
    if line == "Destination: none / outside Node authoring" and allow_none:
        return None
    match = _DESTINATION_RE.match(line)
    if match is None:
        raise _error("Destination must begin with a backtick Node key")
    return match.group("key")


def _paths(value: str, label: str) -> list[str]:
    paths = _PATH_RE.findall(value)
    if not paths:
        raise _error(f"{label} must contain one or more backtick paths")
    if len(paths) != len(set(paths)):
        raise _error(f"{label} contains duplicate paths")
    return paths


def _payload_from_block(kind: str, block: list[str]) -> dict[str, object]:
    if kind == "rule":
        return {
            "statement": _find_line(block, "Statement: ", "Statement"),
            "why": _find_line(block, "Why: ", "Why"),
            "wording_origin": _simple_value(block, "Wording"),
        }
    if kind in {"overview", "state", "plan"}:
        return {
            "text": _find_line(block, "Text: ", "Text"),
            "wording_origin": _simple_value(block, "Wording"),
        }
    if kind == "topic-resource":
        return {
            "condition": _find_line(block, "Condition: ", "Condition"),
            "resource_paths": _paths(_find_line(block, "Resources: ", "Resources"), "Resources"),
        }
    if kind == "ordinary-documentation":
        return {
            "document_paths": _paths(_find_line(block, "Documents: ", "Documents"), "Documents"),
            "reason": _find_line(block, "Reason: ", "Reason"),
        }
    if kind == "authority-mapping":
        return {
            "authority_paths": _paths(_find_line(block, "Authorities: ", "Authorities"), "Authorities"),
            "mapping": _find_line(block, "Mapping: ", "Mapping"),
            "wording_origin": _simple_value(block, "Wording"),
        }
    if kind == "unresolved":
        return {"question": _find_line(block, "Question: ", "Question")}
    raise _error(f"unsupported kind {kind!r}")


def _validate_item_edit(
    item_id: str,
    kind: str,
    action: str,
    destination: str | None,
    payload: dict[str, object],
    proposal: OnboardingPlacementProposal,
    snapshot: EvidenceSnapshot,
) -> None:
    if kind not in PLACEMENT_KINDS:
        raise _error(f"item {item_id} has unsupported Kind {kind!r}")
    if action not in PLACEMENT_ACTIONS:
        raise _error(f"item {item_id} has unsupported Action {action!r}")
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
    if action not in allowed_actions[kind]:
        expected = ", ".join(sorted(allowed_actions[kind]))
        raise _error(f"item {item_id} Kind {kind} must use Action {expected}")
    requires_destination = kind in {"overview", "rule", "topic-resource", "state", "plan", "authority-mapping"}
    if requires_destination and destination is None:
        raise _error(f"item {item_id} Kind {kind} requires a Destination")
    evidence_paths = set(snapshot.by_path)
    if kind in {"overview", "state", "plan"}:
        if payload.get("wording_origin") not in WORDING_ORIGINS or not str(payload.get("text", "")).strip():
            raise _error(f"item {item_id} has invalid {kind} maintained meaning")
    elif kind == "rule":
        if payload.get("wording_origin") not in WORDING_ORIGINS:
            raise _error(f"item {item_id} has invalid Rule wording origin")
        if not str(payload.get("statement", "")).strip() or not str(payload.get("why", "")).strip():
            raise _error(f"item {item_id} Rule requires Statement and Why")
    elif kind == "topic-resource":
        if not str(payload.get("condition", "")).strip():
            raise _error(f"item {item_id} Topic requires Condition")
        for path in payload.get("resource_paths", []):
            if path not in evidence_paths:
                raise _error(f"item {item_id} Resource path is not frozen Evidence: {path}")
    elif kind == "ordinary-documentation":
        for path in payload.get("document_paths", []):
            if path not in evidence_paths:
                raise _error(f"item {item_id} document path is not frozen Evidence: {path}")
    elif kind == "authority-mapping":
        if payload.get("wording_origin") not in WORDING_ORIGINS:
            raise _error(f"item {item_id} has invalid mapping wording origin")
        fixed = set(proposal.structure.fixed_markdown)
        for path in payload.get("authority_paths", []):
            if path not in fixed:
                raise _error(f"item {item_id} authority is not fixed Markdown in the accepted structure: {path}")
    elif kind == "unresolved" and not str(payload.get("question", "")).strip():
        raise _error(f"item {item_id} unresolved finding requires Question")


def _normalize_review(
    proposal: OnboardingPlacementProposal,
    items: tuple[PlacementReviewItem, ...],
    sources: tuple[PlacementReviewSource, ...],
) -> OnboardingPlacementReview:
    value = {
        "schema": PLACEMENT_REVIEW_SCHEMA,
        "evidence_digest": proposal.evidence_digest,
        "structure_digest": proposal.structure_digest,
        "proposal_digest": proposal.proposal_digest,
        "items": [item.to_dict() for item in items],
        "sources": [source.to_dict() for source in sources],
    }
    return OnboardingPlacementReview(
        evidence_digest=proposal.evidence_digest,
        structure_digest=proposal.structure_digest,
        proposal_digest=proposal.proposal_digest,
        items=items,
        sources=sources,
        review_digest=_digest(value),
    )


def load_placement_review(
    path: Path, proposal: OnboardingPlacementProposal, snapshot_root: Path
) -> OnboardingPlacementReview:
    try:
        text = path.resolve().read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContextCanonError(f"Missing onboarding placement review: {path}") from exc
    except UnicodeDecodeError as exc:
        raise _error("placement.md is not valid UTF-8") from exc
    header = _HEADER_RE.search(text)
    if header is None:
        raise _error("placement.md is missing its ContextCanon binding header")
    if header.group("schema") != PLACEMENT_REVIEW_SCHEMA:
        raise _error(f"unsupported review schema {header.group('schema')!r}")
    if header.group("evidence") != proposal.evidence_digest:
        raise _error("evidence_digest does not match the proposal")
    if header.group("structure") != proposal.structure_digest:
        raise _error("structure_digest does not match the proposal")
    if header.group("proposal") != proposal.proposal_digest:
        raise _error(
            "proposal_digest does not match the existing human placement review; create a new review path for a new LLM candidate rather than overwriting human edits"
        )

    snapshot = load_evidence_snapshot(snapshot_root)
    lines = text.splitlines()
    proposal_by_id = {item.id: item for item in proposal.items}
    node_keys = {node.key for node in proposal.structure.nodes}
    parsed_items: list[PlacementReviewItem] = []
    seen: set[str] = set()
    for start, end in _section_blocks(lines, "## "):
        heading = _ITEM_HEADING_RE.match(lines[start])
        if heading is None:
            continue
        item_id = heading.group("id")
        if item_id not in proposal_by_id:
            raise _error(f"placement.md contains unknown proposal item {item_id}")
        if item_id in seen:
            raise _error(f"placement.md contains duplicate item {item_id}")
        seen.add(item_id)
        block = lines[start:end]
        comment = next((line for line in block if _ITEM_COMMENT_RE.match(line)), None)
        if comment is None:
            raise _error(f"item {item_id} is missing its stable authoring-id comment")
        attrs = _ITEM_COMMENT_RE.match(comment)
        assert attrs is not None
        if attrs.group("id") != item_id:
            raise _error(f"item {item_id} comment ID differs from heading")
        decision = _simple_value(block, "Decision")
        if decision not in REVIEW_DECISIONS:
            raise _error(f"item {item_id} Decision must be pending, accept, or reject")
        kind = _simple_value(block, "Kind")
        action = _simple_value(block, "Action")
        destination = _destination(block, allow_none=True)
        if destination is not None and destination not in node_keys:
            raise _error(f"item {item_id} references unknown destination Node {destination}")
        payload = _payload_from_block(kind, block)
        _validate_item_edit(item_id, kind, action, destination, payload, proposal, snapshot)
        note = _find_line(block, "Review note: ", "Review note")
        parsed_items.append(
            PlacementReviewItem(
                proposal_id=item_id,
                authoring_id=attrs.group("authoring"),
                title=heading.group("title").strip(),
                decision=decision,
                destination_node_key=destination,
                kind=kind,
                action=action,
                payload=payload,
                review_note="" if note == "-" else note,
            )
        )
    if seen != set(proposal_by_id):
        missing = sorted(set(proposal_by_id) - seen)
        raise _error(f"placement.md is missing proposal items: {', '.join(missing)}")

    packages = _package_by_id(proposal)
    parsed_sources: list[PlacementReviewSource] = []
    source_ids: set[str] = set()
    for start, end in _section_blocks(lines, "## Source "):
        heading = _SOURCE_HEADING_RE.match(lines[start])
        if heading is None:
            continue
        block = lines[start:end]
        comment = next((line for line in block if _SOURCE_COMMENT_RE.match(line)), None)
        if comment is None:
            raise _error(f"Source {heading.group('id')} is missing exact package metadata")
        attrs = _SOURCE_COMMENT_RE.match(comment)
        assert attrs is not None
        review_id = heading.group("id")
        if attrs.group("id") != review_id or review_id in source_ids:
            raise _error(f"duplicate or mismatched Source review ID {review_id}")
        source_ids.add(review_id)
        source_id = attrs.group("source_id")
        package = packages.get(source_id)
        if package is None:
            raise _error(f"Source {review_id} names package {source_id} not supplied in the exact catalog")
        expected = (
            package.metadata.version,
            package.normalized_digest,
            package.package_digest,
            package.metadata.name,
        )
        actual = (
            attrs.group("version"),
            attrs.group("normalized"),
            attrs.group("package"),
            heading.group("title").strip(),
        )
        if actual != expected:
            raise _error(f"Source {review_id} exact package identity does not match the supplied catalog")
        origin = attrs.group("origin")
        if origin not in {"evidence-derived", "owner-selected"}:
            raise _error(f"Source {review_id} has unsupported origin {origin!r}")
        target = _destination(block, allow_none=False)
        assert target is not None
        if target not in node_keys:
            raise _error(f"Source {review_id} references unknown destination Node {target}")
        decision = _simple_value(block, "Decision")
        if decision not in REVIEW_DECISIONS:
            raise _error(f"Source {review_id} Decision must be pending, accept, or reject")
        proposal_id = review_id if origin == "evidence-derived" else None
        if proposal_id is not None and proposal_id not in {reuse.id for reuse in proposal.source_reuses}:
            raise _error(f"Source {review_id} is not present in the placement proposal")
        note = _find_line(block, "Review note: ", "Review note")
        parsed_sources.append(
            PlacementReviewSource(
                review_id=review_id,
                origin=origin,
                target_node_key=target,
                decision=decision,
                source_node_id=source_id,
                source_name=package.metadata.name,
                source_version=package.metadata.version,
                source_normalized_digest=package.normalized_digest,
                source_package_digest=package.package_digest,
                review_note="" if note == "-" else note,
                proposal_id=proposal_id,
            )
        )

    expected_evidence_sources = {reuse.id for reuse in proposal.source_reuses}
    actual_evidence_sources = {source.review_id for source in parsed_sources if source.origin == "evidence-derived"}
    if actual_evidence_sources != expected_evidence_sources:
        missing = sorted(expected_evidence_sources - actual_evidence_sources)
        raise _error(f"placement.md is missing Evidence-derived Source reviews: {', '.join(missing)}")
    return _normalize_review(proposal, tuple(parsed_items), tuple(parsed_sources))


def create_or_load_placement_review(
    path: Path,
    proposal: OnboardingPlacementProposal,
    snapshot_root: Path,
    *,
    owner_source_specs: Iterable[str] = (),
) -> tuple[OnboardingPlacementReview, bool]:
    path = path.resolve()
    if path.exists():
        if tuple(owner_source_specs):
            raise _error(
                "--owner-source is only used when placement.md is first created; edit the existing human review instead of silently changing it"
            )
        return load_placement_review(path, proposal, snapshot_root), False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_placement_review(proposal, snapshot_root, owner_source_specs=owner_source_specs),
        encoding="utf-8",
        newline="\n",
    )
    return load_placement_review(path, proposal, snapshot_root), True
