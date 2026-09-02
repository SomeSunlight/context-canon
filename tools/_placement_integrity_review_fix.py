from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text.rstrip() + "\n", encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement target, found {count}: {old[:100]!r}")
    write(path, text.replace(old, new, 1))


def append_once(path: str, marker: str, addition: str) -> None:
    text = read(path)
    if marker in text:
        return
    write(path, text.rstrip() + "\n\n" + addition.strip() + "\n")


def plan() -> None:
    append_once(
        "PLAN.md",
        "#### Block N — preserve semantic integrity and make the placement cockpit visibly editable",
        r'''
#### Fast-run status — ACTIVE

The project owner has explicitly delegated the current live `ai-workstation` correction sequence as an owner-approved fast-run. This boundary is now recorded durably instead of living only in conversation.

- **Scope:** corrections discovered while vertically reviewing the real onboarding placement, through the next coherent owner-review candidate.
- **Reduced intermediate ceremony:** repeated PR-description polish, full CI and generated-output refresh may be deferred between small related corrections; focused verification and recovery checkpoints remain required.
- **Exit condition:** the project owner explicitly ends the fast-run, or the current placement line reaches a coherent owner-review candidate. At exit, record **Fast-run status — CLOSED** in PLAN before returning to ordinary review cadence.
- **Authority is unchanged:** fast-run changes cadence only. PR #13 remains review-only and must not be merged without explicit owner approval and the normal exact-head merge gate.

The exact historical instant at which this already-running cadence began is intentionally not invented retroactively; this checkpoint makes the active boundary explicit from here forward.

#### Block N — preserve semantic integrity and make the placement cockpit visibly editable

Purpose: incorporate the next real `ai-workstation` placement-review findings without making the semantic pass brittle. Source cleanup must never silently discard facts, open questions must survive onboarding in the owning Node, and the Markdown cockpit must show human-editable regions even in rendered views.

- [ ] Require a per-Source-edit zero-loss audit: every substantive fact removed from the frozen range must remain in A′ or be carried by linked promoted findings that cite that source range; a duplicate elsewhere may not accidentally rescue an incomplete move.
- [ ] Make `unresolved` a destination-bearing promoted local open question and publish it into the destination Node's State so investigation can happen after onboarding without blocking it.
- [ ] Tighten the one-finding/one-fact guidance enough that lists and three-or-more independently maintainable clauses cannot be hidden inside one `includes A, B, C` or semicolon-heavy bullet.
- [ ] Keep review-only H-fallback cleanup away from retained Topic/Resource documents and release-history/patch documents.
- [ ] Make optional source cleanup explicitly independent from accepting the promoted finding, and add visible rendered Markdown markers around every human-editable control/content region.
- [ ] Clarify historical evidence for volatile State: when only changelog/history supports a value, say `last documented` or leave it unresolved rather than presenting it as proven current state.
- [ ] Record the bounded fast-run start/scope/exit contract in the reusable Development Workflow while leaving this currently active fast-run open.
- [ ] Add focused regressions, run the complete deterministic suite, rebuild/check generated ContextCanon output, and leave PR #13 draft/unmerged for continued owner testing.

### Later documentation follow-up

- [ ] Document the observed onboarding effect that book placement itself surfaces previously hidden responsibilities, boundaries and unresolved questions; concise finding titles become a useful project index before the reader even opens the deeper material.
''',
    )


