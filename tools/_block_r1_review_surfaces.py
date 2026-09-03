from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:80]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def activate_plan() -> None:
    path = Path("PLAN.md")
    text = path.read_text(encoding="utf-8")
    marker = "**Status: NEXT — preserve now, implement in coherent follow-up blocks after post-publish inspection. Fast-run remains ACTIVE.**"
    active = """**Status: ACTIVE — Block R1 review-surface ergonomics. Fast-run remains ACTIVE.**

R1 purpose: make the two human review gates visibly editable without visual shouting, make Step 07 self-contained about its controls, and remove `Action` as a fake independent choice while preserving the existing deterministic Kind→Action contract.

R1 verification: focused structure/placement-review regressions first, then the complete deterministic suite plus self-hosted build/check and hygiene before the clean checkpoint."""
    if "R1 purpose:" not in text:
        if marker not in text:
            raise SystemExit("PLAN.md: Block R status marker not found")
        path.write_text(text.replace(marker, active, 1), encoding="utf-8")


def patch_structure() -> None:
    replace_once("src/contextcanon/onboarding_structure.py", '        "## Node tree",\n        "",\n        _TREE_START,', '        "## Node tree",\n        "",\n        "> ✏️ Edit the Node tree between the markers below. Indentation defines the reviewed semantic parent/child hierarchy.",\n        "",\n        _TREE_START,')
    replace_once("src/contextcanon/onboarding_structure.py", '    lines.extend([_TREE_END, "", "## Proposed non-Node knowledge bodies", ""])', '    lines.extend([_TREE_END, "", "> End editable Node tree.", "", "## Proposed non-Node knowledge bodies", ""])')


