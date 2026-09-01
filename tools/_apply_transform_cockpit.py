from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8", newline="\n")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


PLAN_BLOCK = '''

#### Block J — placement transformation cockpit and canonical-source cleanup

Purpose: make the human placement gate show the complete reviewed transformation rather than only the destination meaning, so onboarding can actually reduce duplicate canonical knowledge instead of merely creating a second copy.

- [ ] Make every promoted finding show the exact editable destination meaning under an honest `Into Node` label when it is actually published into Node authoring; label State/Plan honestly as node-local follow-up until their publication surface is designed.
- [ ] Extend the semantic placement contract with reviewed mutable-Markdown source edits: exact frozen range, linked promoted findings, and a proposed concise replacement/orientation that remains close to source wording when meaning is uncertain.
- [ ] Render `Source before — frozen Evidence` and editable `Source after promotion` in `STEP-07-placement.md`, with one shared edit owning overlapping/multi-finding source ranges so the same replacement is never edited twice.
- [ ] Validate source-edit ranges deterministically: mutable Markdown only, exact frozen hash/range, promoted linked findings only, complete Evidence coverage, and no overlapping edits in one source file.
- [ ] Include accepted source-document deltas in publication preview and apply them transactionally with Context Node changes; accept either original frozen bytes or the exact already-published reviewed result for idempotent reruns.
- [ ] Persist Source-catalog and owner-selected Source run inputs in machine-owned snapshot state so reset/workspace recreation cannot forget them.
- [ ] Tighten placement guidance toward plain source-shaped wording, consolidated Node overviews, and aggressively readable source summaries only when meaning is unambiguous; avoid academic/corporate abstraction and preserve wording when uncertain.
- [ ] Add focused regressions for cockpit rendering/edit round-trip, shared source edits, overlap/authority safety, transactional document publication/idempotency, and run-input recovery; then run the complete suite plus build/check.
'''


def plan() -> None:
    path = "PLAN.md"
    text = read(path)
    if "#### Block J — placement transformation cockpit" not in text:
        text = text.rstrip() + PLAN_BLOCK + "\n"
        write(path, text)


def patch_placement_model() -> None:
    path = "src/contextcanon/onboarding_placement.py"
    text = read(path)
    text = replace_once(
        text,
        '''@dataclass(frozen=True)\nclass OnboardingPlacementProposal:\n    evidence_digest: str\n    structure_digest: str\n    items: tuple[PlacementItem, ...]\n    source_reuses: tuple[PlacementSourceReuse, ...]\n    proposal_digest: str\n    structure: HumanStructurePlan\n    catalog_packages: tuple[CompiledPackage, ...]\n''',
        '''@dataclass(frozen=True)\nclass PlacementSourceEdit:\n    id: str\n    path: str\n    sha256: str\n    start_line: int\n    end_line: int\n    linked_item_ids: tuple[str, ...]\n    replacement: str\n    rationale: str\n    confidence: str\n\n    def to_dict(self) -> dict[str, object]:\n        return {\n            "id": self.id,\n            "path": self.path,\n            "sha256": self.sha256,\n            "start_line": self.start_line,\n            "end_line": self.end_line,\n            "linked_item_ids": list(self.linked_item_ids),\n            "replacement": self.replacement,\n            "rationale": self.rationale,\n            "confidence": self.confidence,\n        }\n\n\n@dataclass(frozen=True)\nclass OnboardingPlacementProposal:\n    evidence_digest: str\n    structure_digest: str\n    items: tuple[PlacementItem, ...]\n    source_edits: tuple[PlacementSourceEdit, ...]\n    source_reuses: tuple[PlacementSourceReuse, ...]\n    proposal_digest: str\n    structure: HumanStructurePlan\n    catalog_packages: tuple[CompiledPackage, ...]\n''',
        "placement proposal dataclass",
    )
    text = replace_once(
        text,
        '''def _optional_string(value: object, label: str) -> str | None:\n    if value is None:\n        return None\n    return _string(value, label)\n''',
        '''def _optional_string(value: object, label: str) -> str | None:\n    if value is None:\n        return None\n    return _string(value, label)\n\n\ndef _replacement(value: object, label: str) -> str:\n    if not isinstance(value, str):\n        raise _error(f"{label} must be a string")\n    if "\\x00" in value:\n        raise _error(f"{label} contains an unsupported NUL character")\n    return value.replace("\\r\\n", "\\n").replace("\\r", "\\n").strip("\\n")\n''',
        "replacement helper",
    )
    text = replace_once(
        text,
        '''    raw = _read_json(proposal_path)\n    _exact_keys(raw, {"schema", "evidence_digest", "structure_digest", "items", "source_reuses"}, "proposal")\n''',
        '''    raw = _read_json(proposal_path)\n    required_top = {"schema", "evidence_digest", "structure_digest", "items", "source_reuses"}\n    allowed_top = required_top | {"source_edits"}\n    unknown_top = sorted(set(raw) - allowed_top)\n    missing_top = sorted(required_top - set(raw))\n    if unknown_top or missing_top:\n        detail = []\n        if missing_top:\n            detail.append(f"missing fields: {', '.join(missing_top)}")\n        if unknown_top:\n            detail.append(f"unknown fields: {', '.join(unknown_top)}")\n        raise _error(f"proposal has {'; '.join(detail)}")\n''',
        "optional source edits top level",
    )
    marker = '''    raw_reuses = raw["source_reuses"]\n'''
    source_parser = '''    raw_source_edits = raw.get("source_edits", [])\n    if not isinstance(raw_source_edits, list):\n        raise _error("source_edits must be a list")\n    source_edits: list[PlacementSourceEdit] = []\n    item_by_id = {item.id: item for item in items}\n    occupied: dict[str, list[tuple[int, int, str]]] = {}\n    fixed_markdown = set(structure.fixed_markdown)\n    for index, raw_edit in enumerate(raw_source_edits):\n        label = f"source_edits[{index}]"\n        if not isinstance(raw_edit, dict):\n            raise _error(f"{label} must be an object")\n        _exact_keys(\n            raw_edit,\n            {"id", "path", "sha256", "start_line", "end_line", "linked_item_ids", "replacement", "rationale", "confidence"},\n            label,\n        )\n        edit_id = _string(raw_edit["id"], f"{label}.id")\n        if edit_id in seen_ids:\n            raise _error(f"duplicate proposal id {edit_id}")\n        seen_ids.add(edit_id)\n        edit_path = _string(raw_edit["path"], f"{label}.path")\n        entry = snapshot.by_path.get(edit_path)\n        if entry is None:\n            raise _error(f"{label}.path is not present in frozen Evidence: {edit_path}")\n        if not edit_path.lower().endswith(".md"):\n            raise _error(f"{label}.path must be mutable Markdown")\n        if edit_path in fixed_markdown:\n            raise _error(f"{label}.path is fixed Markdown and cannot receive a source edit")\n        if raw_edit["sha256"] != entry.sha256:\n            raise _error(f"{label}.sha256 does not match frozen Evidence: {edit_path}")\n        start = raw_edit["start_line"]\n        end = raw_edit["end_line"]\n        if not isinstance(start, int) or isinstance(start, bool) or start < 1:\n            raise _error(f"{label}.start_line must be a positive integer")\n        if not isinstance(end, int) or isinstance(end, bool) or end < start or end > entry.line_count:\n            raise _error(f"{label}.end_line is outside the frozen Evidence range")\n        linked_raw = raw_edit["linked_item_ids"]\n        if not isinstance(linked_raw, list) or not linked_raw:\n            raise _error(f"{label}.linked_item_ids must be a non-empty list")\n        linked = tuple(_string(value, f"{label}.linked_item_ids[{i}]") for i, value in enumerate(linked_raw))\n        if len(linked) != len(set(linked)):\n            raise _error(f"{label}.linked_item_ids contains duplicates")\n        covered: set[int] = set()\n        for linked_id in linked:\n            linked_item = item_by_id.get(linked_id)\n            if linked_item is None:\n                raise _error(f"{label} references unknown placement item {linked_id}")\n            if linked_item.action != "promote":\n                raise _error(f"{label} may link only promoted placement items; {linked_id} uses {linked_item.action}")\n            for reference in linked_item.evidence:\n                if reference.path == edit_path:\n                    covered.update(range(reference.start_line, reference.end_line + 1))\n        if not set(range(start, end + 1)).issubset(covered):\n            raise _error(f"{label} range is not fully covered by Evidence of its linked promoted items")\n        for other_start, other_end, other_id in occupied.setdefault(edit_path, []):\n            if not (end < other_start or start > other_end):\n                raise _error(f"{label} overlaps source edit {other_id} in {edit_path}")\n        occupied[edit_path].append((start, end, edit_id))\n        source_edits.append(\n            PlacementSourceEdit(\n                id=edit_id,\n                path=edit_path,\n                sha256=entry.sha256,\n                start_line=start,\n                end_line=end,\n                linked_item_ids=linked,\n                replacement=_replacement(raw_edit["replacement"], f"{label}.replacement"),\n                rationale=_string(raw_edit["rationale"], f"{label}.rationale"),\n                confidence=_confidence(raw_edit["confidence"], f"{label}.confidence"),\n            )\n        )\n\n'''
    if marker not in text:
        raise RuntimeError("source parser anchor missing")
    text = text.replace(marker, source_parser + marker, 1)
    text = replace_once(
        text,
        '''        "items": [item.to_dict() for item in items],\n        "source_reuses": [reuse.to_dict() for reuse in reuses],\n''',
        '''        "items": [item.to_dict() for item in items],\n        "source_edits": [edit.to_dict() for edit in source_edits],\n        "source_reuses": [reuse.to_dict() for reuse in reuses],\n''',
        "normalized source edits",
    )
    text = replace_once(
        text,
        '''        items=tuple(items),\n        source_reuses=tuple(reuses),\n''',
        '''        items=tuple(items),\n        source_edits=tuple(source_edits),\n        source_reuses=tuple(reuses),\n''',
        "return source edits",
    )
    write(path, text)