def apply_instruction() -> None:
    path = "src/contextcanon/onboarding_placement_instruction.py"
    replace_once(
        path,
        "A stable Overview must not repeat volatile exact versions, compatibility numbers or current-phase details when those facts can be represented as State. If one source sentence mixes durable identity with volatile compatibility, split it into a short versionless Overview plus separate State finding(s).",
        "A stable Overview must not repeat volatile exact versions, compatibility numbers or current-phase details when those facts can be represented as State. If one source sentence mixes durable identity with volatile compatibility, split it into a short versionless Overview plus separate State finding(s). **Splitting is not permission to drop facts:** the State finding(s) must cite the original mixed source range as Evidence so any Source After edit can link the exact promoted destinations that carry those removed details.",
    )
    replace_once(
        path,
        "When a source block is a list or matrix of independently readable facts, emit several short findings instead of compressing them into one comma/semicolon snake sentence. Consolidate only when one genuinely atomic sentence says the job better.",
        "When a source block is a list or matrix of independently readable facts, emit several short findings instead of compressing them into one comma/semicolon snake sentence. If one candidate sentence contains three or more independently maintainable claims, split it. Do not evade this by writing `includes A, B, C` or by joining several facts with semicolons. Consolidate only when one genuinely atomic sentence says the job better.",
    )
    replace_once(
        path,
        "History such as CHANGELOG/patch records normally remains history, fixed Markdown remains untouched, and configuration/CI/manifests remain authoritative technical sources rather than targets for prose cleanup.",
        "History such as CHANGELOG/patch records normally remains history, fixed Markdown remains untouched, and configuration/CI/manifests remain authoritative technical sources rather than targets for prose cleanup. Likewise, Markdown retained as a `topic-resource` remains its own maintenance surface and normally must not receive a Source After cleanup merely because one fact from it was promoted elsewhere.",
    )
    replace_once(
        path,
        "8. Use action `keep` only for ordinary documentation or unresolved information that intentionally stays outside canonical Node authoring.",
        "8. Use action `keep` only for ordinary documentation that intentionally stays outside canonical Node authoring. An `unresolved` finding is different: it is a valuable open project question discovered by onboarding. Give it the most relevant destination Node and action `promote`; ContextCanon will carry it as a local open question in that Node's State. Do not answer the question merely to finish onboarding, and do not let investigation block the migration.",
    )
    replace_once(
        path,
        "13. Preserve project state, planning, important local development constraints, and unresolved contradictions explicitly. Before returning, check that the better structure did not silently drop high-value semantics visible elsewhere in the same frozen Evidence.",
        "13. Preserve project state, planning, important local development constraints, and unresolved contradictions explicitly. A volatile version/value supported only by release history or other historical prose is not proven current merely because it is the newest historical mention: phrase it as `last documented ...` or emit an unresolved question when currentness matters. Before returning, check that the better structure did not silently drop high-value semantics visible elsewhere in the same frozen Evidence.",
    )
    replace_once(
        path,
        "18. Before returning, run a final readability/redundancy audit: every Overview/State/Plan item is one bullet-sized fact; stable Overview does not repeat volatile versions already represented as State; every Source After replacement at a still-useful human location carries a real gist plus its Context link rather than a pointer-only sentence; and every shared edit names all promoted findings whose meaning it summarizes.",
        "18. Before returning, run two final audits. **Readability/redundancy:** every Overview/State/Plan item is one bullet-sized fact; stable Overview does not repeat volatile versions already represented as State; every Source After replacement at a still-useful human location carries a real gist plus its Context link rather than a pointer-only sentence; and every shared edit names all promoted findings whose meaning it summarizes. **Zero semantic loss per Source edit:** enumerate the substantive facts in that exact frozen `start_line..end_line`. Every fact removed from A must either still be present in A′ or be represented by one or more `linked_item_ids` whose Evidence cites the relevant removed source range. Do not rely on the same fact happening to occur elsewhere in another document or duplicate passage.",
    )
    replace_once(
        path,
        "`destination_node_key` must be one key from the human-edited structure. It is required for `overview`, `rule`, `topic-resource`, `state`, `plan`, and `authority-mapping`; it may be `null` for ordinary documentation or unresolved information that stays outside Node authoring.",
        "`destination_node_key` must be one key from the human-edited structure. It is required for `overview`, `rule`, `topic-resource`, `state`, `plan`, `authority-mapping`, and `unresolved`; it may be `null` only for ordinary documentation that stays outside Node authoring.",
    )
    replace_once(
        path,
        '- `unresolved`: `{"question": "..."}` and action must be `keep`',
        '- `unresolved`: `{"question": "..."}` and action must be `promote`; give it the Node that should carry the open question until it is resolved',
    )
    replace_once(
        path,
        "`source_edits` is the proposed A → A′ side of promotion. Use only mutable `.md` Evidence that is not listed as fixed Markdown. Every edited line must be covered by Evidence cited by the linked promoted items; linked IDs must all be `promote` items.",
        "`source_edits` is the proposed A → A′ side of promotion. Use only mutable `.md` Evidence that is not listed as fixed Markdown. Every edited line must be covered by Evidence cited by the linked promoted items; linked IDs must all be `promote` items and must not be `unresolved` findings, because an unanswered question cannot justify deleting uncertain source meaning.",
    )


