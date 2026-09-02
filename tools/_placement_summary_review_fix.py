from pathlib import Path
import sys


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def plan() -> None:
    path = "PLAN.md"
    text = read(path).rstrip()
    marker = "#### Block M — make Source After a real summary and keep the cockpit recoverable"
    if marker in text:
        return
    text += """

#### Block M — make Source After a real summary and keep the cockpit recoverable

Purpose: correct the next live `ai-workstation` Step-7 review failure. The second semantic pass must leave a useful human summary where promoted prose used to live, not a content-free pointer, and the review cockpit must still let the owner create a safe source rewrite when the LLM omitted one.

- [ ] Tighten the placement instruction so stable Overview omits volatile version/platform detail already represented as State, and Overview/State/Plan findings are bullet-sized rather than comma/semicolon snake sentences.
- [ ] Require Source After replacements to preserve a real plain-language gist of the moved block plus the Context link; explicitly reject pointer-only replacements such as “details live in Project Context” when the old location still has first-contact value.
- [ ] Add a conservative review-only Source After fallback for an unambiguous mutable Markdown range when a promoted finding has no LLM source edit; default it to `reject` so it adds editability without adding publication work.
- [ ] Remove self-referential `Linked promoted findings: P-xxx` cockpit noise; show only genuinely shared findings and keep the existing one-edit shared-placement behavior.
- [ ] Add focused regressions for the sharper instruction, optional human Source After override, shared-edit presentation and parser round-trip, then run the complete suite plus build/check/diff-check.
"""
    write(path, text + "\n")