def patch_instruction() -> None:
    path = "src/contextcanon/onboarding_placement_instruction.py"
    text = read(path)
    text = text.replace('PLACEMENT_INSTRUCTION_SCHEMA = "contextcanon/onboarding-placement-instruction/v0"', 'PLACEMENT_INSTRUCTION_SCHEMA = "contextcanon/onboarding-placement-instruction/v1"')
    text = replace_once(
        text,
        '            "Other project Markdown may be treated as mutable: ownership may move into ContextCanon and a later, separate cleanup may shorten/remove redundant prose after human review. Non-Markdown document authorities are unsupported in this placement version.",',
        '            "Other project Markdown may be treated as mutable: when reviewed meaning is promoted into ContextCanon, this same placement pass may propose a concise replacement/orientation for the exact source range so the final repository does not keep two canonical copies. Non-Markdown document authorities are not rewritten by source edits.",',
        "mutable policy",
    )
    old_rules = '''        "1. Preserve precise existing language for facts, constraints, and Rules when it is already the best canonical wording; when a clear self-contained statement already says the right thing, use it verbatim. **Overview is different:** it is a condensation task, not a quotation task. When source orientation mixes purpose with platform/version/current-state detail, synthesize the short durable purpose now and place volatile compatibility/version detail in `state` instead.",\n        "2. Do the semantic cleanup in this placement pass. A later Markdown cleanup is only the reviewed mutation of source documents; it must not require the owner to reopen the same semantic design problem. Use `lightly-edited` for small self-containment edits and `synthesized` when a sharper canonical summary or decomposition is genuinely better than the source sentence.",\n        "3. The primary question is **where should this meaning be maintained from now on?** Minimize future redundancy. Every durable meaning should have one canonical maintenance surface. Do not preserve a poor current file boundary merely because the text happens to live there.",\n        "4. Use kind `overview` plus action `promote` for short durable orientation about what one Node owns or is responsible for. Prefer one crisp sentence or several separate atomic overview findings over a semicolon/comma-heavy snake sentence. If one source passage contains several independently maintainable responsibilities, split them into separate findings so the resulting Node reads naturally as bullets.",\n        "5. Use action `promote` when project-owned canonical Overview, Rule, State, or Plan meaning should be maintained at the destination ContextCanon surface. The destination then becomes the **single canonical maintenance surface for that meaning**. Promotion deliberately does not delete source prose during initial publication, so a temporary duplicate may exist during migration; that duplication is not the desired steady state. A later separately reviewed cleanup should remove the duplicate or replace it with concise human orientation plus a link/reference to the owning Context Node. Do not plan to maintain the same full rule or explanation in both places.",'''
    new_rules = '''        "1. For meaning that moves into a Node, preserve the source's precise language whenever it is already clear. Facts, constraints and Rules should normally move with minimal wording change. Overview is a condensation task, but still use the project's ordinary vocabulary: prefer short concrete language over abstract academic/corporate phrases such as 'provides provisioning and operation' when the source simply says what the thing is and does.",\n        "2. The primary question is **where should this meaning be maintained from now on?** Minimize future redundancy. Every durable meaning should have one canonical maintenance surface. Do not preserve a poor current file boundary merely because the text happens to live there.",\n        "3. Use kind `overview` plus action `promote` for short durable orientation about what one Node owns or is responsible for. Consolidate closely related overview statements for the same Node when one clean overview says the job better; split only independently maintainable responsibilities. Avoid semicolon/comma-heavy snake sentences.",\n        "4. Use action `promote` when project-owned canonical Overview, Rule, State, or Plan meaning belongs at the destination. For Overview/Rule/Topic publication the Node authoring becomes the canonical maintenance surface. State/Plan are currently retained as explicit node-targeted follow-up until their local publication surface is designed; do not pretend they are already written into `CONTEXT.src.md`.",\n        "5. When promoted meaning came from mutable Markdown and leaving the original full prose would create duplicate maintenance, propose a `source_edits` entry in this same semantic pass. It names one exact frozen source range and the promoted item IDs that justify replacing it. The replacement is **orientation, not a second canonical copy**: keep it short, plain and useful to a first-time reader, and point to the owning `CONTEXT.md` when that helps. When the meaning is unambiguous, rewrite freely for readability and a light human touch is welcome; when anything is uncertain, stay close to the original wording and do not invent. Do not create a source edit merely to change style.",\n        "6. If several promoted findings jointly remove or reorganize one source passage, create **one shared source edit** linked to all of them. Never emit overlapping source edits for the same file. History such as CHANGELOG/patch records normally remains history, fixed Markdown remains untouched, and configuration/CI/manifests remain authoritative technical sources rather than targets for prose cleanup.",'''
    if old_rules not in text:
        raise RuntimeError("instruction rules anchor missing")
    text = text.replace(old_rules, new_rules, 1)
    # Renumber the remaining rules so the prose stays readable.
    for old, new in [("6. Use action `reference`", "7. Use action `reference`"), ("7. Use action `keep`", "8. Use action `keep`"), ("8. Use action `map`", "9. Use action `map`"), ("9. Do not split", "10. Do not split"), ("10. Treat README", "11. Treat README"), ("11. Treat CONTRIBUTING", "12. Treat CONTRIBUTING"), ("12. Preserve project state", "13. Preserve project state"), ("13. Compare likely", "14. Compare likely"), ("14. A Source may", "15. A Source may"), ("15. Use only frozen", "16. Use only frozen"), ("16. Every placement item", "17. Every placement item"), ("17. Do not create", "18. Do not create")]:
        text = text.replace(f'"{old}', f'"{new}', 1)
    text = replace_once(
        text,
        '''        '  "items": [],',\n        '  "source_reuses": []',\n''',
        '''        '  "items": [],',\n        '  "source_edits": [],',\n        '  "source_reuses": []',\n''',
        "instruction top-level source edits",
    )
    insert_anchor = '        "All resource/document/authority paths must exist in the frozen Evidence for this v1 experiment.",\n        "",\n        "Every `source_reuses` entry contains exactly:",'
    insert_text = '''        "All resource/document/authority paths must exist in the frozen Evidence for this v1 experiment.",\n        "",\n        "Every `source_edits` entry contains exactly:",\n        "",\n        "```json",\n        "{",\n        '  "id": "E-001",',\n        '  "path": "README.md",',\n        '  "sha256": "<exact frozen file hash>",',\n        '  "start_line": 3,',\n        '  "end_line": 8,',\n        '  "linked_item_ids": ["P-001", "P-003"],',\n        '  "replacement": "Short, plain first-contact orientation\\n\\nFor maintained detail, see [Project Context](CONTEXT.md).",',\n        '  "rationale": "Why replacing this exact mutable-Markdown range removes duplicate maintenance without losing useful orientation",',\n        '  "confidence": "high"',\n        "}",\n        "```",\n        "",\n        "`source_edits` is the proposed A → A′ side of promotion. Use only mutable `.md` Evidence that is not listed as fixed Markdown. Every edited line must be covered by Evidence cited by the linked promoted items; linked IDs must all be `promote` items. One source range may be linked to several findings, but source edits in one file must never overlap. `replacement` may be empty only when removing the range entirely is clearly better than leaving orientation. If no promoted mutable prose needs cleanup, return an empty array.",\n        "",\n        "Every `source_reuses` entry contains exactly:",'''
    if insert_anchor not in text:
        raise RuntimeError("source edit contract anchor missing")
    text = text.replace(insert_anchor, insert_text, 1)
    text = text.replace("Return an empty `source_reuses` array. Do not invent reusable Source identities.", "Return empty `source_edits` and `source_reuses` arrays when neither applies. Do not invent reusable Source identities.")
    write(path, text)


