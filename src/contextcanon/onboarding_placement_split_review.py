from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Iterable, Mapping

from .onboarding_placement import OnboardingPlacementProposal, PlacementItem, PlacementSourceEdit
from .onboarding_placement_review import (
    PLACEMENT_REVIEW_SCHEMA,
    OnboardingPlacementReview,
    PlacementReviewItem,
    PlacementReviewSourceEdit,
    _HEADER_RE,
    _error,
    _fresh_authoring_id,
    _initial_sources,
    _load_monolithic_placement_review,
    _node_entry_link,
    _normalize_review,
    _render_payload,
    _review_source_edit_candidates,
)
from .onboarding_proposal import EvidenceReference, EvidenceSnapshot, load_evidence_snapshot
from .onboarding_workspace import write_utf8
from .parser import ContextCanonError


SPLIT_LAYOUT_MARKER = '<!-- cc:placement-review-layout: split-v2 -->'
LEGACY_SPLIT_LAYOUT_MARKER = '<!-- cc:placement-review-layout: split-v1 -->'
FINDING_BINDING_SCHEMA = "contextcanon/onboarding-placement-finding/v2"
SOURCE_EDIT_BINDING_SCHEMA = "contextcanon/onboarding-placement-source-edit/v1"

_FINDING_BINDING_RE = re.compile(
    r'^<!-- cc:placement-finding schema="(?P<schema>[^"]+)" evidence="(?P<evidence>[0-9a-f]{64})" '
    r'structure="(?P<structure>[0-9a-f]{64})" proposal="(?P<proposal>[0-9a-f]{64})" item="(?P<item>[^"]+)" -->$',
    re.MULTILINE,
)
_SOURCE_EDIT_BINDING_RE = re.compile(
    r'^<!-- cc:placement-source-edit schema="(?P<schema>[^"]+)" evidence="(?P<evidence>[0-9a-f]{64})" '
    r'structure="(?P<structure>[0-9a-f]{64})" proposal="(?P<proposal>[0-9a-f]{64})" edit="(?P<edit>[^"]+)" -->$',
    re.MULTILINE,
)
_SOURCE_AFTER_START_RE = re.compile(r'^<!-- cc:source-after id="(?P<id>[^"]+)":start -->$')
_SOURCE_AFTER_END_RE = re.compile(r'^<!-- cc:source-after id="(?P<id>[^"]+)":end -->$')
_FINDING_TITLE_RE = re.compile(
    r"^# (?P<id>\S+) — (?P<orientation>.+?) · (?P<kind>[^ ]+) — (?P<title>.+)$"
)

_PARSER_BULLET_LABELS = (
    "Destination: ",
    "Decision: ",
    "Kind: ",
    "Review note: ",
    "Statement: ",
    "Why: ",
    "Wording: ",
    "Summary: ",
    "Condition: ",
    "Resources: ",
    "Documents: ",
    "Reason: ",
    "Authorities: ",
    "Mapping: ",
    "Question: ",
    "Source edit decision: ",
    "Source edit note: ",
)


def placement_review_directory(index_path: Path) -> Path:
    return index_path.resolve().with_suffix("")


def placement_source_edit_directory(index_path: Path) -> Path:
    return index_path.resolve().parent / "STEP-10-source-edits"


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return slug[:72] or "review"


def placement_finding_filename(item: PlacementItem) -> str:
    return f"{item.id}-{_slug(item.title)}.md"


def placement_finding_path(index_path: Path, item: PlacementItem) -> Path:
    return placement_review_directory(index_path) / placement_finding_filename(item)


def placement_source_edit_filename(edit: PlacementSourceEdit | PlacementReviewSourceEdit) -> str:
    edit_id = edit.id if isinstance(edit, PlacementSourceEdit) else edit.proposal_id
    return f"{edit_id}-{_slug(edit.path)}-{edit.start_line}-{edit.end_line}.md"


def placement_source_edit_path(
    index_path: Path, edit: PlacementSourceEdit | PlacementReviewSourceEdit
) -> Path:
    return placement_source_edit_directory(index_path) / placement_source_edit_filename(edit)


