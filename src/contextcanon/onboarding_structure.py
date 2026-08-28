from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .onboarding_proposal import EvidenceReference, EvidenceSnapshot, load_evidence_snapshot
from .parser import ContextCanonError


STRUCTURE_PROPOSAL_SCHEMA = "contextcanon/onboarding-structure-proposal/v0"
STRUCTURE_MARKDOWN_SCHEMA = "contextcanon/onboarding-structure-markdown/v0"
CONFIDENCE_LEVELS = {"high", "medium", "low"}
NODE_LIFECYCLES = {"current", "reserved"}
KNOWLEDGE_BODY_KINDS = {
    "project-documentation",
    "authoritative-reference",
    "imported-corpus",
}
_ITEM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TREE_LINE_RE = re.compile(
    r"^(?P<indent> *)- \*\*(?P<name>.+?)\*\* \(`(?P<path>[^`]+)`\)"
    r"(?: \[(?P<lifecycle>current|reserved)\])?"
    r"(?: <!-- cc:key=(?P<key>[A-Za-z0-9][A-Za-z0-9._-]{0,63}) -->)?$"
)
_HEADER_RE = re.compile(
    r"<!-- contextcanon-structure\n"
    r"schema: (?P<schema>[^\n]+)\n"
    r"evidence_digest: (?P<evidence>[0-9a-f]{64})\n"
    r"proposal_digest: (?P<proposal>[0-9a-f]{64})\n"
    r"-->"
)
_TREE_START = "<!-- contextcanon-node-tree:start -->"
_TREE_END = "<!-- contextcanon-node-tree:end -->"


@dataclass(frozen=True)
class StructureNodeProposal:
    key: str
    name: str
    parent_key: str | None
    suggested_path: str
    lifecycle: str
    purpose: str
    rationale: str
    confidence: str
    evidence: tuple[EvidenceReference, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "parent_key": self.parent_key,
            "suggested_path": self.suggested_path,
            "lifecycle": self.lifecycle,
            "purpose": self.purpose,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "evidence": [reference.to_dict() for reference in self.evidence],
        }


@dataclass(frozen=True)
class StructureKnowledgeBody:
    key: str
    kind: str
    name: str
    suggested_node_key: str | None
    paths: tuple[str, ...]
    purpose: str
    rationale: str
    confidence: str
    evidence: tuple[EvidenceReference, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "kind": self.kind,
            "name": self.name,
            "suggested_node_key": self.suggested_node_key,
            "paths": list(self.paths),
            "purpose": self.purpose,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "evidence": [reference.to_dict() for reference in self.evidence],
        }


@dataclass(frozen=True)
class StructureSourceReuse:
    key: str
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
            "key": self.key,
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
class OnboardingStructureProposal:
    evidence_digest: str
    nodes: tuple[StructureNodeProposal, ...]
    knowledge_bodies: tuple[StructureKnowledgeBody, ...]
    source_reuses: tuple[StructureSourceReuse, ...]
    proposal_digest: str

    @property
    def nodes_by_key(self) -> dict[str, StructureNodeProposal]:
        return {node.key: node for node in self.nodes}

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": STRUCTURE_PROPOSAL_SCHEMA,
            "evidence_digest": self.evidence_digest,
            "nodes": [node.to_dict() for node in self.nodes],
            "knowledge_bodies": [body.to_dict() for body in self.knowledge_bodies],
            "source_reuses": [reuse.to_dict() for reuse in self.source_reuses],
        }


@dataclass(frozen=True)
class HumanStructureNode:
    key: str
    name: str
    path: str
    lifecycle: str
    parent_key: str | None
    proposal_key: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "path": self.path,
            "lifecycle": self.lifecycle,
            "parent_key": self.parent_key,
            "proposal_key": self.proposal_key,
        }


@dataclass(frozen=True)
class HumanStructurePlan:
    evidence_digest: str
    proposal_digest: str
    nodes: tuple[HumanStructureNode, ...]
    structure_digest: str



def _error(message: str) -> ContextCanonError:
    return ContextCanonError(f"Invalid onboarding structure: {message}")


def _canonical_digest(value: dict[str, object]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _expect_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _error(f"{label} must be a JSON object")
    return value


def _expect_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) == expected:
        return
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    detail: list[str] = []
    if unknown:
        detail.append(f"unknown fields: {', '.join(unknown)}")
    if missing:
        detail.append(f"missing fields: {', '.join(missing)}")
    raise _error(f"{label} has {'; '.join(detail)}")


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(f"{label} must be a non-empty string")
    return value.strip()


