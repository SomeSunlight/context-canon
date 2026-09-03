from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .onboarding_placement import OnboardingPlacementProposal
from .onboarding_placement_review import OnboardingPlacementReview, PlacementReviewItem, PlacementReviewSourceEdit
from .onboarding_proposal import EvidenceSnapshot, load_evidence_snapshot
from .parser import ContextCanonError


PLACEMENT_SOURCE_AUDIT_SCHEMA = "contextcanon/onboarding-placement-source-audit/v0"


def _fenced(text: str, language: str = "text") -> list[str]:
    longest = 2
    run = 0
    for char in text:
        if char == "`":
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    fence = "`" * max(3, longest + 1)
    return [f"{fence}{language}", *text.split("\n"), fence]


def _before_text(edit: PlacementReviewSourceEdit, snapshot: EvidenceSnapshot) -> str:
    entry = snapshot.by_path.get(edit.path)
    if entry is None or entry.sha256 != edit.sha256:
        raise ContextCanonError(f"Source audit Evidence binding no longer matches snapshot: {edit.path}")
    path = snapshot.root / "evidence" / edit.path
    lines = path.read_text(encoding="utf-8").splitlines()
    if edit.start_line < 1 or edit.end_line > len(lines) or edit.end_line < edit.start_line:
        raise ContextCanonError(f"Source audit range is outside frozen Evidence: {edit.path}:{edit.start_line}-{edit.end_line}")
    return "\n".join(lines[edit.start_line - 1 : edit.end_line])


def _destination_line(item: PlacementReviewItem, proposal: OnboardingPlacementProposal) -> str:
    if item.destination_node_key is None:
        return "Destination: none / outside Node authoring"
    nodes = {node.key: node for node in proposal.structure.nodes}
    node = nodes.get(item.destination_node_key)
    if node is None:
        raise ContextCanonError(f"Source audit references unknown destination Node: {item.destination_node_key}")
    return f"Destination: `{node.key}` — **{node.name}** (`{node.path}`)"


def _payload_lines(item: PlacementReviewItem) -> list[str]:
    payload = item.payload
    if item.kind == "rule":
        return [
            f"Statement: {payload['statement']}",
            f"Why: {payload['why']}",
            f"Wording: `{payload['wording_origin']}`",
        ]
    if item.kind in {"overview", "state", "plan"}:
        return [f"Summary: {payload['text']}", f"Wording: `{payload['wording_origin']}`"]
    if item.kind == "topic-resource":
        resources = ", ".join(f"`{path}`" for path in payload["resource_paths"])
        return [f"Condition: {payload['condition']}", f"Resources: {resources}"]
    if item.kind == "ordinary-documentation":
        documents = ", ".join(f"`{path}`" for path in payload["document_paths"])
        return [f"Documents: {documents}", f"Reason: {payload['reason']}"]
    if item.kind == "authority-mapping":
        authorities = ", ".join(f"`{path}`" for path in payload["authority_paths"])
        return [
            f"Authorities: {authorities}",
            f"Mapping: {payload['mapping']}",
            f"Wording: `{payload['wording_origin']}`",
        ]
    if item.kind == "unresolved":
        return [f"Question: {payload['question']}"]
    raise ContextCanonError(f"Source audit cannot render unsupported placement kind: {item.kind}")


def render_placement_source_audit(
    proposal: OnboardingPlacementProposal,
    review: OnboardingPlacementReview,
    snapshot_root: Path,
    *,
    review_filename: str = "STEP-07-placement.md",
) -> str:
    if review.evidence_digest != proposal.evidence_digest:
        raise ContextCanonError("Source audit review Evidence digest does not match placement proposal")
    if review.structure_digest != proposal.structure_digest:
        raise ContextCanonError("Source audit review structure digest does not match placement proposal")
    if review.proposal_digest != proposal.proposal_digest:
        raise ContextCanonError("Source audit review proposal digest does not match placement proposal")

    snapshot = load_evidence_snapshot(snapshot_root)
    items = {item.proposal_id: item for item in review.items}
    grouped: dict[str, list[PlacementReviewSourceEdit]] = defaultdict(list)
    for edit in review.source_edits:
        grouped[edit.path].append(edit)

    lines = [
        "# ContextCanon source transformation audit",
        "",
        "> **Generated, read-only view.** Edit `STEP-07-placement.md`, not this file. Rerunning `contextcanon onboard placement-review ...` validates the human gate and regenerates this audit from that exact parsed review.",
        "",
        "This view answers one question per source range: **if this text is shortened or replaced, where does every linked piece of maintained meaning land?** It is grouped by original source file rather than destination Node so semantic-loss review does not require chasing scattered findings.",
        "",
        "<!-- contextcanon-placement-source-audit",
        f"schema: {PLACEMENT_SOURCE_AUDIT_SCHEMA}",
        f"evidence_digest: {review.evidence_digest}",
        f"structure_digest: {review.structure_digest}",
        f"proposal_digest: {review.proposal_digest}",
        f"review_digest: {review.review_digest}",
        "-->",
        "",
    ]

    if not grouped:
        lines.extend([
            "No Source After transformations are currently present in the reviewed placement.",
            "",
            "That is valid: promoted meaning may leave its source untouched when the original document remains independently useful or authoritative.",
        ])
        return "\n".join(lines).rstrip() + "\n"

    for path in sorted(grouped):
        lines.extend([f"## `{path}`", ""])
        for edit in sorted(grouped[path], key=lambda value: (value.start_line, value.end_line, value.proposal_id)):
            before = _before_text(edit, snapshot)
            lines.extend([
                f"### {edit.proposal_id} — lines {edit.start_line}-{edit.end_line}",
                "",
                f"Review control: [`{edit.proposal_id}` in {review_filename}]({review_filename}#source-edit-{edit.proposal_id.lower()})",
                "",
                f"Source edit decision: `{edit.decision}`",
                f"Source edit note: {edit.review_note or '-'}",
                f"Frozen SHA-256: `{edit.sha256}`",
                "",
                "#### Before — exact frozen source range",
                "",
            ])
            lines.extend(_fenced(before))
            lines.append("")

            if edit.decision == "accept":
                lines.extend(["#### Effective after — accepted replacement", ""])
                lines.extend(_fenced(edit.replacement))
            elif edit.decision == "reject":
                lines.extend([
                    "#### Effective after — unchanged because this Source edit is rejected",
                    "",
                ])
                lines.extend(_fenced(before))
                lines.extend(["", "#### Proposed replacement — not applied", ""])
                lines.extend(_fenced(edit.replacement))
            else:
                lines.extend([
                    "#### Effective after — undecided",
                    "",
                    "No effective replacement exists while this Source edit remains `pending`.",
                    "",
                    "#### Proposed replacement — candidate under review",
                    "",
                ])
                lines.extend(_fenced(edit.replacement))
            lines.extend(["", "#### Linked maintained meaning", ""])

            for item_id in edit.linked_item_ids:
                item = items.get(item_id)
                if item is None:
                    raise ContextCanonError(f"Source audit edit {edit.proposal_id} references missing review item {item_id}")
                lines.extend([
                    f"##### {item.proposal_id} — {item.title}",
                    "",
                    f"Finding decision: `{item.decision}`",
                    _destination_line(item, proposal),
                    f"Kind: `{item.kind}` · Derived action: `{item.action}`",
                    "",
                    "Reviewed destination content (effective only when this finding is accepted):",
                    "",
                ])
                lines.extend(_payload_lines(item))
                lines.append("")

            lines.extend(["---", ""])

    return "\n".join(lines).rstrip() + "\n"