def apply_proposal_validation() -> None:
    path = "src/contextcanon/onboarding_placement.py"
    replace_once(
        path,
        'if kind in {"overview", "rule", "topic-resource", "state", "plan", "authority-mapping"} and destination is None:',
        'if kind in {"overview", "rule", "topic-resource", "state", "plan", "authority-mapping", "unresolved"} and destination is None:',
    )
    replace_once(path, '"unresolved": {"keep"},', '"unresolved": {"promote"},')
    replace_once(
        path,
        '            if linked_item.action != "promote":\n                raise _error(f"{label} may link only promoted placement items; {linked_id} uses {linked_item.action}")',
        '            if linked_item.action != "promote":\n                raise _error(f"{label} may link only promoted placement items; {linked_id} uses {linked_item.action}")\n            if linked_item.kind == "unresolved":\n                raise _error(f"{label} cannot use unresolved finding {linked_id} to justify source cleanup")',
    )


def apply_review() -> None:
    path = "src/contextcanon/onboarding_placement_review.py"
    replace_once(
        path,
        '    if kind in {"overview", "rule", "topic-resource", "state", "plan"}:\n        heading = "### Into Node — editable"\n    else:\n        heading = "### Reviewed handling — editable"\n    lines = [heading, ""]',
        '    if kind in {"overview", "rule", "topic-resource", "state", "plan", "unresolved"}:\n        heading = "### Into Node — editable"\n    else:\n        heading = "### Reviewed handling — editable"\n    lines = [heading, "", "**✏️ EDITABLE START — destination content**", ""]',
    )
    replace_once(
        path,
        '    else:\n        raise _error(f"unsupported kind {kind!r}")\n    return lines',
        '    else:\n        raise _error(f"unsupported kind {kind!r}")\n    lines.extend(["", "**✏️ EDITABLE END — destination content**"])\n    return lines',
    )
    replace_once(
        path,
        '    grouped: dict[tuple[str, str, int, int], list[str]] = {}\n    for item in proposal.items:',
        '    protected_resources = {\n        str(path)\n        for item in proposal.items\n        if item.kind == "topic-resource"\n        for path in item.payload.get("resource_paths", [])\n    }\n\n    def history_document(path_value: str) -> bool:\n        name = Path(path_value).name.lower()\n        return name.startswith("changelog") or name.startswith("patch-") or "/patch-" in path_value.lower()\n\n    grouped: dict[tuple[str, str, int, int], list[str]] = {}\n    for item in proposal.items:',
    )
    replace_once(
        path,
        '            if not reference.path.lower().endswith(".md") or reference.path in fixed:\n                continue',
        '            if (\n                not reference.path.lower().endswith(".md")\n                or reference.path in fixed\n                or reference.path in protected_resources\n                or history_document(reference.path)\n            ):\n                continue',
    )
    replace_once(
        path,
        '                "**Optional human override — the LLM proposed no Source After rewrite here.**",\n                "It defaults to `reject`. Edit the replacement and switch to `accept` only if you want this exact frozen range cleaned up now.",',
        '                "**Optional source cleanup — independent from promotion.**",\n                "Accepting or rejecting the finding above is separate. Leave this Source edit at `reject` to keep the source unchanged; switch to `accept` only if you want to rewrite this exact frozen range now.",',
    )
    replace_once(
        path,
        '            f"Source edit decision: `{edit.decision}`",\n            f"Source edit note: {edit.review_note or \'-\'}",',
        '            "**✏️ EDITABLE CONTROLS — source cleanup**",\n            f"Source edit decision: `{edit.decision}`",\n            f"Source edit note: {edit.review_note or \'-\'}",\n            "**✏️ END EDITABLE CONTROLS — source cleanup**",',
    )
    replace_once(
        path,
        '            "**Proposed replacement — edit the text between the markers:**",\n            "",\n            f\'<!-- cc:source-after id="{edit.proposal_id}":start -->\',',
        '            "**Proposed replacement — edit the text between the markers:**",\n            "",\n            "**✏️ EDITABLE START — source replacement**",\n            f\'<!-- cc:source-after id="{edit.proposal_id}":start -->\',',
    )
    replace_once(
        path,
        '    lines.extend([f\'<!-- cc:source-after id="{edit.proposal_id}":end -->\', "", f"Why this source edit: {candidate.rationale}", ""])',
        '    lines.extend([f\'<!-- cc:source-after id="{edit.proposal_id}":end -->\', "**✏️ EDITABLE END — source replacement**", "", f"Why this source edit: {candidate.rationale}", ""])',
    )
    replace_once(
        path,
        '        f"## {review_item.proposal_id} — {review_item.title}",\n        f\'<!-- cc:placement-item id="{review_item.proposal_id}" authoring-id="{review_item.authoring_id}" -->\',\n        "",\n        f"Destination: {destination_text}",',
        '        f"## {review_item.proposal_id} — {review_item.title}",\n        f\'<!-- cc:placement-item id="{review_item.proposal_id}" authoring-id="{review_item.authoring_id}" -->\',\n        "",\n        "**✏️ EDITABLE CONTROLS — finding**",\n        f"Destination: {destination_text}",',
    )
    replace_once(
        path,
        '        f"Review note: {review_item.review_note or \'-\'}",\n        "",\n    ]',
        '        f"Review note: {review_item.review_note or \'-\'}",\n        "**✏️ END EDITABLE CONTROLS — finding**",\n        "",\n    ]',
    )
    replace_once(
        path,
        '        "Edit this file directly. **This is the transformation cockpit.** For promoted meaning, review what is going into the destination, the frozen source before, and the proposed source after. Change `Decision`, destination, kind/action, title, destination wording, Source edit decision/replacement, or review notes where necessary.",',
        '        "Edit this file directly. **This is the transformation cockpit.** For promoted meaning, review what is going into the destination, the frozen source before, and the proposed source after. Change `Decision`, destination, kind/action, title, destination wording, Source edit decision/replacement, or review notes where necessary. Rendered Markdown deliberately shows `✏️ EDITABLE` boundary labels; the hidden `cc:*` comments remain machine markers and are not the only way to discover editability.",',
    )
    replace_once(path, '"unresolved": {"keep"},', '"unresolved": {"promote"},')
    replace_once(
        path,
        '    requires_destination = kind in {"overview", "rule", "topic-resource", "state", "plan", "authority-mapping"}',
        '    requires_destination = kind in {"overview", "rule", "topic-resource", "state", "plan", "authority-mapping", "unresolved"}',
    )


