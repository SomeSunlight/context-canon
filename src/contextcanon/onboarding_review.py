from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from .compiler import Compiler
from .model import CompiledPackage
from .onboarding_proposal import (
    EvidenceSnapshot,
    OnboardingProposal,
    ProposalItem,
    load_evidence_snapshot,
    load_onboarding_proposal,
)
from .outputs import check_outputs, write_outputs
from .package import load_package
from .parser import ContextCanonError
from .sources import install_source_package


REVIEW_SCHEMA = "contextcanon/onboarding-review/v0"
ACCEPTANCE_SCHEMA = "contextcanon/onboarding-acceptance/v0"
REUSABLE_CANDIDATES_SCHEMA = "contextcanon/onboarding-reusable-candidates/v0"
UNRESOLVED_SCHEMA = "contextcanon/onboarding-unresolved/v0"
REVIEW_DECISIONS = {"pending", "accept", "reject"}

_REVIEW_TOP_KEYS = {"schema", "evidence_digest", "proposal_digest", "node", "decisions"}
_NODE_KEYS = {"id", "name", "version"}
_DECISION_KEYS = {"id", "decision", "note"}


@dataclass(frozen=True)
class ReviewNode:
    id: str
    name: str
    version: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "name": self.name, "version": self.version}


@dataclass(frozen=True)
class ReviewDecision:
    id: str
    decision: str
    note: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "decision": self.decision, "note": self.note}


@dataclass(frozen=True)
class OnboardingReview:
    evidence_digest: str
    proposal_digest: str
    node: ReviewNode
    decisions: tuple[ReviewDecision, ...]
    review_digest: str

    @property
    def by_id(self) -> dict[str, ReviewDecision]:
        return {decision.id: decision for decision in self.decisions}

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": REVIEW_SCHEMA,
            "evidence_digest": self.evidence_digest,
            "proposal_digest": self.proposal_digest,
            "node": self.node.to_dict(),
            "decisions": [decision.to_dict() for decision in self.decisions],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True)
class OnboardingAcceptance:
    acceptance_path: Path
    source_path: Path
    normalized_digest: str
    package_digest: str
    changed_outputs: tuple[str, ...]