def patch_review() -> None:
    path = "src/contextcanon/onboarding_placement_review.py"
    text = read(path)
    text = text.replace("    PlacementItem,\n)", "    PlacementItem,\n    PlacementSourceEdit,\n)")
    text = replace_once(
        text,
        '''_AUTHORING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")\n''',
        '''_AUTHORING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")\n_SOURCE_EDIT_COMMENT_RE = re.compile(\n    r'^<!-- cc:source-edit id="(?P<id>[^"]+)" path="(?P<path>[^"]+)" sha256="(?P<sha>[0-9a-f]{64})" '\n    r'start-line="(?P<start>[0-9]+)" end-line="(?P<end>[0-9]+)" linked-items="(?P<linked>[^"]+)" -->$'\n)\n_SOURCE_AFTER_START_RE = re.compile(r'^<!-- cc:source-after id="(?P<id>[^"]+)":start -->$')\n_SOURCE_AFTER_END_RE = re.compile(r'^<!-- cc:source-after id="(?P<id>[^"]+)":end -->$')\n''',
        "source edit regex",
    )
    text = replace_once(
        text,
        '''@dataclass(frozen=True)\nclass PlacementReviewSource:\n''',
        '''@dataclass(frozen=True)\nclass PlacementReviewSourceEdit:\n    proposal_id: str\n    decision: str\n    path: str\n    sha256: str\n    start_line: int\n    end_line: int\n    linked_item_ids: tuple[str, ...]\n    replacement: str\n    review_note: str\n\n    def to_dict(self) -> dict[str, object]:\n        return {\n            "proposal_id": self.proposal_id,\n            "decision": self.decision,\n            "path": self.path,\n            "sha256": self.sha256,\n            "start_line": self.start_line,\n            "end_line": self.end_line,\n            "linked_item_ids": list(self.linked_item_ids),\n            "replacement": self.replacement,\n            "review_note": self.review_note,\n        }\n\n\n@dataclass(frozen=True)\nclass PlacementReviewSource:\n''',
        "review source edit dataclass",
    )
    text = replace_once(
        text,
        '''    items: tuple[PlacementReviewItem, ...]\n    sources: tuple[PlacementReviewSource, ...]\n    review_digest: str\n\n    @property\n    def is_complete(self) -> bool:\n        return all(item.decision != "pending" for item in self.items) and all(\n            source.decision != "pending" for source in self.sources\n        )\n''',
        '''    items: tuple[PlacementReviewItem, ...]\n    source_edits: tuple[PlacementReviewSourceEdit, ...]\n    sources: tuple[PlacementReviewSource, ...]\n    review_digest: str\n\n    @property\n    def is_complete(self) -> bool:\n        return (\n            all(item.decision != "pending" for item in self.items)\n            and all(edit.decision != "pending" for edit in self.source_edits)\n            and all(source.decision != "pending" for source in self.sources)\n        )\n''',
        "review complete source edits",
    )
    text = replace_once(
        text,
        '''def _render_payload(kind: str, payload: dict[str, object]) -> list[str]:\n    lines = ["### Maintained meaning", ""]\n''',
        '''def _render_payload(kind: str, payload: dict[str, object]) -> list[str]:\n    if kind in {"overview", "rule", "topic-resource"}:\n        heading = "### Into Node — editable"\n    elif kind in {"state", "plan"}:\n        heading = "### Node-local follow-up — editable"\n    else:\n        heading = "### Reviewed handling — editable"\n    lines = [heading, ""]\n''',
        "into node heading",
    )
    # Replace section block scanner to ignore headings inside editable Source After material.
    text = replace_once(
        text,
        '''def _section_blocks(lines: list[str], prefix: str) -> list[tuple[int, int]]:\n    starts = [i for i, line in enumerate(lines) if line.startswith(prefix)]\n    result: list[tuple[int, int]] = []\n    for index, start in enumerate(starts):\n        end = starts[index + 1] if index + 1 < len(starts) else len(lines)\n        result.append((start, end))\n    return result\n''',
        '''def _section_blocks(lines: list[str], prefix: str) -> list[tuple[int, int]]:\n    starts: list[int] = []\n    source_after_id: str | None = None\n    for index, line in enumerate(lines):\n        start_match = _SOURCE_AFTER_START_RE.match(line)\n        if start_match is not None:\n            source_after_id = start_match.group("id")\n            continue\n        end_match = _SOURCE_AFTER_END_RE.match(line)\n        if end_match is not None and source_after_id == end_match.group("id"):\n            source_after_id = None\n            continue\n        if source_after_id is None and line.startswith(prefix):\n            starts.append(index)\n    result: list[tuple[int, int]] = []\n    for index, start in enumerate(starts):\n        end = starts[index + 1] if index + 1 < len(starts) else len(lines)\n        result.append((start, end))\n    return result\n''',
        "section scanner",
    )
    # Add rendering helpers before _render_item.
    anchor = '''def _render_item(\n'''
    helpers = '''def _source_edit_excerpt(edit: PlacementSourceEdit, snapshot: EvidenceSnapshot) -> list[str]:\n    reference = EvidenceReference(edit.path, edit.sha256, edit.start_line, edit.end_line)\n    return _evidence_excerpt(reference, snapshot)\n\n\ndef _render_source_edit(edit: PlacementReviewSourceEdit, proposal_edit: PlacementSourceEdit, snapshot: EvidenceSnapshot) -> list[str]:\n    linked = ", ".join(proposal_edit.linked_item_ids)\n    lines = [\n        f'<a id="source-edit-{edit.proposal_id.lower()}"></a>',\n        f"#### Source edit {edit.proposal_id}",\n        f'<!-- cc:source-edit id="{edit.proposal_id}" path="{edit.path}" sha256="{edit.sha256}" start-line="{edit.start_line}" end-line="{edit.end_line}" linked-items="{linked}" -->',\n        "",\n        f"Source edit decision: `{edit.decision}`",\n        f"Source edit note: {edit.review_note or '-'}",\n        f"Linked promoted findings: {', '.join(f'`{item}`' for item in edit.linked_item_ids)}",\n        "",\n        "**Exact range being replaced:**",\n        "",\n    ]\n    lines.extend(_source_edit_excerpt(proposal_edit, snapshot))\n    lines.extend(\n        [\n            "",\n            "**Proposed replacement — edit the text between the markers:**",\n            "",\n            f'<!-- cc:source-after id="{edit.proposal_id}":start -->',\n        ]\n    )\n    if edit.replacement:\n        lines.extend(edit.replacement.split("\\n"))\n    lines.extend([f'<!-- cc:source-after id="{edit.proposal_id}":end -->', "", f"Why this source edit: {proposal_edit.rationale}", ""])\n    return lines\n\n\n'''
    if anchor not in text:
        raise RuntimeError("render item anchor missing")
    text = text.replace(anchor, helpers + anchor, 1)
    # Extend render item signature/body and evidence section.
    text = replace_once(
        text,
        '''def _render_item(\n    item: PlacementItem,\n    review_item: PlacementReviewItem,\n    proposal: OnboardingPlacementProposal,\n    snapshot: EvidenceSnapshot,\n) -> list[str]:\n''',
        '''def _render_item(\n    item: PlacementItem,\n    review_item: PlacementReviewItem,\n    proposal: OnboardingPlacementProposal,\n    snapshot: EvidenceSnapshot,\n    source_edits: tuple[PlacementReviewSourceEdit, ...],\n) -> list[str]:\n''',
        "render item signature",
    )
    old_tail = '''    lines.extend(_render_payload(review_item.kind, review_item.payload))\n    lines.extend(\n        [\n            "",\n            "### Proposal rationale",\n            "",\n            item.rationale,\n            "",\n            f"Original confidence: `{item.confidence}`",\n            "",\n            "### Evidence",\n            "",\n        ]\n    )\n    for reference in item.evidence:\n        lines.extend(_evidence_excerpt(reference, snapshot))\n    lines.append("")\n    return lines\n'''
    new_tail = '''    lines.extend(_render_payload(review_item.kind, review_item.payload))\n    lines.extend(["", "### Source before — frozen Evidence", ""])\n    for reference in item.evidence:\n        lines.extend(_evidence_excerpt(reference, snapshot))\n    linked_edits = [edit for edit in source_edits if review_item.proposal_id in edit.linked_item_ids]\n    if linked_edits:\n        proposal_edits = {edit.id: edit for edit in proposal.source_edits}\n        lines.extend(["", "### Source after promotion", ""])\n        for edit in linked_edits:\n            proposal_edit = proposal_edits[edit.proposal_id]\n            if proposal_edit.linked_item_ids[0] == review_item.proposal_id:\n                lines.extend(_render_source_edit(edit, proposal_edit, snapshot))\n            else:\n                owner = proposal_edit.linked_item_ids[0]\n                lines.extend(\n                    [\n                        f"Shared source edit [`{edit.proposal_id}`](#source-edit-{edit.proposal_id.lower()}) also covers this finding and is edited once under `{owner}`.",\n                        "",\n                    ]\n                )\n    elif review_item.action == "promote":\n        lines.extend(\n            [\n                "",\n                "### Source after promotion",\n                "",\n                "No mutable-Markdown rewrite is proposed for this finding. The cited source either remains independently useful/authoritative, is not mutable Markdown, or no duplicate-maintenance cleanup was justified.",\n            ]\n        )\n    lines.extend(\n        [\n            "",\n            "### Proposal rationale",\n            "",\n            item.rationale,\n            "",\n            f"Original confidence: `{item.confidence}`",\n            "",\n        ]\n    )\n    return lines\n'''
    if old_tail not in text:
        raise RuntimeError("render item tail missing")
    text = text.replace(old_tail, new_tail, 1)
    # Review construction and intro.
    text = replace_once(
        text,
        '''    sources = _initial_sources(proposal, owner_source_specs)\n    lines = [\n''',
        '''    source_edits = tuple(\n        PlacementReviewSourceEdit(\n            proposal_id=edit.id,\n            decision="pending",\n            path=edit.path,\n            sha256=edit.sha256,\n            start_line=edit.start_line,\n            end_line=edit.end_line,\n            linked_item_ids=edit.linked_item_ids,\n            replacement=edit.replacement,\n            review_note="",\n        )\n        for edit in proposal.source_edits\n    )\n    sources = _initial_sources(proposal, owner_source_specs)\n    lines = [\n''',
        "initial source edits",
    )
    text = text.replace(
        "Edit this file directly. **Destination comes first** because future ownership is the primary review decision. Change `Decision`, destination, kind/action, title, or maintained wording where necessary. Evidence and proposal rationale below each item are review support, not a second decision file.",
        "Edit this file directly. **This is the transformation cockpit.** For promoted meaning, review what is going into the destination, the frozen source before, and the proposed source after. Change `Decision`, destination, kind/action, title, destination wording, Source edit decision/replacement, or review notes where necessary.",
    )
    text = text.replace(
        "Decisions are `pending`, `accept`, or `reject`. ContextCanon never publishes a pending review.",
        "Item, Source-edit and reusable-Source decisions are `pending`, `accept`, or `reject`. ContextCanon never publishes a pending review. Frozen source excerpts are read-only; text between `cc:source-after` markers is editable and becomes the reviewed replacement if that Source edit is accepted.",
    )
    text = replace_once(
        text,
        '''    for review_item in review_items:\n        lines.extend(_render_item(by_id[review_item.proposal_id], review_item, proposal, snapshot))\n''',
        '''    for review_item in review_items:\n        lines.extend(_render_item(by_id[review_item.proposal_id], review_item, proposal, snapshot, source_edits))\n''',
        "render source edits",
    )
    # Normalize review signature.
    text = replace_once(
        text,
        '''def _normalize_review(\n    proposal: OnboardingPlacementProposal,\n    items: tuple[PlacementReviewItem, ...],\n    sources: tuple[PlacementReviewSource, ...],\n) -> OnboardingPlacementReview:\n''',
        '''def _normalize_review(\n    proposal: OnboardingPlacementProposal,\n    items: tuple[PlacementReviewItem, ...],\n    source_edits: tuple[PlacementReviewSourceEdit, ...],\n    sources: tuple[PlacementReviewSource, ...],\n) -> OnboardingPlacementReview:\n''',
        "normalize signature",
    )
    text = replace_once(
        text,
        '''        "items": [item.to_dict() for item in items],\n        "sources": [source.to_dict() for source in sources],\n''',
        '''        "items": [item.to_dict() for item in items],\n        "source_edits": [edit.to_dict() for edit in source_edits],\n        "sources": [source.to_dict() for source in sources],\n''',
        "normalize payload",
    )
    text = replace_once(
        text,
        '''        items=items,\n        sources=sources,\n        review_digest=_digest(value),\n''',
        '''        items=items,\n        source_edits=source_edits,\n        sources=sources,\n        review_digest=_digest(value),\n''',
        "normalize return",
    )
    # Parse source edits before reusable Sources.
    parse_anchor = '''    packages = _package_by_id(proposal)\n    parsed_sources: list[PlacementReviewSource] = []\n'''
    parse_source = '''    proposal_source_edits = {edit.id: edit for edit in proposal.source_edits}\n    parsed_source_edits: list[PlacementReviewSourceEdit] = []\n    seen_source_edits: set[str] = set()\n    for index, line in enumerate(lines):\n        match = _SOURCE_EDIT_COMMENT_RE.match(line)\n        if match is None:\n            continue\n        edit_id = match.group("id")\n        proposed = proposal_source_edits.get(edit_id)\n        if proposed is None:\n            raise _error(f"placement.md contains unknown Source edit {edit_id}")\n        if edit_id in seen_source_edits:\n            raise _error(f"placement.md contains duplicate Source edit {edit_id}")\n        seen_source_edits.add(edit_id)\n        linked = tuple(part.strip() for part in match.group("linked").split(",") if part.strip())\n        immutable = (\n            match.group("path"), match.group("sha"), int(match.group("start")), int(match.group("end")), linked\n        )\n        expected = (proposed.path, proposed.sha256, proposed.start_line, proposed.end_line, proposed.linked_item_ids)\n        if immutable != expected:\n            raise _error(f"Source edit {edit_id} immutable Evidence binding was changed")\n        next_item = next(\n            (i for i in range(index + 1, len(lines)) if _ITEM_HEADING_RE.match(lines[i]) or _SOURCE_HEADING_RE.match(lines[i])),\n            len(lines),\n        )\n        block = lines[index:next_item]\n        decision_line = next((entry for entry in block if entry.startswith("Source edit decision:")), None)\n        if decision_line is None:\n            raise _error(f"Source edit {edit_id} is missing Source edit decision")\n        decision_match = re.match(r"^Source edit decision: `([^`]+)`$", decision_line)\n        if decision_match is None or decision_match.group(1) not in REVIEW_DECISIONS:\n            raise _error(f"Source edit {edit_id} decision must be pending, accept, or reject")\n        note = _find_line(block, "Source edit note: ", "Source edit note")\n        start_marker = f'<!-- cc:source-after id="{edit_id}":start -->'\n        end_marker = f'<!-- cc:source-after id="{edit_id}":end -->'\n        if block.count(start_marker) != 1 or block.count(end_marker) != 1:\n            raise _error(f"Source edit {edit_id} must contain one editable source-after marker pair")\n        source_start = block.index(start_marker)\n        source_end = block.index(end_marker, source_start + 1)\n        replacement = "\\n".join(block[source_start + 1 : source_end]).strip("\\n")\n        parsed_source_edits.append(\n            PlacementReviewSourceEdit(\n                proposal_id=edit_id,\n                decision=decision_match.group(1),\n                path=proposed.path,\n                sha256=proposed.sha256,\n                start_line=proposed.start_line,\n                end_line=proposed.end_line,\n                linked_item_ids=proposed.linked_item_ids,\n                replacement=replacement,\n                review_note="" if note == "-" else note,\n            )\n        )\n    if seen_source_edits != set(proposal_source_edits):\n        missing = sorted(set(proposal_source_edits) - seen_source_edits)\n        raise _error(f"placement.md is missing Source edits: {', '.join(missing)}")\n\n    item_decisions = {item.proposal_id: item.decision for item in parsed_items}\n    for edit in parsed_source_edits:\n        if edit.decision == "accept":\n            not_accepted = [item_id for item_id in edit.linked_item_ids if item_decisions.get(item_id) != "accept"]\n            if not_accepted:\n                raise _error(\n                    f"Source edit {edit.proposal_id} cannot be accepted until all linked promoted findings are accepted: {', '.join(not_accepted)}"\n                )\n\n    packages = _package_by_id(proposal)\n    parsed_sources: list[PlacementReviewSource] = []\n'''
    if parse_anchor not in text:
        raise RuntimeError("parse source anchor missing")
    text = text.replace(parse_anchor, parse_source, 1)
    text = replace_once(
        text,
        '''    return _normalize_review(proposal, tuple(parsed_items), tuple(parsed_sources))\n''',
        '''    return _normalize_review(proposal, tuple(parsed_items), tuple(parsed_source_edits), tuple(parsed_sources))\n''',
        "normalize parsed review",
    )
    write(path, text)