def apply_publication() -> None:
    path = "src/contextcanon/onboarding_placement_publish.py"
    replace_once(
        path,
        'def _render_summaries(items: list[PlacementReviewItem], kind: str) -> str:\n    lines: list[str] = []\n    for item in items:\n        text = _safe_line(item.payload["text"], f"item {item.proposal_id} {kind}")\n        lines.extend([f\'<!-- cc:placement-{kind} id="{item.authoring_id}" -->\', f"- {text}", ""])\n    return "\\n".join(lines).rstrip()\n',
        'def _render_summaries(items: list[PlacementReviewItem], kind: str) -> str:\n    lines: list[str] = []\n    for item in items:\n        text = _safe_line(item.payload["text"], f"item {item.proposal_id} {kind}")\n        lines.extend([f\'<!-- cc:placement-{kind} id="{item.authoring_id}" -->\', f"- {text}", ""])\n    return "\\n".join(lines).rstrip()\n\n\ndef _render_state(items: list[PlacementReviewItem]) -> str:\n    lines: list[str] = []\n    for item in items:\n        if item.kind == "state":\n            text = _safe_line(item.payload["text"], f"item {item.proposal_id} state")\n            lines.extend([f\'<!-- cc:placement-state id="{item.authoring_id}" -->\', f"- {text}", ""])\n        elif item.kind == "unresolved":\n            question = _safe_line(item.payload["question"], f"item {item.proposal_id} unresolved question")\n            lines.extend([f\'<!-- cc:placement-unresolved id="{item.authoring_id}" -->\', f"- Open question: {question}", ""])\n    return "\\n".join(lines).rstrip()\n',
    )
    replace_once(
        path,
        '    states = [item for item in items if item.kind == "state"]',
        '    states = [item for item in items if item.kind in {"state", "unresolved"}]',
    )
    replace_once(
        path,
        '    text = _replace_managed_section(text, "State", "state", _render_summaries(states, "state"))',
        '    text = _replace_managed_section(text, "State", "state", _render_state(states))',
    )
    replace_once(
        path,
        '        if item.kind not in {"overview", "rule", "topic-resource", "state", "plan"}:',
        '        if item.kind not in {"overview", "rule", "topic-resource", "state", "plan", "unresolved"}:',
    )
    replace_once(
        path,
        '        if item.decision == "accept" and item.kind in {"ordinary-documentation", "authority-mapping", "unresolved"}',
        '        if item.decision == "accept" and item.kind in {"ordinary-documentation", "authority-mapping"}',
    )
    replace_once(
        path,
        '"No accepted Overview, State, Plan, Rule, Topic/Resource or Source changes currently touch a Context Node.",',
        '"No accepted Overview, State/open-question, Plan, Rule, Topic/Resource or Source changes currently touch a Context Node.",',
    )
    replace_once(
        path,
        'groups = (("state", "State"), ("plan", "Plan"), ("authority-mapping", "Fixed-authority mappings"), ("ordinary-documentation", "Ordinary documentation"), ("unresolved", "Unresolved"))',
        'groups = (("authority-mapping", "Fixed-authority mappings"), ("ordinary-documentation", "Ordinary documentation"))',
    )


