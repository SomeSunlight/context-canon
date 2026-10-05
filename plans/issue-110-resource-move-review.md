# Resource Move Review — Owner-test Correction (#110)

The owner confirms the correction works and accepted Phase 1 on 2026-10-05. PR #108 is being prepared for the owner's squash merge after exact-head verification. The original report was successful migration and a useful history index, followed by `KeyError: 'moved'` during the final Parent review, before acceptance of the affected Child.

Purpose: complete the CLI representation of the already-supported deterministic Resource move; do not change identities, package binding, acceptance, migration or onboarding.

- [x] Reproduce the real move through guided propagation and audit other review writers.
- [x] Count/display moves, show old/new paths, and share the complete CLI change-symbol mapping.
- [x] Prove interactive refusal preserves the old Child pin, acceptance completes, and subsequent build/check is clean; cover Source-update review too.
- [x] Update PLAN/STATE/CHANGELOG and pass focused/full tests plus self-host checks.
- [x] Publish the correction on PR #108 and confirm exact-head Linux/Windows CI.
- [x] Owner reports successful resumed maintenance and approves the corrected Phase-1 result.

Resume at the first unfinished item. Earlier applied edges in a multi-edge propagation remain accepted if a later review fails; the reported one-edge failure occurred before the affected Child acceptance.

Reproduction: both guided propagation and guided Source updates crash at `_print_human_change_details` with a real identified Resource rename; the propagation and Source-update technical identity writers contain the same incomplete symbol table. The human summary also omits moved entries. Two end-to-end regressions use the normal shared version store, canonical imports, a Child directory with spaces, Parent/Reference variants and explicit n/y decisions.

Focused checkpoint: all 30 shared-store/propagation/configuration tests pass, including two new end-to-end Resource-move regressions. The shared CLI symbol mapping covers human and technical writers; summaries count moves and details show old/new package paths. Refusal keeps exact authored pins; resumed acceptance and subsequent build/check succeed. Source-update coverage includes Parent and Reference, then offline build/check after provider removal. The existing native Windows job runs these new shared-store tests automatically.

Local review candidate: all 396 deterministic tests pass. Self-host build reports no generated changes; check is clean with all four local Parent/Child relationships current, and diff hygiene passes. No package/Resource migration is needed. Exact-head CI and publication are the next gate; real owner acceptance remains pending.

Publication checkpoint: correction head `63da510fad05607faa7b57fbe2f929b51c2887f5` passes Actions run [37362883992](https://github.com/SomeSunlight/context-canon/actions/runs/37362883992): Linux complete 396-test suite/self-host check and all 25 native Windows tests, including the new move review regressions. The owner subsequently confirmed the correction works and accepted Phase 1. No repeat migration or reinstall is needed. Final merge-head CI is linked on PR #108; close #110 with the owner's merge. Onboarding storage remains separate Phase 2.