def patch_placement() -> None:
    path = "src/contextcanon/onboarding_placement_review.py"
    replace_once(path, 'REVIEW_DECISIONS = {"pending", "accept", "reject"}\n', 'REVIEW_DECISIONS = {"pending", "accept", "reject"}\nACTION_FOR_KIND = {\n    "overview": "promote",\n    "rule": "promote",\n    "topic-resource": "reference",\n    "ordinary-documentation": "keep",\n    "state": "promote",\n    "plan": "promote",\n    "authority-mapping": "map",\n    "unresolved": "promote",\n}\n')
    replace_once(path, '    lines = [heading, "", "**✏️ EDITABLE START — destination content**", ""]', '    lines = [heading, "", "> ✏️ Editable destination content starts below.", ""]')
    replace_once(path, '    lines.extend(["", "**✏️ EDITABLE END — destination content**"])', '    lines.extend(["", "> End editable destination content."])')
    replace_once(path, '            "**✏️ EDITABLE CONTROLS — source cleanup**",', '            "> ✏️ Editable source-cleanup controls",')
    replace_once(path, '            "**✏️ END EDITABLE CONTROLS — source cleanup**",', '            "> End editable source-cleanup controls",')
    replace_once(path, '        "Edit this file directly. **This is the transformation cockpit.** For promoted meaning, review what is going into the destination, the frozen source before, and the proposed source after. Change `Decision`, destination, kind/action, title, destination wording, Source edit decision/replacement, or review notes where necessary. Rendered Markdown deliberately shows `✏️ EDITABLE` boundary labels; the hidden `cc:*` comments remain machine markers and are not the only way to discover editability.",', '        "Edit this file directly. **This is the transformation cockpit.** For promoted meaning, review what is going into the destination, the frozen source before, and the proposed source after. Change `Decision`, destination, `Kind`, title, destination wording, Source edit decision/replacement, or review notes where necessary. `Action` is derived from `Kind`; it is shown for clarity but is not an independent control. Quiet `✏️` boundary cues mark editable regions; hidden `cc:*` comments remain machine markers.",')
    replace_once(path, '        "Item, Source-edit and reusable-Source decisions are `pending`, `accept`, or `reject`. ContextCanon never publishes a pending review. Frozen source excerpts are read-only; text between `cc:source-after` markers is editable and becomes the reviewed replacement if that Source edit is accepted. When the LLM omitted a rewrite for one unambiguous mutable range, ContextCanon may expose a review-only optional Source edit that defaults to `reject`; it exists only so the owner can edit that exact range without reconstructing it later.",\n        "",', '        "Item, Source-edit and reusable-Source decisions are `pending`, `accept`, or `reject`. ContextCanon never publishes a pending review. Frozen source excerpts are read-only; text between `cc:source-after` markers is editable and becomes the reviewed replacement if that Source edit is accepted. When the LLM omitted a rewrite for one unambiguous mutable range, ContextCanon may expose a review-only optional Source edit that defaults to `reject`; it exists only so the owner can edit that exact range without reconstructing it later.",\n        "",\n        "## Editable control glossary",\n        "",\n        "- `Decision`: `pending` while undecided, then `accept` or `reject`.",\n        "- `Destination`: the reviewed Context Node that owns this finding; `none / outside Node authoring` is valid only for kinds that intentionally stay outside Node authoring.",\n        "- `Kind`: `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, or `unresolved`.",\n        "- Derived `Action`: `overview`/`rule`/`state`/`plan`/`unresolved` → `promote`; `topic-resource` → `reference`; `ordinary-documentation` → `keep`; `authority-mapping` → `map`. Change the Kind, not the derived Action.",\n        "- `Wording` where shown: `exact`, `lightly-edited`, or `synthesized`.",\n        "- `Review note`: optional owner rationale or reminder; use `-` for none.",\n        "",')
    replace_once(path, '        "**✏️ EDITABLE CONTROLS — finding**",\n        f"Destination: {destination_text}",\n        f"Decision: `{review_item.decision}`",\n        f"Kind: `{review_item.kind}`",\n        f"Action: `{review_item.action}`",\n        f"Review note: {review_item.review_note or \'-\'}",\n        "**✏️ END EDITABLE CONTROLS — finding**",', '        "> ✏️ Editable finding controls",\n        f"Destination: {destination_text}",\n        f"Decision: `{review_item.decision}`",\n        f"Kind: `{review_item.kind}`",\n        f"Derived action: `{review_item.action}` (from Kind; do not edit)",\n        f"Review note: {review_item.review_note or \'-\'}",\n        "> End editable finding controls",')
    replace_once(path, '        kind = _simple_value(block, "Kind")\n        action = _simple_value(block, "Action")\n        destination = _destination(block, allow_none=True)', '        kind = _simple_value(block, "Kind")\n        action = ACTION_FOR_KIND.get(kind, "")\n        destination = _destination(block, allow_none=True)')
    replace_once(path, '    allowed_actions = {\n        "overview": {"promote"},\n        "rule": {"promote"},\n        "topic-resource": {"reference"},\n        "ordinary-documentation": {"keep"},\n        "state": {"promote"},\n        "plan": {"promote"},\n        "authority-mapping": {"map"},\n        "unresolved": {"promote"},\n    }\n    if action not in allowed_actions[kind]:\n        expected = ", ".join(sorted(allowed_actions[kind]))\n        raise _error(f"item {item_id} Kind {kind} must use Action {expected}")', '    expected_action = ACTION_FOR_KIND[kind]\n    if action != expected_action:\n        raise _error(f"item {item_id} Kind {kind} must use Action {expected_action}")')


