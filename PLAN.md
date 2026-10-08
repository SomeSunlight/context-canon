# Plan

This is the recovery index, not the implementation diary. Read [STATE.md](STATE.md) for current facts, then the linked detail plan for the work you are doing. Check off completed detail items immediately; keep older checkpoints in the archive.

## Resource target notes (#113)

Accepted baseline: the owner squash-merged Phase 2 as `d0a9db3d3b0d1cc1dfce32caadf2a52b1eb5ae80` (#111). The older Phase-2 preparation blocks below are historical. Resource notes are a separate review branch, `agent/issue-113-resource-notes`; Topic inheritance visibility remains deferred.

Purpose: add an optional indented single-line `Why:` below each Resource target, following the owner's preference for explicit syntax. Preserve explanations through rendering, immutable packages, composition, review and Resource maintenance. VALID/OBSOLETE are ordinary text, not status enums or Required/Optional control. Existing syntax and unannotated package identities stay compatible; arbitrary trailing prose remains unsupported.

- [x] Implement Resource-only Why parsing, typed/package preservation, rendering, review identity and register/move/reconcile preservation. Before documentation edits, all six self-hosted Nodes still have zero generated drift and all four normative edges remain current, proving unannotated output compatibility.
- [x] Cover the reported mixed identified/path-only targets, malformed syntax, offline Parent/Reference packages, Why-only review changes and Resource lifecycle. Seven focused regressions pass, including metadata before/after Why, canonical target reordering, registration idempotence, explicit move and external rename reconciliation.
- [x] Document syntax and prepare a separate Draft PR: all 451 deterministic/repository-consistency tests pass, including seven new regressions; diff hygiene is clean. Expected generated drift is confined to Foundation and Framework Development copies of the two edited syntax guides. All four normative edges remain current. Regeneration follows owner review; no merge is authorized.

The owner authorized finalization on 2026-10-08. No merge is authorized; leave the squash merge to the owner.

- [x] Regenerate Foundation at `0.2.5-draft` and Framework Development at `0.3.23-draft`, advance the explicit local Foundation import and retain both previous immutable publications. All six Nodes now have zero generated drift; all four normative edges are current.
- [x] Pass all 451 deterministic/repository-consistency tests, zero generated drift for six Nodes, current normative state for all four local edges and diff hygiene. Final candidate is prepared for publication. Exact-head hosted Linux/Windows evidence and PR readiness are live metadata in #114; mark ready only after both jobs succeed, without a status-only commit that invalidates the verified head.

## Phase-2 owner acceptance and merge preparation (#107 / #111)

Purpose: the owner confirms successful real migration and orderly short paths, accepts the result for main, and explicitly defers a new end-to-end onboarding to the next real adoption. Record that precise test boundary in PLAN/STATE, the Phase-2 plan and backlog; prepare PR #111 for the owner's squash merge. Future onboarding findings belong in new Issues. No executable, packaged Resource or release-version change belongs to this closure.

- [x] Record successful migration/path validation and owner acceptance without claiming a fresh end-to-end onboarding test.
- [x] Reconcile the current planning surfaces and verify documentation links (all four repository-consistency tests pass), zero generated drift for six Nodes, all four normative edges current and diff hygiene before publishing the closure.

Exact-head Linux/Windows CI and PR readiness remain live PR metadata. Keep #107 open until the merge closes it. After the owner's squash merge, record the actual accepted main commit in the baseline checkpoint; do not merge on the owner's behalf.

## Active owner-test correction — preserve unbound IDE metadata (#107)

Purpose: the reported STEP-04 extras are JetBrains `.idea/` files, including its own `.gitignore`. The owner wants ordinary IDE metadata to stop blocking ContextCanon. Existing handoff PLAN already excludes post-preparation `.idea/`/`.vscode/` from Evidence. Inventory respects Git standard ignores for untracked files; migration cannot use Git ignores as an ownership boundary because complete managed workspaces/runs are ignored too.

- [x] Exclude unbound `.idea/`/`.vscode/` metadata at workspace/task roots from migration inputs, copying and retirement; preserve those paths in place and report them. Explicitly bound Evidence/Parent/control/result bytes and isolated immutable packages stay fully verified; other unknown files still refuse.
- [x] Preserve metadata during interrupted package install/copy/retirement, including IDE edits/new files during recovery. Keep ownership/path/symlink protections for governed inputs and avoid treating arbitrary Git-ignored files as harmless.
- [x] Regress root/subtree and STEP 04/08 metadata, existing destination metadata, immutable/bound tampering and unrelated ignored files; all 32 migration tests pass and owner guidance/checkpoints are updated.
- [x] Regenerate the two self-hosted packages affected by the packaged owner-guide update (Gateway `0.3.23-draft`, Framework Development `0.3.22-draft`), retain their previous immutable versions, and repeat the complete local gate: 444 tests pass, all six Nodes have zero drift and all four normative edges are current. The implementation already passes 444 Linux and 82 native Windows tests on `06adaed`; its hosted failure was only the stale guide copies. Fast-forward publication and fresh exact-head Linux/native Windows proof remain live PR metadata; owner retries preview/apply without moving IDE files.

## Active owner-test correction — handoff file diagnostics (#107)

Purpose: the owner's migration in Itop now refuses `unknown/missing handoff files` without identifying the task or files. First make this refusal actionable without assuming its cause or claiming/deleting unrecognized content. Preserve frozen inputs, review decisions and result bytes; distinguish unknown files from missing required files and report STEP/root paths.

- [x] Report sorted unknown and missing relative paths, selected handoff STEP/root, unchanged-state assurance, and distinct preserve/report versus restore guidance.
- [x] Regress root/subtree, STEP 04/08 and preview/apply with unknown/missing/mixed files; preserve all remaining bytes/directories and avoid receipts. Retain successful RESULT.json migration and existing tampering guards; all 28 migration tests pass.
- [x] Verify the bounded correction locally and prepare publication on Draft #111: 440 tests pass, six self-hosted Nodes have zero drift, all four normative edges are current, and diff hygiene is clean. Fresh exact-head Linux/native Windows evidence remains live PR metadata.
- [x] Owner reported six JetBrains `.idea/` files in STEP 04 and explicitly requested IDE metadata tolerance. Continue with the bounded preservation block above; no blanket Git-ignore bypass.

## Active owner-test correction — legacy frozen Catalog recovery (#107)

Purpose: migration reaches an original Foundation authoring directory and rejects its authoring files as unknown immutable-package content. Distinguish isolated stores from live authoring roots, prefer exact retained packages, and reuse the existing Git-history recovery path for pre-freezing onboarding state. Snapshot/consumer/provider retained bytes take precedence; only full Node/version/normalized/package bindings may recover missing legacy bytes. Preview must not write into either repository or change provider checkouts, review files or accepted digests.

- [x] Factor the existing package validator/Git recovery reader for verified in-memory historical bytes; keep one package semantic/digest validation implementation and existing recovery writers.
- [x] Resolve missing legacy Catalog bytes and provenance deterministically, distinguish authoring files from strict store contents, and refuse advanced/unrecoverable provider substitution with useful diagnostics.
- [x] Regress exact live-package fallback, changed provider with retained history/Git history, missing/corrupt historical bytes, preview/apply/interruption and unchanged STEP-07/08/10/publication.
- [x] Verify the full correction and prepare publication on Draft #111; fresh exact-head Linux/Windows evidence remains live PR metadata.
- [x] Close native Windows findings: restore legacy CRLF artifact bytes only when size and full hash prove the original bytes, add a portable Git-autocrlf regression, and correct UTF-8/path-alias assumptions in tests. All 438 tests and self-host checks pass locally; prepare the fast-forward publication and record fresh hosted evidence in #111.
- [x] Owner confirms successful migration and orderly short paths, accepts Phase 2 for main, and defers a fresh onboarding to the next real adoption. See the closure block above.

## Active owner-test correction — migration workspace diagnostics (#107)

Purpose: the owner supplied a valid legacy snapshot but migration reports unknown workspace content without naming it. Keep the existing conservative ownership check; report the exact top-level blockers so the owner can distinguish personal/IDE files from unsupported historical ContextCanon artifacts. No automatic claiming, movement or deletion of unrecognized content is authorized.

- [x] Report sorted concrete unknown files/directories, selected workspace and unchanged-state/action guidance.
- [x] Regress preview and apply refusal with default/explicit snapshots, root/subtree workspaces and empty unknown directories; preserve all bytes and avoid creating receipts.
- [x] Verify the full candidate and prepare publication on Draft #111; fresh exact-head Linux/Windows CI remains live PR metadata.
- [x] Owner identified three obsolete anonymized exchange copies, removed them and successfully passed the workspace guard; no compatibility exception is needed.

## Post-merge baseline reconciliation — PR #108 (2026-10-06)

Purpose: record the owner's actual Phase-1 squash merge at `dc20fdb86980d5b6adb801d299a4610e0a297ae3`, integrate that accepted baseline into Draft PR #111, and run fresh exact-head Linux/Windows CI while the owner tests onboarding. The accepted Phase-1 tree exactly matches the previous stacked base. Preserve branch ancestry with a merge so an existing editable test checkout can continue using fast-forward pulls; do not rewrite the owner's active branch history or alter executable behavior.

- [x] Verify the actual Phase-1 merge and identical accepted/base trees; keep #107 open for Phase 2.
- [x] Integrate accepted main and reconcile PLAN/STATE/detail-plan current status.
- [x] Verify the documentation-only reconciliation and prepare its publication on #111 targeting main.

- [x] Owner accepts Phase 2 after successful real migration/path validation; a new end-to-end onboarding is deferred by the owner. Squash merge remains the owner's next action.

Fresh exact-head Linux/Windows results are a live gate recorded in PR #111, not another status-only commit.

## Phase-2 pre-merge position (historical)

Accepted `main`: `dc20fdb86980d5b6adb801d299a4610e0a297ae3` (owner-tested PR #108, squash-merged on 2026-10-06).

Owner-accepted change: **#107 Phase 2 onboarding storage**, branch `agent/issue-107-onboarding-versions`, PR #111 targeting `main`, being finalized for the owner's squash merge. Its original stacked Phase-1 base exactly matches the accepted squash tree. Accepted main is integrated with preserved editable-test branch ancestry. Real migration succeeds and the owner reports no remaining long paths in that project; a fresh end-to-end onboarding is explicitly deferred. See the [Phase-2 plan](plans/issue-107-phase-2.md) and [owner test](plans/issue-107-onboarding-owner-test.md).

[PR #108](https://github.com/SomeSunlight/context-canon/pull/108) is accepted: shared complete Node versions, shorter new Resource layouts and separate preview/apply migration for normal operation. #109 recovery and the #110 Resource-move correction are included. Phase 2 is now owner accepted; keep #107 open until the owner's merge of #111 closes it.

| Main point | Status | Detail / next action |
| --- | --- | --- |
| Restore a usable plan and review the interrupted work (#109) | Complete; owner accepted | [Recovery checklist](plans/issue-107-phase-1.md#recovery-and-owner-test-preparation-109) |
| Resource-move review correction (#110) | Fixed; owner retest successful | [Correction checklist](plans/issue-110-resource-move-review.md) |
| Shared versions and migration (#107 Phase 1) | Accepted in main via PR #108 | [Implementation contract and checkpoints](plans/issue-107-phase-1.md); [internal-project owner test](plans/issue-107-owner-test.md); [operator guide](docs/node-versions.md) |
| Onboarding storage and reset/recovery (#107 Phase 2) | Owner accepted after real migration; preparing #111 for squash merge | [Phase-2 checklist](plans/issue-107-phase-2.md) |
| Safe unused-version pruning | Deferred; complete reachability required | [Phase-2 prerequisite](plans/issue-107-phase-2.md) |
| Reinitialization / copied-project ID remapping (#106) | Separate open issue | [Backlog](plans/backlog.md) |
| Other proposed work and unresolved issue bookkeeping | Unscheduled | [Backlog](plans/backlog.md) |
| Previous accepted work and historical decisions | Archived | [Implementation history through PR #105](plans/archive/implementation-history-through-pr-105.md) |

## Current block — recovery and owner testing (#109)

Purpose: make the plan resumable after a lost Work chat, independently verify PR #108, and give the owner an executable test/migration sequence for the already-onboarded internal project. Recovery and real owner testing are complete; the owner squash-merged PR #108 on 2026-10-06 after the complete gate passed.

- [x] Preserve and separate overview, Phase-1 detail, deferred Phase-2 work and history.
- [x] Verify the published implementation and record remaining work or test limitations.
- [x] Document the internal-project migration/test sequence, checkpoints and rollback.
- [x] Publish the documentation on PR #108 and confirm final verification.
- [x] Owner tests and approves Phase 1, including the corrected propagation.

## Current block — Phase-1 merge readiness (#107 / #109 / #110)

Scope: record the owner's successful test/acceptance, preserve the remaining onboarding and legacy-candidate cleanup scope, publish one documentation closure, confirm exact-head full Linux/Windows verification, and mark PR #108 ready for the owner's squash merge. No product change or Phase-2 implementation belongs to this block.

- [x] Record owner acceptance and the next Phase-2 boundary in the current status/detail plans.
- [x] Prepare and locally verify the documentation-only closure, including repository links, zero generated drift and propagation health.
- [x] Owner squash-merged PR #108 after complete exact-head Linux/Windows CI as `dc20fdb86980d5b6adb801d299a4610e0a297ae3`; #107 stays open for Phase 2.

Final CI and readiness are live PR metadata: record them there without creating another status-only commit that invalidates the verified head. This index and STATE are reconciled with the actual Phase-1 squash baseline; new Phase-2 verification remains live PR metadata.

## Active owner-test correction (#110)

Completed scope: render Resource moves in guided Parent/Source review, preserve review/acceptance safety, regression-test the real failure and publish the correction on PR #108. See the [bounded checklist](plans/issue-110-resource-move-review.md). The owner confirms the correction works; migration need not be repeated.

## Resuming after an interruption

1. Read root `CONTEXT.md`, follow its applicable Topics, then read `STATE.md` and this index.
2. Open the active detail plan and resume at its first unfinished action. Consult history only when a decision needs explanation.
3. Verify the current branch/head before writing; do not let two chats write the same review branch concurrently.
4. Keep implementation completion, automated verification, owner approval and merge as distinct states.

The original PLAN text is retained in the linked detail/history files. Historical open boxes are listed in the backlog for reconciliation rather than treated as new implementation authority.
