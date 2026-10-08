# Onboarding short-path owner test (#107 Phase 2)

PR #108 is accepted in main. PR #111 includes that baseline and stays Draft for this onboarding test; no Phase-2 merge is authorized. No confidential project data needs to leave your machine.

## Update the editable tool checkout

In your local **ContextCanon code repository**, not the internal project:

```text
git fetch origin
git switch agent/issue-107-onboarding-versions
git pull --ff-only
uv tool install --force --editable .
contextcanon --version
```

Check that the displayed Git revision belongs to PR #111. With an editable installation, later branch pulls are used directly; reinstall is needed when entry points/dependencies change.

## New onboarding

From the selected project or subtree root:

```text
contextcanon onboard init .
```

Open the `PLAN.md` printed by the command. A root project keeps `contextcanon-onboarding/`; a subtree gets a visible workspace at the outer Git root. Continue the ordinary STEP 01–12 flow. Evidence and exact reusable/enclosing-Parent packages no longer accumulate under every nested Node. STEP 04/08 print short root-level handoff locations; use only that directory or ZIP as the reasoning environment. Follow the generated PLAN instead of typing tokens.

Exercise a reusable Parent plus a Reference at STEP 07, then STEP 08, STEP 10, preview and publication. Check that the selected types appear in the final canonical imports and that an enclosing Parent was not added twice.

## Existing active onboarding

First make a **complete filesystem return copy** of the consuming repository, including ignored ContextCanon workspaces/state. Git alone does not preserve pending human reviews, Evidence, handoffs or receipts. Keep the old executable checkout/branch available if you need to return to it.

From the particular project/subtree whose old onboarding you want to continue:

```text
contextcanon onboard migrate .
```

Inspect the selected snapshot, new workspace and copy/retirement counts. Preview must not change files. If there is no unique active run, use the old PLAN's snapshot:

```text
contextcanon onboard migrate . --snapshot <old-snapshot>
```

For an in-repository custom workspace, also pass `--workspace <path>`; it stays in place. Use the identical selection with `--apply` only after inspecting the preview:

```text
contextcanon onboard migrate . --apply
```

The command prints the new PLAN. Confirm your existing STEP-07 decisions, placement proposal/review and any handoff RESULT.json remain. Continue at the already reached step; no new LLM run is required for relocation. Repeat `--apply` to confirm a completed migration is idempotent. If an operation is interrupted, that same command verifies and resumes its narrow recovery receipt.

Post-preparation `.idea/` and `.vscode/` metadata at workspace/STEP-04/08 task roots does not block migration. It remains at its original location, is excluded from migration inputs/copies/retirement, and appears in `preserved_tool_metadata`; do not move/delete IDE settings just to migrate. Old directories can therefore remain containing only IDE metadata. Explicitly declared Evidence is still verified even inside those namespaces. This is a narrow metadata policy, not a Git-ignore bypass: ignored frozen inputs remain binding and other unknown files still require classification/preservation.

If exact old frozen bytes are missing or a destination has unrelated files, migration refuses before mutation and identifies the input/problem. Preserve it and report the exact message; do not replace a reviewed provider with a newer package or delete whole stores to force continuation.

## Publication and recovery

After the normal preview/publish gates, run from the consuming Git root:

```text
contextcanon build --all .
contextcanon check --all .
contextcanon propagate --status --all .
```

Pending genuine normative provider changes need ordinary reviewed `propagate --all .` acceptance before the final health check. References should not produce normative Child propagation.

If old normal accepted stores still exist, migrate those separately after the active onboarding migration:

```text
contextcanon versions migrate .
contextcanon versions migrate . --apply
contextcanon build --all .
contextcanon check --all .
```

In a test return copy, exercise `contextcanon onboard reset . --from 7`, `--from 10` or `--from 12` from the selected project scope. Verify only that run's later artifacts/publication reverse; other projects, exact shared versions and historical runs remain. To undo the entire storage migration, restore the full return copy rather than expecting a Git rollback or semantic reset to reconstruct ignored transport directories.

The path reduction applies to ContextCanon-owned stores and new compact exports. Exact retained old packages keep their original interior paths; genuinely long project document paths still count. Inspect a warning's longest destination instead of renaming documents blindly. Report successful continuation/reset and any remaining long destination on PR #111. Keep #107 open until both phases have owner acceptance.

PR #111 targets accepted main and preserves the active editable test branch's ancestry for fast-forward pulls. Require fresh exact-head CI and explicit owner approval before a Phase-2 merge.
