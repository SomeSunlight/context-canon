# Shared Node Versions — Phase 1 (#107 / PR #108)

Status: implementation complete; owner testing pending. Start at [PLAN.md](../PLAN.md) for the current next action.

The dated checkpoints below preserve the implementation history. Earlier resume instructions are superseded by the final checkpoint.

## Owner-test candidate: shared Node versions — Issue #107, Phase 1

**Fast Track status — COMPLETE FOR OWNER TESTING / DRAFT PR #108**

Purpose: retain whole immutable Node package versions once per Git working tree, keep consumer acceptance explicit, reduce generated path overhead, and migrate existing projects without re-onboarding. The owner authorized implementation on 2026-10-05 and will test Phase 1 before Phase 2.

Scope: normal build/check, published version history, Parent/Reference adoption and updates, candidate/review lifecycle, readable version inventory, separately implemented migration, package Resource layout, documentation and Windows verification. Onboarding Evidence, frozen Catalogs, handoffs, workspace/reset migration are **Phase 2**, not this review candidate. Generic reinit/identity remapping remains #106. Keep the PR Draft; do not merge.

Implementation contract / recovery map:

- Use `<worktree>/.context/versions/<verified-digest-prefix>/` for whole packages. The directory key binds full Node ID + normalized digest + exact package digest; exact human package bytes alone can coincide for genuinely different Nodes. Full identity remains in `.context/package.json`; compact names are locators, with collision extension and full verification. No sequential allocation ledger; context.yaml stays regenerable.
- Normal publication retains the previous verified package and new package; imports install once in that library. Exact pins remain independent for every consumer and Reference stays non-normative/non-transitive. Reads support legacy consumer-local sources until explicit migration.
- Centralize package scratch, but scope reviews and transport provenance by consumer. Cleanup may remove only its transaction; accepted versions and other consumers' input survive.
- Preserve document subdirectories inside packages. Use a compact verified origin namespace and a common Resource-closure base (including the authoring Node root) to avoid repeating needless repository prefixes without rewriting exact authored Markdown. Bind full origin/path mapping in authenticated package content; preserve legacy reads and Resource rename baselines.
- Migration lives in a removable `storage_migration.py`, separate from the runtime resolver. Default to read-only preview; explicit apply verifies/copies old exact packages before removing verified owned wrappers. Preserve pins and interrupted-run retry; do not migrate onboarding state in Phase 1.
- History inventory shows Node/name/version/full identity, current consumers and retained history. Automatic pruning is deferred: Phase 2 must first make onboarding/recovery reachability explicit.

- [x] Reconcile accepted PR #105 baseline (`28ce62ef7aca4960bcf238b8d2221b7e445aa236`), reconstruct current storage/package/Resource/review boundaries, create the Phase-1 branch and persist scope.
- [x] Implement one verified package-location/install contract and legacy resolution; prove shared versions, collisions/tampering and offline loading.
- [x] Route normal Parent/Reference installation and package scratch through root storage, preserving consumer-specific review/provenance and acceptance cleanup.
- [x] Retain published local versions at normal build and expose a human-readable repository version inventory.
- [x] Shorten new Resource layouts while preserving closure, full origin mapping, exact package identity and Resource move/status behavior; keep old packages readable.
- [x] Implement separate preview/apply migration with idempotent retry, verification-before-removal and unchanged pins; prove duplicate legacy stores and unavailable providers.
- [x] Add end-to-end normal Authoring/Parent/Reference, deep Node hierarchy, history retention, migration interruption and Windows regressions; run existing onboarding tests as compatibility checks without changing its workflow.
- [x] Update accepted architecture/operator docs, migration instructions, Framework Development Rule, STATE/CHANGELOG; regenerate self-hosted Context provider-first.
- [x] Pass complete tests, build/check, propagation health, diff hygiene and exact-head Linux/Windows CI; publish one Draft PR with concise owner-test instructions.
- [x] Close Phase-1 Fast Track for owner testing and record exact head/results/remaining Phase-2 onboarding work.

Implementation checkpoint (2026-10-05): all 392 deterministic tests pass. `version_store.py` owns shared immutable installations and consumer-scoped root scratch; `version_history.py` retains previous/current publication and renders inventory; package v4 binds `.context/resource-origins.json` as exact package content; `storage_migration.py` is removable and preview-first. Migration preserves exact pins and packages, moves only owned legacy carrier URLs, and narrowly rebinds already-valid frozen review hashes after that mechanical locator change; CRLF, stale-review refusal and interrupted link/cleanup recovery are covered. Different Node IDs with identical human bytes are a real complete-binding collision case, explicitly tested. Existing onboarding uses its legacy carriers/install transaction until Phase 2; only generic format compatibility changes are present. Resume with architecture/operator docs, Framework storage Rule, provider-first self-host regeneration and final Linux/native-Windows gates. Draft PR #108 is not ready for owner testing yet.

