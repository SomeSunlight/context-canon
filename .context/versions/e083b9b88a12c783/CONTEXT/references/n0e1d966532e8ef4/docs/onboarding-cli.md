# ContextCanon onboarding CLI

This is the compact command reference for **onboarding an existing Git project or a later project subtree inside one**.

For an actual run, the generated `contextcanon-onboarding/PLAN.md` remains the primary operator console because it contains the current checkpoint and exact snapshot-bound commands. This page is the stable place to rediscover commands when the workspace is missing, when you need to step backwards, or when you want to understand the CLI stages.

Use `contextcanon onboard <command> --help` for every flag.

## Start

From the project scope you want to onboard:

```text
contextcanon --version
contextcanon onboard init .
```

For a first adoption this is usually the Git repository root. For a later subproject inside an already-onboarded repository, run the same command from that subtree root. Git still defines the outer repository boundary; authored material stays inside the selected subtree; new machine payloads and the default visible workspace use short, owned locations at the outer Git root. `init` prints the exact PLAN path.

Then open:

```text
contextcanon-onboarding/PLAN.md
```

## Relocate an existing active run

From its project/subtree root:

```text
contextcanon onboard migrate .
contextcanon onboard migrate . --apply
```

The first command is read-only. It selects accepted inventory or requires `--snapshot <old-snapshot>` when ambiguous. An in-repository custom workspace uses `--workspace <path>` and remains in place. Continue with the printed new PLAN; original reviews, frozen bindings, handoff results and portable ZIP bytes are preserved. Retry the same apply after interruption. See [storage, safety and recovery](onboarding-storage.md) and the [owner test](../plans/issue-107-onboarding-owner-test.md).

All examples below use `<snapshot>`: copy the exact snapshot variable/commands from the generated PLAN, whose relative locators remain usable when the checkout moves. Historical full-digest local runs remain readable.

## Go back or restart

This works on a live project; a fresh clone is not required:

```text
contextcanon onboard reset . --from <STEP>
```

| Reset target | What is kept | What is discarded |
| --- | --- | --- |
| `--from 1` | normal project files | all ContextCanon-owned onboarding workspace/machine state; later journaled onboarding mutations are rolled back first |
| `--from 2` | initialized onboarding workspace | inventory CSV, accepted Evidence and all later onboarding work |
| `--from 3` | reviewed STEP-02 inventory CSV + inventory scope/rules | accepted Evidence and all later semantic work |
| `--from 4` … `--from 12` | accepted inventory + frozen Evidence | managed artifacts/mutations from that semantic step onward |

STEP 01 also removes ContextCanon's marked onboarding block from the project `.gitignore`. Running `contextcanon onboard init .` adds it again.

For compatibility, STEP 04–12 reset still accepts an explicit Evidence snapshot path instead of `.` when needed.

## STEP 01–03 — define the Evidence boundary

STEP 01 is human cleanup guidance; it has no separate command.

Generate or refresh the reviewed file inventory:

```text
contextcanon onboard inventory .
```

Useful inventory options:

```text
contextcanon onboard inventory . --directory P1 --directory P2
contextcanon onboard inventory . --rule "docs/*.csv=structured-data:source"
```

Obvious copies that should not participate in onboarding may be marked `kind=duplicate` with `handling=ignore`; this is a human inventory decision, not automatic deduplication.

Freeze the reviewed `source` / `interpret` rows:

```text
contextcanon onboard prepare . --inventory contextcanon-onboarding/STEP-02-inventory.csv
```

The command prints the immutable Evidence snapshot path:

```text
<snapshot>
```

## STEP 04–07 — design the shelves

Generate the structure task:

```text
contextcanon onboard structure-instruction <snapshot>
```

The instruction command automatically creates `<git-root>/.context/handoffs/<STEP-04-token>/` and a matching `.zip`. Open only the directory as an agent project, or upload the ZIP. Tell the model to follow `.contextcanon-handoff/PLAN.md`.

Import the result, then validate it as a separate explicit step:

```text
contextcanon onboard handoff-import <snapshot> --step 4
contextcanon onboard structure-validate <snapshot>
```

To rebuild/export the handoff manually:

```text
contextcanon onboard handoff <snapshot> --step 4
```