def _optional_key(value: object, label: str) -> str | None:
    if value is None:
        return None
    result = _nonempty_string(value, label)
    if not _ITEM_ID_RE.fullmatch(result):
        raise _error(f"{label} has invalid format: {result!r}")
    return result


def _key(value: object, label: str) -> str:
    result = _nonempty_string(value, label)
    if not _ITEM_ID_RE.fullmatch(result):
        raise _error(f"{label} has invalid format: {result!r}")
    return result


def _safe_relative_path(value: object, label: str) -> str:
    path = _nonempty_string(value, label)
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != path:
        raise _error(f"{label} must be a normalized repository-relative POSIX path")
    return path


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


def _parse_reference(raw: object, label: str, snapshot: EvidenceSnapshot) -> EvidenceReference:
    reference = _expect_object(raw, label)
    expected = {"path", "sha256", "start_line", "end_line"}
    _expect_exact_keys(reference, expected, label)
    path = _safe_relative_path(reference["path"], f"{label}.path")
    entry = snapshot.by_path.get(path)
    if entry is None:
        raise _error(f"{label} references evidence not present in snapshot: {path}")
    if reference["sha256"] != entry.sha256:
        raise _error(f"{label} evidence hash does not match snapshot: {path}")
    start = reference["start_line"]
    end = reference["end_line"]
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        raise _error(f"{label}.start_line must be a positive integer")
    if not isinstance(end, int) or isinstance(end, bool) or end < start:
        raise _error(f"{label}.end_line must be >= start_line")
    if end > entry.line_count:
        raise _error(f"{label} range {start}-{end} exceeds {path} line count {entry.line_count}")
    return EvidenceReference(path, entry.sha256, start, end)


def _parse_references(raw: object, label: str, snapshot: EvidenceSnapshot) -> tuple[EvidenceReference, ...]:
    if not isinstance(raw, list) or not raw:
        raise _error(f"{label} must be a non-empty list")
    return tuple(_parse_reference(item, f"{label}[{index}]", snapshot) for index, item in enumerate(raw))


def _confidence(value: object, label: str) -> str:
    if value not in CONFIDENCE_LEVELS:
        raise _error(f"{label} must be high, medium, or low")
    return str(value)


def _validate_node_graph(nodes: tuple[StructureNodeProposal, ...]) -> None:
    if not nodes:
        raise _error("nodes must contain one proposed root Node")
    by_key = {node.key: node for node in nodes}
    if len(by_key) != len(nodes):
        raise _error("node keys must be unique")
    paths = [node.suggested_path for node in nodes]
    if len(set(paths)) != len(paths):
        raise _error("suggested Node paths must be unique")
    roots = [node for node in nodes if node.parent_key is None]
    if len(roots) != 1:
        raise _error("nodes must contain exactly one primary root")
    root = roots[0]
    if root.suggested_path != ".":
        raise _error("the primary root Node must use suggested_path '.'")

    children: dict[str, list[str]] = {key: [] for key in by_key}
    for node in nodes:
        if node.parent_key is None:
            continue
        parent = by_key.get(node.parent_key)
        if parent is None:
            raise _error(f"node {node.key} references unknown parent_key {node.parent_key}")
        children[parent.key].append(node.key)
        parent_path = parent.suggested_path
        expected_prefix = "" if parent_path == "." else parent_path.rstrip("/") + "/"
        if node.suggested_path == "." or (
            expected_prefix and not node.suggested_path.startswith(expected_prefix)
        ):
            raise _error(
                f"node {node.key} path {node.suggested_path!r} must be nested under parent path {parent_path!r}"
            )

    visited: set[str] = set()
    active: set[str] = set()

    def walk(key: str) -> None:
        if key in active:
            raise _error(f"node hierarchy contains a cycle at {key}")
        if key in visited:
            return
        active.add(key)
        for child in children[key]:
            walk(child)
        active.remove(key)
        visited.add(key)

    walk(root.key)
    if visited != set(by_key):
        missing = sorted(set(by_key) - visited)
        raise _error(f"node hierarchy contains nodes not reachable from the primary root: {', '.join(missing)}")