def apply_instruction() -> None:
    path = "src/contextcanon/onboarding_placement_instruction.py"
    text = read(path)
    text = replace_once(
        text,
        '        "1. For meaning that moves into a Node, preserve the source\'s precise language whenever it is already clear. Facts, constraints and Rules should normally move with minimal wording change. Overview is a condensation task, but still use the project\'s ordinary vocabulary: prefer short concrete language over abstract academic/corporate phrases such as \'provides provisioning and operation\' when the source simply says what the thing is and does.",\n',
        '        "1. For meaning that moves into a Node, preserve the source\'s precise language whenever it is already clear. Facts, constraints and Rules should normally move with minimal wording change. Overview is a condensation task, but still use the project\'s ordinary vocabulary: prefer short concrete language over abstract academic/corporate phrases such as \'provides provisioning and operation\' when the source simply says what the thing is and does. A stable Overview must not repeat volatile exact versions, compatibility numbers or current-phase details when those facts can be represented as State. If one source sentence mixes durable identity with volatile compatibility, split it into a short versionless Overview plus separate State finding(s).",\n',
        "instruction overview volatility",
    )
    text = replace_once(
        text,
        '        "3. Use kind `overview` plus action `promote` for short durable orientation about what one Node owns or is responsible for. Consolidate closely related overview statements for the same Node when one clean overview says the job better; split only independently maintainable responsibilities. Avoid semicolon/comma-heavy snake sentences.",\n',
        '        "3. Use kind `overview` plus action `promote` for short durable orientation about what one Node owns or is responsible for. One `overview`, `state`, or `plan` placement item becomes one bullet in the final Node: make each item one bullet-sized fact. When a source block is a list or matrix of independently readable facts, emit several short findings instead of compressing them into one comma/semicolon snake sentence. Consolidate only when one genuinely atomic sentence says the job better.",\n',
        "instruction bullet-sized items",
    )
    text = replace_once(
        text,
        '        "5. When promoted meaning came from mutable Markdown and leaving the original full prose would create duplicate maintenance, propose a `source_edits` entry in this same semantic pass. It names one exact frozen source range and the promoted item IDs that justify replacing it. The replacement is **orientation, not a second canonical copy**: prefer concise human orientation plus a link/reference to the owning `CONTEXT.md` when that helps. When the meaning is unambiguous, rewrite freely for readability and a light human touch is welcome; when anything is uncertain, stay close to the original wording and do not invent. If no safe Source After edit is proposed or accepted, a temporary duplicate may exist during migration, but it remains migration debt. Do not plan to maintain the same full rule or explanation in both places. Do not create a source edit merely to change style.",\n',
        '        "5. When promoted meaning came from mutable Markdown and leaving the original full prose would create duplicate maintenance, propose a `source_edits` entry in this same semantic pass. It names one exact frozen source range and the promoted item IDs that justify replacing it. The replacement is the useful A′ left behind after A moves into the Node: **write a real plain-language summary of what the removed block said, then add the link/reference to the owning `CONTEXT.md`**. A reader should learn the gist without following the link. Pointer-only replacements such as \'The maintained details are in Project Context\' are not acceptable when the old location still has first-contact, safety, architecture, contribution, or operating value. Keep only enough substance to orient the reader without recreating a second canonical copy. When meaning is unambiguous, rewrite freely for readability and a light human touch is welcome; when anything is uncertain, stay close to the original wording and do not invent. If no safe Source After edit is proposed or accepted, a temporary duplicate may exist during migration, but it remains migration debt. Do not create a source edit merely to change style.",\n',
        "instruction source-after summary",
    )
    text = replace_once(
        text,
        '        "11. Treat README as first-contact orientation/navigation rather than the default store for volatile state, future plan, detailed architecture, or every implementation invariant. Its durable project summary should be short and human-facing; exact supported versions/platforms normally belong in root `state` or a narrower Node. Use `state` for current local situation, `plan` for future work, `overview` for stable Node responsibility, Rules for durable governance, and Topics/Resources for genuinely useful deeper task material.",\n',
        '        "11. Treat README as first-contact orientation/navigation rather than the default store for volatile state, future plan, detailed architecture, or every implementation invariant. Its durable project summary should be short and human-facing; exact supported versions/platforms normally belong in root `state` or a narrower Node. If the existing README identity line mixes the durable project idea with exact OS/runtime versions, normally keep a simpler versionless first-contact sentence in README and maintain the exact compatibility matrix as State. Use `state` for current local situation, `plan` for future work, `overview` for stable Node responsibility, Rules for durable governance, and Topics/Resources for genuinely useful deeper task material.",\n',
        "instruction README versionless summary",
    )
    text = replace_once(
        text,
        '        "18. Do not create, edit, move, or delete project files. Return a proposal only. ContextCanon will render an evidence-rich review before any canonical placement or cleanup is designed.",\n',
        '        "18. Before returning, run a final readability/redundancy audit: every Overview/State/Plan item is one bullet-sized fact; stable Overview does not repeat volatile versions already represented as State; every Source After replacement at a still-useful human location carries a real gist plus its Context link rather than a pointer-only sentence; and every shared edit names all promoted findings whose meaning it summarizes.",\n        "19. Do not create, edit, move, or delete project files. Return a proposal only. ContextCanon will render an evidence-rich review before any canonical placement or cleanup is designed.",\n',
        "instruction final audit",
    )
    text = replace_once(
        text,
        '        \'  "replacement": "Short, plain first-contact orientation\\n\\nFor maintained detail, see [Project Context](CONTEXT.md).",\',\n',
        '        \'  "replacement": "AI Workstation runs on Windows with WSL/Linux. Exact supported versions and current compatibility are maintained in [Project Context](CONTEXT.md).",\',\n',
        "source edit example",
    )
    write(path, text)