Use `--refresh` only when you deliberately want to discard an existing handoff result and rebuild changed inputs.

After the reasoning model result has been imported as `STEP-04b-structure-proposal.json`:

```text
contextcanon onboard structure-validate <snapshot>
contextcanon onboard structure-review <snapshot>
contextcanon onboard structure-preview <snapshot>
contextcanon onboard structure-materialize <snapshot>
contextcanon onboard reusable-contexts <snapshot>
```

The generated PLAN gives the exact command variant required by the current checkpoint.

STEP 07 requires an explicit relationship on each additional reusable Assignment:

```text
My Project (.) ← Development Workflow (0.3.6-draft) [Parent]
Why: Workflow rules govern this project.

My Project (.) ← Knowledge Archive (1.0.0) [Reference]
Why: Informational context; its rules do not govern this project.
```

Existing enclosing Parents are shown separately; do not assign them again. Parent Rules apply and propagate to semantic Children. Reference Rules do not apply, and the relationship is not inherited. An empty additional Assignment list is valid.

## STEP 08–12 — place meaning and publish

Generate the placement task:

```text
contextcanon onboard placement-instruction <snapshot>
```

STEP 08 creates a separate `<git-root>/.context/handoffs/<STEP-08-token>/` workspace and ZIP. Never reuse the STEP-04 agent workspace. The handoff binds its input set from the frozen snapshot manifest; files an IDE later adds inside the directory are not semantic inputs and are not added to regenerated ZIPs.

When the selected project is a subtree inside an existing ContextCanon Node, STEP 04 and STEP 08 also receive that nearest enclosing Node as already-accepted inherited Context. Its exact compiled package is bound under `.contextcanon-handoff/enclosing-parent/`; the model may read its `CONTEXT.md` and packaged Topic Resources, but they are not subtree Evidence. Publication pins the subtree root to that exact Parent package.

```text
contextcanon onboard handoff-import <snapshot> --step 8
contextcanon onboard placement-validate <snapshot>
```

If onboarding uses a non-default visible workspace, pass the same `--workspace PATH` to instruction, handoff/import, validation and reset commands. The STEP-specific handoff stays below that workspace; it never falls back to the default directory silently.

After import, `STEP-08b-placement-proposal.json` is the canonical machine proposal:

```text
contextcanon onboard placement-validate <snapshot>
contextcanon onboard placement-review <snapshot>
contextcanon onboard placement-preview <snapshot>
contextcanon onboard placement-publish <snapshot>
```

STEP 09 is validation-only and intentionally creates no separate review document. STEP 10 is the human placement gate; STEP 11 is the deterministic publication preview; STEP 12 is the explicit publication action.

The new STEP-08 proposal uses `contextcanon/onboarding-placement-proposal/v2`: `items` and optional `source_edits`, without `source_reuses`. STEP 07 owns reusable Parent/Reference decisions. STEP 10 and preview/publication preserve those choices exactly; change them through `onboard reset <snapshot> --from 7`, then repeat STEP 07 onward. Reset from STEP 08 or STEP 10 preserves the exact accepted STEP-07 choice and frozen packages. Legacy v1 placement proposals and untyped historical STEP-07 states remain readable with Parent semantics.

Published sources contain only canonical `Context Imports`, explicit `relationship=parent|reference`, and `ctx:source` metadata for all structural and additional imports.

## Git persistence during onboarding

`onboard init` maintains a bounded marked block in the project `.gitignore`.

Normally ignored:

```text
contextcanon-onboarding/
<snapshot>/
```

Normally Git-visible after STEP 03:

```text
.context/onboarding/inventory-state.json
.context/onboarding/inventory-acceptance.json
```

Those two compact files let a later clone/recovery rebuild the reviewed inventory baseline without keeping the entire working directory or Evidence cache in Git.

ContextCanon never runs `git add` or creates a Git commit for the project.

## Coming soon: interpretation

The current inventory already distinguishes `interpret` from direct `source`, but the dedicated semantic **interpretation** stage is deliberately not implemented yet. It will sit between triage/Evidence selection and durable Context placement: raw chats, meeting notes, exploratory material, and similar records can be converted into explicit reviewed meaning without pretending the raw record itself is canonical truth.
