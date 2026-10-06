# Plan

This is the recovery index, not the implementation diary. Read [STATE.md](STATE.md) for current facts, then the linked detail plan for the work you are doing. Check off completed detail items immediately; keep older checkpoints in the archive.

## Post-merge baseline reconciliation — PR #108 (2026-10-06)

Purpose: record the owner's actual Phase-1 squash merge at `dc20fdb86980d5b6adb801d299a4610e0a297ae3`, integrate that accepted baseline into Draft PR #111, and run fresh exact-head Linux/Windows CI while the owner tests onboarding. The accepted Phase-1 tree exactly matches the previous stacked base. Preserve branch ancestry with a merge so an existing editable test checkout can continue using fast-forward pulls; do not rewrite the owner's active branch history or alter executable behavior.

- [x] Verify the actual Phase-1 merge and identical accepted/base trees; keep #107 open for Phase 2.
- [x] Integrate accepted main and reconcile PLAN/STATE/detail-plan current status.
- [x] Verify the documentation-only reconciliation and prepare its publication on #111 targeting main.

- [ ] Owner finishes onboarding testing; Phase-2 approval/merge remain separate.

Fresh exact-head Linux/Windows results are a live gate recorded in PR #111, not another status-only commit.

## Current position

Accepted `main`: `dc20fdb86980d5b6adb801d299a4610e0a297ae3` (owner-tested PR #108, squash-merged on 2026-10-06).

Active owner review: **#107 Phase 2 onboarding storage**, branch `agent/issue-107-onboarding-versions`, Draft PR #111 targeting `main`. Its original stacked Phase-1 base exactly matches the accepted squash tree. The accepted main commit is integrated without rewriting the editable test branch's ancestry or changing executable/package bytes. The owner is now testing onboarding. See the [Phase-2 plan](plans/issue-107-phase-2.md) and [owner test](plans/issue-107-onboarding-owner-test.md).

[PR #108](https://github.com/SomeSunlight/context-canon/pull/108) is accepted: shared complete Node versions, shorter new Resource layouts and separate preview/apply migration for normal operation. #109 recovery and the #110 Resource-move correction are included. Keep #107 open for Phase-2 acceptance; no merge of #111 is authorized.

| Main point | Status | Detail / next action |
| --- | --- | --- |
| Restore a usable plan and review the interrupted work (#109) | Complete; owner accepted | [Recovery checklist](plans/issue-107-phase-1.md#recovery-and-owner-test-preparation-109) |
| Resource-move review correction (#110) | Fixed; owner retest successful | [Correction checklist](plans/issue-110-resource-move-review.md) |
| Shared versions and migration (#107 Phase 1) | Accepted in main via PR #108 | [Implementation contract and checkpoints](plans/issue-107-phase-1.md); [internal-project owner test](plans/issue-107-owner-test.md); [operator guide](docs/node-versions.md) |
| Onboarding storage and reset/recovery (#107 Phase 2) | Implementation complete; owner testing Draft #111 on main | [Phase-2 checklist](plans/issue-107-phase-2.md) |
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
