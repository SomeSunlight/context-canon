# Phase-2 next block: active-run migration (#107)

Implementation has **not started** in a migration module yet. This is the handoff for block D after the published runtime checkpoint. Keep migration removable and normal readers independent of its receipts. Do not merge or ask the owner to migrate the confidential project yet.

## Known readers and remaining writers

- New runtime boundary: `onboarding_storage.py` (scope/run ownership, complete frozen bindings, provenance, enclosing Parent).
- Read-only Evidence validation: `onboarding_proposal.load_evidence_snapshot`. `run_path` currently creates a scope; provide a non-creating locator for migration preview.
- Accepted STEP-07 state hashes the original `catalog_packages` roots/bindings and Assignments. `frozen_catalog_packages` is a physical locator list outside that review payload. Preserve original Catalog rows, review digest and human-file SHA exactly.
- `load_accepted_reusable_contexts` can freeze/recover missing legacy inputs and enclosing-Parent state. Do not call it as an allegedly read-only preview without separating its validation from those writes.
- STEP 04/08 instruction and handoff readers, STEP 07, publication and journaled reset now use frozen Parents. Tests explicitly cover provider edit/removal across both instruction stages.
- Inventory state `csv_path` and acceptance `inventory_path` are mechanical locators; accepted CSV bytes, inventory SHA, Evidence digest and semantic scope stay unchanged.
- Legacy single-pass `onboarding_review.accept_onboarding_review` still uses project-local acceptance staging and legacy package carriers. Route its preview via exact package overrides and final installation through shared versions; retain old acceptance readers and first-adoption rollback safety.

## Migration decisions to implement and verify

1. Prefer an explicit `contextcanon onboard migrate` preview/`--apply` surface, separate from ordinary onboarding reads. Resolve a selected project/current accepted snapshot or an explicit snapshot; never choose arbitrarily among historical runs.
2. Verify the complete old Evidence/file set and exact frozen Catalog bindings before creating destinations. Refuse malformed packages, unknown package files, foreign destination contents and symlinks. Missing frozen bytes must not cause substitution of an advanced live provider. Exact historical recovery is a distinct verified operation or a clear refusal condition.
3. Plan root-scoped run locators, shared versions and a shallow default workspace. Preserve explicit custom workspaces. Move/copy human review files and handoffs byte-for-byte; portable handoff manifests/results and instruction digests must not be regenerated merely for storage relocation.
4. For an old enclosing Parent, prefer its exact retained run record or the frozen package inside the semantic handoff. Compare every full binding. A live Parent after human review is not a substitute. Recover its authoring locator from the accepted pin/relationship or verified scope; refuse ambiguity.
5. Rebind only schema-defined physical fields. Preserve STEP-07 normalized review payload, STEP-08 proposal, STEP-10 decisions, rationale and stale-review hashes. Rewrite only the framework-owned PLAN command/checkpoint surfaces after proving the old snapshot binding; never replace snapshot strings throughout human prose or proposals.
6. Old reset journals may address `.context/onboarding/<digest>/placement-acceptance.json` relative to the project. Rebind this one owned acceptance path to the new restricted run locator; preserve before bytes, after hashes and record ordering. Old immutable `.context/sources/<digest>/...` installation entries need explicit handling: reset must retain shared packages. Only drop/translate entries proven to be new immutable installations (before absent, exact after bytes/full binding verified); preserve unrelated prior files and the original journal in the recovery receipt.
7. Verify/copy all inputs and mutable state before switching authoritative run/workspace locators. Record a receipt before destructive retirement, with narrow source/destination ownership and byte hashes. Decide an explicit runtime-owned activation marker if old/new state must coexist during interrupted retirement; adding it requires resolver, Git-visibility and reset ownership tests. Preview must write nothing.
8. Retire only the selected run's verified files and old owned workspace after the new authoritative state is usable. Other scopes, historical runs, accepted pins and shared versions stay. Unknown/changed files cause refusal, never blanket cleanup. A retry must recognize already copied/published/retired files without overwriting later human edits.
9. Confirm idempotence after normal post-migration review edits: a completed receipt must not demand that mutable human state still equals its migration-time bytes. Incomplete receipts should detect such edits conservatively and leave authoritative state usable.

## Required regression matrix

- Accepted STEP 07/08/10 and existing publication acceptance/journal; same full bindings, digests, decisions and source bytes after relocation.
- Changed/deleted/offline providers; exact frozen enclosing Parent retained in a handoff; old unfrozen state must recover exact bytes or refuse safely.
- Root and deeply nested projects, identical Evidence in two scopes, custom/default workspaces, older neighboring runs and shared immutable packages used by another consumer.
- Failure during copy, after locator activation and during retirement; deterministic retry, rollback/reset from STEP 07/10/12 and old journal compatibility.
- A genuinely stale human review remains stale; no schema rebinding can newly validate it. Foreign files, tampered bindings, symlinks and unsafe receipt/journal paths remain protected.
- Native Windows staging/final path budgets, lock failure/retry, ordinary Git staging visibility and relocated-checkout recovery.

After this block, finish owner preview/apply/test instructions and affected canonical docs. Regenerate affected packages provider-first, verify the complete Linux suite/zero drift/propagation health and native Windows CI on the exact review head, then retain Draft status for owner testing. No automatic pruning or merge belongs to this phase.