def load_onboarding_structure_proposal(proposal_path: Path, snapshot_root: Path) -> OnboardingStructureProposal:
    snapshot = load_evidence_snapshot(snapshot_root)
    raw = _read_json(proposal_path.resolve(), "onboarding structure proposal")
    expected_top = {"schema", "evidence_digest", "nodes", "knowledge_bodies", "source_reuses"}
    _expect_exact_keys(raw, expected_top, "proposal")
    if raw["schema"] != STRUCTURE_PROPOSAL_SCHEMA:
        raise _error(f"unsupported schema {raw['schema']!r}")
    if raw["evidence_digest"] != snapshot.evidence_digest:
        raise _error("evidence_digest does not match the supplied evidence snapshot")

    raw_nodes = raw["nodes"]
    if not isinstance(raw_nodes, list):
        raise _error("nodes must be a list")
    nodes: list[StructureNodeProposal] = []
    for index, raw_node in enumerate(raw_nodes):
        node = _expect_object(raw_node, f"nodes[{index}]")
        expected = {
            "key",
            "name",
            "parent_key",
            "suggested_path",
            "lifecycle",
            "purpose",
            "rationale",
            "confidence",
            "evidence",
        }
        _expect_exact_keys(node, expected, f"nodes[{index}]")
        lifecycle = node["lifecycle"]
        if lifecycle not in NODE_LIFECYCLES:
            raise _error(f"nodes[{index}].lifecycle must be current or reserved")
        nodes.append(
            StructureNodeProposal(
                key=_key(node["key"], f"nodes[{index}].key"),
                name=_nonempty_string(node["name"], f"nodes[{index}].name"),
                parent_key=_optional_key(node["parent_key"], f"nodes[{index}].parent_key"),
                suggested_path=_safe_relative_path(node["suggested_path"], f"nodes[{index}].suggested_path"),
                lifecycle=str(lifecycle),
                purpose=_nonempty_string(node["purpose"], f"nodes[{index}].purpose"),
                rationale=_nonempty_string(node["rationale"], f"nodes[{index}].rationale"),
                confidence=_confidence(node["confidence"], f"nodes[{index}].confidence"),
                evidence=_parse_references(node["evidence"], f"nodes[{index}].evidence", snapshot),
            )
        )
    node_tuple = tuple(nodes)
    _validate_node_graph(node_tuple)
    node_keys = {node.key for node in node_tuple}

    raw_bodies = raw["knowledge_bodies"]
    if not isinstance(raw_bodies, list):
        raise _error("knowledge_bodies must be a list")
    bodies: list[StructureKnowledgeBody] = []
    for index, raw_body in enumerate(raw_bodies):
        body = _expect_object(raw_body, f"knowledge_bodies[{index}]")
        expected = {
            "key",
            "kind",
            "name",
            "suggested_node_key",
            "paths",
            "purpose",
            "rationale",
            "confidence",
            "evidence",
        }
        _expect_exact_keys(body, expected, f"knowledge_bodies[{index}]")
        kind = body["kind"]
        if kind not in KNOWLEDGE_BODY_KINDS:
            raise _error(
                f"knowledge_bodies[{index}].kind must be project-documentation, authoritative-reference, or imported-corpus"
            )
        suggested = _optional_key(body["suggested_node_key"], f"knowledge_bodies[{index}].suggested_node_key")
        if suggested is not None and suggested not in node_keys:
            raise _error(f"knowledge body {body['key']} references unknown suggested_node_key {suggested}")
        raw_paths = body["paths"]
        if not isinstance(raw_paths, list):
            raise _error(f"knowledge_bodies[{index}].paths must be a list")
        paths: list[str] = []
        for path_index, raw_path in enumerate(raw_paths):
            path = _safe_relative_path(raw_path, f"knowledge_bodies[{index}].paths[{path_index}]")
            if path not in snapshot.by_path:
                raise _error(f"knowledge body path is not in evidence snapshot: {path}")
            paths.append(path)
        if len(set(paths)) != len(paths):
            raise _error(f"knowledge_bodies[{index}].paths contains duplicates")
        bodies.append(
            StructureKnowledgeBody(
                key=_key(body["key"], f"knowledge_bodies[{index}].key"),
                kind=str(kind),
                name=_nonempty_string(body["name"], f"knowledge_bodies[{index}].name"),
                suggested_node_key=suggested,
                paths=tuple(paths),
                purpose=_nonempty_string(body["purpose"], f"knowledge_bodies[{index}].purpose"),
                rationale=_nonempty_string(body["rationale"], f"knowledge_bodies[{index}].rationale"),
                confidence=_confidence(body["confidence"], f"knowledge_bodies[{index}].confidence"),
                evidence=_parse_references(body["evidence"], f"knowledge_bodies[{index}].evidence", snapshot),
            )
        )

    raw_reuses = raw["source_reuses"]
    if not isinstance(raw_reuses, list):
        raise _error("source_reuses must be a list")
    reuses: list[StructureSourceReuse] = []
    for index, raw_reuse in enumerate(raw_reuses):
        reuse = _expect_object(raw_reuse, f"source_reuses[{index}]")
        expected = {
            "key",
            "target_node_key",
            "source_node_id",
            "source_name",
            "source_version",
            "source_normalized_digest",
            "source_package_digest",
            "reason",
            "confidence",
            "evidence",
        }
        _expect_exact_keys(reuse, expected, f"source_reuses[{index}]")
        target = _key(reuse["target_node_key"], f"source_reuses[{index}].target_node_key")
        if target not in node_keys:
            raise _error(f"source reuse {reuse['key']} references unknown target_node_key {target}")
        normalized_digest = reuse["source_normalized_digest"]
        package_digest = reuse["source_package_digest"]
        if not isinstance(normalized_digest, str) or not _SHA256_RE.fullmatch(normalized_digest):
            raise _error(f"source_reuses[{index}].source_normalized_digest must be a lowercase SHA-256")
        if not isinstance(package_digest, str) or not _SHA256_RE.fullmatch(package_digest):
            raise _error(f"source_reuses[{index}].source_package_digest must be a lowercase SHA-256")
        reuses.append(
            StructureSourceReuse(
                key=_key(reuse["key"], f"source_reuses[{index}].key"),
                target_node_key=target,
                source_node_id=_nonempty_string(reuse["source_node_id"], f"source_reuses[{index}].source_node_id"),
                source_name=_nonempty_string(reuse["source_name"], f"source_reuses[{index}].source_name"),
                source_version=_nonempty_string(reuse["source_version"], f"source_reuses[{index}].source_version"),
                source_normalized_digest=normalized_digest,
                source_package_digest=package_digest,
                reason=_nonempty_string(reuse["reason"], f"source_reuses[{index}].reason"),
                confidence=_confidence(reuse["confidence"], f"source_reuses[{index}].confidence"),
                evidence=_parse_references(reuse["evidence"], f"source_reuses[{index}].evidence", snapshot),
            )
        )

    all_keys = [node.key for node in node_tuple] + [body.key for body in bodies] + [reuse.key for reuse in reuses]
    if len(all_keys) != len(set(all_keys)):
        raise _error("proposal keys must be unique across nodes, knowledge_bodies, and source_reuses")

    normalized = {
        "schema": STRUCTURE_PROPOSAL_SCHEMA,
        "evidence_digest": snapshot.evidence_digest,
        "nodes": [node.to_dict() for node in node_tuple],
        "knowledge_bodies": [body.to_dict() for body in bodies],
        "source_reuses": [reuse.to_dict() for reuse in reuses],
    }
    return OnboardingStructureProposal(
        evidence_digest=snapshot.evidence_digest,
        nodes=node_tuple,
        knowledge_bodies=tuple(bodies),
        source_reuses=tuple(reuses),
        proposal_digest=_canonical_digest(normalized),
    )