def apply_review() -> None:
    path = "src/contextcanon/onboarding_placement_review.py"
    text = read(path)
    anchor = '''def _source_edit_excerpt(edit: PlacementSourceEdit, snapshot: EvidenceSnapshot) -> list[str]:\n    reference = EvidenceReference(edit.path, edit.sha256, edit.start_line, edit.end_line)\n    return _evidence_excerpt(reference, snapshot)\n\n\n'''
    addition = '''def _source_edit_excerpt(edit: PlacementSourceEdit, snapshot: EvidenceSnapshot) -> list[str]:\n    reference = EvidenceReference(edit.path, edit.sha256, edit.start_line, edit.end_line)\n    return _evidence_excerpt(reference, snapshot)\n\n\ndef _source_reference_text(reference: EvidenceReference, snapshot: EvidenceSnapshot) -> str:\n    evidence_file = snapshot.root / "evidence" / reference.path\n    lines = evidence_file.read_text(encoding="utf-8").splitlines()\n    return "\\n".join(lines[reference.start_line - 1 : reference.end_line])\n\n\ndef _ranges_overlap(path_a: str, start_a: int, end_a: int, path_b: str, start_b: int, end_b: int) -> bool:\n    return path_a == path_b and max(start_a, start_b) <= min(end_a, end_b)\n\n\ndef _review_source_edit_candidates(\n    proposal: OnboardingPlacementProposal, snapshot: EvidenceSnapshot\n) -> tuple[PlacementSourceEdit, ...]:\n    \"\"\"Return LLM source edits plus conservative review-only edit affordances.\n\n    The fallback exists only when the LLM supplied no source edit for a promoted\n    finding. It is bound to exact mutable frozen Evidence, defaults to reject in\n    the human review, and therefore cannot silently add a cleanup mutation.\n    \"\"\"\n    proposed = list(proposal.source_edits)\n    linked_by_proposal = {item_id for edit in proposed for item_id in edit.linked_item_ids}\n    fixed = set(proposal.structure.fixed_markdown)\n    item_order = {item.id: index for index, item in enumerate(proposal.items)}\n\n    grouped: dict[tuple[str, str, int, int], list[str]] = {}\n    for item in proposal.items:\n        if item.action != "promote" or item.id in linked_by_proposal:\n            continue\n        for reference in item.evidence:\n            if not reference.path.lower().endswith(".md") or reference.path in fixed:\n                continue\n            if any(\n                _ranges_overlap(\n                    reference.path, reference.start_line, reference.end_line,\n                    edit.path, edit.start_line, edit.end_line,\n                )\n                for edit in proposed\n            ):\n                continue\n            key = (reference.path, reference.sha256, reference.start_line, reference.end_line)\n            grouped.setdefault(key, []).append(item.id)\n\n    keys = list(grouped)\n    ambiguous: set[tuple[str, str, int, int]] = set()\n    for index, left in enumerate(keys):\n        for right in keys[index + 1 :]:\n            if left == right:\n                continue\n            if _ranges_overlap(left[0], left[2], left[3], right[0], right[2], right[3]):\n                ambiguous.add(left)\n                ambiguous.add(right)\n\n    fallbacks: list[PlacementSourceEdit] = []\n    for key in sorted((key for key in keys if key not in ambiguous), key=lambda value: (value[0], value[2], value[3])):\n        path_value, sha256, start_line, end_line = key\n        linked = tuple(sorted(set(grouped[key]), key=item_order.__getitem__))\n        reference = EvidenceReference(path_value, sha256, start_line, end_line)\n        identity = f"{path_value}:{start_line}:{end_line}:{','.join(linked)}"\n        edit_id = "H-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:10].upper()\n        fallbacks.append(\n            PlacementSourceEdit(\n                id=edit_id,\n                path=path_value,\n                sha256=sha256,\n                start_line=start_line,\n                end_line=end_line,\n                linked_item_ids=linked,\n                replacement=_source_reference_text(reference, snapshot),\n                rationale=(\n                    "No LLM Source After rewrite was proposed for this unambiguous mutable Evidence range. "\n                    "ContextCanon exposes it as a review-only fallback so the project owner can optionally "\n                    "replace it without reconstructing the source range by hand."\n                ),\n                confidence="low",\n            )\n        )\n    return tuple(proposed + fallbacks)\n\n\n'''
    text = replace_once(text, anchor, addition, "review source-edit candidate helpers")

    old = '''def _render_source_edit(edit: PlacementReviewSourceEdit, proposal_edit: PlacementSourceEdit, snapshot: EvidenceSnapshot) -> list[str]:\n    linked = ", ".join(proposal_edit.linked_item_ids)\n    lines = [\n        f'<a id="source-edit-{edit.proposal_id.lower()}"></a>',\n        f"#### Source edit {edit.proposal_id}",\n        f'<!-- cc:source-edit id="{edit.proposal_id}" path="{edit.path}" sha256="{edit.sha256}" start-line="{edit.start_line}" end-line="{edit.end_line}" linked-items="{linked}" -->',\n        "",\n        f"Source edit decision: `{edit.decision}`",\n        f"Source edit note: {edit.review_note or '-'}",\n        f"Linked promoted findings: {', '.join(f'`{item}`' for item in edit.linked_item_ids)}",\n        "",\n        "**Exact range being replaced:**",\n        "",\n    ]\n    lines.extend(_source_edit_excerpt(proposal_edit, snapshot))\n    lines.extend(\n        [\n            "",\n            "**Proposed replacement — edit the text between the markers:**",\n            "",\n            f'<!-- cc:source-after id="{edit.proposal_id}":start -->',\n        ]\n    )\n    if edit.replacement:\n        lines.extend(edit.replacement.split("\\n"))\n    lines.extend([f'<!-- cc:source-after id="{edit.proposal_id}":end -->', "", f"Why this source edit: {proposal_edit.rationale}", ""])\n    return lines\n'''
    new = '''def _render_source_edit(\n    edit: PlacementReviewSourceEdit,\n    candidate: PlacementSourceEdit,\n    snapshot: EvidenceSnapshot,\n    *,\n    proposal: OnboardingPlacementProposal,\n) -> list[str]:\n    linked = ", ".join(candidate.linked_item_ids)\n    proposal_ids = {item.id for item in proposal.source_edits}\n    item_titles = {item.id: item.title for item in proposal.items}\n    owner = candidate.linked_item_ids[0]\n    related = [item_id for item_id in edit.linked_item_ids if item_id != owner]\n    heading = f"#### Source edit {edit.proposal_id}"\n    lines = [\n        f'<a id="source-edit-{edit.proposal_id.lower()}"></a>',\n        heading,\n        f'<!-- cc:source-edit id="{edit.proposal_id}" path="{edit.path}" sha256="{edit.sha256}" start-line="{edit.start_line}" end-line="{edit.end_line}" linked-items="{linked}" -->',\n        "",\n    ]\n    if edit.proposal_id not in proposal_ids:\n        lines.extend(\n            [\n                "**Optional human override — the LLM proposed no Source After rewrite here.**",\n                "It defaults to `reject`. Edit the replacement and switch to `accept` only if you want this exact frozen range cleaned up now.",\n                "",\n            ]\n        )\n    lines.extend(\n        [\n            f"Source edit decision: `{edit.decision}`",\n            f"Source edit note: {edit.review_note or '-'}",\n        ]\n    )\n    if related:\n        lines.append(\n            "Also covers: " + ", ".join(f"`{item_id}` — {item_titles[item_id]}" for item_id in related)\n        )\n    lines.extend(["", "**Exact range being replaced:**", ""])\n    lines.extend(_source_edit_excerpt(candidate, snapshot))\n    lines.extend(\n        [\n            "",\n            "**Proposed replacement — edit the text between the markers:**",\n            "",\n            f'<!-- cc:source-after id="{edit.proposal_id}":start -->',\n        ]\n    )\n    if edit.replacement:\n        lines.extend(edit.replacement.split("\\n"))\n    lines.extend([f'<!-- cc:source-after id="{edit.proposal_id}":end -->', "", f"Why this source edit: {candidate.rationale}", ""])\n    return lines\n'''
    text = replace_once(text, old, new, "render source edit UX")

    old = '''    linked_edits = [edit for edit in source_edits if review_item.proposal_id in edit.linked_item_ids]\n    if linked_edits:\n        proposal_edits = {edit.id: edit for edit in proposal.source_edits}\n        lines.extend(["", "### Source after promotion", ""])\n        for edit in linked_edits:\n            proposal_edit = proposal_edits[edit.proposal_id]\n            if proposal_edit.linked_item_ids[0] == review_item.proposal_id:\n                lines.extend(_render_source_edit(edit, proposal_edit, snapshot))\n            else:\n                owner = proposal_edit.linked_item_ids[0]\n                lines.extend(\n                    [\n                        f"Shared source edit [`{edit.proposal_id}`](#source-edit-{edit.proposal_id.lower()}) also covers this finding and is edited once under `{owner}`.",\n                        "",\n                    ]\n                )\n'''
    new = '''    linked_edits = [edit for edit in source_edits if review_item.proposal_id in edit.linked_item_ids]\n    if linked_edits:\n        candidate_edits = {edit.id: edit for edit in _review_source_edit_candidates(proposal, snapshot)}\n        item_titles = {item.id: item.title for item in proposal.items}\n        lines.extend(["", "### Source after promotion", ""])\n        for edit in linked_edits:\n            candidate = candidate_edits[edit.proposal_id]\n            if candidate.linked_item_ids[0] == review_item.proposal_id:\n                lines.extend(_render_source_edit(edit, candidate, snapshot, proposal=proposal))\n            else:\n                owner = candidate.linked_item_ids[0]\n                lines.extend(\n                    [\n                        f"Shared source edit [`{edit.proposal_id}`](#source-edit-{edit.proposal_id.lower()}) also covers this finding and is edited once under `{owner}` — {item_titles[owner]}.",\n                        "",\n                    ]\n                )\n'''
    text = replace_once(text, old, new, "render item shared edit UX")

    old = '''    source_edits = tuple(\n        PlacementReviewSourceEdit(\n            proposal_id=edit.id,\n            decision="pending",\n            path=edit.path,\n            sha256=edit.sha256,\n            start_line=edit.start_line,\n            end_line=edit.end_line,\n            linked_item_ids=edit.linked_item_ids,\n            replacement=edit.replacement,\n            review_note="",\n        )\n        for edit in proposal.source_edits\n    )\n'''
    new = '''    candidate_edits = _review_source_edit_candidates(proposal, snapshot)\n    proposal_edit_ids = {edit.id for edit in proposal.source_edits}\n    source_edits = tuple(\n        PlacementReviewSourceEdit(\n            proposal_id=edit.id,\n            decision="pending" if edit.id in proposal_edit_ids else "reject",\n            path=edit.path,\n            sha256=edit.sha256,\n            start_line=edit.start_line,\n            end_line=edit.end_line,\n            linked_item_ids=edit.linked_item_ids,\n            replacement=edit.replacement,\n            review_note="",\n        )\n        for edit in candidate_edits\n    )\n'''
    text = replace_once(text, old, new, "initialize review source edits")

    text = replace_once(
        text,
        '        "Item, Source-edit and reusable-Source decisions are `pending`, `accept`, or `reject`. ContextCanon never publishes a pending review. Frozen source excerpts are read-only; text between `cc:source-after` markers is editable and becomes the reviewed replacement if that Source edit is accepted.",\n',
        '        "Item, Source-edit and reusable-Source decisions are `pending`, `accept`, or `reject`. ContextCanon never publishes a pending review. Frozen source excerpts are read-only; text between `cc:source-after` markers is editable and becomes the reviewed replacement if that Source edit is accepted. When the LLM omitted a rewrite for one unambiguous mutable range, ContextCanon may expose a review-only optional Source edit that defaults to `reject`; it exists only so the owner can edit that exact range without reconstructing it later.",\n',
        "review header optional override",
    )

    old = '''    proposal_source_edits = {edit.id: edit for edit in proposal.source_edits}\n    parsed_source_edits: list[PlacementReviewSourceEdit] = []\n'''
    new = '''    review_source_edits = {edit.id: edit for edit in _review_source_edit_candidates(proposal, snapshot)}\n    parsed_source_edits: list[PlacementReviewSourceEdit] = []\n'''
    text = replace_once(text, old, new, "load review candidate map")
    text = replace_once(
        text,
        '        proposed = proposal_source_edits.get(edit_id)\n',
        '        proposed = review_source_edits.get(edit_id)\n',
        "load review candidate lookup",
    )
    text = replace_once(
        text,
        '    if seen_source_edits != set(proposal_source_edits):\n        missing = sorted(set(proposal_source_edits) - seen_source_edits)\n',
        '    if seen_source_edits != set(review_source_edits):\n        missing = sorted(set(review_source_edits) - seen_source_edits)\n',
        "review candidate completeness",
    )
    write(path, text)