def patch_publish() -> None:
    path = "src/contextcanon/onboarding_placement_publish.py"
    text = read(path)
    text = text.replace(
        "from .onboarding_placement_review import OnboardingPlacementReview, PlacementReviewItem, PlacementReviewSource",
        "from .onboarding_placement_review import (OnboardingPlacementReview, PlacementReviewItem, PlacementReviewSource, PlacementReviewSourceEdit)",
    )
    text = replace_once(
        text,
        '''@dataclass(frozen=True)\nclass PlacementPublicationPreview:\n''',
        '''@dataclass(frozen=True)\nclass PlacementDocumentDelta:\n    path: str\n    source_path: Path\n    before: str\n    after: str\n    source_edit_ids: tuple[str, ...]\n\n    @property\n    def changed(self) -> bool:\n        return self.before != self.after\n\n\n@dataclass(frozen=True)\nclass PlacementPublicationPreview:\n''',
        "document delta dataclass",
    )
    text = replace_once(
        text,
        '''    sources: tuple[SourceGitProvenance, ...]\n    followups: tuple[PlacementReviewItem, ...]\n    mutable_cleanup_candidates: tuple[dict[str, object], ...]\n''',
        '''    sources: tuple[SourceGitProvenance, ...]\n    followups: tuple[PlacementReviewItem, ...]\n    documents: tuple[PlacementDocumentDelta, ...]\n''',
        "preview documents field",
    )
    # Replace old live evidence verification with edit-aware helpers.
    start = text.index("def _verify_live_evidence(")
    end = text.index("\ndef _catalog_roots", start)
    new_helpers = '''def _apply_line_edits(original: str, edits: list[PlacementReviewSourceEdit]) -> str:\n    lines = original.splitlines(keepends=True)\n    for edit in sorted(edits, key=lambda item: item.start_line, reverse=True):\n        segment = lines[edit.start_line - 1 : edit.end_line]\n        needs_newline = bool(segment and segment[-1].endswith(("\\n", "\\r"))) or edit.end_line < len(lines)\n        replacement = edit.replacement\n        if replacement and needs_newline and not replacement.endswith("\\n"):\n            replacement += "\\n"\n        lines[edit.start_line - 1 : edit.end_line] = [replacement] if replacement else []\n    return "".join(lines)\n\n\ndef _accepted_source_edits(review: OnboardingPlacementReview) -> dict[str, list[PlacementReviewSourceEdit]]:\n    result: dict[str, list[PlacementReviewSourceEdit]] = {}\n    for edit in review.source_edits:\n        if edit.decision == "accept":\n            result.setdefault(edit.path, []).append(edit)\n    return result\n\n\ndef _expected_document_deltas(\n    snapshot: EvidenceSnapshot, project_root: Path, review: OnboardingPlacementReview\n) -> tuple[PlacementDocumentDelta, ...]:\n    accepted = _accepted_source_edits(review)\n    result: list[PlacementDocumentDelta] = []\n    for path, edits in sorted(accepted.items()):\n        entry = snapshot.by_path[path]\n        frozen = (snapshot.root / "evidence" / Path(*PurePosixPath(path).parts)).read_text(encoding="utf-8")\n        expected = _apply_line_edits(frozen, edits)\n        live_path = project_root / Path(*PurePosixPath(path).parts)\n        if not live_path.is_file():\n            raise _error(f"frozen Evidence path is missing from the live project: {path}")\n        live = live_path.read_text(encoding="utf-8")\n        if live not in {frozen, expected}:\n            raise _error(\n                f"frozen Evidence changed outside the reviewed source transformation: {path}; prepare/review again rather than publishing stale placement"\n            )\n        result.append(PlacementDocumentDelta(path, live_path, live, expected, tuple(edit.proposal_id for edit in edits)))\n    edited_paths = set(accepted)\n    for entry in snapshot.entries:\n        if entry.path in edited_paths:\n            continue\n        live = project_root / Path(*PurePosixPath(entry.path).parts)\n        if not live.is_file():\n            raise _error(f"frozen Evidence path is missing from the live project: {entry.path}")\n        if _sha256_bytes(live.read_bytes()) != entry.sha256:\n            raise _error(\n                f"frozen Evidence changed after semantic review: {entry.path}; prepare a new snapshot rather than publishing stale placement"\n            )\n    return tuple(result)\n\n'''
    text = text[:start] + new_helpers + text[end+1:]
    # Remove mutable cleanup helper entirely.
    start = text.index("def _mutable_cleanup_candidates(")
    end = text.index("\ndef build_placement_publication_preview", start)
    text = text[:start] + text[end+1:]
    text = text.replace("    _verify_live_evidence(snapshot, project)\n", "    documents = _expected_document_deltas(snapshot, project, review)\n", 1)
    text = replace_once(
        text,
        '''        followups=_followups(review),\n        mutable_cleanup_candidates=_mutable_cleanup_candidates(review, proposal),\n''',
        '''        followups=_followups(review),\n        documents=documents,\n''',
        "preview return documents",
    )
    text = text.replace(
        '        "No project file was changed by this preview. Existing README, architecture, CONTRIBUTING and other mutable Markdown remain untouched; possible duplicate cleanup is a separate later review.",',
        '        "No project file was changed by this preview. Accepted mutable-Markdown Source After edits are shown below and will be published transactionally with the reviewed Context changes.",',
    )
    # Replace cleanup rendering section with document diffs.
    old_section = '''    lines.extend(["## Mutable Markdown cleanup candidates — deferred", ""])\n    if not preview.mutable_cleanup_candidates:\n        lines.extend(["None.", ""])\n    else:\n        for candidate in preview.mutable_cleanup_candidates:\n            paths = ", ".join(f"`{path}`" for path in candidate["paths"])\n            lines.append(f"- `{candidate['proposal_id']}` — {paths}: {candidate['note']}")\n        lines.append("")\n'''
    new_section = '''    lines.extend(["## Reviewed source-document deltas", ""])\n    if not preview.documents:\n        lines.extend(["No Source After edits are accepted in the current review.", ""])\n    for document in preview.documents:\n        lines.extend([f"### `{document.path}`", "", f"Source edits: {', '.join(f'`{item}`' for item in document.source_edit_ids)}", ""])\n        diff = list(\n            difflib.unified_diff(\n                document.before.splitlines(), document.after.splitlines(),\n                fromfile=f"current/{document.path}", tofile=f"reviewed/{document.path}", lineterm="",\n            )\n        )\n        if diff:\n            lines.extend(["```diff", *diff, "```", ""])\n        else:\n            lines.extend(["No document delta; this reviewed Source After transformation is already materialized.", ""])\n'''
    if old_section not in text:
        raise RuntimeError("cleanup render section missing")
    text = text.replace(old_section, new_section, 1)
    # Acceptance payload.
    text = replace_once(
        text,
        '''        "followups": [item.to_dict() for item in preview.followups],\n        "mutable_cleanup_candidates": list(preview.mutable_cleanup_candidates),\n''',
        '''        "followups": [item.to_dict() for item in preview.followups],\n        "source_edits": [edit.to_dict() for edit in review.source_edits if edit.decision == "accept"],\n        "documents": [\n            {\n                "path": document.path,\n                "source_edit_ids": list(document.source_edit_ids),\n                "after_sha256": _sha256_bytes(document.after.encode("utf-8")),\n            }\n            for document in preview.documents\n        ],\n''',
        "acceptance source edits",
    )
    # Followup cleanup section.
    old_follow = '''    lines.extend(["## Mutable Markdown cleanup candidates — not applied", ""])\n    if not preview.mutable_cleanup_candidates:\n        lines.append("None.")\n    else:\n        for candidate in preview.mutable_cleanup_candidates:\n            paths = ", ".join(f"`{path}`" for path in candidate["paths"])\n            lines.append(f"- `{candidate['proposal_id']}` — {paths}")\n'''
    new_follow = '''    lines.extend(["## Reviewed mutable-Markdown transformations", ""])\n    if not preview.documents:\n        lines.append("None.")\n    else:\n        for document in preview.documents:\n            state = "changed" if document.changed else "already materialized"\n            lines.append(f"- `{document.path}` — {state}; Source edits: {', '.join(document.source_edit_ids)}")\n'''
    if old_follow not in text:
        raise RuntimeError("followup cleanup section missing")
    text = text.replace(old_follow, new_follow, 1)
    # Publish verification and rollback.
    text = text.replace("    _verify_live_evidence(snapshot, project)\n", "    expected_documents = _expected_document_deltas(snapshot, project, review)\n    if expected_documents != preview.documents:\n        raise _error(\"reviewed source documents changed after publication preview; build a fresh preview\")\n", 1)
    verify_anchor = '''    for delta in preview.nodes:\n        if not delta.source_path.is_file() or delta.source_path.read_text(encoding="utf-8") != delta.before:\n            raise _error(\n                f"Context Node source changed after publication preview: {delta.source_path}; build a fresh preview"\n            )\n'''
    verify_new = verify_anchor + '''    for document in preview.documents:\n        if not document.source_path.is_file() or document.source_path.read_text(encoding="utf-8") != document.before:\n            raise _error(f"Source document changed after publication preview: {document.path}; build a fresh preview")\n'''
    if verify_anchor not in text:
        raise RuntimeError("publish verify anchor missing")
    text = text.replace(verify_anchor, verify_new, 1)
    text = replace_once(
        text,
        '''    original_sources = {delta.source_path: delta.before.encode("utf-8") for delta in preview.nodes}\n''',
        '''    original_sources = {delta.source_path: delta.before.encode("utf-8") for delta in preview.nodes}\n    original_documents = {document.source_path: document.before.encode("utf-8") for document in preview.documents}\n''',
        "document originals",
    )
    text = replace_once(
        text,
        '''        for delta in preview.nodes:\n            if delta.changed:\n                _atomic_write(delta.source_path, delta.after.encode("utf-8"))\n\n        accepted_sources_by_node = _sources_by_node(review)\n''',
        '''        for delta in preview.nodes:\n            if delta.changed:\n                _atomic_write(delta.source_path, delta.after.encode("utf-8"))\n        for document in preview.documents:\n            if document.changed:\n                _atomic_write(document.source_path, document.after.encode("utf-8"))\n\n        accepted_sources_by_node = _sources_by_node(review)\n''',
        "write documents",
    )
    text = replace_once(
        text,
        '''        for path, content in original_sources.items():\n            _atomic_write(path, content)\n''',
        '''        for path, content in original_sources.items():\n            _atomic_write(path, content)\n        for path, content in original_documents.items():\n            _atomic_write(path, content)\n''',
        "rollback documents",
    )
    write(path, text)