def _node_depths(proposal: OnboardingStructureProposal) -> dict[str, int]:
    by_key = proposal.nodes_by_key
    result: dict[str, int] = {}

    def depth(node: StructureNodeProposal) -> int:
        if node.key in result:
            return result[node.key]
        value = 0 if node.parent_key is None else depth(by_key[node.parent_key]) + 1
        result[node.key] = value
        return value

    for node in proposal.nodes:
        depth(node)
    return result


def _render_evidence(reference: EvidenceReference, snapshot: EvidenceSnapshot) -> list[str]:
    lines = [f"- `{reference.path}` lines {reference.start_line}-{reference.end_line} · `{reference.sha256}`"]
    evidence_file = snapshot.root / "evidence" / Path(*PurePosixPath(reference.path).parts)
    text = evidence_file.read_text(encoding="utf-8").splitlines()
    excerpt = text[reference.start_line - 1 : reference.end_line]
    lines.append("  ```text")
    for offset, content in enumerate(excerpt, start=reference.start_line):
        lines.append(f"  {offset:>5}: {content}")
    lines.append("  ```")
    return lines


def render_structure_markdown(proposal: OnboardingStructureProposal, snapshot: EvidenceSnapshot) -> str:
    depths = _node_depths(proposal)
    children: dict[str | None, list[StructureNodeProposal]] = {}
    for node in proposal.nodes:
        children.setdefault(node.parent_key, []).append(node)

    lines = [
        "# ContextCanon onboarding structure",
        "",
        "This file is intentionally human-editable. Edit the Node tree below; indentation defines the primary parent/child hierarchy.",
        "Keep one root at path `.`. You may rename, move, remove, or add proposed Nodes. Add `[reserved]` for an explicitly planned area that should get a place before implementation exists.",
        "The `cc:key` comments bind lines back to the LLM proposal. A newly added line may omit the comment; ContextCanon will assign a review-local key when it reads the file.",
        "",
        "<!-- contextcanon-structure",
        f"schema: {STRUCTURE_MARKDOWN_SCHEMA}",
        f"evidence_digest: {proposal.evidence_digest}",
        f"proposal_digest: {proposal.proposal_digest}",
        "-->",
        "",
        "## Node tree",
        "",
        _TREE_START,
    ]

    def render_children(parent: str | None) -> None:
        for node in children.get(parent, []):
            indent = "  " * depths[node.key]
            lifecycle = " [reserved]" if node.lifecycle == "reserved" else ""
            lines.append(
                f"{indent}- **{node.name}** (`{node.suggested_path}`){lifecycle} <!-- cc:key={node.key} -->"
            )
            render_children(node.key)

    render_children(None)
    lines.extend([_TREE_END, "", "## Proposed non-Node knowledge bodies", ""])
    if proposal.knowledge_bodies:
        for body in proposal.knowledge_bodies:
            target = body.suggested_node_key or "unassigned"
            path_text = ", ".join(f"`{path}`" for path in body.paths) if body.paths else "no local snapshot path"
            lines.append(
                f"- `{body.key}` · **{body.name}** · `{body.kind}` · suggested Node `{target}` · {path_text}"
            )
    else:
        lines.append("None proposed.")

    lines.extend(["", "## Proposed reusable Source matches", ""])
    if proposal.source_reuses:
        for reuse in proposal.source_reuses:
            lines.append(
                f"- `{reuse.key}` · **{reuse.source_name}** `{reuse.source_version}` → Node `{reuse.target_node_key}` · package `{reuse.source_package_digest}`"
            )
    else:
        lines.append("None proposed.")

    lines.extend(["", "## Proposal details", "", "The details below explain the original LLM proposal and are not parsed when you edit the Node tree.", ""])
    for node in proposal.nodes:
        lines.extend(
            [
                f"### {node.key} — {node.name}",
                "",
                f"Purpose: {node.purpose}",
                "",
                f"Why this grouping: {node.rationale}",
                "",
                f"Confidence: `{node.confidence}`",
                "",
                "Evidence:",
            ]
        )
        for reference in node.evidence:
            lines.extend(_render_evidence(reference, snapshot))
        lines.append("")

    for body in proposal.knowledge_bodies:
        lines.extend(
            [
                f"### {body.key} — {body.name}",
                "",
                f"Kind: `{body.kind}`",
                "",
                f"Purpose: {body.purpose}",
                "",
                f"Why it stays outside the Node tree: {body.rationale}",
                "",
                f"Confidence: `{body.confidence}`",
                "",
                "Evidence:",
            ]
        )
        for reference in body.evidence:
            lines.extend(_render_evidence(reference, snapshot))
        lines.append("")

    for reuse in proposal.source_reuses:
        lines.extend(
            [
                f"### {reuse.key} — reuse {reuse.source_name}",
                "",
                f"Target Node: `{reuse.target_node_key}`",
                "",
                reuse.reason,
                "",
                f"Confidence: `{reuse.confidence}`",
                "",
                "Evidence:",
            ]
        )
        for reference in reuse.evidence:
            lines.extend(_render_evidence(reference, snapshot))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _human_key(name: str, path: str, parent_key: str | None, lifecycle: str) -> str:
    payload = f"{parent_key or ''}\0{name}\0{path}\0{lifecycle}".encode("utf-8")
    return "H-" + hashlib.sha256(payload).hexdigest()[:12]


