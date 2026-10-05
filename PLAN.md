# Plan

This is the recovery index, not the implementation diary. Read [STATE.md](STATE.md) for current facts, then the linked detail plan for the work you are doing. Check off completed detail items immediately; keep older checkpoints in the archive.

## Current position

Accepted `main`: `28ce62ef7aca4960bcf238b8d2221b7e445aa236` (owner-tested PR #105).

[Draft PR #108](https://github.com/SomeSunlight/context-canon/pull/108), branch `agent/issue-107-shared-node-versions`, implements #107 Phase 1: shared complete Node versions, shorter new Resource layouts and separate preview/apply migration for normal operation. Implementation is complete; the real internal-project owner test is pending. Keep the PR Draft and unmerged until explicit owner approval.

| Main point | Status | Detail / next action |
| --- | --- | --- |
| Restore a usable plan and review the interrupted work (#109) | Complete; owner test pending | [Recovery checklist](plans/issue-107-phase-1.md#recovery-and-owner-test-preparation-109) |
| Shared versions and migration (#107 Phase 1) | Implemented; owner test pending | [Implementation contract and checkpoints](plans/issue-107-phase-1.md); [internal-project owner test](plans/issue-107-owner-test.md); [operator guide](docs/node-versions.md) |
| Onboarding storage and reset/recovery (#107 Phase 2) | Deferred until Phase-1 owner testing | [Phase-2 checklist](plans/issue-107-phase-2.md) |
| Safe unused-version pruning | Deferred; complete reachability required | [Phase-2 prerequisite](plans/issue-107-phase-2.md) |
| Reinitialization / copied-project ID remapping (#106) | Separate open issue | [Backlog](plans/backlog.md) |
| Other proposed work and unresolved issue bookkeeping | Unscheduled | [Backlog](plans/backlog.md) |
| Previous accepted work and historical decisions | Archived | [Implementation history through PR #105](plans/archive/implementation-history-through-pr-105.md) |

## Current block — recovery and owner testing (#109)

Purpose: make the plan resumable after a lost Work chat, independently verify PR #108, and give the owner an executable test/migration sequence for the already-onboarded internal project. Scope is plan/state/operator documentation and review; no Phase-2 implementation or merge is authorized.

- [x] Preserve and separate overview, Phase-1 detail, deferred Phase-2 work and history.
- [x] Verify the published implementation and record remaining work or test limitations.
- [x] Document the internal-project migration/test sequence, checkpoints and rollback.
- [x] Publish the documentation on PR #108 and confirm final verification.
- [ ] Owner tests and approves Phase 1; then finish the exact-head merge gate.

## Resuming after an interruption

1. Read root `CONTEXT.md`, follow its applicable Topics, then read `STATE.md` and this index.
2. Open the active detail plan and resume at its first unfinished action. Consult history only when a decision needs explanation.
3. Verify the current branch/head before writing; do not let two chats write the same review branch concurrently.
4. Keep implementation completion, automated verification, owner approval and merge as distinct states.

The original PLAN text is retained in the linked detail/history files. Historical open boxes are listed in the backlog for reconciliation rather than treated as new implementation authority.