def patch_workspace() -> None:
    path = "src/contextcanon/onboarding_workspace.py"
    text = read(path)
    text = text.replace("import os\nimport re", "import json\nimport os\nimport re")
    text = replace_once(
        text,
        '''COMMANDS_END = "<!-- contextcanon-onboarding-commands:end -->"\n''',
        '''COMMANDS_END = "<!-- contextcanon-onboarding-commands:end -->"\nRUN_INPUTS_SCHEMA = "contextcanon/onboarding-run-inputs/v0"\nRUN_INPUTS_NAME = "run-inputs.json"\n''',
        "run inputs constants",
    )
    # Add persistence helpers before update checkpoint.
    anchor = '''def update_workspace_checkpoint(\n'''
    helpers = '''def _run_inputs_path(snapshot_root: Path) -> Path:\n    return snapshot_root.resolve() / RUN_INPUTS_NAME\n\n\ndef _load_run_inputs(snapshot_root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:\n    path = _run_inputs_path(snapshot_root)\n    if not path.is_file():\n        return (), ()\n    try:\n        value = json.loads(path.read_text(encoding="utf-8"))\n    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:\n        raise ContextCanonError(f"Invalid onboarding run input state: {path}") from exc\n    if not isinstance(value, dict) or set(value) != {"schema", "catalog_package_inputs", "owner_source_specs"}:\n        raise ContextCanonError(f"Invalid onboarding run input state shape: {path}")\n    if value.get("schema") != RUN_INPUTS_SCHEMA:\n        raise ContextCanonError(f"Unsupported onboarding run input state schema: {value.get('schema')!r}")\n    catalog = value.get("catalog_package_inputs")\n    owners = value.get("owner_source_specs")\n    if not isinstance(catalog, list) or not all(isinstance(item, str) and item for item in catalog):\n        raise ContextCanonError(f"Invalid catalog inputs in onboarding run state: {path}")\n    if not isinstance(owners, list) or not all(isinstance(item, str) and item for item in owners):\n        raise ContextCanonError(f"Invalid owner Source inputs in onboarding run state: {path}")\n    return tuple(catalog), tuple(owners)\n\n\ndef remember_run_inputs(\n    snapshot_root: Path, *, catalog_inputs: tuple[str, ...] = (), owner_source_specs: tuple[str, ...] = ()\n) -> tuple[tuple[str, ...], tuple[str, ...]]:\n    remembered_catalog, remembered_owner = _load_run_inputs(snapshot_root)\n    catalog = catalog_inputs or remembered_catalog\n    owners = owner_source_specs or remembered_owner\n    if not catalog and not owners and not _run_inputs_path(snapshot_root).exists():\n        return (), ()\n    payload = {\n        "schema": RUN_INPUTS_SCHEMA,\n        "catalog_package_inputs": list(catalog),\n        "owner_source_specs": list(owners),\n    }\n    write_utf8(_run_inputs_path(snapshot_root), json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\\n")\n    return catalog, owners\n\n\n'''
    if anchor not in text:
        raise RuntimeError("workspace checkpoint anchor missing")
    text = text.replace(anchor, helpers + anchor, 1)
    # Prefer persisted state in checkpoint.
    old = '''    remembered_catalog = _remembered_values(\n        text, "- Reuse these exact `--catalog-package` inputs for copy/paste commands:"\n    )\n    remembered_owner = _remembered_values(\n        text, "- Owner-selected Source choices already recorded in the human review (do not repeat on preview/publish):"\n    )\n    catalog_inputs = source_catalog_inputs or remembered_catalog\n    owner_specs = owner_source_specs or remembered_owner\n'''
    new = '''    remembered_catalog = _remembered_values(\n        text, "- Reuse these exact `--catalog-package` inputs for copy/paste commands:"\n    )\n    remembered_owner = _remembered_values(\n        text, "- Owner-selected Source choices already recorded in the human review (do not repeat on preview/publish):"\n    )\n    machine_catalog, machine_owner = _load_run_inputs(snapshot_root)\n    catalog_inputs = source_catalog_inputs or machine_catalog or remembered_catalog\n    owner_specs = owner_source_specs or machine_owner or remembered_owner\n    if source_catalog_inputs or owner_source_specs or machine_catalog or machine_owner:\n        catalog_inputs, owner_specs = remember_run_inputs(\n            snapshot_root, catalog_inputs=catalog_inputs, owner_source_specs=owner_specs\n        )\n'''
    if old not in text:
        raise RuntimeError("checkpoint remembered inputs anchor missing")
    text = text.replace(old, new, 1)
    # Refresh missing/stale plan from machine state.
    text = replace_once(
        text,
        '''    if not workspace.plan_path.exists():\n        write_utf8(workspace.plan_path, _workspace_plan())\n        return\n''',
        '''    if not workspace.plan_path.exists():\n        write_utf8(workspace.plan_path, _workspace_plan())\n        plan = workspace.plan_path.read_text(encoding="utf-8")\n        catalog_inputs, owner_specs = _load_run_inputs(snapshot_root)\n        plan = _replace_commands(plan, workspace, snapshot_root, catalog_inputs, owner_specs)\n        write_utf8(workspace.plan_path, plan)\n        return\n''',
        "missing plan run inputs",
    )
    text = replace_once(
        text,
        '''    catalog_inputs = _remember_first(\n        plan,\n''',
        '''    machine_catalog, machine_owner = _load_run_inputs(snapshot_root)\n    catalog_inputs = machine_catalog or _remember_first(\n        plan,\n''',
        "refresh machine catalog",
    )
    text = replace_once(
        text,
        '''    owner_specs = _remember_first(\n        plan,\n''',
        '''    owner_specs = machine_owner or _remember_first(\n        plan,\n''',
        "refresh machine owner",
    )
    write(path, text)


