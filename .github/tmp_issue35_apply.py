from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing replacement target: {label}")
    if text.count(old) != 1:
        raise SystemExit(f"replacement target is not unique ({text.count(old)}): {label}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Split STEP-08 layout module.
# ---------------------------------------------------------------------------
split_module = r'''from __future__ import annotations

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
'''
Path("src/contextcanon/onboarding_placement_split_review.py").write_text(split_module, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Keep the existing v1 parser as the semantic engine, but expose split wrappers.
# ---------------------------------------------------------------------------
review_path = Path("src/contextcanon/onboarding_placement_review.py")
review = review_path.read_text(encoding="utf-8")
review = replace_once(
    review,
    "def load_placement_review(\n    path: Path, proposal: OnboardingPlacementProposal, snapshot_root: Path\n) -> OnboardingPlacementReview:\n",
    "def _load_monolithic_placement_review(\n    path: Path, proposal: OnboardingPlacementProposal, snapshot_root: Path\n) -> OnboardingPlacementReview:\n",
    "rename monolithic loader",
)
review = replace_once(
    review,
    "        replacement = \"\\n\".join(block[source_start + 1 : source_end]).strip(\"\\n\")\n",
    "        replacement_lines = block[source_start + 1 : source_end]\n"
    "        if replacement_lines and all(line == \">\" or line.startswith(\"> \") for line in replacement_lines):\n"
    "            replacement_lines = [\"\" if line == \">\" else line[2:] for line in replacement_lines]\n"
    "        replacement = \"\\n\".join(replacement_lines).strip(\"\\n\")\n",
    "strip one split-review quote layer",
)
review = replace_once(
    review,
    "def create_or_load_placement_review(\n",
    "def _create_or_load_monolithic_placement_review(\n",
    "rename monolithic create/load",
)
review = review.replace(
    "        return load_placement_review(path, proposal, snapshot_root), False\n",
    "        return _load_monolithic_placement_review(path, proposal, snapshot_root), False\n",
    1,
)
review = review.replace(
    "    return load_placement_review(path, proposal, snapshot_root), True\n",
    "    return _load_monolithic_placement_review(path, proposal, snapshot_root), True\n",
    1,
)
review += r'''


def load_placement_review(
    path: Path, proposal: OnboardingPlacementProposal, snapshot_root: Path
) -> OnboardingPlacementReview:
    from .onboarding_placement_split_review import load_split_placement_review

    return load_split_placement_review(path, proposal, snapshot_root)


def create_or_load_placement_review(
    path: Path,
    proposal: OnboardingPlacementProposal,
    snapshot_root: Path,
    *,
    owner_source_specs: Iterable[str] = (),
    owner_source_whys: Mapping[str, str] | None = None,
    preaccepted_owner_sources: bool = False,
) -> tuple[OnboardingPlacementReview, bool]:
    from .onboarding_placement_split_review import create_or_load_split_placement_review

    return create_or_load_split_placement_review(
        path,
        proposal,
        snapshot_root,
        owner_source_specs=owner_source_specs,
        owner_source_whys=owner_source_whys,
        preaccepted_owner_sources=preaccepted_owner_sources,
    )
'''
review_path.write_text(review, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Workspace owns the index plus its finding directory.
# ---------------------------------------------------------------------------
workspace_path = Path("src/contextcanon/onboarding_workspace.py")
workspace = workspace_path.read_text(encoding="utf-8")
workspace = replace_once(
    workspace,
    'PLACEMENT_REVIEW_NAME = "STEP-08-placement.md"\n',
    'PLACEMENT_REVIEW_NAME = "STEP-08-placement.md"\nPLACEMENT_REVIEW_DIR_NAME = "STEP-08-placement"\n',
    "workspace split dir constant",
)
workspace = replace_once(
    workspace,
    "    def placement_path(self) -> Path:\n        return self.root / PLACEMENT_REVIEW_NAME\n\n",
    "    def placement_path(self) -> Path:\n        return self.root / PLACEMENT_REVIEW_NAME\n\n"
    "    @property\n"
    "    def placement_dir_path(self) -> Path:\n"
    "        return self.root / PLACEMENT_REVIEW_DIR_NAME\n\n",
    "workspace split dir property",
)
workspace = replace_once(
    workspace,
    '- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.\n',
    '- `{PLACEMENT_REVIEW_NAME}` — compact STEP-08 index/status; linked files in `{PLACEMENT_REVIEW_DIR_NAME}/` are the human-owned per-finding placement decisions.\n',
    "workspace README artifact wording",
)
workspace = replace_once(
    workspace,
    '- **Human gate 2:** review/edit `STEP-08-placement.md`.\n',
    '- **Human gate 2:** use `STEP-08-placement.md` as the index and review/edit the linked files under `STEP-08-placement/`.\n',
    "workspace PLAN human gate wording",
)
workspace_path.write_text(workspace, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Reset removes the framework-owned split review directory at STEP 08.
# ---------------------------------------------------------------------------
reset_path = Path("src/contextcanon/onboarding_reset.py")
reset = reset_path.read_text(encoding="utf-8")
reset = replace_once(reset, "import re\n", "import re\nimport shutil\n", "reset shutil import")
reset = replace_once(
    reset,
    "    PLACEMENT_REVIEW_NAME,\n",
    "    PLACEMENT_REVIEW_NAME,\n    PLACEMENT_REVIEW_DIR_NAME,\n",
    "reset split dir import",
)
reset = replace_once(
    reset,
    "    PLACEMENT_REVIEW_NAME: 8,\n",
    "    PLACEMENT_REVIEW_NAME: 8,\n    PLACEMENT_REVIEW_DIR_NAME: 8,\n",
    "reset split dir step",
)
reset = replace_once(
    reset,
    "        if path.is_file() or path.is_symlink():\n            path.unlink()\n            removed.append(path.name)\n",
    "        if name == PLACEMENT_REVIEW_DIR_NAME and path.is_dir() and not path.is_symlink():\n"
    "            shutil.rmtree(path)\n"
    "            removed.append(path.name + \"/\")\n"
    "        elif path.is_file() or path.is_symlink():\n"
    "            path.unlink()\n"
    "            removed.append(path.name)\n",
    "reset split dir deletion",
)
reset_path.write_text(reset, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# CLI points operators to the index + linked sheets, not a giant file.
# ---------------------------------------------------------------------------
cli_path = Path("src/contextcanon/cli.py")
cli = cli_path.read_text(encoding="utf-8")
cli = replace_once(
    cli,
    "                        f\"Inspect `{workspace.placement_audit_path.name}` source-by-source, edit `{workspace.placement_path.name}` where needed, and set every item/Source-edit/Source Decision to `accept` or `reject`. \"\n"
    "                        f\"Then rerun `contextcanon onboard placement-review {_snapshot_cli(snapshot)}`; it validates the edited human gate and regenerates the audit.\"\n",
    "                        f\"Inspect `{workspace.placement_audit_path.name}` source-by-source, then use `{workspace.placement_path.name}` as the index and edit its linked finding files under `{workspace.placement_dir_path.name}/`. \"\n"
    "                        f\"Set every item/Source-edit/Source Decision to `accept` or `reject`, then rerun `contextcanon onboard placement-review {_snapshot_cli(snapshot)}`; it validates the split human gate, refreshes the index, and regenerates the audit.\"\n",
    "CLI split review next action",
)
cli = replace_once(
    cli,
    '                        "Return to `STEP-08-placement.md`, resolve all pending decisions, and preview again."\n',
    '                        "Return to the `STEP-08-placement.md` index and its linked finding files, resolve all pending decisions, and preview again."\n',
    "CLI incomplete preview wording",
)
cli_path.write_text(cli, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Adapt the focused editable-review regression suite to the split layout.
# ---------------------------------------------------------------------------
test_review = r'''from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.onboarding_placement import load_onboarding_placement_proposal
from contextcanon.onboarding_placement_review import (
    create_or_load_placement_review,
    load_placement_review,
    render_placement_review,
)
from contextcanon.onboarding_placement_split_review import (
    placement_finding_path,
    placement_review_directory,
)
from contextcanon.parser import ContextCanonError
import tests.test_onboarding_placement as placement_fixture


class EditablePlacementReviewTests(unittest.TestCase):
    def make_proposal(self, *, owner_source: bool = True):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        if owner_source:
            raw["source_reuses"] = []
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        specs = [f"N-001={package.metadata.id}"] if owner_source else []
        return prepared, workspace, source_root, package, proposal, specs

    def make_review(self, *, owner_source: bool = True):
        prepared, workspace, source_root, package, proposal, specs = self.make_proposal(owner_source=owner_source)
        review, created = create_or_load_placement_review(
            workspace.placement_path,
            proposal,
            prepared.snapshot_root,
            owner_source_specs=specs,
        )
        return prepared, workspace, source_root, package, proposal, review, created

    def finding(self, workspace, proposal, item_id="P-001") -> Path:
        item = next(item for item in proposal.items if item.id == item_id)
        return placement_finding_path(workspace.placement_path, item)

    def test_review_is_split_navigable_and_owner_source_is_distinct(self):
        prepared, workspace, source_root, package, proposal, review, created = self.make_review()
        self.assertTrue(created)
        index = workspace.placement_path.read_text(encoding="utf-8")
        finding = self.finding(workspace, proposal).read_text(encoding="utf-8")
        review_dir = placement_review_directory(workspace.placement_path)
        self.assertTrue(review_dir.is_dir())
        self.assertEqual(len(list(review_dir.glob("*.md"))), len(proposal.items))
        self.assertIn("cc:placement-review-layout: split-v1", index)
        self.assertIn("## Findings", index)
        self.assertIn("STEP-08-placement/", index)
        self.assertNotIn("### Source before — frozen Evidence", index)
        self.assertIn("### Into Node — editable", finding)
        self.assertIn("### Source before — frozen Evidence", finding)
        self.assertIn("✏️ Editable finding controls", finding)
        self.assertNotIn("```text", finding)
        self.assertIn("\n> ", finding)
        self.assertIn('origin="owner-selected"', index)
        self.assertEqual(len(review.sources), 1)
        self.assertEqual(review.sources[0].origin, "owner-selected")

    def test_human_edits_round_trip_and_authoring_identity_stays_stable(self):
        prepared, workspace, source_root, package, proposal, first, _ = self.make_review(owner_source=False)
        first_id = first.items[0].authoring_id
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8")
        text = text.replace("## P-001 — Repository is the installation specification", "## P-001 — Canonical installation authority")
        text = text.replace("Decision: `pending`", "Decision: `accept`", 1)
        text = text.replace(
            "Statement: The repository is the installation specification.",
            "Statement: The repository is the canonical installation specification.",
            1,
        )
        path.write_text(text, encoding="utf-8")
        second = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(second.items[0].authoring_id, first_id)
        self.assertEqual(second.items[0].title, "Canonical installation authority")
        self.assertEqual(second.items[0].decision, "accept")
        self.assertEqual(second.items[0].payload["statement"], "The repository is the canonical installation specification.")
        self.assertEqual(len(second.source_edits), 1)

    def test_existing_human_review_is_loaded_not_overwritten(self):
        prepared, workspace, source_root, package, proposal, first, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8").replace("Decision: `pending`", "Decision: `reject`", 1)
        path.write_text(text, encoding="utf-8")
        loaded, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertFalse(created)
        self.assertEqual(loaded.items[0].decision, "reject")
        self.assertEqual(loaded.items[0].authoring_id, first.items[0].authoring_id)
        self.assertIn("`reject`", workspace.placement_path.read_text(encoding="utf-8"))

    def test_changed_proposal_refuses_to_replace_existing_review(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        index = workspace.placement_path.read_text(encoding="utf-8")
        workspace.placement_path.write_text(index.replace(proposal.proposal_digest, "0" * 64), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "new review path"):
            create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_action_is_derived_from_kind_and_rendered_text_is_not_a_control(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8").replace(
            "Derived action: `promote` (from Kind; do not edit)",
            "Derived action: `reference` (tampered display text)",
            1,
        )
        path.write_text(text, encoding="utf-8")
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(loaded.items[0].kind, "rule")
        self.assertEqual(loaded.items[0].action, "promote")

    def test_invalid_or_duplicate_stable_authoring_id_is_rejected_early(self):
        prepared, workspace, source_root, package, proposal, review, _ = self.make_review(owner_source=False)
        first_id = review.items[0].authoring_id
        second_id = review.items[1].authoring_id
        first_path = self.finding(workspace, proposal, "P-001")
        second_path = self.finding(workspace, proposal, "P-002")
        original_first = first_path.read_text(encoding="utf-8")
        first_path.write_text(original_first.replace(f'authoring-id="{first_id}"', 'authoring-id="bad id"', 1), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "invalid stable authoring ID"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        first_path.write_text(original_first, encoding="utf-8")
        second = second_path.read_text(encoding="utf-8")
        second_path.write_text(second.replace(f'authoring-id="{second_id}"', f'authoring-id="{first_id}"', 1), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "duplicate stable authoring ID"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_source_after_is_visually_quoted_but_round_trips_as_plain_markdown(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8")
        old = "> Installation authority is maintained in [AI Workstation Context](../CONTEXT.md)."
        new_plain = "Architecture starts here; maintained installation authority lives in [AI Workstation Context](../CONTEXT.md)."
        text = text.replace(old, "> " + new_plain, 1)
        text = text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        text = text.replace("Decision: `pending`", "Decision: `accept`", 1)
        path.write_text(text, encoding="utf-8")
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(loaded.source_edits[0].replacement, new_plain)
        self.assertEqual(loaded.source_edits[0].decision, "accept")

    def test_source_after_requires_single_quote_frame(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8").replace(
            "> Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).",
            "Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).",
            1,
        )
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "single Markdown quote frame"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_source_edit_cannot_be_accepted_when_linked_finding_is_rejected(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8")
        text = text.replace("Decision: `pending`", "Decision: `reject`", 1)
        text = text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "cannot be accepted until all linked promoted findings are accepted"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_state_and_plan_are_rendered_as_into_node(self):
        from contextcanon.onboarding_placement_review import _render_payload
        for kind in ("state", "plan"):
            lines = _render_payload(kind, {"text": "Example", "wording_origin": "synthesized"})
            self.assertEqual(lines[0], "### Into Node — editable")

    def test_promote_without_llm_source_edit_gets_rejected_editable_human_fallback(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        raw["source_edits"] = []
        raw["items"][0]["evidence"] = [{"path": "README.md", "sha256": readme.sha256, "start_line": 2, "end_line": 2}]
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertTrue(created)
        self.assertEqual(len(review.source_edits), 1)
        fallback = review.source_edits[0]
        self.assertTrue(fallback.proposal_id.startswith("H-"))
        self.assertEqual(fallback.decision, "reject")
        path = self.finding(workspace, proposal)
        rendered = path.read_text(encoding="utf-8")
        self.assertIn("Optional source cleanup — independent from promotion", rendered)
        self.assertIn("Source edit decision: `reject`", rendered)
        replacement = "Architecture in one sentence. Maintained detail lives in [AI Workstation Context](../CONTEXT.md)."
        start_marker = f'<!-- cc:source-after id="{fallback.proposal_id}":start -->'
        end_marker = f'<!-- cc:source-after id="{fallback.proposal_id}":end -->'
        start = rendered.index(start_marker) + len(start_marker)
        end = rendered.index(end_marker, start)
        rendered = rendered[:start] + "\n> " + replacement + "\n" + rendered[end:]
        rendered = rendered.replace("Decision: `pending`", "Decision: `accept`", 1)
        rendered = rendered.replace("Source edit decision: `reject`", "Source edit decision: `accept`", 1)
        path.write_text(rendered, encoding="utf-8")
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(loaded.source_edits[0].decision, "accept")
        self.assertEqual(loaded.source_edits[0].replacement, replacement)

    def test_review_fallback_does_not_offer_cleanup_for_topic_resource(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        raw["source_edits"] = []
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertTrue(created)
        self.assertEqual(review.source_edits, ())
        combined = "\n".join(path.read_text(encoding="utf-8") for path in placement_review_directory(workspace.placement_path).glob("*.md"))
        self.assertNotIn("Optional source cleanup", combined)

    def test_multiple_source_edits_owned_by_one_finding_parse_independently(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        raw["items"][0]["evidence"][0]["start_line"] = 1
        raw["source_edits"].append(
            {
                "id": "E-002",
                "path": "docs/architecture.md",
                "sha256": architecture.sha256,
                "start_line": 1,
                "end_line": 1,
                "linked_item_ids": ["P-001"],
                "replacement": "# Architecture gateway",
                "rationale": "Keep a compact architecture gateway beside the promoted canonical rule.",
                "confidence": "high",
            }
        )
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertTrue(created)
        rendered = self.finding(workspace, proposal).read_text(encoding="utf-8")
        self.assertEqual(rendered.count("Source edit note:"), 2)
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual([edit.proposal_id for edit in loaded.source_edits], ["E-001", "E-002"])
        self.assertEqual(
            [edit.replacement for edit in loaded.source_edits],
            [
                "Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).",
                "# Architecture gateway",
            ],
        )

    def test_legacy_monolith_migrates_without_losing_human_decisions(self):
        prepared, workspace, source_root, package, proposal, specs = self.make_proposal(owner_source=False)
        legacy = render_placement_review(proposal, prepared.snapshot_root)
        legacy = legacy.replace("## P-001 — Repository is the installation specification", "## P-001 — Human edited title", 1)
        legacy = legacy.replace("Decision: `pending`", "Decision: `accept`", 1)
        legacy = legacy.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        workspace.placement_path.write_text(legacy, encoding="utf-8")
        review, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertFalse(created)
        self.assertEqual(review.items[0].title, "Human edited title")
        self.assertEqual(review.items[0].decision, "accept")
        self.assertEqual(review.source_edits[0].decision, "accept")
        self.assertTrue(placement_review_directory(workspace.placement_path).is_dir())
        self.assertIn("cc:placement-review-layout: split-v1", workspace.placement_path.read_text(encoding="utf-8"))

    def test_missing_or_foreign_split_finding_is_rejected(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        first = self.finding(workspace, proposal)
        original = first.read_text(encoding="utf-8")
        first.unlink()
        with self.assertRaisesRegex(ContextCanonError, "missing finding files"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        first.write_text(original, encoding="utf-8")
        foreign = placement_review_directory(workspace.placement_path) / "notes.md"
        foreign.write_text("human stray file", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "foreign files"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)


if __name__ == "__main__":
    unittest.main()
'''
Path("tests/test_onboarding_placement_review.py").write_text(test_review, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Publication tests accept all decisions across split finding sheets + index.
# ---------------------------------------------------------------------------
publish_path = Path("tests/test_onboarding_placement_publish.py")
publish = publish_path.read_text(encoding="utf-8")
publish = replace_once(
    publish,
    "from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review\n",
    "from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review\n"
    "from contextcanon.onboarding_placement_split_review import placement_finding_path\n",
    "publication split helper import",
)
publish = replace_once(
    publish,
    "        review_text = workspace.placement_path.read_text(encoding=\"utf-8\").replace(\n"
    "            \"Decision: `pending`\", \"Decision: `accept`\"\n"
    "        ).replace(\"Source edit decision: `pending`\", \"Source edit decision: `accept`\")\n"
    "        workspace.placement_path.write_text(review_text, encoding=\"utf-8\")\n"
    "        review = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)\n",
    "        for item in proposal.items:\n"
    "            finding_path = placement_finding_path(workspace.placement_path, item)\n"
    "            review_text = finding_path.read_text(encoding=\"utf-8\").replace(\n"
    "                \"Decision: `pending`\", \"Decision: `accept`\"\n"
    "            ).replace(\"Source edit decision: `pending`\", \"Source edit decision: `accept`\")\n"
    "            finding_path.write_text(review_text, encoding=\"utf-8\")\n"
    "        index_text = workspace.placement_path.read_text(encoding=\"utf-8\").replace(\n"
    "            \"Decision: `pending`\", \"Decision: `accept`\"\n"
    "        )\n"
    "        workspace.placement_path.write_text(index_text, encoding=\"utf-8\")\n"
    "        review = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)\n",
    "publication accept split review",
)
publish_path.write_text(publish, encoding="utf-8", newline="\n")

print("Issue 35 product patch applied")