def apply_tests() -> None:
    path = "tests/test_onboarding_placement.py"
    text = read(path)
    old = '''        self.assertIn("Overview is a condensation task", instruction.text)\n        self.assertIn("Consolidate closely related overview statements", instruction.text)\n        self.assertIn("source_edits", instruction.text)\n'''
    new = '''        self.assertIn("Overview is a condensation task", instruction.text)\n        self.assertIn("one bullet-sized fact", instruction.text)\n        self.assertIn("short versionless Overview", instruction.text)\n        self.assertIn("real plain-language summary", instruction.text)\n        self.assertIn("Pointer-only replacements", instruction.text)\n        self.assertIn("A reader should learn the gist without following the link", instruction.text)\n        self.assertIn("source_edits", instruction.text)\n'''
    text = replace_once(text, old, new, "placement instruction regression assertions")
    write(path, text)

    path = "tests/test_onboarding_placement_review.py"
    text = read(path)
    marker = '\n\n    def test_multiple_source_edits_owned_by_one_finding_parse_independently(self):'
    test = r'''

    def test_promote_without_llm_source_edit_gets_rejected_editable_human_fallback(self):
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
        review, created = create_or_load_placement_review(
            workspace.placement_path, proposal, prepared.snapshot_root
        )
        self.assertTrue(created)
        self.assertEqual(len(review.source_edits), 1)
        fallback = review.source_edits[0]
        self.assertTrue(fallback.proposal_id.startswith("H-"))
        self.assertEqual(fallback.decision, "reject")
        rendered = workspace.placement_path.read_text(encoding="utf-8")
        self.assertIn("Optional human override", rendered)
        self.assertIn("Source edit decision: `reject`", rendered)
        self.assertNotIn("Linked promoted findings:", rendered)

        replacement = "Architecture in one sentence. Maintained detail lives in [AI Workstation Context](../CONTEXT.md)."
        rendered = rendered.replace(f'<!-- cc:source-after id="{fallback.proposal_id}":start -->\n# Architecture\nThe repository is the installation specification.\n<!-- cc:source-after', f'<!-- cc:source-after id="{fallback.proposal_id}":start -->\n{replacement}\n<!-- cc:source-after', 1)
        rendered = rendered.replace("Decision: `pending`", "Decision: `accept`", 1)
        rendered = rendered.replace("Source edit decision: `reject`", "Source edit decision: `accept`", 1)
        workspace.placement_path.write_text(rendered, encoding="utf-8")
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(loaded.source_edits[0].decision, "accept")
        self.assertEqual(loaded.source_edits[0].replacement, replacement)
'''
    if "test_promote_without_llm_source_edit_gets_rejected_editable_human_fallback" not in text:
        text = text.replace(marker, test + marker)
    old = '''        self.assertEqual(rendered.count("Source edit note:"), 2)\n        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)\n'''
    new = '''        self.assertEqual(rendered.count("Source edit note:"), 2)\n        self.assertNotIn("Linked promoted findings:", rendered)\n        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)\n'''
    text = replace_once(text, old, new, "shared edit self-reference regression")
    write(path, text)


