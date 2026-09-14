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
    PlacementReviewItem,
    PlacementReviewSource,
    PlacementReviewSourceEdit,
    OnboardingPlacementReview,
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


SPLIT_LAYOUT_MARKER = '<!-- cc:placement-review-layout: split-v1 -->'
FINDING_BINDING_SCHEMA = "contextcanon/onboarding-placement-finding/v1"
_FINDING_BINDING_RE = re.compile(
    r'^<!-- cc:placement-finding schema="(?P<schema>[^"]+)" evidence="(?P<evidence>[0-9a-f]{64})" '
    r'structure="(?P<structure>[0-9a-f]{64})" proposal="(?P<proposal>[0-9a-f]{64})" item="(?P<item>[^"]+)" -->$',
    re.MULTILINE,
)
_SOURCE_AFTER_START_RE = re.compile(r'^<!-- cc:source-after id="(?P<id>[^"]+)":start -->$')
_SOURCE_AFTER_END_RE = re.compile(r'^<!-- cc:source-after id="(?P<id>[^"]+)":end -->$')


def placement_review_directory(index_path: Path) -> Path:
    return index_path.resolve().with_suffix("")


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return slug[:72] or "finding"


def placement_finding_filename(item: PlacementItem) -> str:
    return f"{item.id}-{_slug(item.title)}.md"


def placement_finding_path(index_path: Path, item: PlacementItem) -> Path:
    return placement_review_directory(index_path) / placement_finding_filename(item)


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


def _source_edit_reference(edit: PlacementSourceEdit) -> EvidenceReference:
    return EvidenceReference(edit.path, edit.sha256, edit.start_line, edit.end_line)


def _binding_line(proposal: OnboardingPlacementProposal, item_id: str) -> str:
    return (
        f'<!-- cc:placement-finding schema="{FINDING_BINDING_SCHEMA}" evidence="{proposal.evidence_digest}" '
        f'structure="{proposal.structure_digest}" proposal="{proposal.proposal_digest}" item="{item_id}" -->'
    )


