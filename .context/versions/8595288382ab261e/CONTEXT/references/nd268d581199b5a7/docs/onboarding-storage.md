# Onboarding storage and migration

Onboarding uses the same shared whole-Node version library as ordinary ContextCanon authoring. Each consuming Git working tree has its own library, including imported Nodes from other repositories. Project nesting adds no repeated ContextCanon store prefix.

| Location | Purpose |
| --- | --- |
| `<git-root>/.context/onboarding/<project token>/<Evidence token>/` | One project's frozen Evidence, review state, provenance and reset journal |
| `<git-root>/.context/versions/<binding token>/` | Complete immutable reusable/enclosing-Parent packages, shared with normal authoring |
| `<git-root>/.context/handoffs/<handoff token>/` and matching `.zip` | Isolated STEP-04/08 reasoning workspaces |
| `<git-root>/contextcanon-onboarding/` | Root project's visible review files and PLAN |
| `<git-root>/contextcanon-onboarding-<project token>/` | Subtree project's default visible review files and PLAN |

Tokens normally contain 16 hexadecimal characters and extend on a verified collision. They are locators, not identity. `.scope.json` records the complete repository-relative project path; `.run.json` records that path and the full Evidence digest. A handoff's `.owner.json` binds project, full Evidence digest and step. Unsafe paths, symlinks and mismatched ownership are refused. No editable allocation ledger is needed; `context.yaml` remains regenerable bookkeeping.

Evidence keeps its original project-relative paths and exact v0 manifest/file bytes. Identical Evidence in two project scopes has independent decisions, mutable state and recovery ownership. Custom workspaces and old project-local runs remain readable. The generated PLAN supplies exact relative commands and handoff locations; moving the whole checkout does not change the Node or Evidence identity.

## Exact packages and decisions

STEP 07 freezes full Node ID, version, normalized digest and exact package digest in the normal shared library. Different Nodes with equal human file bytes cannot alias. Provenance is a run-owned `catalog-provenance/` sidecar, never a mutation inside shared immutable packages. Original Catalog rows remain part of the accepted review digest; frozen physical locators are outside it.

An enclosing Parent is frozen once per run. STEP 04/07/08, handoffs, preview and publication use those exact bytes even when a provider changes or disappears. Additional Parents apply Rules and propagate to semantic Children; References stay informational and do not propagate. Publication writes the same canonical Context Imports as ordinary authoring.

Handoffs remain whole isolated reasoning tasks. Their short physical locator is outside the portable input contract: ZIPs retain readable `STEP-04-structure/` or `STEP-08-placement/` top directories, and `.owner.json` is excluded. Evidence, instruction, manifest, frozen Parent and RESULT.json keep their exact bytes during relocation. The PLAN tells the operator which directory or ZIP to give the model.

## Migrate an active old run

From the selected project/subtree root, first preview:

```text
contextcanon onboard migrate .
```

This writes nothing. It reports the selected old/new snapshot, visible workspace, receipt and copy/retirement counts. Then apply that same selection:

```text
contextcanon onboard migrate . --apply
```

Continue at the reported workspace's `PLAN.md`. There is no new semantic LLM pass merely because storage changed. The accepted inventory selects the active run; if no unique active run is provable, supply `--snapshot <old-snapshot>` from the old PLAN. An existing custom workspace inside this Git repository needs `--workspace <path>` and stays in place. External custom workspaces remain supported by normal onboarding; this migration conservatively requires an in-repository workspace.

The separate `onboarding_migration.py` module verifies all old Evidence and exact packages before creating a receipt or destination. It copies and verifies inputs/reviews first, installs shared packages, then activates the central project scope and retires only recorded old files. A compact `.active.json` is runtime routing, independent of migration receipts. Historical neighboring runs, other projects, accepted authoring and shared history are retained.

Only schema-defined physical fields and owned PLAN command/checkpoint blocks change. STEP-07 review digests and human-file hashes, STEP-08 proposals, STEP-10 decisions/rationale, handoff inputs/results/ZIPs and original acceptance bytes stay unchanged. A stale review remains stale. Unknown files, changed packages or foreign destinations cause refusal. Missing exact frozen bytes require the exact historical package/provenance; a newer provider is never silently substituted. An old enclosing Parent can be recovered from its retained exact run record or frozen handoff, with a verified ancestor locator.

Keep a complete filesystem return copy before an apply: active workspaces, Evidence and receipts are ignored by Git. A Git commit alone does not back them up. The [owner-test sequence](../plans/issue-107-onboarding-owner-test.md) includes installation, migration, continuation and reset checks.

## Interruption and reset

Rerun the same `--apply` command after interruption. A receipt under `.context/onboarding-migrations/` binds narrow old/new ownership, source/destination hashes and original transformed records. Copy retry refuses changed human inputs. After activation, retirement retry preserves subsequent human edits in the authoritative new run. A completed receipt does not restore migration-time human files or require that later reviews stay unchanged.

Reset addresses central acceptance through the restricted `@run/placement-acceptance.json` journal locator. Legacy project-relative journals remain readable; migration translates only that owned acceptance entry. Verified new immutable installation entries are outside reset ownership, so shared history survives. Actual old generated Resource trees and original acceptance bytes can still be restored byte-for-byte. Reversal verifies each record, atomically marks it in progress, and persists each completed reversal; retry accepts only recorded before/after bytes.

`onboard reset` removes only the selected run's handoffs and workspace artifacts. Other scopes, histories and shared packages survive. Compact routing/ownership metadata can remain after STEP-01/02 resets so historical local runs are not accidentally reactivated. Inventory state/acceptance, scope and activation metadata remain Git-visible; Evidence, visible workspaces, handoffs and migration receipts are ignored.

Migration preserves exact old package interiors. Their old Resource paths can remain longer than new exports; providers receive the new compact layout when rebuilt and consumers accept those new versions through normal review. The root store removes consumer nesting, but existing project-owned document paths and the absolute checkout prefix still contribute to Windows limits. Preview checks actual final and temporary destinations before applying. Accepted normal `.context/sources/` stores use the separate `versions migrate` command; abandoned legacy candidates and automatic history pruning are separate work.