def apply_docs() -> None:
    path = "docs/onboarding.md"
    text = read(path)
    old = '''The non-redundancy goal is therefore **one canonical meaning, many useful routes**. After a promoted meaning is safely canonical in its Node, later reviewed cleanup should remove a true duplicate from mutable documentation or replace it with concise orientation and a mechanically derived link to the owning Context Node. Friendly or informal summary wording is fine when it helps the human reader; the same full rule or explanation must not remain maintained in both places.\n\nPreserve precise existing wording for facts, constraints, and Rules when it is already the best canonical wording. **Overview is a condensation task, not a quotation task:** summarize the durable responsibility sharply, move volatile platform/version compatibility into `state`, and split long snake sentences into separate atomic findings so the resulting Node can read naturally as bullets.\n'''
    new = '''The non-redundancy goal is therefore **one canonical meaning, many useful routes**. After a promoted meaning is safely canonical in its Node, reviewed cleanup should remove the duplicate from mutable documentation or replace it with a **real short summary plus the link** to the owning Context Node. The summary is not allowed to collapse into a content-free “details are in Context” pointer when the old location still matters to a first-time reader: it should preserve the gist, while the Node owns the exact maintained detail. Friendly or informal wording is fine when it improves comprehension; the same full rule or explanation must not remain maintained in both places.\n\nPreserve precise existing wording for facts, constraints, and Rules when it is already the best canonical wording. **Overview is a condensation task, not a quotation task:** summarize the durable responsibility sharply and move volatile platform/version compatibility into `state`. Overview, State and Plan findings are deliberately bullet-sized; when one source block contains a list or matrix, prefer several short findings over one comma/semicolon snake sentence.\n\nThe human cockpit has one additional safety net: when a promoted finding has one unambiguous mutable Markdown range but the LLM proposes no Source After edit, `STEP-07-placement.md` exposes that exact range as an optional human override. It defaults to `reject`, so it never creates cleanup work by itself; the owner can edit the replacement and switch it to `accept` without hunting for the source range later.\n'''
    text = replace_once(text, old, new, "onboarding docs source-after summary")
    write(path, text)


