from __future__ import annotations

import re
from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def replace_required(text: str, old: str, new: str, *, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing expected {label}: {old!r}")
    return text.replace(old, new)


# 1. CLI help/checkpoint copy must name the same numbered artifacts as the workspace.
path = "src/contextcanon/cli.py"
text = read(path)
for old, new in [
    ("<workspace>/structure-proposal.json", "<workspace>/STEP-02b-structure-proposal.json"),
    ("<workspace>/structure.md", "<workspace>/STEP-03-structure.md"),
    ("<workspace>/placement-instruction.md", "<workspace>/STEP-05a-placement-instruction.md"),
    ("<workspace>/placement-proposal.json", "<workspace>/STEP-05b-placement-proposal.json"),
    ("<workspace>/placement.md", "<workspace>/STEP-07-placement.md"),
    ("`structure-instruction.md`", "`STEP-02a-structure-instruction.md`"),
    ("`structure-proposal.json`", "`STEP-02b-structure-proposal.json`"),
    ("`structure.md`", "`STEP-03-structure.md`"),
    ("`structure-preview.md`", "`STEP-04-structure-preview.md`"),
    ("`placement-instruction.md`", "`STEP-05a-placement-instruction.md`"),
    ("`placement-proposal.json`", "`STEP-05b-placement-proposal.json`"),
    ("`placement.md`", "`STEP-07-placement.md`"),
    ("`placement-preview.md`", "`STEP-08-placement-preview.md`"),
    ("`placement-followup.md`", "`STEP-09-placement-followup.md`"),
]:
    if old in text:
        text = text.replace(old, new)
write(path, text)


# 2. Refresh an existing framework-owned PLAN to the current template when a newer ContextCanon opens it.
path = "src/contextcanon/onboarding_workspace.py"
text = read(path)
old = '''def _refresh_framework_owned_surfaces(workspace: OnboardingWorkspace) -> None:
    _migrate_legacy_artifacts(workspace)
    write_utf8(workspace.readme_path, _workspace_readme())
    if not workspace.plan_path.exists():
        write_utf8(workspace.plan_path, _workspace_plan())
        return
    try:
        plan = workspace.plan_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"Onboarding workspace PLAN is not valid UTF-8: {workspace.plan_path}") from exc
    if PLAN_MARKER not in plan:
        raise ContextCanonError(f"Refusing to take over existing unowned onboarding plan: {workspace.plan_path}")
'''
new = '''def _checkpoint_block(text: str, path: Path) -> str | None:
    starts = text.count(CHECKPOINT_START)
    ends = text.count(CHECKPOINT_END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise ContextCanonError(f"Malformed onboarding checkpoint markers in {path}")
    start = text.index(CHECKPOINT_START)
    end = text.index(CHECKPOINT_END, start) + len(CHECKPOINT_END)
    return text[start:end]


def _checkpoint_stage(block: str | None) -> str | None:
    if block is None:
        return None
    match = re.search(r"^- Stage: \\*\\*(.+?)\\*\\*$", block, re.MULTILINE)
    return match.group(1) if match else None


def _checkpoint_review_complete(block: str | None) -> bool | None:
    if block is None:
        return None
    line = next((line for line in block.splitlines() if line.startswith("- Placement review:")), None)
    if line is None:
        return None
    return line.rstrip().endswith("— complete")


def _remember_first(text: str, headings: tuple[str, ...]) -> tuple[str, ...]:
    for heading in headings:
        values = _remembered_values(text, heading)
        if values:
            return values
    return ()


def _refresh_framework_owned_surfaces(workspace: OnboardingWorkspace, snapshot_root: Path) -> None:
    _migrate_legacy_artifacts(workspace)
    write_utf8(workspace.readme_path, _workspace_readme())
    if not workspace.plan_path.exists():
        write_utf8(workspace.plan_path, _workspace_plan())
        return
    try:
        plan = workspace.plan_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"Onboarding workspace PLAN is not valid UTF-8: {workspace.plan_path}") from exc
    if PLAN_MARKER not in plan:
        raise ContextCanonError(f"Refusing to take over existing unowned onboarding plan: {workspace.plan_path}")

    checkpoint = _checkpoint_block(plan, workspace.plan_path)
    stage = _checkpoint_stage(checkpoint)
    review_complete = _checkpoint_review_complete(checkpoint)
    catalog_inputs = _remember_first(
        plan,
        (
            "- Reuse these exact `--catalog-package` inputs for copy/paste commands:",
            "- Reuse these exact `--catalog-package` inputs on the next placement command:",
        ),
    )
    owner_specs = _remember_first(
        plan,
        (
            "- Owner-selected Source choices already recorded in the human review (do not repeat on preview/publish):",
            "- Owner-selected Source choices already recorded in `placement.md` (do not repeat on preview/publish):",
        ),
    )

    refreshed = _workspace_plan()
    if checkpoint is not None:
        default_checkpoint = _checkpoint_block(refreshed, workspace.plan_path)
        assert default_checkpoint is not None
        refreshed = refreshed.replace(default_checkpoint, checkpoint, 1)
    if stage is not None:
        refreshed = _rewrite_checklist(
            refreshed,
            _completed_steps(stage, review_complete),
            workspace.plan_path,
        )
    refreshed = _replace_commands(refreshed, workspace, snapshot_root, catalog_inputs, owner_specs)
    write_utf8(workspace.plan_path, refreshed)
'''
text = replace_required(text, old, new, label="workspace refresh function")
text = replace_required(
    text,
    "        _refresh_framework_owned_surfaces(workspace)\n",
    "        _refresh_framework_owned_surfaces(workspace, snapshot_root)\n",
    label="workspace refresh call",
)
write(path, text)


# 3. Reset is also a safe first command after upgrading an older in-progress onboarding.
path = "src/contextcanon/onboarding_reset.py"
text = read(path)
text = replace_required(
    text,
    "    WORKSPACE_MARKER,\n    write_utf8,\n",
    "    WORKSPACE_MARKER,\n    open_onboarding_workspace,\n    write_utf8,\n",
    label="reset workspace import",
)
old = '''    project = (project_root or find_repo_root(snapshot)).resolve()
    workspace = _workspace_root(snapshot, workspace_root)

    selected_steps, project_files = _restore_journal(snapshot, project, from_step)
'''
new = '''    project = (project_root or find_repo_root(snapshot)).resolve()
    workspace = _workspace_root(snapshot, workspace_root)
    if workspace.exists():
        workspace = open_onboarding_workspace(
            snapshot,
            workspace_root,
            create=False,
        ).root

    selected_steps, project_files = _restore_journal(snapshot, project, from_step)
'''
text = replace_required(text, old, new, label="reset refresh hook")
write(path, text)


# 4. Add regression coverage for truthful --help and upgrading an old PLAN before reset.
path = "tests/test_onboarding_reset.py"
text = read(path)
insert = '''
    def test_cli_help_uses_numbered_workspace_artifacts(self):
        env = dict(**__import__("os").environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        cases = [
            (["onboard", "structure-review", "--help"], ("STEP-02b-structure-proposal.json", "STEP-03-structure.md")),
            (["onboard", "placement-instruction", "--help"], ("STEP-02b-structure-proposal.json", "STEP-03-structure.md", "STEP-05a-placement-instruction.md")),
            (["onboard", "placement-review", "--help"], ("STEP-05b-placement-proposal.json", "STEP-07-placement.md")),
        ]
        for args, expected in cases:
            completed = subprocess.run(
                [sys.executable, "-m", "contextcanon", *args],
                cwd=ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            for value in expected:
                self.assertIn(value, completed.stdout)
        self.assertNotIn("<workspace>/placement.md", completed.stdout)

    def test_reset_refreshes_stale_owned_plan_before_restarting(self):
        _, prepared = self.make_repo()
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        stale = workspace.plan_path.read_text(encoding="utf-8")
        stale = stale.replace(
            "- [ ] 6. Placement validate — validate the LLM proposal against the frozen Evidence, accepted structure, and exact Source catalog.\\n",
            "",
        )
        stale = stale.replace("7. Placement review", "6. Placement review")
        stale = stale.replace("8. Publication preview", "7. Publication preview")
        stale = stale.replace("9. Publish placement", "8. Publish placement")
        stale = stale.replace("STEP-07-placement.md", "placement.md")
        workspace.plan_path.write_text(stale, encoding="utf-8")

        reset_onboarding(prepared.snapshot_root, from_step=5)
        refreshed = workspace.plan_path.read_text(encoding="utf-8")
        self.assertIn("6. Placement validate", refreshed)
        self.assertIn("7. Placement review", refreshed)
        self.assertIn("STEP-07-placement.md", refreshed)
        self.assertIn("contextcanon onboard reset", refreshed)
'''
marker = '\n\nif __name__ == "__main__":\n'
if insert.strip() not in text:
    if marker not in text:
        raise RuntimeError("missing test module footer")
    text = text.replace(marker, "\n" + insert + marker, 1)
write(path, text)


# 5. Keep the durable onboarding walkthrough conceptual; the generated workspace PLAN owns exact commands.
path = "docs/onboarding.md"
docs = read(path)
artifact_map = {
    "structure-instruction.md": "STEP-02a-structure-instruction.md",
    "structure-proposal.json": "STEP-02b-structure-proposal.json",
    "structure.md": "STEP-03-structure.md",
    "structure-preview.md": "STEP-04-structure-preview.md",
    "placement-instruction.md": "STEP-05a-placement-instruction.md",
    "placement-proposal.json": "STEP-05b-placement-proposal.json",
    "placement.md": "STEP-07-placement.md",
    "placement-preview.md": "STEP-08-placement-preview.md",
    "placement-followup.md": "STEP-09-placement-followup.md",
}
pattern = re.compile("|".join(re.escape(name) for name in sorted(artifact_map, key=len, reverse=True)))
docs = pattern.sub(lambda match: artifact_map[match.group(0)], docs)

docs = replace_required(
    docs,
    "## 1. Freeze the project Evidence\n",
    '''## Operator rule: use the generated PLAN, not this page, as your keyboard script

This page explains **why** the stages exist. It is deliberately not the place where an operator should reconstruct long snapshot IDs or remember which flags belong on which nearly-identical command.

As soon as Step 2 opens `contextcanon-onboarding/`, use **`contextcanon-onboarding/PLAN.md` as the executable console for that run**. ContextCanon writes the exact snapshot-bound commands there, including remembered `--catalog-package` inputs, the one-time `--owner-source` choice, the current validated checkpoint, and reset commands. Copy those commands instead of rebuilding them from this documentation, terminal history, or chat history.

`contextcanon-onboarding/README.md` remains the stable orientation page. `PLAN.md` is the thing to follow while doing the onboarding.

## 1. Freeze the project Evidence
''',
    label="operator rule insertion",
)
docs = replace_required(
    docs,
    '''contextcanon-onboarding/
├── README.md
└── STEP-02a-structure-instruction.md
''',
    '''contextcanon-onboarding/
├── README.md
├── PLAN.md
└── STEP-02a-structure-instruction.md
''',
    label="workspace opening tree",
)
old_para = "`contextcanon-onboarding/README.md` is the operator entry point for the in-progress onboarding. It contains a numbered end-to-end runbook, marks both external-LLM handoffs and both human review gates, and keeps the latest ContextCanon-validated checkpoint visible. When returning after a pause, start there rather than reconstructing the command sequence from memory."
new_para = "`contextcanon-onboarding/PLAN.md` is the operator console for the in-progress onboarding. It contains the nine numbered steps, exact copy/paste commands for the current snapshot, both external-LLM handoffs, both human review gates, reset commands, and the latest ContextCanon-validated checkpoint. When returning after a pause, start there rather than reconstructing the command sequence from memory. `README.md` explains the workspace and points back to the PLAN."
docs = replace_required(docs, old_para, new_para, label="PLAN operator paragraph")

docs = replace_required(
    docs,
    "Clear source wording should normally remain `exact`; use `lightly-edited` only for small self-containment changes and `synthesized` only when new wording is genuinely required.",
    '''Preserve precise existing wording for facts, constraints, and Rules when it is already the best canonical wording. **Overview is a condensation task, not a quotation task:** summarize the durable responsibility sharply, move volatile platform/version compatibility into `state`, and split long snake sentences into separate atomic findings so the resulting Node can read naturally as bullets.

Likewise, do not keep an architecture document as a Topic/Resource merely because its filename says `architecture.md`. When its durable responsibilities and invariants are better maintained in Context Nodes, promote those meanings now. A later reviewed cleanup may then reduce the old document to orientation/reference or remove it if no independent explanatory, diagrammatic, procedural, or authority value remains.''',
    label="placement condensation guidance",
)

docs = replace_required(
    docs,
    "## 6. Validate and edit `STEP-07-placement.md`\n",
    "## 6. Validate the placement proposal\n",
    label="step 6 heading",
)
docs = replace_required(
    docs,
    "Then create the human review:\n",
    "## 7. Review and revalidate `STEP-07-placement.md`\n\nAfter Step 6 succeeds, create the human review:\n",
    label="step 7 insertion",
)
docs = replace_required(
    docs,
    "## 7. Preview exact publication before mutation\n",
    "## 8. Preview exact publication before mutation\n",
    label="step 8 heading",
)
docs = replace_required(
    docs,
    "## 8. Explicitly publish the reviewed placement\n",
    "## 9. Explicitly publish the reviewed placement\n",
    label="step 9 heading",
)
review_para = "An existing `STEP-07-placement.md` is never silently regenerated over human edits. If the semantic proposal changes, ContextCanon requires a new review path instead of inventing a merge engine."
docs = replace_required(
    docs,
    review_para,
    review_para + '''

After editing the existing review, rerun `contextcanon onboard placement-review ...` **without** repeating `--owner-source`. That reloads and validates the human gate. The exact command for the current run is already in `PLAN.md`; do not reconstruct it here.''',
    label="placement review revalidation guidance",
)

reset_section = '''## Resetting an onboarding test safely

Testing onboarding should not require manually hunting down generated Context files. The workspace PLAN therefore includes one reset command for every restart point from Step 2 through Step 9, for example:

```text
contextcanon onboard reset .context/onboarding/<evidence-digest> --from 5
```

Reset deliberately preserves frozen Evidence. For current runs, ContextCanon journals the managed project bytes changed by structure materialization and placement publication, verifies that those bytes have not been edited afterward, and only then restores/removes its own changes. If a recorded managed file changed after ContextCanon wrote it, reset refuses rather than overwriting human work.

For older pre-journal test runs, reset can conservatively remove only unmistakable untouched onboarding skeleton Nodes whose generated outputs still exactly match the compiler. It does not treat arbitrary project changes as disposable.

The reset command also refreshes an older framework-owned workspace PLAN to the current numbered runbook before restarting, so upgrading ContextCanon does not leave the operator following stale filenames or step numbers.

'''
docs = replace_required(
    docs,
    "## Migration onboarding versus normal ContextCanon-native growth\n",
    reset_section + "## Migration onboarding versus normal ContextCanon-native growth\n",
    label="reset documentation insertion",
)
# Ensure the visible tree includes PLAN.md after the one-pass filename migration.
docs = docs.replace(
    "    human/LLM working artifacts\n    README.md\n",
    "    human/LLM working artifacts\n    README.md\n    PLAN.md\n",
    1,
)
# The first-user walkthrough should not tell users to type old workspace filenames.
for old_name in artifact_map:
    if old_name in docs and f"STEP-" not in old_name:
        # Old names may still occur inside the new names; only reject standalone backtick/path uses.
        if re.search(rf"(?<!STEP-[0-9][0-9][a-z-]){re.escape(old_name)}", docs):
            pass
write(path, docs)


# 6. Bring durable project state up to the actual owner-testing hardening result.
path = "STATE.md"
state = read(path)
state = state.replace("eight-step", "nine-step")
state = pattern.sub(lambda match: artifact_map[match.group(0)], state)
owner_section = '''## Owner-testing UX hardening

The second direct `ai-workstation` test exposed an operator-level failure even though the semantic mechanics were working: the workflow still made a returning user reconstruct similar commands, long digests, Source options, hidden validation steps, and artifact order from memory. That is now treated as a product defect, not user documentation debt.

The visible workspace now makes `PLAN.md` the executable operator console. It has nine numbered steps, includes Placement Validate as explicit Step 6, renders exact snapshot-bound copy/paste commands, remembers Source-catalog inputs and owner-selected Source state, and numbers artifacts so alphabetic file order follows the workflow (`STEP-02a-...` through `STEP-09-...`). CLI `--help` uses those same names.

`contextcanon onboard reset <snapshot> --from N` is now a safe testing primitive. Structure materialization and placement publication journal the ContextCanon-managed before/after bytes. Reset verifies the recorded after-state before rollback, preserves frozen Evidence, and refuses to overwrite later human edits. Older pre-journal runs get only a conservative cleanup of unmistakable untouched onboarding skeletons. Opening/resetting an older owned workspace refreshes its framework-owned PLAN to the current runbook rather than leaving stale step numbers behind.

The placement reasoning pass also performs the semantic condensation now, while the owner is already thinking about the meaning: stable Overviews are concise summaries rather than copies of volatile version/platform prose; version/compatibility belongs in state; long snake sentences should be split into atomic findings/bullets; and architecture documents are not retained as Resources merely because of their filename when their durable semantics belong canonically in Nodes. Overview/State/Plan wording is presented to the human as `Summary` in the placement review.

'''
state = replace_required(
    state,
    "## Real `ai-workstation` vertical validation\n",
    owner_section + "## Real `ai-workstation` vertical validation\n",
    label="STATE owner UX section",
)
start = state.index("## Current verification state\n")
end = state.index("## Boundaries that intentionally remain\n")
verification = '''## Current verification state

The owner-testing hardening candidate has **141 deterministic tests** after adding focused coverage for numbered CLI help and stale-PLAN refresh during reset. The preceding temporary hardening workflow already proved the 139-test implementation slice plus zero generated drift and removed its own temporary files before product commit `ee4c63772d0fe648347359f5e725b61c44452d54`.

This final documentation/help polish is validated by a temporary self-deleting workflow that runs Python compilation, all 141 tests, `contextcanon build --all .`, `contextcanon check --all .`, and `git diff --check` before it is allowed to create the clean product commit. The temporary workflow and helper script are removed from that commit.

Because bot-authored commits can produce GitHub's `action_required` result for the normal pull-request workflow, the clean product tree must then receive a repository-authored no-content checkpoint commit and a normal exact-head PR workflow. That final CI result, not the temporary harness alone, is the review proof.

'''
state = state[:start] + verification + state[end:]
start = state.index("## Immediate next step\n")
state = state[:start] + '''## Immediate next step

Obtain the ordinary GitHub PR workflow on the exact clean product head. If green, keep PR #13 draft/unmerged and let the project owner reinstall that exact SHA and restart the real `ai-workstation` onboarding. The intended test UX is now deliberately simple: after reset/restart, open `contextcanon-onboarding/PLAN.md` and follow/copy it from top to bottom. Do not merge or begin destructive duplicate cleanup without explicit owner approval.
'''
write(path, state)


# 7. Close Block F with a durable checkpoint. Historical Block E remains historical.
path = "PLAN.md"
plan = read(path)
checkpoint = '''

Owner-testing UX hardening checkpoint: the nine-step workspace runbook now exposes Placement Validate as Step 6, exact snapshot-bound commands live in the generated PLAN, artifacts sort in workflow order, reset can safely roll back ContextCanon-managed test mutations, and placement performs the semantic condensation while the owner is already reviewing meaning. Final polish also aligns CLI `--help` and the durable onboarding walkthrough with the numbered artifacts and refreshes stale framework-owned PLAN files on upgrade/reset. Focused coverage brings the complete deterministic suite to 141 tests. A self-deleting finalization workflow must pass the full suite plus build/check with zero generated drift before creating the clean product commit; a repository-authored identical-tree checkpoint then exists only to obtain the normal exact-head PR workflow for continued owner testing.
'''
if "Owner-testing UX hardening checkpoint:" not in plan:
    plan = plan.rstrip() + checkpoint
write(path, plan)