def patch_cli() -> None:
    path = "src/contextcanon/cli.py"
    text = read(path)
    text = text.replace("    update_workspace_checkpoint,\n", "    update_workspace_checkpoint,\n    remember_run_inputs,\n")
    # If import is a one-line form fallback handled below.
    if "remember_run_inputs" not in text.split("\n", 80)[0:80]:
        pass
    # Persist inputs as soon as placement commands receive them.
    anchor = '''                catalog = tuple(Path(path) for path in args.catalog_package)\n                catalog_inputs = tuple(args.catalog_package)\n\n                if args.onboard_command == "placement-instruction":\n'''
    repl = '''                catalog = tuple(Path(path) for path in args.catalog_package)\n                catalog_inputs = tuple(args.catalog_package)\n                remembered_catalog, remembered_owner = remember_run_inputs(\n                    snapshot,\n                    catalog_inputs=catalog_inputs,\n                    owner_source_specs=tuple(args.owner_source) if hasattr(args, "owner_source") else (),\n                )\n                if not catalog_inputs and remembered_catalog:\n                    catalog_inputs = remembered_catalog\n                    catalog = tuple(Path(path) for path in catalog_inputs)\n\n                if args.onboard_command == "placement-instruction":\n'''
    if anchor not in text:
        raise RuntimeError("cli catalog anchor missing")
    text = text.replace(anchor, repl, 1)
    text = text.replace('print(f"Source reuses: {len(proposal.source_reuses)}")', 'print(f"Source edits: {len(proposal.source_edits)}")\n                    print(f"Source reuses: {len(proposal.source_reuses)}")', 1)
    text = text.replace('print(f"Items: {len(review.items)} · Sources: {len(review.sources)} · complete: {review.is_complete}")', 'print(f"Items: {len(review.items)} · Source edits: {len(review.source_edits)} · Sources: {len(review.sources)} · complete: {review.is_complete}")', 1)
    text = text.replace(
        'f"Edit `{workspace.placement_path.name}`: set every Decision to `accept` or `reject` and correct destination/maintained meaning where needed. "',
        'f"Edit `{workspace.placement_path.name}`: review Into Node, Source Before/After, and set every item/Source-edit/Source Decision to `accept` or `reject`. "',
        1,
    )
    text = text.replace(
        '"Review `STEP-09-placement-followup.md`. Mutable-Markdown duplicate cleanup is deliberately a separate later operation; "',
        '"Review `STEP-09-placement-followup.md`. Accepted mutable-Markdown Source After transformations were published transactionally with canonical Context; "',
        1,
    )
    write(path, text)