def apply_workflow_docs() -> None:
    replace_once(
        "nodes/library/development-workflow/CONTEXT.src.md",
        "- **Use owner-approved fast-run blocks without weakening the final gate:** When the project owner explicitly approves a coherent implementation scope and says intermediate product review is unnecessary, keep durable PLAN/recovery checkpoints and focused verification inside bounded work blocks, but defer repeated PR-description polish, full CI, generated-output regeneration, and other review ceremony until the coherent review candidate.\n  Why: Explicit delegation can remove intermediate coordination cost without sacrificing recoverability, final human review, or exact-head merge verification.",
        "- **Use owner-approved fast-run blocks without weakening the final gate:** When the project owner explicitly approves a coherent implementation scope and says intermediate product review is unnecessary, mark the fast-run as active in the durable PLAN with its scope and exit condition, keep recovery checkpoints and focused verification inside bounded work blocks, and defer repeated PR-description polish, full CI, generated-output regeneration, and other review ceremony until the coherent review candidate. When the fast-run ends, record that closure before returning to ordinary review cadence.\n  Why: Explicit delegation can remove intermediate coordination cost without sacrificing recoverability. Visible start/scope/exit/closure boundaries prevent a long single-worker fast-run from becoming undocumented process state, while final human review and exact-head merge verification remain unchanged.",
    )
    replace_once(
        "nodes/library/development-workflow/docs/change-workflow.md",
        "Fast-run changes **cadence, not authority**: the work still stays on a review branch, PLAN remains current enough to resume after interruption, unknown failures are investigated, and the resulting coherent candidate still requires project-owner review followed by the ordinary exact-head merge gate.",
        "Fast-run changes **cadence, not authority**: the work still stays on a review branch, PLAN remains current enough to resume after interruption, unknown failures are investigated, and the resulting coherent candidate still requires project-owner review followed by the ordinary exact-head merge gate.\n\nMake the boundary visible in PLAN rather than leaving the mode implicit in chat history. A compact form is enough:\n\n```text\nFast-run status — ACTIVE\nScope: <delegated coherent work>\nDeferred ceremony: <what is intentionally batched>\nExit: <owner ends it or named coherent review boundary>\n\n... work/checkpoints ...\n\nFast-run status — CLOSED\nResult/checkpoint: <where normal cadence resumes>\n```\n\nDo not invent a historical start time after the fact. If a fast-run is already under way when this convention is adopted, record that it is active now, its current scope, and its exit condition. The important property is recoverable mode state, not timestamp theatre.",
    )


