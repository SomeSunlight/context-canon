# Shared Node Versions — Deferred Phase 2 (#107)

Status: not started. Phase 1 is owner tested and accepted on 2026-10-05. Begin after the owner's squash merge of [PR #108](https://github.com/SomeSunlight/context-canon/pull/108) and accepted-baseline reconciliation; that PR intentionally excludes this work. Keep #107 open for this phase.

Phase-2 recovery plan — next development block after the Phase-1 merge:

- [ ] Reconstruct onboarding Evidence, frozen reusable Catalog, semantic handoffs, placement publication and reset-journal ownership; record exact frozen bindings before any storage change.
- [ ] Reuse the shared whole-Node library for frozen reusable packages, preserving complete reviewed identity and per-target Parent/Reference kind. Catalog/preview writer keys must use complete binding rather than byte digest alone. Scope Evidence/run state at the Git root by onboarding project/run, with full immutable identity in authoritative metadata and short locators.
- [ ] Adapt STEP 07/08/10, preview/publication and handoffs to those same frozen locations without introducing a parallel import model or fetching live inputs during recovery.
- [ ] Make publication rollback/reset aware of shared-root ownership and reachability: retain another Node/run's packages and all prior accepted inputs; resume interrupted transactions deterministically.
- [ ] Keep active-run migration separate and preview-first; verify/copy old frozen inputs before changing journals/bindings or retiring narrowly owned legacy wrappers. Continue reading old states where safe.
- [ ] Test normal-root/subtree/simultaneous/deep onboarding, exact preview/publication bindings and reset/recovery from STEP 07 onward on Linux/Windows; document and self-host, then prepare a separately owner-tested Draft candidate.
- [ ] Before any history-pruning feature, enumerate current pins, dependencies of retained versions, pending reviews, onboarding frozen inputs and recovery receipts. The Phase-1 inventory alone is deliberately insufficient deletion authority.


No automatic pruning is authorized by a row marked retained history. Complete reachability is a prerequisite, not an implemented deletion guarantee.
