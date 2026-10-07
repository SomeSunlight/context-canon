# Shared Node Versions — Onboarding Phase 2 (#107)

**Fast Track status — CLOSED / OWNER ACCEPTED.** The owner authorized starting this phase on 2026-10-05 before PR #108 was merged. Its starting base was owner-tested Phase-1 head `9ec581121df2592a93f5b97b365b165cf7a6d3f8`; Phase 1 is accepted main `dc20fdb86980d5b6adb801d299a4610e0a297ae3` and integrated with preserved test-branch ancestry. On 2026-10-06 the owner confirms successful migration and orderly short paths and accepts Phase 2 for main. A fresh end-to-end onboarding is deferred to the next real adoption; later findings become new Issues. The owner squash-merged PR #111 on 2026-10-06 as `d0a9db3d3b0d1cc1dfce32caadf2a52b1eb5ae80`. Earlier checkpoints below describe pre-merge facts.

Purpose: make onboarding payload/storage overhead independent of physical project nesting, reuse the shared complete-Node library, and migrate active old runs without losing reviewed meaning or recoverable state.

Scope: Evidence/run ownership, frozen reusable Catalogs and enclosing Parents, STEP 07/08/10, semantic handoffs, visible workspace location, preview/publication, rollback/reset journals, separate preview/apply active-run migration, old-state compatibility, documentation and Linux/Windows verification. Exact Evidence and complete package bindings remain immutable. Parent/Reference semantics, live authoring locations and human acceptance stay unchanged. Generic reinit/remapping (#106), automatic pruning, unrelated onboarding UX and silent rewriting of package interiors are excluded. Legacy abandoned review-candidate cleanup remains recorded follow-up work rather than a blanket deletion permission.

Exit: coherent implemented candidate, focused checkpoint tests, full deterministic/self-host verification, Windows regressions, separate migration/operator instructions and an owner-testable Draft PR. Batch full CI/package regeneration/PR polish at that boundary; checkpoint each meaningful block immediately. No owner merge is authorized by implementation or CI success.

## A. Reconstruct and settle the storage contract

- [x] Create the isolated stacked branch and record the owner's authorization/scope before executable changes.
- [x] Read applicable framework/onboarding contracts and map current Evidence, Catalog, handoff, workspace, publication and reset-journal readers/writers.
- [x] Record exact frozen identities and ownership boundaries; prototype measured root-scoped paths, identical Evidence in separate scopes and complete-binding package collisions before choosing layouts/schema changes.
- [x] Publish this planning/contract checkpoint so a lost chat can resume from repository state.

## B. Shared library and shallow run storage

- [x] Introduce one verified onboarding storage/resolution boundary with explicit repository/project/run ownership, short collision-checked locators and legacy reads. Derive the original project scope from authenticated metadata, not directory depth.
- [x] Freeze reusable packages/enclosing Parents through the shared whole-Node library; keep provenance and mutable review decisions scoped to their run, not as mutations inside a shared immutable package. Use full Node ID + normalized/package digests for Catalog/preview identity.
- [x] Route Evidence/new default workspaces and STEP 07/08/10 readers/writers through that boundary; preserve frozen input bytes, portable handoffs, project-relative paths and custom workspace behavior.
- [x] Checkpoint focused deep/simultaneous/subtree/frozen-input/identity regressions and publish the block.

## C. Publication and reset/recovery

- [x] Use the same shared package bindings in preview/publication and keep each target's Parent/Reference choice unchanged; never fetch live providers during frozen recovery.
- [x] Make rollback/reset ownership explicit for shared-root state: preserve another Node/run's packages, accepted pins and prior accepted inputs; deterministic retry must survive interrupted writes/deletions.
- [x] Test failure before/after publication, resets from STEP 07 onward, offline providers, simultaneous runs and legacy journal compatibility; checkpoint and publish.

## D. Separate active-run migration

Resume with the [migration handoff and safety matrix](issue-107-phase-2-migration.md). The final closure block is authorized by the owner on 2026-10-06; implement the migration and finish the testable candidate without another intermediate owner handoff.

- [x] Implement a removable read-only preview / explicit apply module and CLI entry. Verify/copy exact old frozen inputs before switching authoritative locators or retiring narrowly owned legacy wrappers.
- [x] Preserve exact STEP 07/08/10 bindings, decisions, proposals/results and journal recovery; schema-aware mechanical rebinding must not make stale reviews valid or broadly replace prose. Handle interruption, foreign files and concurrent ownership conservatively.
- [x] Test idempotence, interrupted migration/reset, changed/unavailable providers, legacy layouts and Windows staging/final path budgets; checkpoint and publish.

## E. Review candidate

- [x] Document storage/ownership/migration and owner tests; regenerate only affected self-hosted packages provider-first.
- [x] Pass the complete local deterministic suite, zero generated drift, propagation health and diff hygiene. Exact-head hosted Linux/Windows CI is a live gate in PR #111; do not create a new commit merely to mirror its result.
- [x] Publish the separate Draft implementation PR, update PLAN/STATE and leave the concrete owner-test guide. Final closure content is published on the same PR; keep #107 open until the owner accepts both phases.
- [x] Owner accepts Phase 2 after successful real migration/path validation, explicitly deferring fresh onboarding to the next real adoption. Exact-head merge readiness remains live PR metadata; the owner performs the squash merge.

## Recovery notes

Implementation, owner acceptance and the squash merge of #111 are complete. Accepted main is `d0a9db3d3b0d1cc1dfce32caadf2a52b1eb5ae80`; resume new work from the current PLAN/STATE. PR #108 is accepted and closed. Do not create a new commit merely to mirror a live CI status: record final CI evidence in the PR. The implementation checkpoints below are historical; current owner acceptance supersedes their earlier merge restrictions.

Before any future pruning feature, enumerate current pins, retained-version dependencies, pending reviews, frozen onboarding inputs and recovery receipts. The Phase-1 inventory alone is insufficient deletion authority.

## Runtime checkpoint — 2026-10-05

Storage contract: [docs/onboarding-storage.md](../docs/onboarding-storage.md). New project scopes/runs and subtree workspaces live at the Git root with authenticated collision-checked tokens. Full package bindings share immutable versions; provenance and review state remain per run. Enclosing Parent packages are frozen, not reopened during recovery. Preview/publication use the compact compiler. Reset journals include run-owned acceptance state and survive a partial reversal. Shared versions survive reset; foreign files and sibling scopes are protected.

Added 14 focused storage regressions, including deep Windows-budget preflight, identical Evidence/scope separation, real token collision, full-binding/equal-byte packages, offline Catalogs, changed/removed enclosing Parent, Parent/Reference publication/reset and interrupted-reset retry. Existing end-to-end tests now assert shared locators and retained immutable history. **410 deterministic tests pass**; self-host `check --all .` reports zero drift for all six Nodes and all four local Parent/Child edges are normatively current. Native Windows/hosted exact-head checks remain the final candidate gate.

Resume at **D**: explicit active-run migration and legacy single-pass acceptance staging. Preserve reviewed payload digests and human file hashes; never broadly rewrite old snapshot paths inside proposals or prose. Keep custom/legacy workspaces usable and preserve exact old acceptance bytes for reset. After this block, finish operator/canonical documentation and the final exact-head Linux/Windows gate before owner tests. No Draft PR, owner acceptance or merge is implied by this runtime checkpoint.

The follow-up reader/ownership audit routes both STEP-04/08 instructions through the same frozen Parent, refuses a conflicting `--project` before project mutations, validates unknown machine entries before deleting any workspace review, and restores retired generated Resource files byte-for-byte. Native Windows CI now includes all 14 onboarding-storage regressions (39 Windows-targeted tests total). A Draft checkpoint PR may be opened for durable review/CI before D/E are complete; it remains WIP, with migration explicitly pending.

## Final closure block — 2026-10-06

- [x] Add a non-creating run locator and an authenticated runtime activation record in the central project scope. This makes the new scope authoritative during interrupted retirement without making runtime depend on migration receipts. Preserve direct legacy readers for historical runs.
- [x] Implement `onboard migrate` (read-only by default, `--apply` explicit) in a removable module. Select the accepted/current run or require an explicit snapshot when ambiguous; authenticate the workspace checkpoint. Copy exact Evidence/reviews/handoffs, shared complete packages and narrow physical fields, then activate and retire only verified selected files. Keep receipt hashes and original transformed records for recovery.
- [x] Route compatibility single-pass staging/publication through shallow storage and shared packages. Exercise accepted STEP 07/08/10/publication, offline providers, stale reviews, interruptions, sibling/history protection, custom workspaces, reset and Windows path/Git behavior.
- [x] Finish operator instructions and canonical documentation; regenerate affected self-host packages and pass full local gates. Publish final Draft content and verify Linux/native Windows on the exact head; hosted proof remains live PR metadata.

Migration is conservative when exact frozen bytes or historical Parent identity cannot be proved: refuse before mutation and explain the exact recovery input. Never substitute a newer provider or recalculate human acceptance merely because locators changed. The activation record is compact runtime-owned project/workspace routing; the receipt is separate, removable tooling state. Immutable shared history survives reset.

### Handoff path audit

The final audit found that a shallow visible workspace alone still adds `handoffs/STEP-xx-.../.contextcanon-handoff/enclosing-parent/` before a whole frozen Parent package. A legacy full-ID export can therefore remain over 260 units even after scope relocation. Include root-scoped, collision-checked handoff working directories in this closure block. Authenticate project/Evidence/step ownership outside the portable input contract; preserve original manifest/instruction/result/ZIP bytes during migration. The visible PLAN points to the exact short handoff; custom workspaces and legacy local handoffs stay readable. Reset must reverse only this run's handoffs, and independent same-Evidence project scopes must stay isolated.

### Migration implementation checkpoint

`onboarding_migration.py` now provides read-only preview and explicit `onboard migrate --apply`. All exact frozen packages are verified before copying; schema-defined physical fields and owned PLAN blocks are rebound without changing review hashes, human files, proposals, handoff inputs/results or ZIP bytes. Central activation survives interrupted retirement and resets without reactivating historical local runs. Receipts retain original transformed records and narrow byte hashes; completed retry leaves later human edits untouched. Compatibility single-pass acceptance now uses compact compiler overrides and shared packages, with shallow staging and explicit canonical Parents.

Focused regressions cover Root/subtree STEP 07/08/10/publication, offline Catalogs, retained Parent handoffs after provider source removal, stale reviews, copy/in-place PLAN/activation/retirement interruption, post-activation edits, custom workspaces, relocated checkouts, old acceptance journal reset, foreign files/packages/destinations/symlinks/receipt paths, Git visibility and Windows preflight. Shared root handoffs preserve stable portable ZIP directory names; ten-level same-Evidence project scopes stay isolated under reset. The complete suite passed 422 tests before the four additional recovery/deep-scope cases; those focused cases now also pass. Final native Windows/full-suite/docs gates remain E.

### Windows finalization audit

Hosted checkpoint CI verified all 426 Linux tests plus zero drift. Native Windows exposed 8.3 versus long-path aliases in migration/workspace fixtures and CRLF checkpoint parsing; fix by canonicalizing only after lexical symlink checks and parsing owned locator/stage lines across CRLF without rewriting unmanaged PLAN notes. Additional explicit CRLF and handoff/ZIP tampering regressions verify byte preservation and read-only refusal. Operator docs and affected Gateway/Framework packages are regenerated; final exact-head Windows rerun is mandatory before owner handoff.

### Final review boundary

All implementation blocks A–D are complete. Operator/canonical docs and the two affected self-hosted Nodes are regenerated (Gateway 0.3.22-draft; Framework Development 0.3.21-draft). Recovery now checks the exact head's live Linux/native Windows results in Draft PR #111, then continues at owner testing. No merge is authorized. The final gate includes complete old package-installation journal recovery even after Phase-1 wrapper retirement, atomic no-clobber activation publication, CRLF note preservation and portable checkout relocation.

Normal legacy packages and new imports retain full bindings; human review SHA/digests are never recalculated to make a stale decision current. Onboarding migration remains removable transition code. No shared-version pruning, reinit/remapping or blanket abandoned-candidate deletion belongs to this result.

Final local verification: **430 deterministic tests pass**, all six self-hosted Nodes report zero generated drift, all four local normative edges are current, and diff hygiene is clean. The final native Windows job runs **67 targeted tests**. These counts describe this assembled candidate; hosted exact-head success is recorded in PR #111 after publication.

## Phase-1 post-merge baseline checkpoint — 2026-10-06

The owner merged Phase 1 after its CI recovered and started testing Phase 2. Accepted main is integrated without rewriting the test branch history; the original Phase-1 base and squash tree are byte-identical. PLAN/STATE now record the real accepted baseline and owner-test status. Only planning documents change; keep the already-tested executable/packages and preserve ordinary editable-install pulls. Fresh exact-head hosted Linux/Windows evidence is maintained in Draft PR #111. #107 stays open through Phase-2 owner approval.

## Owner-test correction — missing legacy Catalog freezes (2026-10-06)

The Foundation authoring path in the owner's error proved that migration's fallback conflated normal Node authoring with an isolated immutable package. The earlier workspace blocker was only three obsolete owner-created exchange copies and is resolved.

Prefer exact snapshot/consumer/provider retained packages. For legacy states created before Catalog freezing, reuse the existing Git-history recovery reader; verify committed manifest/file bytes in memory with the same package validator used by filesystem loads. Preview creates no freeze, staging directory or provider checkout. Apply installs those exact full bindings in the consuming shared library and preserves provenance/review identity. The exact current authoring fallback reads only manifest artifacts, not every authoring/IDE file, and may not accept an advanced binding. Missing/corrupt history refuses before mutation with the required historical Node/version/package identity.

Regressions exercise current authoring with unrelated notes, newer/deleted providers, retained provider history with old run provenance, corrupt/missing Git bytes, interrupted package installation and retirement, unchanged STEP 07/08/10 Parent/Reference publication, and legacy untyped v0 review/publication without rewriting its human SHA or accepted digest. The native Windows job additionally includes memory-package tampering checks and ordinary historical freeze recovery. Owner retest and live exact-head gate follow this correction; no merge is authorized.

Native Windows then exposed Git's legacy LF/CRLF transport conversion: a committed blob can contain LF while the manifest binds original CRLF Resource bytes. The shared historical reader restores CRLF only when the manifest's complete SHA-256 and size prove those original bytes, before the ordinary full package and accepted-binding checks. This narrow recovery does not normalize or rewrite packages and corrupt historical bytes still refuse. A portable regression forces Git autocrlf, proves the stored LF/original CRLF distinction, removes the provider Nodes, and checks preview, exact migration bytes, review identity and publication. Test fixture text reads explicitly use UTF-8; canonical returned paths account for Windows 8.3 aliases. The corrected candidate passes 438 local tests (26 migration), zero generated drift for six Nodes and four current normative edges; fresh hosted Linux/native Windows evidence remains in Draft #111.

## Owner-test finding — unidentified handoff files (2026-10-06)

Migration in Itop now reaches the frozen handoff file-set guard, but `unknown/missing handoff files` does not identify STEP 04/08, the selected task root, or either set of paths. The owner-side names/cause remain unknown. First make that refusal actionable; do not guess a historical writer variant or claim personal/IDE files.

Report sorted unknown and missing files separately, preserve the read-only preview/apply guard, and keep RESULT.json and all other remaining bytes/directories. Guide unrelated-file preservation versus reporting ContextCanon artifacts; restore missing frozen files only from the original ZIP/backup. Regress both steps and root/subtree scopes, including mixed unknown/missing entries, unchanged state/no receipts, and successful exact RESULT.json migration. Existing integrity and ZIP checks stay in place. Publish on Draft #111 with fresh Linux/native Windows evidence, then obtain concrete owner-side names before expanding compatibility.

The bounded correction passes all 28 migration tests and all 440 deterministic tests locally, six self-hosted Nodes have zero generated drift, and all four normative edges are current. The guard and migration ownership semantics are unchanged. Exact-head hosted proof remains in Draft #111; actual owner-side file classification is pending.

## Owner-requested correction — unbound IDE metadata (2026-10-06)

The concrete extras are JetBrains `.idea/` metadata. Existing handoff PLAN already excludes post-preparation `.idea/`/`.vscode/` from Evidence. Align migration with that task boundary, preserving unbound metadata at its original location rather than claiming/copying/deleting it. Report existing preserved namespaces in the preview/apply result. Inventory uses Git standard excludes for untracked files; migration must not exempt arbitrary ignored files because the entire authoritative workspace/run can be ignored.

One narrow path policy applies at workspace/task roots through planning, copying and retirement. Reads skip unbound metadata; declared Evidence wins over namespace and retains normal SHA/size validation. Verified handoff files define source/copy/retirement ownership, while preserved metadata and required ancestors survive cleanup. IDE edits or newly generated metadata do not invalidate interrupted package-install/copy/retirement recovery. Existing owner markers, strict immutable packages and unrelated-file/symlink guards on governed inputs remain in force; no receipt schema change or new abstraction layer.

All 32 migration tests pass, including exact legacy review/publication with root/subtree and both tasks, existing destination metadata, prevented unbound reads/claims, new/changed IDE files during three interruption phases, declared metadata-path Evidence tampering, and ignored unknown/tampered-file rejection. Finish full verification and fresh native Windows/Linux proof on Draft #111, then the owner retries preview/apply without manual IDE cleanup. This does not change the separately documented disposable-workspace reset lifecycle.

Final local verification passes all 444 deterministic tests, zero generated drift for six self-hosted Nodes, four current normative edges and diff hygiene. Fresh exact-head hosted Linux/native Windows proof remains in Draft #111; no merge is authorized.

Hosted `06adaed` passes 444 Linux and 82 native Windows tests but finds stale generated copies of the packaged owner test guide. Regeneration publishes Gateway `0.3.23-draft` and Framework Development `0.3.22-draft`, retains their previous immutable packages, and passes the complete local gate again. The correction requires a fresh exact-head hosted gate; no executable behavior or release version changes in this finalization.