def apply_tests() -> None:
    path = "tests/test_onboarding_placement.py"
    replace_once(
        path,
        '        self.assertIn("one bullet-sized fact", instruction.text)\n        self.assertIn("short versionless Overview", instruction.text)',
        '        self.assertIn("one bullet-sized fact", instruction.text)\n        self.assertIn("three or more independently maintainable claims", instruction.text)\n        self.assertIn("short versionless Overview", instruction.text)\n        self.assertIn("Splitting is not permission to drop facts", instruction.text)\n        self.assertIn("Zero semantic loss per Source edit", instruction.text)\n        self.assertIn("last documented", instruction.text)\n        self.assertIn("local open question", instruction.text)',
    )
    insert = r'''
    def test_unresolved_requires_destination_and_promotes_for_later_investigation(self):
        _, prepared, workspace, readme, architecture, source_root, package = self.make_case()
        raw = self.placement_dict(prepared, workspace, readme, architecture, package)
        raw["items"].append({
            "id": "P-003",
            "title": "Version semantics unclear",
            "kind": "unresolved",
            "action": "keep",
            "destination_node_key": None,
            "rationale": "The question should survive onboarding.",
            "confidence": "medium",
            "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 1}],
            "payload": {"question": "Which version surface is canonical?"},
        })
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "requires destination_node_key"):
            load_onboarding_placement_proposal(
                workspace.placement_proposal_path, prepared.snapshot_root, workspace.structure_proposal_path,
                workspace.structure_path, catalog_package_roots=[source_root],
            )

        raw["items"][-1]["destination_node_key"] = "N-001"
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "kind unresolved must use action promote"):
            load_onboarding_placement_proposal(
                workspace.placement_proposal_path, prepared.snapshot_root, workspace.structure_proposal_path,
                workspace.structure_path, catalog_package_roots=[source_root],
            )

        raw["items"][-1]["action"] = "promote"
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path, prepared.snapshot_root, workspace.structure_proposal_path,
            workspace.structure_path, catalog_package_roots=[source_root],
        )
        self.assertEqual(proposal.items[-1].kind, "unresolved")
        self.assertEqual(proposal.items[-1].destination_node_key, "N-001")

'''
    text = read(path)
    marker = "    def test_cli_writes_instruction_validates_and_renders_review_without_redirects(self):\n"
    if "test_unresolved_requires_destination_and_promotes_for_later_investigation" not in text:
        if marker not in text:
            raise SystemExit(f"{path}: insertion marker missing")
        write(path, text.replace(marker, insert + marker, 1))

    path = "tests/test_onboarding_placement_review.py"
    replace_once(
        path,
        '        self.assertIn("### Source after promotion", text)\n        self.assertIn(\'origin="owner-selected"\', text)',
        '        self.assertIn("### Source after promotion", text)\n        self.assertIn("✏️ EDITABLE CONTROLS — finding", text)\n        self.assertIn("✏️ EDITABLE START — destination content", text)\n        self.assertIn("✏️ EDITABLE START — source replacement", text)\n        self.assertIn(\'origin="owner-selected"\', text)',
    )
    replace_once(
        path,
        '        raw["source_edits"] = []\n        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")',
        '        raw["source_edits"] = []\n        # Put the promoted finding on a mutable gateway line; architecture.md is\n        # retained as the fixture Topic/Resource and therefore must not receive\n        # an automatically invented H-fallback cleanup.\n        raw["items"][0]["evidence"] = [{"path": "README.md", "sha256": readme.sha256, "start_line": 2, "end_line": 2}]\n        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")',
    )
    replace_once(
        path,
        '        self.assertIn("Optional human override", rendered)\n        self.assertIn("Source edit decision: `reject`", rendered)',
        '        self.assertIn("Optional source cleanup — independent from promotion", rendered)\n        self.assertIn("Leave this Source edit at `reject` to keep the source unchanged", rendered)\n        self.assertIn("Source edit decision: `reject`", rendered)',
    )
    insert = r'''
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
        self.assertNotIn("Optional source cleanup", workspace.placement_path.read_text(encoding="utf-8"))

'''
    text = read(path)
    marker = "    def test_multiple_source_edits_owned_by_one_finding_parse_independently(self):\n"
    if "test_review_fallback_does_not_offer_cleanup_for_topic_resource" not in text:
        if marker not in text:
            raise SystemExit(f"{path}: insertion marker missing")
        write(path, text.replace(marker, insert + marker, 1))

    path = "tests/test_onboarding_placement_publish.py"
    replace_once(
        path,
        '                {\n                    "id": "P-006",\n                    "title": "README authority mapping",',
        '                {\n                    "id": "P-008",\n                    "title": "Project version semantics remain unresolved",\n                    "kind": "unresolved",\n                    "action": "promote",\n                    "destination_node_key": "N-001",\n                    "rationale": "The open question should survive onboarding without blocking publication.",\n                    "confidence": "medium",\n                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 1}],\n                    "payload": {"question": "Should the project and release version surfaces be aligned?"},\n                },\n                {\n                    "id": "P-006",\n                    "title": "README authority mapping",',
    )
    replace_once(
        path,
        '        self.assertIn("Migration is in progress.", root.after)\n        self.assertIn("## Plan", root.after)',
        '        self.assertIn("Migration is in progress.", root.after)\n        self.assertIn("Open question: Should the project and release version surfaces be aligned?", root.after)\n        self.assertIn("## Plan", root.after)',
    )
    replace_once(
        path,
        '        self.assertIn("Migration is in progress.", parsed_root.state)\n        self.assertIn("Continue Goose changes through reviewed pull requests.", parsed_root.plan)',
        '        self.assertIn("Migration is in progress.", parsed_root.state)\n        self.assertIn("Open question: Should the project and release version surfaces be aligned?", parsed_root.state)\n        self.assertIn("Continue Goose changes through reviewed pull requests.", parsed_root.plan)',
    )