def _finding_node_link(node_path: str) -> str:
    return "../../CONTEXT.md" if node_path == "." else f"../../{node_path}/CONTEXT.md"


def _quote_markdown(lines: Iterable[str]) -> list[str]:
    return [">" if line == "" else f"> {line}" for line in lines]


def _evidence_markdown(reference: EvidenceReference, snapshot: EvidenceSnapshot) -> list[str]:
    evidence_file = snapshot.root / "evidence" / reference.path
    source = evidence_file.read_text(encoding="utf-8").splitlines()
    selected = source[reference.start_line - 1 : reference.end_line]
    lines = [
        f"`{reference.path}` · lines {reference.start_line}–{reference.end_line} · `{reference.sha256}`",
        "",
    ]
    lines.extend(_quote_markdown(selected))
    return lines


def _source_edit_reference(edit: PlacementSourceEdit | PlacementReviewSourceEdit) -> EvidenceReference:
    return EvidenceReference(edit.path, edit.sha256, edit.start_line, edit.end_line)


def _finding_binding_line(proposal: OnboardingPlacementProposal, item_id: str) -> str:
    return (
        f'<!-- cc:placement-finding schema="{FINDING_BINDING_SCHEMA}" evidence="{proposal.evidence_digest}" '
        f'structure="{proposal.structure_digest}" proposal="{proposal.proposal_digest}" item="{item_id}" -->'
    )


def _source_edit_binding_line(proposal: OnboardingPlacementProposal, edit_id: str) -> str:
    return (
        f'<!-- cc:placement-source-edit schema="{SOURCE_EDIT_BINDING_SCHEMA}" evidence="{proposal.evidence_digest}" '
        f'structure="{proposal.structure_digest}" proposal="{proposal.proposal_digest}" edit="{edit_id}" -->'
    )


def _payload_lines(
    review_item: PlacementReviewItem,
    destination_name: str | None,
) -> list[str]:
    rendered = _render_payload(review_item.kind, review_item.payload)
    if review_item.destination_node_key is not None and destination_name is not None:
        rendered[0] = f"## Into Node {review_item.destination_node_key} — {destination_name}"
    else:
        rendered[0] = "## Reviewed handling — outside Node authoring"
    result: list[str] = []
    for line in rendered:
        if line.startswith("### "):
            line = "## " + line[4:]
        if line and not line.startswith("#") and not line.startswith(">"):
            line = "- " + line
        result.append(line)
    return result