def patch_tests() -> None:
    # Extend the common placement fixture with one real source transformation.
    path = "tests/test_onboarding_placement.py"
    text = read(path)
    text = replace_once(
        text,
        '''            ],\n            "source_reuses": [\n''',
        '''            ],\n            "source_edits": [\n                {\n                    "id": "E-001",\n                    "path": "docs/architecture.md",\n                    "sha256": architecture.sha256,\n                    "start_line": 2,\n                    "end_line": 2,\n                    "linked_item_ids": ["P-001"],\n                    "replacement": "Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).",\n                    "rationale": "Keep architecture orientation without maintaining the promoted rule twice.",\n                    "confidence": "high",\n                }\n            ],\n            "source_reuses": [\n''',
        "fixture source edits",
    )
    text = text.replace('self.assertEqual(first.source_reuses[0].source_node_id, package.metadata.id)', 'self.assertEqual(first.source_edits[0].linked_item_ids, ("P-001",))\n        self.assertEqual(first.source_reuses[0].source_node_id, package.metadata.id)', 1)
    text = text.replace('self.assertIn("Source reuses: 1", stdout.getvalue())', 'self.assertIn("Source edits: 1", stdout.getvalue())\n        self.assertIn("Source reuses: 1", stdout.getvalue())', 1)
    text = text.replace('self.assertIn("Wording: `exact`", workspace.placement_path.read_text(encoding="utf-8"))', 'review_text = workspace.placement_path.read_text(encoding="utf-8")\n        self.assertIn("Wording: `exact`", review_text)\n        self.assertIn("### Into Node — editable", review_text)\n        self.assertIn("### Source before — frozen Evidence", review_text)\n        self.assertIn("### Source after promotion", review_text)', 1)
    # Instruction assertions.
    text = text.replace('self.assertIn("split them into separate findings", instruction.text)', 'self.assertIn("Consolidate closely related overview statements", instruction.text)\n        self.assertIn("source_edits", instruction.text)\n        self.assertIn("one shared source edit", instruction.text)', 1)
    write(path, text)

    path = "tests/test_onboarding_placement_review.py"
    text = read(path)
    text = text.replace('self.assertIn("### Maintained meaning", text)', 'self.assertIn("### Into Node — editable", text)\n        self.assertIn("### Source before — frozen Evidence", text)\n        self.assertIn("### Source after promotion", text)', 1)
    # Round-trip edit source replacement as well.
    insert = '''        self.assertEqual(\n            second.items[0].payload["statement"],\n            "The repository is the canonical installation specification.",\n        )\n'''
    replacement = insert + '''        self.assertEqual(len(second.source_edits), 1)\n'''
    text = replace_once(text, insert, replacement, "review source edit roundtrip assertion")
    # Add safety tests before __main__.
    extra = '''\n    def test_source_after_is_editable_and_round_trips(self):\n        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)\n        text = workspace.placement_path.read_text(encoding="utf-8")\n        old = "Installation authority is maintained in [AI Workstation Context](../CONTEXT.md)."\n        new = "Architecture starts here; maintained installation authority lives in [AI Workstation Context](../CONTEXT.md)."\n        text = text.replace(old, new, 1).replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)\n        text = text.replace("Decision: `pending`", "Decision: `accept`", 1)\n        workspace.placement_path.write_text(text, encoding="utf-8")\n        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)\n        self.assertEqual(loaded.source_edits[0].replacement, new)\n        self.assertEqual(loaded.source_edits[0].decision, "accept")\n\n    def test_source_edit_cannot_be_accepted_when_linked_finding_is_rejected(self):\n        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)\n        text = workspace.placement_path.read_text(encoding="utf-8")\n        text = text.replace("Decision: `pending`", "Decision: `reject`", 1)\n        text = text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)\n        workspace.placement_path.write_text(text, encoding="utf-8")\n        with self.assertRaisesRegex(ContextCanonError, "cannot be accepted until all linked promoted findings are accepted"):\n            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)\n'''
    text = text.replace('\n\nif __name__ == "__main__":', extra + '\n\nif __name__ == "__main__":')
    write(path, text)

    path = "tests/test_onboarding_placement_publish.py"
    text = read(path)
    # Fixed README means fixture edit on architecture remains mutable and publishable.
    text = text.replace('self.assertTrue(preview.mutable_cleanup_candidates)', 'self.assertEqual(len(preview.documents), 1)\n        self.assertEqual(preview.documents[0].path, "docs/architecture.md")\n        self.assertTrue(preview.documents[0].changed)\n        self.assertIn("Reviewed source-document deltas", text)', 1)
    text = text.replace('architecture_before = (repo / "docs" / "architecture.md").read_bytes()', 'architecture_before = (repo / "docs" / "architecture.md").read_bytes()', 1)
    text = text.replace('self.assertEqual((repo / "docs" / "architecture.md").read_bytes(), architecture_before)', 'self.assertNotEqual((repo / "docs" / "architecture.md").read_bytes(), architecture_before)\n        self.assertIn("maintained in [AI Workstation Context]", (repo / "docs" / "architecture.md").read_text(encoding="utf-8"))', 1)
    text = text.replace('self.assertTrue(all(not delta.changed for delta in second.nodes))', 'self.assertTrue(all(not delta.changed for delta in second.nodes))\n        self.assertTrue(all(not document.changed for document in second.documents))', 1)
    write(path, text)

    # Run-input recovery regression.
    path = "tests/test_onboarding_reset.py"
    text = read(path)
    marker = '\n\nif __name__ == "__main__":'
    extra = '''\n    def test_machine_run_inputs_survive_missing_workspace_plan(self):\n        repo, prepared, workspace = self.make_workspace()\n        from contextcanon.onboarding_workspace import remember_run_inputs, open_onboarding_workspace\n        remember_run_inputs(\n            prepared.snapshot_root,\n            catalog_inputs=("C:/catalog/development-workflow",),\n            owner_source_specs=("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40",),\n        )\n        workspace.plan_path.unlink()\n        reopened = open_onboarding_workspace(prepared.snapshot_root, create=False)\n        plan = reopened.plan_path.read_text(encoding="utf-8")\n        self.assertIn("C:/catalog/development-workflow", plan)\n        self.assertIn("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40", plan)\n'''
    if "test_machine_run_inputs_survive_missing_workspace_plan" not in text:
        text = text.replace(marker, extra + marker)
    write(path, text)