def patch_tests() -> None:
    replace_once("tests/test_onboarding_structure.py", '        self.assertIn("- **AI Workstation** (`.`) <!-- cc:key=N-001 -->", text)', '        self.assertIn("> ✏️ Edit the Node tree between the markers below.", text)\n        self.assertIn("> End editable Node tree.", text)\n        self.assertIn("- **AI Workstation** (`.`) <!-- cc:key=N-001 -->", text)')
    path = "tests/test_onboarding_placement_review.py"
    replace_once(path, '        self.assertIn("### Into Node — editable", text)', '        self.assertIn("### Into Node — editable", text)\n        self.assertIn("## Editable control glossary", text)\n        self.assertIn("Change the Kind, not the derived Action.", text)\n        self.assertIn("Derived action: `promote` (from Kind; do not edit)", text)\n        self.assertNotIn("\\nAction: `", text)')
    replace_once(path, '        self.assertIn("✏️ EDITABLE CONTROLS — finding", text)\n        self.assertIn("✏️ EDITABLE START — destination content", text)', '        self.assertIn("✏️ Editable finding controls", text)\n        self.assertIn("✏️ Editable destination content starts below.", text)')
    replace_once(path, '    def test_invalid_human_rule_reference_is_rejected(self):\n        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)\n        text = workspace.placement_path.read_text(encoding="utf-8").replace("Action: `promote`", "Action: `reference`", 1)\n        workspace.placement_path.write_text(text, encoding="utf-8")\n        with self.assertRaisesRegex(ContextCanonError, "Kind rule must use Action promote"):\n            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)\n', '    def test_action_is_derived_from_kind_and_rendered_text_is_not_a_control(self):\n        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)\n        text = workspace.placement_path.read_text(encoding="utf-8").replace(\n            "Derived action: `promote` (from Kind; do not edit)",\n            "Derived action: `reference` (tampered display text)",\n            1,\n        )\n        workspace.placement_path.write_text(text, encoding="utf-8")\n        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)\n        self.assertEqual(loaded.items[0].kind, "rule")\n        self.assertEqual(loaded.items[0].action, "promote")\n')


def complete_plan_and_state() -> None:
    plan = Path("PLAN.md")
    text = plan.read_text(encoding="utf-8")
    text = text.replace("**Status: ACTIVE — Block R1 review-surface ergonomics. Fast-run remains ACTIVE.**", "**Status: NEXT — Block R1 complete; continue with the remaining Block R follow-up slices. Fast-run remains ACTIVE.**", 1)
    for old in [
        "- [ ] Give Step 03 the same visible edit affordance as Step 07, but use a quieter presentation that preserves the visual dominance of the Node tree. Apply the same lower-noise treatment to Step 07 so editable boundaries are obvious without overwhelming headings/content.",
        "- [ ] Make Step 07 self-contained about every editable control. Show allowed `Decision` values and a concise Kind/Action glossary directly in the review artifact; an operator inside another repository must not need to know that `docs/onboarding.md` exists in the ContextCanon repository.",
        "- [ ] Reconsider whether `Action` should be independently editable at all. Current validation effectively derives one action from each kind (`promote`, `reference`, `keep`, `map`); the review UX should expose meaningful choices rather than a pseudo-choice that can only form one valid Kind/Action pair.",
    ]:
        if old not in text:
            raise SystemExit(f"PLAN.md: expected R1 checklist item not found: {old[:80]}")
        text = text.replace(old, old.replace("- [ ]", "- [x]", 1), 1)
    text = text.replace("R1 verification: focused structure/placement-review regressions first, then the complete deterministic suite plus self-hosted build/check and hygiene before the clean checkpoint.", "R1 verification: focused structure/placement-review regressions passed, followed by the complete deterministic suite, self-hosted build/check and `git diff --check`. Step 03 now has quiet visible edit boundaries; Step 07 contains its own control glossary and quieter edit cues; Action is derived deterministically from Kind and is no longer parsed as an independent owner control.", 1)
    plan.write_text(text, encoding="utf-8")
    state = Path("STATE.md")
    st = state.read_text(encoding="utf-8")
    marker = "## Latest Block R1 review-surface checkpoint"
    if marker not in st:
        st = st.rstrip() + "\n\n" + marker + "\n\nThe first post-publish UX slice is complete. Step 03 now marks the editable semantic Node tree with quiet visible cues instead of relying only on hidden comments. Step 07 is self-contained about Decision, Destination, Kind, derived Action, Wording and Review-note semantics, and its editable regions use lower-noise visual boundaries.\n\n`Action` is no longer an independent human control in placement review. The renderer shows it as derived from `Kind`, and the parser deterministically reconstructs the only valid Kind→Action mapping. Stable review semantics and the existing placement proposal contract are unchanged. The remaining Block R work — source-file-first transformation audit, ordinary post-onboarding authoring ergonomics, semantic parent composition/Topic inheritance and Source-update UX — remains pending. Fast-run stays active and PR #13 remains draft/unmerged.\n"
        state.write_text(st, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    if args.complete:
        complete_plan_and_state()
        return
    activate_plan()
    patch_structure()
    patch_placement()
    patch_tests()


if __name__ == "__main__":
    main()