def apply() -> None:
    apply_instruction()
    apply_review()
    apply_tests()
    apply_docs()


def finalize() -> None:
    path = "PLAN.md"
    text = read(path)
    start = text.index("#### Block M — make Source After a real summary and keep the cockpit recoverable")
    block = text[start:]
    block = block.replace("- [ ] ", "- [x] ")
    checkpoint = """

Placement summary/cockpit checkpoint: the placement instruction now requires a real A′ summary plus the Context link, explicitly rejects pointer-only Source After prose at still-useful human surfaces, keeps volatile compatibility out of stable Overview, and treats Overview/State/Plan findings as one bullet-sized fact each. STEP-07 hides self-referential linked-finding noise and exposes a deterministic review-only Source edit when a promoted finding has an unambiguous mutable Markdown range but the LLM omitted cleanup; that fallback defaults to reject and therefore cannot mutate the project unless the owner edits and accepts it. Focused regressions cover the instruction and human fallback round-trip; full suite/build/check/diff-check are green before cleanup.
"""
    write(path, (text[:start] + block.rstrip() + checkpoint).rstrip() + "\n")

    path = "STATE.md"
    state = read(path).rstrip()
    section = "## Latest placement-summary and cockpit correction"
    if section not in state:
        state += """

## Latest placement-summary and cockpit correction

The real `ai-workstation` Step-7 review showed that the LLM could still satisfy the earlier placement prompt with version-heavy stable Overview, comma-heavy State, and Source After replacements that were little more than “see Project Context”. The semantic instruction now requires stable Overview to shed volatile compatibility already modeled as State, makes Overview/State/Plan findings bullet-sized, and requires a useful plain-language gist plus the canonical Context link wherever a human-facing source location remains useful. STEP-07 also keeps a conservative human escape hatch: an unambiguous mutable source range omitted by the LLM is rendered as an optional review-only edit defaulting to reject, so the owner may correct the source aftermath in place without reconstructing paths/ranges. Single-finding source edits no longer print a tautological self-reference such as `Linked promoted findings: P-004`; genuinely shared edits still point to the one editable owner block.
"""
    write(path, state + "\n")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "apply"
    {"plan": plan, "apply": apply, "finalize": finalize}[command]()
