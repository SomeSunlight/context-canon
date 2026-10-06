# Plan

This is the recovery index, not the implementation diary. Read [STATE.md](STATE.md) for current facts, then the linked detail plan for the work you are doing. Check off completed detail items immediately; keep older checkpoints in the archive.

## Current position

Accepted `main`: `28ce62ef7aca4960bcf238b8d2221b7e445aa236` (owner-tested PR #105).

[PR #108](https://github.com/SomeSunlight/context-canon/pull/108), branch `agent/issue-107-shared-node-versions`, implements #107 Phase 1: shared complete Node versions, shorter new Resource layouts and separate preview/apply migration for normal operation. On 2026-10-05 the owner reported successful migration/history browsing and corrected propagation, accepted Phase 1, and requested preparation for an owner-performed squash merge. The product correction passed Linux/Windows CI. The subsequent documentation-head run passed Windows but its Linux job was cancelled; the final current head must pass the complete merge gate before readiness is confirmed.

| Main point | Status | Detail / next action |
| --- | --- | --- |
| Restore a usable plan and review the interrupted work (#109) | Complete; owner accepted | [Recovery checklist](plans/issue-107-phase-1.md#recovery-and-owner-test-preparation-109) |
| Resource-move review correction (#110) | Fixed; owner retest successful | [Correction checklist](plans/issue-110-resource-move-review.md) |
| Shared versions and migration (#107 Phase 1) | Owner accepted; exact-head gate/readiness on PR #108 | [Implementation contract and checkpoints](plans/issue-107-phase-1.md); [internal-project owner test](plans/issue-107-owner-test.md); [operator guide](docs/node-versions.md) |
| Onboarding storage and reset/recovery (#107 Phase 2) | Next after Phase-1 merge and baseline reconciliation | [Phase-2 checklist](plans/issue-107-phase-2.md) |
| Safe unused-version pruning | Deferred; complete reachability required | [Phase-2 prerequisite](plans/issue-107-phase-2.md) |
| Reinitialization / copied-project ID remapping (#106) | Separate open issue | [Backlog](plans/backlog.md) |
| Other proposed work and unresolved issue bookkeeping | Unscheduled | [Backlog](plans/backlog.md) |
| Previous accepted work and historical decisions | Archived | [Implementation history through PR #105](plans/archive/implementation-history-through-pr-105.md) |

## Current block — recovery and owner testing (#109)

Purpose: make the plan resumable after a lost Work chat, independently verify PR #108, and give the owner an executable test/migration sequence for the already-onboarded internal project. Recovery and real owner testing are complete; the owner will perform the squash merge after the gate below.

- [x] Preserve and separate overview, Phase-1 detail, deferred Phase-2 work and history.
- [x] Verify the published implementation and record remaining work or test limitations.
- [x] Document the internal-project migration/test sequence, checkpoints and rollback.
- [x] Publish the documentation on PR #108 and confirm final verification.
- [x] Owner tests and approves Phase 1, including the corrected propagation.

## Current block — Phase-1 merge readiness (#107 / #109 / #110)

Scope: record the owner's successful test/acceptance, preserve the remaining onboarding and legacy-candidate cleanup scope, publish one documentation closure, confirm exact-head full Linux/Windows verification, and mark PR #108 ready for the owner's squash merge. No product change or Phase-2 implementation belongs to this block.

- [x] Record owner acceptance and the next Phase-2 boundary in the current status/detail plans.
- [x] Prepare and locally verify the documentation-only closure, including repository links, zero generated drift and propagation health.
- [ ] Owner squash-merges after complete exact-head Linux/Windows CI and readiness evidence recorded on PR #108; keep #107 open for Phase 2.

Final CI and readiness are live PR metadata: record them there without creating another status-only commit that invalidates the verified head. Reconcile this index and STATE with the actual accepted baseline after the owner merges.

## Active owner-test correction (#110)

Completed scope: render Resource moves in guided Parent/Source review, preserve review/acceptance safety, regression-test the real failure and publish the correction on PR #108. See the [bounded checklist](plans/issue-110-resource-move-review.md). The owner confirms the correction works; migration need not be repeated.

## Resuming after an interruption

1. Read root `CONTEXT.md`, follow its applicable Topics, then read `STATE.md` and this index.
2. Open the active detail plan and resume at its first unfinished action. Consult history only when a decision needs explanation.
3. Verify the current branch/head before writing; do not let two chats write the same review branch concurrently.
4. Keep implementation completion, automated verification, owner approval and merge as distinct states.

The original PLAN text is retained in the linked detail/history files. Historical open boxes are listed in the backlog for reconciliation rather than treated as new implementation authority.