def _render_finding(
    item: PlacementItem,
    review_item: PlacementReviewItem,
    proposal: OnboardingPlacementProposal,
    review: OnboardingPlacementReview,
    snapshot: EvidenceSnapshot,
) -> str:
    nodes = {node.key: node for node in proposal.structure.nodes}
    destination = nodes.get(review_item.destination_node_key) if review_item.destination_node_key else None
    destination_text = (
        f"`{destination.key}` — [**{destination.name}**]({_finding_node_link(destination.path)}) (`{destination.path}`)"
        if destination is not None
        else "none / outside Node authoring"
    )
    orientation = (
        f"{destination.key} — {destination.name}"
        if destination is not None
        else "outside Node authoring"
    )
    if review_item.kind == "ordinary-documentation":
        explanation = (
            "Decide whether this project document is intentionally kept outside Context Node authoring. "
            "This P finding does **not** itself modify the source file; a concrete rewrite exists only when a linked E sheet says so."
        )
    elif destination is not None:
        explanation = (
            f"Decide whether this maintained meaning belongs in Context Node **{destination.key} — {destination.name}** "
            f"as kind `{review_item.kind}`. Accepting the P controls semantic placement; it does not by itself rewrite frozen Evidence."
        )
    else:
        explanation = (
            f"Decide how this `{review_item.kind}` finding is handled outside Context Node authoring. "
            "Any concrete source rewrite is reviewed separately in a linked E sheet."
        )

    lines = [
        f"# {review_item.proposal_id} — {orientation} · {review_item.kind} — {review_item.title}",
        _finding_binding_line(proposal, review_item.proposal_id),
        f'<!-- cc:placement-item id="{review_item.proposal_id}" authoring-id="{review_item.authoring_id}" -->',
        "",
        "[← STEP 10 index](../STEP-10-placement.md)",
        "",
        "## What this page decides",
        "",
        explanation,
        "",
        "P = **semantic interpretation/placement**. E = **concrete source transformation**. They are reviewed separately.",
        "",
        "## Review controls",
        "",
        "> ✏️ Editable finding controls",
        f"- Destination: {destination_text}",
        f"- Decision: `{review_item.decision}`",
        f"- Kind: `{review_item.kind}`",
        f"- Derived action: `{review_item.action}` (from Kind; do not edit)",
        f"- Review note: {review_item.review_note or '-'}",
        "> End editable finding controls",
        "",
    ]
    lines.extend(_payload_lines(review_item, None if destination is None else destination.name))

    linked_edits = [
        edit for edit in review.source_edits if review_item.proposal_id in edit.linked_item_ids
    ]
    lines.extend(["", "## Related source edits", ""])
    if linked_edits:
        candidates = {
            edit.id: edit for edit in _review_source_edit_candidates(proposal, snapshot)
        }
        for edit in linked_edits:
            candidate = candidates[edit.proposal_id]
            filename = placement_source_edit_filename(candidate)
            lines.append(
                f"- [`{edit.proposal_id}` — `{edit.path}` lines {edit.start_line}–{edit.end_line}]"
                f"(../STEP-10-source-edits/{filename}) — decision `{edit.decision}`"
            )
    else:
        lines.append("- None. This finding does not propose a concrete source-file rewrite.")

    lines.extend(["", "## Evidence", ""])
    for index, reference in enumerate(item.evidence, start=1):
        lines.extend([f"### Evidence {index}", ""])
        lines.extend(_evidence_markdown(reference, snapshot))
        lines.append("")

    lines.extend(
        [
            "## Proposal rationale",
            "",
            item.rationale,
            "",
            f"Original confidence: `{item.confidence}`",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_source_edit(
    edit: PlacementReviewSourceEdit,
    candidate: PlacementSourceEdit,
    proposal: OnboardingPlacementProposal,
    review: OnboardingPlacementReview,
    snapshot: EvidenceSnapshot,
) -> str:
    linked_ids = ", ".join(candidate.linked_item_ids)
    review_by_id = {item.proposal_id: item for item in review.items}
    proposal_by_id = {item.id: item for item in proposal.items}
    linked_title = ", ".join(edit.linked_item_ids)
    proposal_ids = {source_edit.id for source_edit in proposal.source_edits}

    lines = [
        f"# {edit.proposal_id} — {linked_title} — `{edit.path}` lines {edit.start_line}–{edit.end_line}",
        _source_edit_binding_line(proposal, edit.proposal_id),
        f'<!-- cc:source-edit id="{edit.proposal_id}" path="{edit.path}" sha256="{edit.sha256}" '
        f'start-line="{edit.start_line}" end-line="{edit.end_line}" linked-items="{linked_ids}" -->',
        "",
        "[← STEP 10 index](../STEP-10-placement.md)",
        "",
        "## What this page decides",
        "",
        "This E sheet reviews one **concrete transformation of the original source range**. "
        "It is separate from the P findings that decide where the maintained meaning belongs.",
        "",
        "**Dependency:** this Source edit may be accepted only when every linked promoted P finding is accepted. "
        "ContextCanon validates that dependency; the current linked decisions are shown below before you decide.",
        "",
    ]
    if edit.proposal_id not in proposal_ids:
        lines.extend(
            [
                "**Optional cleanup:** this review-only E defaults to `reject`. Leave it rejected to keep the source unchanged.",
                "",
            ]
        )
    lines.extend(
        [
            "## Review controls",
            "",
            "> ✏️ Editable source-cleanup controls",
            f"- Source edit decision: `{edit.decision}`",
            f"- Source edit note: {edit.review_note or '-'}",
            "> End editable source-cleanup controls",
            "",
            "## Linked findings",
            "",
        ]
    )
    for item_id in edit.linked_item_ids:
        item = review_by_id[item_id]
        filename = placement_finding_filename(proposal_by_id[item_id])
        lines.append(
            f"- [`{item_id}` — {item.title}](../STEP-10-placement/{filename}) — decision `{item.decision}`"
        )

    lines.extend(["", "## Before — frozen source", ""])
    lines.extend(_evidence_markdown(_source_edit_reference(candidate), snapshot))
    lines.extend(
        [
            "",
            "## After — editable replacement",
            "",
            "The quote frame is presentation only. Keep every replacement line inside it; "
            "ContextCanon removes exactly one `>` layer when validating the reviewed replacement.",
            "",
            f'<!-- cc:source-after id="{edit.proposal_id}":start -->',
        ]
    )
    lines.extend(_quote_markdown(edit.replacement.split("\n")))
    lines.extend(
        [
            f'<!-- cc:source-after id="{edit.proposal_id}":end -->',
            "",
            "## Proposal rationale",
            "",
            candidate.rationale,
            "",
            f"Original confidence: `{candidate.confidence}`",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _status_counts(values: Iterable[str]) -> str:
    values = tuple(values)
    return " · ".join(
        f"{name}: {sum(value == name for value in values)}"
        for name in ("pending", "accept", "reject")
    )


def _render_index(
    proposal: OnboardingPlacementProposal,
    review: OnboardingPlacementReview,
    snapshot: EvidenceSnapshot,
) -> str:
    proposal_by_id = {item.id: item for item in proposal.items}
    nodes = {node.key: node for node in proposal.structure.nodes}
    candidates = {
        edit.id: edit for edit in _review_source_edit_candidates(proposal, snapshot)
    }
    edits_by_item: dict[str, list[PlacementReviewSourceEdit]] = {
        item.id: [] for item in proposal.items
    }
    for edit in review.source_edits:
        for item_id in edit.linked_item_ids:
            edits_by_item.setdefault(item_id, []).append(edit)

    lines = [
        "# ContextCanon onboarding placement review",
        SPLIT_LAYOUT_MARKER,
        "",
        "This is the STEP-10 **index**. P sheets review semantic placement; E sheets review concrete source transformations.",
        "",
        "## Status",
        "",
        f"- Findings — {_status_counts(item.decision for item in review.items)}",
        f"- Source edits — {_status_counts(edit.decision for edit in review.source_edits)}",
        f"- Reusable Sources — {_status_counts(source.decision for source in review.sources)}",
        f"- Complete: `{str(review.is_complete).lower()}`",
        "",
        "## Editable control glossary",
        "",
        "- `Decision`: `pending`, `accept`, or `reject`.",
        "- `Destination`: the Context Node that owns the finding; `none / outside Node authoring` is intentional for kinds that stay outside Node authoring.",
        "- `Kind`: change this rather than the displayed derived Action.",
        "- `Review note`: optional owner rationale/reminder; use `-` for none.",
        "- E replacement text is editable between hidden `cc:source-after` markers inside one Markdown quote frame.",
        "",
        "<!-- contextcanon-placement-review",
        f"schema: {PLACEMENT_REVIEW_SCHEMA}",
        f"evidence_digest: {proposal.evidence_digest}",
        f"structure_digest: {proposal.structure_digest}",
        f"proposal_digest: {proposal.proposal_digest}",
        "-->",
        "",
        "## Findings",
        "",
        "**This table is generated Markdown, not a live view.** After editing P or E sheets, run "
        "`contextcanon onboard placement-review $SNAPSHOT` to validate the review and refresh this index.",
        "",
        "| Decision | Finding | Destination | Kind | Source edits |",
        "|---|---|---|---|---|",
    ]
    for review_item in review.items:
        proposal_item = proposal_by_id[review_item.proposal_id]
        filename = placement_finding_filename(proposal_item)
        destination = (
            nodes.get(review_item.destination_node_key)
            if review_item.destination_node_key
            else None
        )
        destination_label = (
            "outside Node authoring"
            if destination is None
            else f"{destination.key} — {destination.name} (`{destination.path}`)"
        )
        edit_links: list[str] = []
        for edit in edits_by_item.get(review_item.proposal_id, []):
            candidate = candidates[edit.proposal_id]
            edit_links.append(
                f"[`{edit.proposal_id}`](STEP-10-source-edits/{placement_source_edit_filename(candidate)}) "
                f"`{edit.decision}`"
            )
        edit_label = ", ".join(edit_links) or "—"
        lines.append(
            f"| `{review_item.decision}` | [`{review_item.proposal_id}` — {review_item.title}]"
            f"(STEP-10-placement/{filename}) | {destination_label} | `{review_item.kind}` | {edit_label} |"
        )

    lines.extend(
        [
            "",
            "## Source edits",
            "",
            "**This table is also a generated snapshot.** Rerun "
            "`contextcanon onboard placement-review $SNAPSHOT` after edits to validate dependencies and refresh it.",
            "",
        ]
    )
    if not review.source_edits:
        lines.extend(["No source transformations are proposed.", ""])
    else:
        lines.extend(
            [
                "| Decision | Source edit | Source range | Linked findings |",
                "|---|---|---|---|",
            ]
        )
        for edit in review.source_edits:
            candidate = candidates[edit.proposal_id]
            filename = placement_source_edit_filename(candidate)
            linked = ", ".join(
                f"[`{item_id}`](STEP-10-placement/{placement_finding_filename(proposal_by_id[item_id])})"
                for item_id in edit.linked_item_ids
            )
            lines.append(
                f"| `{edit.decision}` | [`{edit.proposal_id}`](STEP-10-source-edits/{filename}) | "
                f"`{edit.path}` {edit.start_line}–{edit.end_line} | {linked} |"
            )

    lines.extend(["", "## Reusable Sources", ""])
    if not review.sources:
        lines.extend(["No reusable Source is currently proposed or owner-selected.", ""])
    else:
        by_reuse = {reuse.id: reuse for reuse in proposal.source_reuses}
        for source in review.sources:
            target = nodes[source.target_node_key]
            lines.extend(
                [
                    f"## Source {source.review_id} — {source.source_name}",
                    f'<!-- cc:placement-source id="{source.review_id}" origin="{source.origin}" '
                    f'source-id="{source.source_node_id}" version="{source.source_version}" '
                    f'normalized-digest="{source.source_normalized_digest}" package-digest="{source.source_package_digest}" -->',
                    "",
                    f"Destination: `{target.key}` — [**{target.name}**]({_node_entry_link(target.path)}) (`{target.path}`)",
                    f"Decision: `{source.decision}`",
                    f"Origin: `{source.origin}`",
                    f"Why this Source applies: {source.relationship_why or '-'}",
                    f"Review note: {source.review_note or '-'}",
                    "",
                    f"Exact package: `{source.source_version}` · `{source.source_package_digest}`",
                    "",
                ]
            )
            if source.proposal_id is not None:
                reuse = by_reuse[source.proposal_id]
                lines.extend(["Proposal rationale:", "", reuse.reason, ""])
            else:
                lines.extend(
                    [
                        "This Source was selected explicitly by the project owner. When it came from STEP 07, "
                        "that relationship is already accepted here and is shown only for compact traceability; "
                        "it is design input, not a claim derived from frozen project Evidence.",
                        "",
                    ]
                )
    return "\n".join(lines).rstrip() + "\n"


def _initial_review(
    proposal: OnboardingPlacementProposal,
    snapshot_root: Path,
    *,
    owner_source_specs: Iterable[str],
    owner_source_whys: Mapping[str, str] | None,
    preaccepted_owner_sources: bool,
) -> OnboardingPlacementReview:
    snapshot = load_evidence_snapshot(snapshot_root)
    items = tuple(
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
    candidates = _review_source_edit_candidates(proposal, snapshot)
    proposal_edit_ids = {edit.id for edit in proposal.source_edits}
    source_edits = tuple(
        PlacementReviewSourceEdit(
            proposal_id=edit.id,
            decision="pending" if edit.id in proposal_edit_ids else "reject",
            path=edit.path,
            sha256=edit.sha256,
            start_line=edit.start_line,
            end_line=edit.end_line,
            linked_item_ids=edit.linked_item_ids,
            replacement=edit.replacement,
            review_note="",
        )
        for edit in candidates
    )
    sources = _initial_sources(
        proposal,
        owner_source_specs,
        owner_source_whys=owner_source_whys,
        preaccepted_owner_sources=preaccepted_owner_sources,
    )
    return _normalize_review(proposal, items, source_edits, sources)


def _validate_index_binding(text: str, proposal: OnboardingPlacementProposal) -> None:
    header = _HEADER_RE.search(text)
    if header is None:
        raise _error("STEP-10-placement.md is missing its ContextCanon binding header")
    if header.group("schema") != PLACEMENT_REVIEW_SCHEMA:
        raise _error(f"unsupported review schema {header.group('schema')!r}")
    if header.group("evidence") != proposal.evidence_digest:
        raise _error("evidence_digest does not match the proposal")
    if header.group("structure") != proposal.structure_digest:
        raise _error("structure_digest does not match the proposal")
    if header.group("proposal") != proposal.proposal_digest:
        raise _error(
            "proposal_digest does not match the existing human placement review; "
            "create a new review path for a new LLM candidate rather than overwriting human edits"
        )


def _validate_finding_binding(
    text: str, proposal: OnboardingPlacementProposal, item_id: str
) -> None:
    matches = list(_FINDING_BINDING_RE.finditer(text))
    if len(matches) != 1:
        raise _error(
            f"split finding {item_id} must contain exactly one ContextCanon finding binding"
        )
    match = matches[0]
    actual = (
        match.group("schema"),
        match.group("evidence"),
        match.group("structure"),
        match.group("proposal"),
        match.group("item"),
    )
    expected = (
        FINDING_BINDING_SCHEMA,
        proposal.evidence_digest,
        proposal.structure_digest,
        proposal.proposal_digest,
        item_id,
    )
    if actual != expected:
        raise _error(
            f"split finding {item_id} binding does not match the exact placement proposal"
        )


def _validate_source_edit_binding(
    text: str, proposal: OnboardingPlacementProposal, edit_id: str
) -> None:
    matches = list(_SOURCE_EDIT_BINDING_RE.finditer(text))
    if len(matches) != 1:
        raise _error(
            f"split Source edit {edit_id} must contain exactly one ContextCanon Source-edit binding"
        )
    match = matches[0]
    actual = (
        match.group("schema"),
        match.group("evidence"),
        match.group("structure"),
        match.group("proposal"),
        match.group("edit"),
    )
    expected = (
        SOURCE_EDIT_BINDING_SCHEMA,
        proposal.evidence_digest,
        proposal.structure_digest,
        proposal.proposal_digest,
        edit_id,
    )
    if actual != expected:
        raise _error(
            f"split Source edit {edit_id} binding does not match the exact placement proposal"
        )


def _validate_replacement_quote_frames(text: str, edit_id: str) -> None:
    lines = text.splitlines()
    active: str | None = None
    content: list[str] = []
    for line in lines:
        start = _SOURCE_AFTER_START_RE.match(line)
        if start is not None:
            if active is not None:
                raise _error(f"split Source edit {edit_id} has nested source-after markers")
            active = start.group("id")
            content = []
            continue
        end = _SOURCE_AFTER_END_RE.match(line)
        if end is not None:
            if active != end.group("id"):
                raise _error(
                    f"split Source edit {edit_id} has mismatched source-after markers"
                )
            if any(entry != ">" and not entry.startswith("> ") for entry in content):
                raise _error(
                    f"Source edit {active} must keep every editable replacement line "
                    "inside the single Markdown quote frame"
                )
            active = None
            content = []
            continue
        if active is not None:
            content.append(line)
    if active is not None:
        raise _error(f"split Source edit {edit_id} has an unterminated source-after marker")


def _strip_review_bullet(line: str) -> str:
    if line.startswith("- ") and line[2:].startswith(_PARSER_BULLET_LABELS):
        return line[2:]
    return line


def _finding_parser_text(text: str, item_id: str) -> str:
    lines = text.splitlines()
    if not lines:
        raise _error(f"split finding {item_id} is empty")
    heading = _FINDING_TITLE_RE.match(lines[0])
    if heading is None or heading.group("id") != item_id:
        raise _error(
            f"split finding {item_id} must start with ID, Destination, Kind, and editable title"
        )
    result = [f"## {item_id} — {heading.group('title').strip()}"]
    for line in lines[1:]:
        if line.startswith("## "):
            line = "### " + line[3:]
        result.append(_strip_review_bullet(line))
    return "\n".join(result)


def _source_edit_parser_text(text: str) -> str:
    result: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            line = "### " + line[3:]
        result.append(_strip_review_bullet(line))
    return "\n".join(result)


def _exact_directory_entries(
    directory: Path,
    expected: Mapping[str, object],
    label: str,
) -> dict[str, Path]:
    if not directory.is_dir() or directory.is_symlink():
        raise _error(f"split STEP-10 {label} directory is missing or invalid: {directory}")
    actual = {entry.name: entry for entry in directory.iterdir()}
    missing = sorted(set(expected) - set(actual))
    foreign = sorted(set(actual) - set(expected))
    if missing:
        raise _error(
            f"split STEP-10 review is missing {label} files: " + ", ".join(missing)
        )
    if foreign:
        raise _error(
            f"split STEP-10 review contains foreign {label} files/directories: "
            + ", ".join(foreign)
        )
    return actual


def _parse_split(
    index_path: Path,
    proposal: OnboardingPlacementProposal,
    snapshot_root: Path,
) -> OnboardingPlacementReview:
    index_path = index_path.resolve()
    try:
        index_text = index_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContextCanonError(f"Missing onboarding placement review: {index_path}") from exc
    except UnicodeDecodeError as exc:
        raise _error("STEP-10-placement.md is not valid UTF-8") from exc

    if LEGACY_SPLIT_LAYOUT_MARKER in index_text:
        raise _error(
            "STEP-10 split-v1 is an interim owner-test layout and is intentionally not migrated. "
            "Run `contextcanon onboard reset $SNAPSHOT --from 10`, then recreate STEP 10."
        )
    if SPLIT_LAYOUT_MARKER not in index_text:
        return _load_monolithic_placement_review(index_path, proposal, snapshot_root)
    _validate_index_binding(index_text, proposal)

    snapshot = load_evidence_snapshot(snapshot_root)
    finding_expected = {placement_finding_filename(item): item for item in proposal.items}
    finding_entries = _exact_directory_entries(
        placement_review_directory(index_path), finding_expected, "finding"
    )
    candidates = _review_source_edit_candidates(proposal, snapshot)
    edit_expected = {placement_source_edit_filename(edit): edit for edit in candidates}
    edit_entries = _exact_directory_entries(
        placement_source_edit_directory(index_path), edit_expected, "Source-edit"
    )

    finding_texts: list[str] = []
    for item in proposal.items:
        path = finding_entries[placement_finding_filename(item)]
        if not path.is_file() or path.is_symlink():
            raise _error(f"split finding path is not a regular file: {path.name}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise _error(f"split finding {path.name} is not valid UTF-8") from exc
        _validate_finding_binding(text, proposal, item.id)
        finding_texts.append(_finding_parser_text(text, item.id))

    edit_texts: list[str] = []
    for candidate in candidates:
        path = edit_entries[placement_source_edit_filename(candidate)]
        if not path.is_file() or path.is_symlink():
            raise _error(f"split Source edit path is not a regular file: {path.name}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise _error(f"split Source edit {path.name} is not valid UTF-8") from exc
        _validate_source_edit_binding(text, proposal, candidate.id)
        _validate_replacement_quote_frames(text, candidate.id)
        edit_texts.append(_source_edit_parser_text(text))

    synthetic = "\n\n".join(
        [*finding_texts, *edit_texts, index_text.rstrip()]
    ) + "\n"
    fd, temporary_name = tempfile.mkstemp(
        prefix=".contextcanon-placement-split-",
        suffix=".md",
        dir=index_path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(synthetic)
        return _load_monolithic_placement_review(temporary, proposal, snapshot_root)
    finally:
        temporary.unlink(missing_ok=True)


def load_split_placement_review(
    path: Path,
    proposal: OnboardingPlacementProposal,
    snapshot_root: Path,
) -> OnboardingPlacementReview:
    return _parse_split(path, proposal, snapshot_root)


def _write_split_layout(
    index_path: Path,
    proposal: OnboardingPlacementProposal,
    review: OnboardingPlacementReview,
    snapshot_root: Path,
    *,
    creating: bool,
) -> None:
    index_path = index_path.resolve()
    finding_dir = placement_review_directory(index_path)
    edit_dir = placement_source_edit_directory(index_path)
    snapshot = load_evidence_snapshot(snapshot_root)
    review_by_id = {item.proposal_id: item for item in review.items}
    review_edits = {edit.proposal_id: edit for edit in review.source_edits}
    candidates = {
        edit.id: edit for edit in _review_source_edit_candidates(proposal, snapshot)
    }

    if creating:
        for directory in (finding_dir, edit_dir):
            if directory.exists() or directory.is_symlink():
                raise _error(f"refusing to replace existing STEP-10 review directory: {directory}")
            directory.mkdir(parents=False, exist_ok=False)

    for item in proposal.items:
        write_utf8(
            finding_dir / placement_finding_filename(item),
            _render_finding(
                item,
                review_by_id[item.id],
                proposal,
                review,
                snapshot,
            ),
        )
    for candidate in candidates.values():
        edit = review_edits[candidate.id]
        write_utf8(
            edit_dir / placement_source_edit_filename(candidate),
            _render_source_edit(edit, candidate, proposal, review, snapshot),
        )
    write_utf8(index_path, _render_index(proposal, review, snapshot))


def create_or_load_split_placement_review(
    path: Path,
    proposal: OnboardingPlacementProposal,
    snapshot_root: Path,
    *,
    owner_source_specs: Iterable[str] = (),
    owner_source_whys: Mapping[str, str] | None = None,
    preaccepted_owner_sources: bool = False,
) -> tuple[OnboardingPlacementReview, bool]:
    path = path.resolve()
    finding_dir = placement_review_directory(path)
    edit_dir = placement_source_edit_directory(path)

    if path.exists():
        if tuple(owner_source_specs):
            raise _error(
                "--owner-source is only used when STEP-10 review is first created; "
                "edit the existing human review instead of silently changing it"
            )
        try:
            index_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise _error("STEP-10-placement.md is not valid UTF-8") from exc

        if LEGACY_SPLIT_LAYOUT_MARKER in index_text:
            raise _error(
                "STEP-10 split-v1 is intentionally not migrated during owner testing. "
                "Reset from STEP 10 and recreate the review."
            )
        if SPLIT_LAYOUT_MARKER not in index_text:
            if (
                finding_dir.exists()
                or finding_dir.is_symlink()
                or edit_dir.exists()
                or edit_dir.is_symlink()
            ):
                raise _error(
                    "legacy STEP-10 review exists beside split directories; refusing to guess "
                    "which human edits are authoritative"
                )
            legacy = _load_monolithic_placement_review(path, proposal, snapshot_root)
            path.unlink()
            _write_split_layout(
                path, proposal, legacy, snapshot_root, creating=True
            )
            return _parse_split(path, proposal, snapshot_root), False

        loaded = _parse_split(path, proposal, snapshot_root)
        _write_split_layout(
            path, proposal, loaded, snapshot_root, creating=False
        )
        return _parse_split(path, proposal, snapshot_root), False

    if (
        finding_dir.exists()
        or finding_dir.is_symlink()
        or edit_dir.exists()
        or edit_dir.is_symlink()
    ):
        raise _error(
            "STEP-10 review index is missing but one or more split review directories already exist"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    review = _initial_review(
        proposal,
        snapshot_root,
        owner_source_specs=owner_source_specs,
        owner_source_whys=owner_source_whys,
        preaccepted_owner_sources=preaccepted_owner_sources,
    )
    _write_split_layout(path, proposal, review, snapshot_root, creating=True)
    return _parse_split(path, proposal, snapshot_root), True
