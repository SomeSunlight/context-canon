from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one occurrence, found {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# Console entry point journals materializing onboarding commands and exposes reset in CLI help.
replace_once(
    "pyproject.toml",
    'contextcanon = "contextcanon.cli:main"',
    'contextcanon = "contextcanon.entry:main"',
)
(ROOT / "src/contextcanon/__main__.py").write_text(
    "from .entry import main\n\nraise SystemExit(main())\n", encoding="utf-8", newline="\n"
)
replace_once(
    "src/contextcanon/cli.py",
    "from .onboarding_workspace import open_onboarding_workspace, update_workspace_checkpoint, write_utf8\n",
    "from .onboarding_workspace import open_onboarding_workspace, update_workspace_checkpoint, write_utf8\n"
    "from .onboarding_reset import add_reset_parser, handle_reset_args\n",
)
replace_once(
    "src/contextcanon/cli.py",
    "    onboard_prepare.add_argument(\n        \"--include\",\n",
    "    add_reset_parser(onboard_sub)\n\n"
    "    onboard_prepare.add_argument(\n        \"--include\",\n",
)
replace_once(
    "src/contextcanon/cli.py",
    '            if args.onboard_command == "structure-instruction":\n',
    '            if args.onboard_command == "reset":\n'
    '                result = handle_reset_args(args)\n'
    '                print(f"reset onboarding from step {result[\'from_step\']}")\n'
    '                print(f"Journal records reversed: {result[\'journal_records_reversed\']}")\n'
    '                print(f"Project files restored/removed: {len(result[\'project_files_restored_or_removed\'])}")\n'
    '                print(f"Workspace files removed: {len(result[\'workspace_files_removed\'])}")\n'
    '                print("Frozen Evidence: preserved")\n'
    '                return 0\n\n'
    '            if args.onboard_command == "structure-instruction":\n',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                update_workspace_checkpoint(
                    workspace, snapshot,
                    stage="structure instruction ready",
                    next_action=(
''',
    '''                update_workspace_checkpoint(
                    workspace, snapshot,
                    stage="structure instruction ready",
                    source_catalog=_catalog_labels(instruction.catalog_packages),
                    source_catalog_inputs=tuple(args.catalog_package),
                    next_action=(
''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                    next_action = (
                        f"Run `contextcanon onboard placement-preview {_snapshot_cli(snapshot)}` with the exact `--catalog-package` inputs listed above."
                        if review.is_complete else
                        "Edit `placement.md`: set every Decision to `accept` or `reject` and correct destination/maintained meaning where needed. "
                        f"Then run `contextcanon onboard placement-preview {_snapshot_cli(snapshot)}` with the exact `--catalog-package` inputs listed above."
                    )
''',
    '''                    next_action = (
                        f"Run `contextcanon onboard placement-preview {_snapshot_cli(snapshot)}` after checking the exact command in PLAN.md."
                        if review.is_complete else
                        f"Edit `{workspace.placement_path.name}`: set every Decision to `accept` or `reject` and correct destination/maintained meaning where needed. "
                        f"Then rerun `contextcanon onboard placement-review {_snapshot_cli(snapshot)}` to validate the edited human gate before preview."
                    )
''',
)

# Placement reasoning: summarize now, split snake sentences, and extract architecture semantics instead of deferring the thinking.
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        "1. Preserve good existing project language. When a clear, self-contained source statement already says the right thing, use it verbatim and set `wording_origin` to `exact`.",
        "2. Use `lightly-edited` only when small changes are necessary to make a fragment self-contained, remove accidental surrounding context, or combine adjacent wording without changing meaning. Use `synthesized` only when no good source wording exists and the semantic idea genuinely needs a new formulation.",
        "3. The primary question is **where should this meaning be maintained from now on?** Minimize future redundancy. Every durable meaning should have one canonical maintenance surface. Do not preserve a poor current file boundary merely because the text happens to live there, and do not beautify terminology merely because you can.",
        "4. Use kind `overview` plus action `promote` for short durable orientation about what one Node owns or is responsible for. Overview is stable local presentation, not temporary project `state` and not inherited governance.",
''',
    '''        "1. Preserve precise existing language for facts, constraints, and Rules when it is already the best canonical wording. **Overview is different:** it is a condensation task, not a quotation task. When source orientation mixes purpose with platform/version/current-state detail, synthesize the short durable purpose now and place volatile compatibility/version detail in `state` instead.",
        "2. Do the semantic cleanup in this placement pass. A later Markdown cleanup is only the reviewed mutation of source documents; it must not require the owner to reopen the same semantic design problem. Use `lightly-edited` for small self-containment edits and `synthesized` when a sharper canonical summary or decomposition is genuinely better than the source sentence.",
        "3. The primary question is **where should this meaning be maintained from now on?** Minimize future redundancy. Every durable meaning should have one canonical maintenance surface. Do not preserve a poor current file boundary merely because the text happens to live there.",
        "4. Use kind `overview` plus action `promote` for short durable orientation about what one Node owns or is responsible for. Prefer one crisp sentence or several separate atomic overview findings over a semicolon/comma-heavy snake sentence. If one source passage contains several independently maintainable responsibilities, split them into separate findings so the resulting Node reads naturally as bullets.",
''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        "10. Treat README as first-contact orientation/navigation rather than the default store for volatile state, future plan, detailed architecture, or every implementation invariant. Use `state` for current local situation, `plan` for future work, `overview` for stable Node responsibility, Rules for durable governance, and Topics/Resources for deeper task material.",
        "11. Treat CONTRIBUTING, architecture notes, implementation/configuration, CI, tests, security policy, state/planning text, and imported documentation according to their actual semantic role. Conventional files can be stale; prefer direct implementation/configuration/CI/test evidence for current behavior when it clearly conflicts with prose.",
''',
    '''        "10. Treat README as first-contact orientation/navigation rather than the default store for volatile state, future plan, detailed architecture, or every implementation invariant. Its durable project summary should be short and human-facing; exact supported versions/platforms normally belong in root `state` or a narrower Node. Use `state` for current local situation, `plan` for future work, `overview` for stable Node responsibility, Rules for durable governance, and Topics/Resources for genuinely useful deeper task material.",
        "11. Treat CONTRIBUTING, architecture notes, implementation/configuration, CI, tests, security policy, state/planning text, and imported documentation according to their actual semantic role. In particular, do **not** keep `architecture.md` as a Topic/Resource merely because its filename says architecture: promote its durable responsibilities/invariants into the owning Nodes when that is the better maintenance surface. It is acceptable for a later reviewed cleanup to reduce such a document to a short orientation/reference or remove it when no independent procedural, explanatory, diagrammatic, or authority value remains. Conventional files can be stale; prefer direct implementation/configuration/CI/test evidence for current behavior when it clearly conflicts with prose.",
''',
)

# Human review calls the proposed canonical wording what it is: Summary. Old Text: files still load.
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''    elif kind in {"overview", "state", "plan"}:
        lines.append(f"Text: {_one_line(payload['text'])}")
        lines.append(f"Wording: `{payload['wording_origin']}`")
''',
    '''    elif kind in {"overview", "state", "plan"}:
        lines.append(f"Summary: {_one_line(payload['text'])}")
        lines.append(f"Wording: `{payload['wording_origin']}`")
''',
)
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''    if kind in {"overview", "state", "plan"}:
        return {
            "text": _find_line(block, "Text: ", "Text"),
            "wording_origin": _simple_value(block, "Wording"),
        }
''',
    '''    if kind in {"overview", "state", "plan"}:
        summary_lines = [line[len("Summary: ") :] for line in block if line.startswith("Summary: ")]
        text_lines = [line[len("Text: ") :] for line in block if line.startswith("Text: ")]
        if len(summary_lines) == 1 and not text_lines:
            maintained = summary_lines[0].strip()
        elif len(text_lines) == 1 and not summary_lines:
            maintained = text_lines[0].strip()
        else:
            raise _error("Summary must appear exactly once (legacy Text is accepted only when Summary is absent)")
        return {
            "text": maintained,
            "wording_origin": _simple_value(block, "Wording"),
        }
''',
)

# Multiple canonical overview findings become a naturally scannable bullet list.
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '''        lines.extend([f'<!-- cc:placement-overview id="{item.authoring_id}" -->', text, ""])
''',
    '''        lines.extend([f'<!-- cc:placement-overview id="{item.authoring_id}" -->', f"- {text}", ""])
''',
)

# Update existing assertions to the nine-step runbook.
test_path = ROOT / "tests/test_onboarding_workspace_checkpoint.py"
test = test_path.read_text(encoding="utf-8")
test = test.replace(
    'self.assertIn("- [x] 5. Placement proposal", first)\n        self.assertIn("- [ ] 6. Placement review", first)',
    'self.assertIn("- [x] 5. Placement proposal", first)\n        self.assertIn("- [x] 6. Placement validate", first)\n        self.assertIn("- [ ] 7. Placement review", first)',
)
test = test.replace(
    'self.assertIn("- [x] 8. Publish placement", second)',
    'self.assertIn("- [x] 9. Publish placement", second)',
)
test_path.write_text(test, encoding="utf-8", newline="\n")

# Focused instruction regression checks.
test_path = ROOT / "tests/test_onboarding_placement.py"
test = test_path.read_text(encoding="utf-8")
needle = '        self.assertIn("README as first-contact orientation/navigation", instruction.text)\n'
if needle not in test:
    raise RuntimeError("placement instruction assertion anchor missing")
test = test.replace(
    needle,
    needle
    + '        self.assertIn("Overview is different", instruction.text)\n'
    + '        self.assertIn("split them into separate findings", instruction.text)\n'
    + '        self.assertIn("do **not** keep `architecture.md` as a Topic/Resource merely because", instruction.text)\n',
    1,
)
test_path.write_text(test, encoding="utf-8", newline="\n")

# Durable PLAN checkpoint: this commit is created only if all tests below pass.
plan_path = ROOT / "PLAN.md"
plan = plan_path.read_text(encoding="utf-8")
if "#### Block F — owner-testing UX hardening" not in plan:
    plan += '''

#### Block F — owner-testing UX hardening

Purpose: remove operator reconstruction work exposed by the second live `ai-workstation` onboarding. ContextCanon should make a difficult semantic migration easier to execute, not require the operator to memorize similar CLI spellings, long digests, artifact names, or hidden validation steps.

- [x] Make placement validation an explicit numbered step between LLM placement proposal and human placement review.
- [x] Turn the workspace PLAN into a snapshot-bound copy/paste console with exact commands, persisted Source-catalog arguments, and reset commands for each restart point.
- [x] Prefix workflow artifacts with their step number so alphabetic file order matches the human onboarding flow; migrate unambiguous legacy workspace filenames safely.
- [x] Add safe `onboard reset --from N`: journal ContextCanon-managed project mutations, verify current bytes before rollback, preserve frozen Evidence, and conservatively remove untouched pre-journal onboarding skeleton Nodes.
- [x] Make semantic condensation part of the placement reasoning pass itself: present Overview/State/Plan wording as `Summary`, move volatile compatibility detail out of stable Overview, prefer atomic findings/bullets over snake sentences, and do not preserve architecture documents as Resources when their durable meaning belongs canonically in Nodes.
- [x] Require edited placement review to be revalidated through `placement-review` before advancing to publication preview.
- [x] Add focused regression coverage for runbook numbering/copy-paste commands, reset safety, legacy skeleton cleanup, and the sharper placement instruction.
'''
    plan_path.write_text(plan, encoding="utf-8", newline="\n")
