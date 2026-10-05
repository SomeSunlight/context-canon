# Shared Node Versions — Onboarding Phase 2 (#107)

**Fast Track status — ACTIVE.** The owner authorized starting this phase on 2026-10-05 while PR #108 remains unmerged. Branch `agent/issue-107-onboarding-versions` starts at owner-tested Phase-1 head `9ec581121df2592a93f5b97b365b165cf7a6d3f8`; accepted `main` remains `28ce62ef7aca4960bcf238b8d2221b7e445aa236`. The earlier wait-for-merge start condition is explicitly superseded. Keep this change on a separate Draft PR initially based on the Phase-1 branch; rebase/retarget and reconcile the accepted baseline after the owner merges Phase 1. Never merge either phase implicitly.

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

- [ ] Implement a removable read-only preview / explicit apply module and CLI entry. Verify/copy exact old frozen inputs before switching authoritative locators or retiring narrowly owned legacy wrappers.
- [ ] Preserve exact STEP 07/08/10 bindings, decisions, proposals/results and journal recovery; schema-aware mechanical rebinding must not make stale reviews valid or broadly replace prose. Handle interruption, foreign files and concurrent ownership conservatively.
- [ ] Test idempotence, interrupted migration/reset, changed/unavailable providers, legacy layouts and Windows staging/final path budgets; checkpoint and publish.

## E. Review candidate

- [ ] Document storage/ownership/migration and owner tests; regenerate only affected self-hosted packages provider-first.
- [ ] Pass the complete deterministic suite, zero generated drift, propagation health, diff hygiene and exact-head Linux/Windows CI (disclose hosted-runner outages rather than changing product semantics to mask them).
- [ ] Publish the final separate Draft PR, update PLAN/STATE and leave concrete remaining owner checks. Keep #107 open until the owner accepts both phases.
- [ ] Owner tests and accepts Phase 2; exact-head merge gate and explicit merge follow separately.

## Recovery notes

Resume at the first unchecked item. Read root CONTEXT, applicable Topics, STATE and this plan; verify this Phase-2 branch rather than writing to PR #108. Publish meaningful checkpoints during the night so recovery does not depend on scratch or this chat. Do not create a new commit merely to mirror a live CI status: record final CI evidence in the PR.

Before any future pruning feature, enumerate current pins, retained-version dependencies, pending reviews, frozen onboarding inputs and recovery receipts. The Phase-1 inventory alone is insufficient deletion authority.

## Runtime checkpoint — 2026-10-05

Storage contract: [docs/onboarding-storage.md](../docs/onboarding-storage.md). New project scopes/runs and subtree workspaces live at the Git root with authenticated collision-checked tokens. Full package bindings share immutable versions; provenance and review state remain per run. Enclosing Parent packages are frozen, not reopened during recovery. Preview/publication use the compact compiler. Reset journals include run-owned acceptance state and survive a partial reversal. Shared versions survive reset; foreign files and sibling scopes are protected.

Added 11 focused storage regressions, including deep Windows-budget preflight, identical Evidence/scope separation, real token collision, full-binding/equal-byte packages, offline Catalogs, changed/removed enclosing Parent, Parent/Reference publication/reset and interrupted-reset retry. Existing end-to-end tests now assert shared locators and retained immutable history. **407 deterministic tests pass**; self-host `check --all .` reports zero drift for all six Nodes and all four local Parent/Child edges are normatively current. Native Windows/hosted exact-head checks remain the final candidate gate.

Resume at **D**: explicit active-run migration and legacy single-pass acceptance staging. Preserve reviewed payload digests and human file hashes; never broadly rewrite old snapshot paths inside proposals or prose. Keep custom/legacy workspaces usable and preserve exact old acceptance bytes for reset. After this block, finish operator/canonical documentation and the final exact-head Linux/Windows gate before owner tests. No Draft PR, owner acceptance or merge is implied by this runtime checkpoint.