def apply() -> None:
    apply_instruction()
    apply_proposal_validation()
    apply_review()
    apply_publication()
    apply_workflow_docs()
    apply_tests()


def finalize() -> None:
    path = "PLAN.md"
    text = read(path)
    block_start = text.index("#### Block N — preserve semantic integrity and make the placement cockpit visibly editable")
    later = text.index("### Later documentation follow-up", block_start)
    before = text[:block_start]
    block = text[block_start:later].replace("- [ ]", "- [x]")
    after = text[later:]
    checkpoint = """
Placement semantic-integrity checkpoint: the second semantic pass now audits every proposed Source After transformation for zero semantic loss against its exact frozen range; splitting volatile detail out of Overview requires destination State findings to cite that same mixed source. Unresolved findings are destination-bearing promoted open questions and publish into local Node State instead of disappearing into follow-up. The review-only H-fallback no longer offers cleanup for retained Topic/Resource documents or release-history/patch documents, optional cleanup explicitly says it is independent from accepting the finding, and rendered Markdown shows visible ✏️ boundaries around editable controls/content. The Development Workflow now requires an explicit fast-run ACTIVE scope/exit boundary and later CLOSED checkpoint; the current owner-approved fast-run remains ACTIVE. Focused placement regressions, the complete deterministic suite, full build/check and diff hygiene passed before this checkpoint.
"""
    if "Placement semantic-integrity checkpoint:" not in block:
        block = block.rstrip() + "\n\n" + checkpoint.strip() + "\n\n"
    write(path, before + block + after)

    append_once(
        "STATE.md",
        "## Latest placement semantic-integrity correction",
        r'''
## Latest placement semantic-integrity correction

The latest real `ai-workstation` placement review exposed a more important invariant than wording quality: Source After cleanup must not be able to remove a fact merely because another duplicate passage happens to mention it elsewhere. The placement instruction therefore performs a per-edit zero-loss audit against the exact frozen source range. Every removed substantive fact must remain in the source summary or be carried by linked promoted findings whose Evidence cites that removed range. Stable Overview can still shed volatile versions, but the corresponding State findings must explicitly carry those facts from the same mixed source.

Open semantic questions discovered during onboarding are now first-class local project state. `unresolved` findings require a destination Node and action `promote`; publication renders them under that Node's State as `Open question: ...`. The question remains unanswered and can be investigated after onboarding, so semantic archaeology improves the project backlog without turning the migration itself into a research project.

The Step-07 cockpit now visibly marks editable controls, destination content and Source After replacement regions with `✏️ EDITABLE` labels that survive ordinary rendered Markdown views. Review-only optional source cleanup is explicitly independent from finding acceptance: leaving an H-edit at `reject` keeps the source byte range unchanged while the promoted finding may still be accepted. Automatically invented H-fallbacks are deliberately withheld for Markdown retained as Topic/Resource and for CHANGELOG/patch history.

## Active fast-run boundary

The current project-owner testing sequence is explicitly recorded as **Fast-run status — ACTIVE** in PLAN. Its scope is the live `ai-workstation` onboarding corrections through the next coherent owner-review candidate. Fast-run reduces repeated intermediate ceremony but does not alter authority: PR #13 remains draft/unmerged, unknown failures still require investigation, and final owner review plus exact-head merge verification remain mandatory. The reusable Development Workflow now requires both the ACTIVE scope/exit checkpoint and a later CLOSED checkpoint when ordinary cadence resumes.
''',
    )


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"plan", "apply", "finalize"}:
        raise SystemExit("usage: _placement_integrity_review_fix.py plan|apply|finalize")
    {"plan": plan, "apply": apply, "finalize": finalize}[sys.argv[1]]()


if __name__ == "__main__":
    main()