def patch_docs() -> None:
    path = "docs/onboarding.md"
    text = read(path)
    text = text.replace(
        "Placement publication does not destructively clean mutable project Markdown. Promoted meaning becomes canonical ContextCanon authoring first; duplicate source prose is migration debt for a later reviewed cleanup pass.",
        "Placement review is a transformation cockpit: promoted meaning shows the editable destination, frozen source-before Evidence, and any editable Source After replacement. Accepted mutable-Markdown Source After edits are previewed as exact document diffs and published transactionally with the canonical Context changes, so duplicate maintenance can be removed in the same reviewed migration rather than deferred to an unspecified cleanup pass.",
    )
    write(path, text)

    path = "nodes/internal/framework-development/docs/onboarding-cleanup.md"
    text = read(path)
    text = text.replace(
        "This cleanup is deliberately a separate operation after placement publication.",
        "The original cleanup design was a separate post-publication operation. Owner testing showed that this hid half of the A → Node + A′ transformation during the actual semantic review. Mutable-Markdown replacement is therefore now reviewed in the placement cockpit and published transactionally; this document retains the safety rationale and boundaries for that source-side transformation.",
    )
    write(path, text)


def apply() -> None:
    patch_placement_model()
    patch_instruction()
    patch_review()
    patch_publish()
    patch_workspace()
    patch_cli()
    patch_tests()
    patch_docs()


def finalize() -> None:
    path = "PLAN.md"
    text = read(path)
    start = text.index("#### Block J — placement transformation cockpit")
    block = text[start:]
    block = block.replace("- [ ] ", "- [x] ")
    checkpoint = '''\n\nPlacement transformation cockpit checkpoint: owner testing showed that showing only a synthesized "maintained meaning" hid the actual migration. `STEP-07-placement.md` now makes the A → Node + A′ transformation explicit: destination wording is editable, frozen source-before Evidence is visible, and shared exact mutable-Markdown Source After edits are editable once and linked to every promoted finding they cover. Accepted source edits are range/hash bound, non-overlapping, previewed as document diffs, and published/rolled back in the same transaction as Context Node changes. Exact already-published A′ bytes are accepted for idempotent reruns; unrelated Evidence drift still stops publication. Run inputs now persist in snapshot-owned `run-inputs.json`, so reset/workspace recreation retains exact catalog and owner-Source choices. The semantic instruction also favors source-shaped plain language, consolidated overviews, and readable orientation over inflated abstraction while remaining conservative under uncertainty.\n'''
    text = text[:start] + block.rstrip() + checkpoint
    write(path, text)

    state_path = "STATE.md"
    state = read(state_path).rstrip()
    state += '''\n\n## Latest placement transformation owner-test correction\n\nThe active PR now treats placement review as the complete migration cockpit rather than a destination-only findings report. Promoted mutable-Markdown meaning can carry an exact reviewed Source After transformation in the same semantic proposal and human gate. Publication applies accepted source-document edits transactionally with Context Node authoring and preserves idempotency by recognizing the exact reviewed post-migration bytes. Frozen Evidence remains immutable review input; fixed Markdown, non-Markdown technical authorities and unrelated Evidence remain protected from this cleanup path. Placement review labels State/Plan honestly as node-local follow-up because current publication does not yet write those kinds into `CONTEXT.src.md`. Exact Source catalog and owner-selected Source inputs are now also retained in snapshot-owned run state so reset cannot forget them.\n'''
    write(state_path, state + "\n")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "apply"
    {"plan": plan, "apply": apply, "finalize": finalize}[command]()