Review-candidate checkpoint (2026-10-05): all 393 deterministic tests pass, including 14 shared-version/history/migration regressions. Normal build/check and all four local Parent/Child health edges pass; repeated build is stable and diff hygiene is clean. The native Windows job now runs those 14 tests plus the existing eight path-budget/Git-visibility tests. Framework Rule CCI-013 records nested-Node storage constraints. Operator instructions are in `docs/node-versions.md`; migration is preview-first, separate and retryable. Self-host retains 13 whole-package versions, including accepted v3 packages unchanged. Current Nodes: Gateway 0.3.20-draft; Framework Development 0.3.19-draft; Foundation 0.2.4-draft; Development Workflow 0.3.7-draft; GitHub 0.1.8-draft; GitHub Local 0.1.7-draft. Compiler format is 0.8/package v4; executable release remains 0.10.0. Single-Node publication does not become dependent on unfinished sibling authoring merely to regenerate the inventory. Shared publication reuses only a fully verified concurrent winner.

Resume with final review-candidate publication to Draft PR #108, exact-head Actions checks, and PLAN/STATE closure after green Linux/native-Windows CI. Keep #107 open for Phase 2; do not merge. Phase 2 must route onboarding Evidence/frozen packages/workspaces/publication/reset/recovery through the shared library without borrowing normal acceptance cleanup or weakening frozen bindings; only after this may safe pruning account for all pins, retained package dependencies, pending reviews, onboarding and recovery roots.

Native Windows checkpoint: implementation head `9441f2a7f0ee43c6e3a6443089733eb522a8c6e8` passes the complete Linux suite/self-host gate in Actions run `37250207414`. Windows passes 21/22 tests but exposes inconsistent Windows 8.3 versus resolved temp-root spelling in `scratch_root` when the prospective consumer has no source. The resolver now canonicalizes the Node path before deriving scope ownership, matching `find_repo_root`; focused regressions pass. Resume with corrected exact-head Linux/Windows CI, then closure. No package or semantic change is needed for this correction.

Phase-1 closing checkpoint: corrected implementation head `65990b8db27913e9bf415e3bceed306767d4f28e` (tree `47f23fcbd0c57b0e0adb7ae2eab469c5f65fdd36`) passes Actions run `37250407876`: Linux full suite of 393 tests plus self-host zero-drift gate, and all 22 native Windows shared-history/migration/path/Git tests. The owner may now install/test Draft PR #108. This final PLAN/STATE closure changes no code or package behavior; final documentation-head CI is recorded on the PR. No merge is authorized, and #107 remains open for onboarding Phase 2.

Complete-binding preview checkpoint: one additional end-to-end regression reproduces a real legacy assumption when a Reference candidate has identical human bytes to another accepted Node. Digest-only preview overrides substituted the candidate into that other Node and failed identity validation. Normal adoption/Source/Parent preview writers now use the shared complete-binding key; the Compiler normalizes old preview callers at the package boundary for onboarding compatibility. The new test proves review/acceptance retains both distinct Node identities and Reference non-normativity. Local suite is now 394 tests; native Windows runs 23 tests. Previous documentation head `2a67f92571faed09743b563381c455b610f2e99d` was also green in run `37250605091`; final corrected-head CI will be recorded on PR #108. Package outputs are unchanged by this preview-only correction.


## Recovery and owner-test preparation (#109)

- [x] Reorganize PLAN without losing historical decisions or deferred work.
- [x] Independently verify PR #108, complete migration bindings and Linux/Windows evidence; record gaps.
- [x] Publish concrete internal-project owner tests and rollback guidance.
- [x] Prepare and locally verify the documentation checkpoint for PR #108.
- [x] Confirm publication and exact documentation-head CI on PR #108.
- [ ] Owner completes the real internal-project test and explicitly approves Phase 1.

Phase 2 is tracked in [issue-107-phase-2.md](issue-107-phase-2.md).

## Independent review checkpoint (2026-10-05, #109)

Published product head `448d2c1488adf584130760a8c9db50b3a888a3ed` is complete for the authorized Phase-1 scope. Actions run `37251101173` is successful on that exact head (Linux complete suite/self-host, 23 native Windows tests). Independent code review confirms complete-binding storage, verification before legacy retirement, unchanged exact pins/relationships, foreign-file preservation, and retryable cleanup/carrier-review publication. No Phase-1 implementation blocker was found. Real confidential Windows owner testing/approval, Phase-2 onboarding storage/reset and reachability-complete pruning remain outstanding.

The internal-project test is [issue-107-owner-test.md](issue-107-owner-test.md). Later documentation-only changes do not alter executable/package behavior. Final local/CI results are recorded below when complete.

Local recovery verification (#109): all 394 deterministic tests pass again. Self-host `build --all .` reports no changes, `check --all .` is clean with all four local Parent/Child edges current, original PLAN text is preserved verbatim in its split locations, and documentation links/diff hygiene pass. No product-source or generated-package changes were needed.

Publication checkpoint (#109): documentation head `c45137001fd9b7c7af0aebd5a1f94947a1399b2a` passes Actions run [37264734527](https://github.com/SomeSunlight/context-canon/actions/runs/37264734527), including the complete Linux suite/self-host gate and native Windows job. Recovery review and owner-test documentation are complete. This closure changes only planning status; the exact final closure-head run is linked on PR #108. Resume with the real internal-project owner test, not another implementation block. No merge or Phase-2 start is authorized.
