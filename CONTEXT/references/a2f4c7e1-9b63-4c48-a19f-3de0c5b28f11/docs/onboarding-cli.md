# ContextCanon onboarding CLI

This is the compact command reference for **onboarding an existing Git project**.

For an actual run, the generated `contextcanon-onboarding/PLAN.md` remains the primary operator console because it contains the current checkpoint and exact snapshot-bound commands. This page is the stable place to rediscover commands when the workspace is missing, when you need to step backwards, or when you want to understand the CLI stages.

Use `contextcanon onboard <command> --help` for every flag.

## Start

From the Git repository root:

```text
contextcanon --version
contextcanon onboard init .
```

Then open:

```text
contextcanon-onboarding/PLAN.md
```

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

Freeze the reviewed `source` / `interpret` rows:

```text
contextcanon onboard prepare . --inventory contextcanon-onboarding/STEP-02-inventory.csv
```

The command prints the immutable Evidence snapshot path:

```text
.context/onboarding/<evidence-digest>
```

## STEP 04–07 — design the shelves

Generate the structure task:

```text
contextcanon onboard structure-instruction .context/onboarding/<evidence-digest>
```

For IDE/agent models, use a separate scratch project containing only a copy of `STEP-04a-structure-instruction.md` plus the frozen `evidence/` directory; copy only the returned JSON back into the onboarding workspace.

After the reasoning model writes `STEP-04b-structure-proposal.json`:

```text
contextcanon onboard structure-validate .context/onboarding/<evidence-digest>
contextcanon onboard structure-review .context/onboarding/<evidence-digest>
contextcanon onboard structure-preview .context/onboarding/<evidence-digest>
contextcanon onboard structure-materialize .context/onboarding/<evidence-digest>
contextcanon onboard reusable-contexts .context/onboarding/<evidence-digest>
```

The generated PLAN gives the exact command variant required by the current checkpoint.

## STEP 08–12 — place meaning and publish

Generate the placement task:

```text
contextcanon onboard placement-instruction .context/onboarding/<evidence-digest>
```

Use the same isolated scratch-project pattern for STEP 08; do not give the semantic agent the live repository as its workspace.

After the reasoning model writes `STEP-08b-placement-proposal.json`:

```text
contextcanon onboard placement-validate .context/onboarding/<evidence-digest>
contextcanon onboard placement-review .context/onboarding/<evidence-digest>
contextcanon onboard placement-preview .context/onboarding/<evidence-digest>
contextcanon onboard placement-publish .context/onboarding/<evidence-digest>
```

STEP 09 is validation-only and intentionally creates no separate review document. STEP 10 is the human placement gate; STEP 11 is the deterministic publication preview; STEP 12 is the explicit publication action.

## Git persistence during onboarding

`onboard init` maintains a bounded marked block in the project `.gitignore`.

Normally ignored:

```text
contextcanon-onboarding/
.context/onboarding/<evidence-digest>/
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