def _canonical_digest(value: dict[str, object]) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path, label: str) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContextCanonError(f"Missing {label}: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"{label} is not valid UTF-8: {path}") from exc
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContextCanonError(f"Invalid JSON in {label} {path}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ContextCanonError(f"{label} must contain a JSON object: {path}")
    return value


def _nonempty_single_line(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContextCanonError(f"Invalid onboarding review: {label} must be a non-empty string")
    if "\n" in value or "\r" in value:
        raise ContextCanonError(f"Invalid onboarding review: {label} must be one line")
    return value.strip()


def _validate_exact_keys(value: dict[str, object], expected: set[str], label: str) -> None:
    if set(value) == expected:
        return
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    details: list[str] = []
    if unknown:
        details.append(f"unknown fields: {', '.join(unknown)}")
    if missing:
        details.append(f"missing fields: {', '.join(missing)}")
    raise ContextCanonError(f"Invalid onboarding review: {label} has {'; '.join(details)}")


def create_or_load_onboarding_review(
    snapshot_root: Path,
    proposal_path: Path,
    review_path: Path,
    *,
    node_name: str | None = None,
    node_id: str | None = None,
    node_version: str = "0.1.0",
) -> tuple[OnboardingReview, OnboardingProposal, EvidenceSnapshot, bool]:
    """Create a human-editable review decision file, or load an existing one.

    Review creation is the first explicitly human-owned state in onboarding.
    Every proposal item starts as pending. The operator edits only decisions
    (and, if desired, the proposed Node metadata) before final acceptance.
    Semantic corrections belong in proposal.json followed by re-validation and
    a fresh review, rather than being hidden in a second replacement schema.
    """

    snapshot = load_evidence_snapshot(snapshot_root)
    proposal = load_onboarding_proposal(proposal_path, snapshot_root)
    review_path = review_path.resolve()
    if review_path.exists():
        review = load_onboarding_review(review_path, proposal)
        return review, proposal, snapshot, False

    if node_name is None:
        raise ContextCanonError(
            "Creating an onboarding review requires --node-name; the LLM does not choose canonical Node identity"
        )
    name = _nonempty_single_line(node_name, "node.name")
    version = _nonempty_single_line(node_version, "node.version")
    stable_id = _nonempty_single_line(node_id or str(uuid.uuid4()), "node.id")
    node = ReviewNode(stable_id, name, version)
    decisions = tuple(ReviewDecision(item.id, "pending", "") for item in proposal.items)
    payload = {
        "schema": REVIEW_SCHEMA,
        "evidence_digest": snapshot.evidence_digest,
        "proposal_digest": proposal.proposal_digest,
        "node": node.to_dict(),
        "decisions": [decision.to_dict() for decision in decisions],
    }
    review = OnboardingReview(
        snapshot.evidence_digest,
        proposal.proposal_digest,
        node,
        decisions,
        _canonical_digest(payload),
    )
    _atomic_write_text(review_path, review.to_json())
    return review, proposal, snapshot, True


def load_onboarding_review(review_path: Path, proposal: OnboardingProposal) -> OnboardingReview:
    raw = _read_json(review_path.resolve(), "onboarding review")
    _validate_exact_keys(raw, _REVIEW_TOP_KEYS, "review")
    if raw["schema"] != REVIEW_SCHEMA:
        raise ContextCanonError(f"Unsupported onboarding review schema: {raw['schema']!r}")
    if raw["evidence_digest"] != proposal.evidence_digest:
        raise ContextCanonError("Onboarding review evidence_digest does not match the proposal")
    if raw["proposal_digest"] != proposal.proposal_digest:
        raise ContextCanonError(
            "Onboarding proposal changed after review creation; validate it and create a fresh review"
        )

    raw_node = raw["node"]
    if not isinstance(raw_node, dict):
        raise ContextCanonError("Invalid onboarding review: node must be an object")
    _validate_exact_keys(raw_node, _NODE_KEYS, "node")
    node = ReviewNode(
        _nonempty_single_line(raw_node["id"], "node.id"),
        _nonempty_single_line(raw_node["name"], "node.name"),
        _nonempty_single_line(raw_node["version"], "node.version"),
    )

    raw_decisions = raw["decisions"]
    if not isinstance(raw_decisions, list):
        raise ContextCanonError("Invalid onboarding review: decisions must be a list")
    expected_ids = [item.id for item in proposal.items]
    if len(raw_decisions) != len(expected_ids):
        raise ContextCanonError("Invalid onboarding review: decision set does not match proposal items")

    decisions: list[ReviewDecision] = []
    actual_ids: list[str] = []
    for index, raw_decision in enumerate(raw_decisions):
        if not isinstance(raw_decision, dict):
            raise ContextCanonError(f"Invalid onboarding review: decisions[{index}] must be an object")
        _validate_exact_keys(raw_decision, _DECISION_KEYS, f"decisions[{index}]")
        item_id = _nonempty_single_line(raw_decision["id"], f"decisions[{index}].id")
        decision = raw_decision["decision"]
        if decision not in REVIEW_DECISIONS:
            raise ContextCanonError(
                f"Invalid onboarding review: decision for {item_id} must be pending, accept, or reject"
            )
        note = raw_decision["note"]
        if not isinstance(note, str):
            raise ContextCanonError(f"Invalid onboarding review: note for {item_id} must be a string")
        decisions.append(ReviewDecision(item_id, str(decision), note))
        actual_ids.append(item_id)

    if actual_ids != expected_ids:
        raise ContextCanonError(
            "Invalid onboarding review: decisions must contain every proposal item exactly once in proposal order"
        )

    normalized = {
        "schema": REVIEW_SCHEMA,
        "evidence_digest": proposal.evidence_digest,
        "proposal_digest": proposal.proposal_digest,
        "node": node.to_dict(),
        "decisions": [decision.to_dict() for decision in decisions],
    }
    return OnboardingReview(
        proposal.evidence_digest,
        proposal.proposal_digest,
        node,
        tuple(decisions),
        _canonical_digest(normalized),
    )


def render_onboarding_review(
    review: OnboardingReview,
    proposal: OnboardingProposal,
    snapshot: EvidenceSnapshot,
) -> str:
    accepted = sum(decision.decision == "accept" for decision in review.decisions)
    rejected = sum(decision.decision == "reject" for decision in review.decisions)
    pending = sum(decision.decision == "pending" for decision in review.decisions)
    lines = [
        f"# Onboarding review — {review.node.name}",
        "",
        f"Proposal: `{proposal.proposal_digest}`",
        f"Evidence: `{snapshot.evidence_digest}`",
        f"Node: `{review.node.id}` · version `{review.node.version}`",
        f"Decisions: {accepted} accept · {rejected} reject · {pending} pending",
        "",
        "Edit the review JSON to set every finding to `accept` or `reject`.",
        "If a finding itself is wrong, correct proposal.json, validate it again, and create a fresh review.",
        "",
    ]
    decisions = review.by_id
    for item in proposal.items:
        decision = decisions[item.id]
        lines.extend(_render_review_item(item, decision, snapshot))
    return "\n".join(lines).rstrip() + "\n"


def _render_review_item(
    item: ProposalItem,
    decision: ReviewDecision,
    snapshot: EvidenceSnapshot,
) -> list[str]:
    lines = [
        f"## [{decision.decision.upper()}] {item.id} — {item.title}",
        "",
        f"Kind: `{item.kind}` · confidence: `{item.confidence}`",
        "",
        item.rationale,
        "",
        "Proposed payload:",
        "```json",
        json.dumps(item.payload, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "Evidence:",
    ]
    for reference in item.evidence:
        lines.append(
            f"- `{reference.path}` lines {reference.start_line}-{reference.end_line} · `{reference.sha256}`"
        )
        evidence_file = snapshot.root / "evidence" / Path(*PurePosixPath(reference.path).parts)
        text = evidence_file.read_text(encoding="utf-8").splitlines()
        excerpt = text[reference.start_line - 1 : reference.end_line]
        lines.append("  ```text")
        for offset, content in enumerate(excerpt, start=reference.start_line):
            lines.append(f"  {offset:>5}: {content}")
        lines.append("  ```")
    if decision.note:
        lines.extend(["", f"Human note: {decision.note}"])
    lines.append("")
    return lines


def accept_onboarding_review(
    snapshot_root: Path,
    proposal_path: Path,
    review_path: Path,
    project_root: Path,
    *,
    catalog_package_roots: Iterable[Path] = (),
    source_locators: dict[str, str] | None = None,
) -> OnboardingAcceptance:
    """Publish one fully reviewed proposal as the first canonical Context Node.

    Acceptance v0 deliberately creates a Node only when CONTEXT.src.md is
    absent. It refuses destructive replacement until a reviewed merge/update
    contract exists. All frozen evidence is rechecked against the live project
    before publication, so human decisions cannot silently apply to a changed
    repository snapshot.
    """

    snapshot_root = snapshot_root.resolve()
    snapshot = load_evidence_snapshot(snapshot_root)
    proposal = load_onboarding_proposal(proposal_path.resolve(), snapshot_root)
    review = load_onboarding_review(review_path.resolve(), proposal)
    pending = [decision.id for decision in review.decisions if decision.decision == "pending"]
    if pending:
        raise ContextCanonError(
            "Onboarding review still has pending decisions: " + ", ".join(pending)
        )

    project_root = project_root.resolve()
    if not (project_root / ".git").exists():
        raise ContextCanonError(f"Onboarding acceptance target must be a Git repository root: {project_root}")
    source_path = project_root / "CONTEXT.src.md"
    if source_path.exists():
        raise ContextCanonError(
            "Onboarding acceptance v0 will not replace an existing CONTEXT.src.md; use a reviewed update workflow instead"
        )

    _verify_live_evidence(snapshot, project_root)
    accepted_items = [
        item for item in proposal.items if review.by_id[item.id].decision == "accept"
    ]
    packages = _load_catalog_packages(catalog_package_roots)
    locators = dict(source_locators or {})
    source_bindings = _resolve_source_bindings(accepted_items, packages, locators)
    source_text = _render_context_source(review.node, accepted_items, source_bindings)

    staging_parent = project_root / ".context" / "onboarding"
    staging_parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".onboarding-accept-", dir=staging_parent))
    try:
        _prepare_stage(stage, snapshot, source_text, source_bindings)
        Compiler(project_root).compile(stage)
    finally:
        if stage.exists():
            shutil.rmtree(stage)

    for _item_id, package_root, package, _locator in source_bindings:
        installed = install_source_package(project_root, package_root)
        if installed.package_digest != package.package_digest:
            raise ContextCanonError("Installed Source package identity changed during onboarding acceptance")

    _atomic_write_text(source_path, source_text)
    try:
        compiled = Compiler(project_root).compile(project_root)
    except Exception:
        source_path.unlink(missing_ok=True)
        raise

    changed = tuple(write_outputs(compiled))
    drift = check_outputs(compiled)
    if drift:
        raise ContextCanonError(
            "Internal onboarding acceptance error: generated ContextCanon output still has drift after build"
        )

    accepted_root = project_root / ".context" / "onboarding" / "accepted" / proposal.proposal_digest
    accepted_root.mkdir(parents=True, exist_ok=True)
    _write_follow_up_artifacts(accepted_root, proposal, review)
    acceptance = {
        "schema": ACCEPTANCE_SCHEMA,
        "evidence_digest": proposal.evidence_digest,
        "proposal_digest": proposal.proposal_digest,
        "review_digest": review.review_digest,
        "node": review.node.to_dict(),
        "decisions": [decision.to_dict() for decision in review.decisions],
        "accepted_item_ids": [item.id for item in accepted_items],
        "rejected_item_ids": [
            item.id for item in proposal.items if review.by_id[item.id].decision == "reject"
        ],
        "sources": [
            {
                "item_id": item_id,
                "node_id": package.metadata.id,
                "name": package.metadata.name,
                "version": package.metadata.version,
                "normalized_digest": package.normalized_digest,
                "package_digest": package.package_digest,
                "locator": locator,
            }
            for item_id, _root, package, locator in source_bindings
        ],
        "canonical": {
            "context_src_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
            "normalized_digest": compiled.normalized_digest,
            "package_digest": compiled.package_digest,
            "generated_outputs": list(changed),
        },
    }
    acceptance_path = accepted_root / "acceptance.json"
    _atomic_write_text(
        acceptance_path,
        json.dumps(acceptance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return OnboardingAcceptance(
        acceptance_path=acceptance_path,
        source_path=source_path,
        normalized_digest=compiled.normalized_digest,
        package_digest=compiled.package_digest,
        changed_outputs=changed,
    )


def parse_source_locator_arguments(values: Iterable[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise ContextCanonError("--source-locator must use ITEM_ID=LOCATOR")
        item_id, locator = raw.split("=", 1)
        item_id = item_id.strip()
        locator = locator.strip()
        if not item_id or not locator:
            raise ContextCanonError("--source-locator must use non-empty ITEM_ID=LOCATOR")
        if item_id in result:
            raise ContextCanonError(f"Duplicate --source-locator for proposal item {item_id}")
        result[item_id] = locator
    return result


def _verify_live_evidence(snapshot: EvidenceSnapshot, project_root: Path) -> None:
    for entry in snapshot.entries:
        path = project_root / Path(*PurePosixPath(entry.path).parts)
        if path.is_symlink() or not path.is_file():
            raise ContextCanonError(
                f"Project evidence changed after onboarding review: missing or unsafe {entry.path}; prepare and review again"
            )
        data = path.read_bytes()
        if len(data) != entry.size or hashlib.sha256(data).hexdigest() != entry.sha256:
            raise ContextCanonError(
                f"Project evidence changed after onboarding review: {entry.path}; prepare and review again"
            )


def _load_catalog_packages(package_roots: Iterable[Path]) -> dict[str, tuple[Path, CompiledPackage]]:
    result: dict[str, tuple[Path, CompiledPackage]] = {}
    for raw_root in package_roots:
        root = raw_root.resolve()
        package = load_package(root)
        node_id = package.metadata.id
        if node_id in result:
            raise ContextCanonError(f"More than one acceptance package supplied for Source Node ID {node_id}")
        result[node_id] = (root, package)
    return result


def _resolve_source_bindings(
    accepted_items: list[ProposalItem],
    packages: dict[str, tuple[Path, CompiledPackage]],
    locators: dict[str, str],
) -> list[tuple[str, Path, CompiledPackage, str]]:
    bindings: list[tuple[str, Path, CompiledPackage, str]] = []
    accepted_source_items = [item for item in accepted_items if item.kind == "existing-source"]
    accepted_ids = {item.id for item in accepted_source_items}
    extra_locators = sorted(set(locators) - accepted_ids)
    if extra_locators:
        raise ContextCanonError(
            f"--source-locator supplied for non-accepted existing-source item: {extra_locators[0]}"
        )
    used_package_ids: set[str] = set()
    for item in accepted_source_items:
        source_id = str(item.payload["source_node_id"])
        package_entry = packages.get(source_id)
        if package_entry is None:
            raise ContextCanonError(
                f"Accepted existing-source item {item.id} requires --catalog-package for Source Node ID {source_id}"
            )
        locator = locators.get(item.id)
        if locator is None or not locator.strip():
            raise ContextCanonError(
                f"Accepted existing-source item {item.id} requires --source-locator {item.id}=LOCATOR"
            )
        if source_id in used_package_ids:
            raise ContextCanonError(f"Accepted onboarding proposal contains Source Node ID {source_id} more than once")
        used_package_ids.add(source_id)
        root, package = package_entry
        bindings.append((item.id, root, package, locator.strip()))
    extra_packages = sorted(set(packages) - used_package_ids)
    if extra_packages:
        raise ContextCanonError(
            f"Acceptance package supplied for Source not accepted by the review: {extra_packages[0]}"
        )
    return sorted(bindings, key=lambda binding: binding[2].metadata.id)


def _render_context_source(
    node: ReviewNode,
    accepted_items: list[ProposalItem],
    source_bindings: list[tuple[str, Path, CompiledPackage, str]],
) -> str:
    _publishable(node.name, "node.name")
    _publishable(node.id, "node.id")
    _publishable(node.version, "node.version")
    lines = [
        f"# {node.name} — Local Context Source",
        f'<!-- ctx:node id="{node.id}" version="{node.version}" -->',
        "",
    ]

    if source_bindings:
        lines.extend(["## Sources", ""])
        for _item_id, _root, package, locator in source_bindings:
            _publishable(package.metadata.name, "Source name")
            _publishable(locator, "Source locator")
            lines.extend(
                [
                    f"- [{package.metadata.name}]({locator}) — `{package.metadata.version}`",
                    (
                        f'  <!-- ctx:source id="{package.metadata.id}" version="{package.metadata.version}" '
                        f'normalized-digest="{package.normalized_digest}" package-digest="{package.package_digest}" -->'
                    ),
                    "",
                ]
            )

    local_rules = [item for item in accepted_items if item.kind == "local-rule"]
    if local_rules:
        lines.extend(["## Rules", ""])
        current_group: str | None = None
        for item in local_rules:
            group = _publishable(str(item.payload["group"]), f"item {item.id} group")
            if group != current_group:
                lines.extend([f"### {group}", ""])
                current_group = group
            title = _publishable(item.title, f"item {item.id} title")
            statement = _publishable(str(item.payload["statement"]), f"item {item.id} statement")
            why = _publishable(str(item.payload["why"]), f"item {item.id} why")
            _publishable(item.id, f"item {item.id} canonical Rule ID")
            lines.extend(
                [
                    f"- **{title}:** {statement}",
                    f"  Why: {why}",
                    f'  <!-- ctx:rule id="{item.id}" -->',
                    "",
                ]
            )

    topics = [item for item in accepted_items if item.kind == "topic-resource"]
    if topics:
        lines.extend(["## Topics", ""])
        for item in topics:
            title = _publishable(item.title, f"item {item.id} title")
            condition = _publishable(str(item.payload["condition"]), f"item {item.id} condition")
            _publishable(item.id, f"item {item.id} canonical Topic ID")
            lines.extend([f"### {title}", "", condition, "", "Required:"])
            for path in item.payload["resource_paths"]:
                lines.append(f"- Resource: `{path}`")
            lines.extend(["", f'<!-- ctx:topic id="{item.id}" -->', ""])

    return "\n".join(lines).rstrip() + "\n"


def _publishable(value: str, label: str) -> str:
    if not value.strip() or "\n" in value or "\r" in value:
        raise ContextCanonError(f"Accepted onboarding {label} must be non-empty single-line text")
    return value.strip()


def _prepare_stage(
    stage: Path,
    snapshot: EvidenceSnapshot,
    source_text: str,
    source_bindings: list[tuple[str, Path, CompiledPackage, str]],
) -> None:
    stage.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(stage / "CONTEXT.src.md", source_text)
    for entry in snapshot.entries:
        source = snapshot.root / "evidence" / Path(*PurePosixPath(entry.path).parts)
        target = stage / Path(*PurePosixPath(entry.path).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for _item_id, package_root, package, _locator in source_bindings:
        destination = stage / ".context" / "sources" / package.package_digest
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(package_root, destination)
        staged = load_package(destination)
        if staged.package_digest != package.package_digest or staged.normalized_digest != package.normalized_digest:
            raise ContextCanonError("Staged Source package identity changed during onboarding acceptance")


def _write_follow_up_artifacts(
    accepted_root: Path,
    proposal: OnboardingProposal,
    review: OnboardingReview,
) -> None:
    accepted = [item for item in proposal.items if review.by_id[item.id].decision == "accept"]
    reusable = [item.to_dict() for item in accepted if item.kind == "candidate-reusable-node"]
    unresolved = [item.to_dict() for item in accepted if item.kind == "unresolved-question"]
    if reusable:
        payload = {
            "schema": REUSABLE_CANDIDATES_SCHEMA,
            "proposal_digest": proposal.proposal_digest,
            "items": reusable,
        }
        _atomic_write_text(
            accepted_root / "reusable-candidates.json",
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    if unresolved:
        payload = {
            "schema": UNRESOLVED_SCHEMA,
            "proposal_digest": proposal.proposal_digest,
            "items": unresolved,
        }
        _atomic_write_text(
            accepted_root / "unresolved.json",
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise ContextCanonError(f"Could not atomically write {path}: {exc}") from exc
    finally:
        if temporary.exists():
            temporary.unlink()