def _render_source_edit(
    edit: PlacementReviewSourceEdit,
    candidate: PlacementSourceEdit,
    proposal: OnboardingPlacementProposal,
    review_by_id: Mapping[str, PlacementReviewItem],
    snapshot: EvidenceSnapshot,
) -> list[str]:
    linked = ", ".join(candidate.linked_item_ids)
    proposal_ids = {source_edit.id for source_edit in proposal.source_edits}
    owner = candidate.linked_item_ids[0]
    related = [item_id for item_id in edit.linked_item_ids if item_id != owner]
    lines = [
        f'<a id="source-edit-{edit.proposal_id.lower()}"></a>',
        f"#### Source edit {edit.proposal_id}",
        f'<!-- cc:source-edit id="{edit.proposal_id}" path="{edit.path}" sha256="{edit.sha256}" start-line="{edit.start_line}" end-line="{edit.end_line}" linked-items="{linked}" -->',
        "",
    ]
    if edit.proposal_id not in proposal_ids:
        lines.extend(
            [
                "**Optional source cleanup — independent from promotion.**",
                "Accepting or rejecting the finding is separate. Keep this Source edit at `reject` to leave the source unchanged; use `accept` only if this exact range should be rewritten now.",
                "",
            ]
        )
    lines.extend(
        [
            "> ✏️ Editable source-cleanup controls",
            f"Source edit decision: `{edit.decision}`",
            f"Source edit note: {edit.review_note or '-'}",
            "> End editable source-cleanup controls",
        ]
    )
    if related:
        related_links: list[str] = []
        proposal_by_id = {item.id: item for item in proposal.items}
        for item_id in related:
            review_item = review_by_id[item_id]
            filename = placement_finding_filename(proposal_by_id[item_id])
            related_links.append(f"[`{item_id}` — {review_item.title}]({filename})")
        lines.extend(["", "Also covers: " + ", ".join(related_links)])
    lines.extend(
        [
            "",
            "#### Before — frozen",
            "",
        ]
    )
    lines.extend(_evidence_markdown(_source_edit_reference(candidate), snapshot))
    lines.extend(
        [
            "",
            "#### After — editable",
            "",
            "The quote frame is presentation only. Keep each replacement line inside it; ContextCanon removes exactly one `>` layer when validating the reviewed replacement.",
            "",
            f'<!-- cc:source-after id="{edit.proposal_id}":start -->',
        ]
    )
    lines.extend(_quote_markdown(edit.replacement.split("\n")))
    lines.extend(
        [
            f'<!-- cc:source-after id="{edit.proposal_id}":end -->',
            "",
            f"Why this source edit: {candidate.rationale}",
        ]
    )
    return lines


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
        if destination
        else "none / outside Node authoring"
    )
    lines = [
        f"## {review_item.proposal_id} — {review_item.title}",
        _binding_line(proposal, review_item.proposal_id),
        f'<!-- cc:placement-item id="{review_item.proposal_id}" authoring-id="{review_item.authoring_id}" -->',
        "",
        "[← STEP 08 index](../STEP-08-placement.md)",
        "",
        "> ✏️ Editable finding controls",
        f"Destination: {destination_text}",
        f"Decision: `{review_item.decision}`",
        f"Kind: `{review_item.kind}`",
        f"Derived action: `{review_item.action}` (from Kind; do not edit)",
        f"Review note: {review_item.review_note or '-'}",
        "> End editable finding controls",
        "",
        "---",
        "",
    ]
    lines.extend(_render_payload(review_item.kind, review_item.payload))
    lines.extend(["", "---", "", "### Source before — frozen Evidence", ""])
    for index, reference in enumerate(item.evidence):
        if index:
            lines.extend(["", "---", ""])
        lines.extend(_evidence_markdown(reference, snapshot))

    linked_edits = [edit for edit in review.source_edits if review_item.proposal_id in edit.linked_item_ids]
    if linked_edits:
        candidate_edits = {edit.id: edit for edit in _review_source_edit_candidates(proposal, snapshot)}
        proposal_by_id = {entry.id: entry for entry in proposal.items}
        review_by_id = {entry.proposal_id: entry for entry in review.items}
        lines.extend(["", "---", "", "### Source after promotion", ""])
        for position, edit in enumerate(linked_edits):
            if position:
                lines.extend(["", "---", ""])
            candidate = candidate_edits[edit.proposal_id]
            owner = candidate.linked_item_ids[0]
            if owner == review_item.proposal_id:
                lines.extend(_render_source_edit(edit, candidate, proposal, review_by_id, snapshot))
            else:
                owner_review = review_by_id[owner]
                owner_file = placement_finding_filename(proposal_by_id[owner])
                lines.append(
                    f"Shared source edit [`{edit.proposal_id}`]({owner_file}#source-edit-{edit.proposal_id.lower()}) also covers this finding and is edited once under `{owner}` — {owner_review.title}."
                )
    elif review_item.action == "promote":
        lines.extend(
            [
                "",
                "---",
                "",
                "### Source after promotion",
                "",
                "No mutable-Markdown rewrite is proposed for this finding. The cited source remains independently useful/authoritative, is not mutable Markdown, or no duplicate-maintenance cleanup was justified.",
            ]
        )
    lines.extend(
        [
            "",
            "---",
            "",
            "### Proposal rationale",
            "",
            item.rationale,
            "",
            f"Original confidence: `{item.confidence}`",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _status_counts(values: Iterable[str]) -> str:
    values = tuple(values)
    return " · ".join(f"{name}: {sum(value == name for value in values)}" for name in ("pending", "accept", "reject"))


def _render_index(
    proposal: OnboardingPlacementProposal,
    review: OnboardingPlacementReview,
) -> str:
    proposal_by_id = {item.id: item for item in proposal.items}
    nodes = {node.key: node for node in proposal.structure.nodes}
    edits_by_item: dict[str, list[PlacementReviewSourceEdit]] = {item.id: [] for item in proposal.items}
    for edit in review.source_edits:
        for item_id in edit.linked_item_ids:
            edits_by_item.setdefault(item_id, []).append(edit)
    lines = [
        "# ContextCanon onboarding placement review",
        SPLIT_LAYOUT_MARKER,
        "",
        "This is the STEP-08 **index**. Work through the linked finding files in `STEP-08-placement/`; each file is one focused review sheet. Re-run `contextcanon onboard placement-review ...` after edits to validate the whole gate and refresh this status index.",
        "",
        "The split layout is still plain Markdown. Frozen Before and editable After text use the same rendered quote frame so paragraphs wrap, tables remain tables, and source headings stay visually inside the comparison region.",
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
        "- `Destination`: the Context Node that owns the finding.",
        "- `Kind`: change this rather than the displayed derived Action.",
        "- `Review note`: optional owner rationale/reminder; use `-` for none.",
        "- Source replacement text remains editable between its hidden `cc:source-after` markers inside one Markdown quote frame.",
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
        "| Decision | Finding | Destination | Kind | Source edits |",
        "|---|---|---|---|---|",
    ]
    for review_item in review.items:
        proposal_item = proposal_by_id[review_item.proposal_id]
        filename = placement_finding_filename(proposal_item)
        destination = nodes.get(review_item.destination_node_key) if review_item.destination_node_key else None
        destination_label = "outside Node authoring" if destination is None else f"{destination.name} (`{destination.path}`)"
        edits = edits_by_item.get(review_item.proposal_id, [])
        edit_label = ", ".join(f"{edit.proposal_id}: `{edit.decision}`" for edit in edits) or "—"
        lines.append(
            f"| `{review_item.decision}` | [`{review_item.proposal_id}` — {review_item.title}](STEP-08-placement/{filename}) | {destination_label} | `{review_item.kind}` | {edit_label} |"
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
                    f'<!-- cc:placement-source id="{source.review_id}" origin="{source.origin}" source-id="{source.source_node_id}" version="{source.source_version}" normalized-digest="{source.source_normalized_digest}" package-digest="{source.source_package_digest}" -->',
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
                        "This Source was selected explicitly by the project owner. When it came from STEP 05, that relationship is already accepted here and is shown only for compact traceability; it is design input, not a claim derived from frozen project Evidence.",
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
        raise _error("STEP-08-placement.md is missing its ContextCanon binding header")
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


def _validate_finding_binding(text: str, proposal: OnboardingPlacementProposal, item_id: str) -> None:
    matches = list(_FINDING_BINDING_RE.finditer(text))
    if len(matches) != 1:
        raise _error(f"split finding {item_id} must contain exactly one ContextCanon finding binding")
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
        raise _error(f"split finding {item_id} binding does not match the exact placement proposal")


def _validate_replacement_quote_frames(text: str, item_id: str) -> None:
    lines = text.splitlines()
    active: str | None = None
    content: list[str] = []
    for line in lines:
        start = _SOURCE_AFTER_START_RE.match(line)
        if start is not None:
            if active is not None:
                raise _error(f"split finding {item_id} has nested source-after markers")
            active = start.group("id")
            content = []
            continue
        end = _SOURCE_AFTER_END_RE.match(line)
        if end is not None:
            if active != end.group("id"):
                raise _error(f"split finding {item_id} has mismatched source-after markers")
            if any(entry != ">" and not entry.startswith("> ") for entry in content):
                raise _error(
                    f"Source edit {active} in split finding {item_id} must keep every editable replacement line inside the single Markdown quote frame"
                )
            active = None
            content = []
            continue
        if active is not None:
            content.append(line)
    if active is not None:
        raise _error(f"split finding {item_id} has an unterminated source-after marker")


def _parse_split(index_path: Path, proposal: OnboardingPlacementProposal, snapshot_root: Path) -> OnboardingPlacementReview:
    index_path = index_path.resolve()
    try:
        index_text = index_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContextCanonError(f"Missing onboarding placement review: {index_path}") from exc
    except UnicodeDecodeError as exc:
        raise _error("STEP-08-placement.md is not valid UTF-8") from exc
    if SPLIT_LAYOUT_MARKER not in index_text:
        return _load_monolithic_placement_review(index_path, proposal, snapshot_root)
    _validate_index_binding(index_text, proposal)

    review_dir = placement_review_directory(index_path)
    if not review_dir.is_dir() or review_dir.is_symlink():
        raise _error(f"split STEP-08 review directory is missing or invalid: {review_dir}")
    expected = {placement_finding_filename(item): item for item in proposal.items}
    actual_entries = {entry.name: entry for entry in review_dir.iterdir()}
    missing = sorted(set(expected) - set(actual_entries))
    foreign = sorted(set(actual_entries) - set(expected))
    if missing:
        raise _error("split STEP-08 review is missing finding files: " + ", ".join(missing))
    if foreign:
        raise _error("split STEP-08 review contains foreign files/directories: " + ", ".join(foreign))

    finding_texts: list[str] = []
    for item in proposal.items:
        path = actual_entries[placement_finding_filename(item)]
        if not path.is_file() or path.is_symlink():
            raise _error(f"split finding path is not a regular file: {path.name}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise _error(f"split finding {path.name} is not valid UTF-8") from exc
        _validate_finding_binding(text, proposal, item.id)
        _validate_replacement_quote_frames(text, item.id)
        finding_texts.append(text.rstrip())

    # The old v1 semantic parser remains the single validation contract. Feed it
    # one synthetic document with findings first and the compact index (including
    # reusable Source controls and exact proposal binding) last.
    synthetic = "\n\n".join(finding_texts + [index_text.rstrip()]) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=".contextcanon-placement-split-", suffix=".md", dir=index_path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(synthetic)
        return _load_monolithic_placement_review(temporary, proposal, snapshot_root)
    finally:
        temporary.unlink(missing_ok=True)


def load_split_placement_review(
    path: Path, proposal: OnboardingPlacementProposal, snapshot_root: Path
) -> OnboardingPlacementReview:
    return _parse_split(path, proposal, snapshot_root)


def _write_split_layout(
    index_path: Path,
    proposal: OnboardingPlacementProposal,
    review: OnboardingPlacementReview,
    snapshot_root: Path,
) -> None:
    index_path = index_path.resolve()
    review_dir = placement_review_directory(index_path)
    if review_dir.exists() or review_dir.is_symlink():
        raise _error(f"refusing to replace existing STEP-08 review directory: {review_dir}")
    snapshot = load_evidence_snapshot(snapshot_root)
    review_by_id = {item.proposal_id: item for item in review.items}
    temporary_dir = Path(tempfile.mkdtemp(prefix=f".{review_dir.name}.", dir=index_path.parent))
    published_dir = False
    try:
        for item in proposal.items:
            target = temporary_dir / placement_finding_filename(item)
            write_utf8(target, _render_finding(item, review_by_id[item.id], proposal, review, snapshot))
        os.replace(temporary_dir, review_dir)
        published_dir = True
        try:
            write_utf8(index_path, _render_index(proposal, review))
        except BaseException:
            shutil.rmtree(review_dir, ignore_errors=True)
            published_dir = False
            raise
    finally:
        if not published_dir and temporary_dir.exists():
            shutil.rmtree(temporary_dir, ignore_errors=True)


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
    review_dir = placement_review_directory(path)
    if path.exists():
        if tuple(owner_source_specs):
            raise _error(
                "--owner-source is only used when STEP-08 review is first created; edit the existing human review instead of silently changing it"
            )
        try:
            index_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise _error("STEP-08-placement.md is not valid UTF-8") from exc
        if SPLIT_LAYOUT_MARKER not in index_text:
            if review_dir.exists() or review_dir.is_symlink():
                raise _error(
                    "legacy STEP-08 review still exists but the split review directory already exists; refusing to guess which human edits are authoritative"
                )
            legacy = _load_monolithic_placement_review(path, proposal, snapshot_root)
            _write_split_layout(path, proposal, legacy, snapshot_root)
            loaded = _parse_split(path, proposal, snapshot_root)
            return loaded, False
        loaded = _parse_split(path, proposal, snapshot_root)
        # Refresh only the framework-owned compact index/status. Finding files are
        # the human working sheets and are never regenerated over existing edits.
        write_utf8(path, _render_index(proposal, loaded))
        return loaded, False

    if review_dir.exists() or review_dir.is_symlink():
        raise _error(f"STEP-08 review index is missing but its split directory already exists: {review_dir}")
    path.parent.mkdir(parents=True, exist_ok=True)
    review = _initial_review(
        proposal,
        snapshot_root,
        owner_source_specs=owner_source_specs,
        owner_source_whys=owner_source_whys,
        preaccepted_owner_sources=preaccepted_owner_sources,
    )
    _write_split_layout(path, proposal, review, snapshot_root)
    return _parse_split(path, proposal, snapshot_root), True