def load_structure_markdown(
    structure_path: Path,
    proposal: OnboardingStructureProposal,
) -> HumanStructurePlan:
    try:
        text = structure_path.resolve().read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContextCanonError(f"Missing onboarding structure Markdown: {structure_path}") from exc
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"Onboarding structure Markdown is not valid UTF-8: {structure_path}") from exc

    header = _HEADER_RE.search(text)
    if header is None:
        raise _error("structure Markdown is missing its ContextCanon binding header")
    if header.group("schema") != STRUCTURE_MARKDOWN_SCHEMA:
        raise _error(f"unsupported structure Markdown schema {header.group('schema')!r}")
    if header.group("evidence") != proposal.evidence_digest:
        raise _error("structure Markdown evidence_digest does not match the proposal")
    if header.group("proposal") != proposal.proposal_digest:
        raise _error("structure Markdown proposal_digest does not match the proposal")

    raw_lines = text.splitlines()
    try:
        start = raw_lines.index(_TREE_START)
        end = raw_lines.index(_TREE_END)
    except ValueError as exc:
        raise _error("structure Markdown is missing Node-tree boundary markers") from exc
    if end <= start + 1:
        raise _error("structure Markdown Node tree is empty")

    proposal_keys = {node.key for node in proposal.nodes}
    nodes: list[HumanStructureNode] = []
    stack: list[HumanStructureNode] = []
    seen_keys: set[str] = set()
    seen_paths: set[str] = set()
    for line_number, line in enumerate(raw_lines[start + 1 : end], start=start + 2):
        if not line.strip():
            continue
        match = _TREE_LINE_RE.fullmatch(line)
        if match is None:
            raise _error(
                f"Node tree line {line_number} must look like '- **Name** (`path`) [reserved]' with two spaces per nesting level"
            )
        indent = len(match.group("indent"))
        if indent % 2:
            raise _error(f"Node tree line {line_number} indentation must use multiples of two spaces")
        depth = indent // 2
        if depth > len(stack):
            raise _error(f"Node tree line {line_number} jumps more than one hierarchy level")
        stack = stack[:depth]
        parent_key = stack[-1].key if stack else None
        name = _nonempty_string(match.group("name"), f"Node tree line {line_number} name")
        path = _safe_relative_path(match.group("path"), f"Node tree line {line_number} path")
        lifecycle = match.group("lifecycle") or "current"
        proposal_key = match.group("key")
        key = proposal_key or _human_key(name, path, parent_key, lifecycle)
        if key in seen_keys:
            raise _error(f"Node tree contains duplicate key {key}")
        if path in seen_paths:
            raise _error(f"Node tree contains duplicate path {path}")
        seen_keys.add(key)
        seen_paths.add(path)
        node = HumanStructureNode(
            key=key,
            name=name,
            path=path,
            lifecycle=lifecycle,
            parent_key=parent_key,
            proposal_key=proposal_key if proposal_key in proposal_keys else None,
        )
        nodes.append(node)
        stack.append(node)

    roots = [node for node in nodes if node.parent_key is None]
    if len(roots) != 1:
        raise _error("edited Node tree must contain exactly one root")
    if roots[0].path != ".":
        raise _error("edited Node tree root must use path '.'")

    by_key = {node.key: node for node in nodes}
    for node in nodes:
        if node.parent_key is None:
            continue
        parent = by_key[node.parent_key]
        prefix = "" if parent.path == "." else parent.path.rstrip("/") + "/"
        if node.path == "." or (prefix and not node.path.startswith(prefix)):
            raise _error(f"edited Node {node.name!r} path {node.path!r} must be nested under parent path {parent.path!r}")

    normalized = {
        "schema": STRUCTURE_MARKDOWN_SCHEMA,
        "evidence_digest": proposal.evidence_digest,
        "proposal_digest": proposal.proposal_digest,
        "nodes": [node.to_dict() for node in nodes],
    }
    return HumanStructurePlan(
        evidence_digest=proposal.evidence_digest,
        proposal_digest=proposal.proposal_digest,
        nodes=tuple(nodes),
        structure_digest=_canonical_digest(normalized),
    )


def create_or_load_structure_markdown(
    snapshot_root: Path,
    proposal_path: Path,
    structure_path: Path,
) -> tuple[HumanStructurePlan, OnboardingStructureProposal, EvidenceSnapshot, bool]:
    snapshot = load_evidence_snapshot(snapshot_root)
    proposal = load_onboarding_structure_proposal(proposal_path, snapshot_root)
    structure_path = structure_path.resolve()
    if structure_path.exists():
        return load_structure_markdown(structure_path, proposal), proposal, snapshot, False
    structure_path.parent.mkdir(parents=True, exist_ok=True)
    structure_path.write_text(render_structure_markdown(proposal, snapshot), encoding="utf-8")
    return load_structure_markdown(structure_path, proposal), proposal, snapshot, True
