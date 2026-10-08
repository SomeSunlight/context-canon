# Backlog and Issue Reconciliation

Unscheduled work only. This snapshot was read from GitHub on 2026-10-05 (#109); issue bodies are authoritative for scope. An open issue does not prove its implementation is missing: several still-open issues have accepted implementation checkpoints. No issues are closed by this documentation change.

| Issue | Title | Planning position |
| --- | --- | --- |
| [#107](https://github.com/SomeSunlight/context-canon/issues/107) | Share immutable Node versions at repository root and shorten generated paths safely | Both phases merged in #108/#111; fresh onboarding validation deferred to the next adoption |
| [#106](https://github.com/SomeSunlight/context-canon/issues/106) | Define safe project reinitialization and optional identity remapping for project copies | Separate future design |
| [#95](https://github.com/SomeSunlight/context-canon/issues/95) | Expose canonical Evidence line counts to semantic handoffs | Unscheduled; inspect issue before implementation |
| [#94](https://github.com/SomeSunlight/context-canon/issues/94) | Separate visible onboarding artifacts from hidden machine state | Unscheduled; inspect issue before implementation |
| [#90](https://github.com/SomeSunlight/context-canon/issues/90) | Make AGENTS.md adapter discoverable during onboarding/init | Unscheduled; inspect issue before implementation |
| [#89](https://github.com/SomeSunlight/context-canon/issues/89) | Place Sources near the top of authored Context | Unscheduled; inspect issue before implementation |
| [#88](https://github.com/SomeSunlight/context-canon/issues/88) | Guide coordinated updates for shared transitive Contexts | Unscheduled; inspect issue before implementation |
| [#84](https://github.com/SomeSunlight/context-canon/issues/84) | Document the reusable Python version-provenance pattern | Historical implementation checkpoint exists; reconcile issue status separately |
| [#81](https://github.com/SomeSunlight/context-canon/issues/81) | Keep PR and squash-merge titles scan-friendly | Unscheduled; inspect issue before implementation |
| [#79](https://github.com/SomeSunlight/context-canon/issues/79) | Expose development provenance without micro-bumping releases | Historical implementation checkpoint exists; reconcile issue status separately |
| [#66](https://github.com/SomeSunlight/context-canon/issues/66) | Ignore inline data URIs in Markdown Topic Resource closure | Historical implementation checkpoint exists; reconcile issue status separately |
| [#65](https://github.com/SomeSunlight/context-canon/issues/65) | Make STEP 07/08 onboarding self-explanatory for first-time users | Historical implementation checkpoint exists; reconcile issue status separately |
| [#62](https://github.com/SomeSunlight/context-canon/issues/62) | Harden STEP-08 semantic handoff and generic task input boundary | Historical implementation checkpoint exists; reconcile issue status separately |
| [#61](https://github.com/SomeSunlight/context-canon/issues/61) | Add deterministic per-step semantic handoff workspaces and ZIP packages | Historical implementation checkpoint exists; reconcile issue status separately |
| [#60](https://github.com/SomeSunlight/context-canon/issues/60) | Harden semantic handoffs: immutable snapshot binding, structured-data bodies, and isolated LLM workspace guidance | Historical implementation checkpoint exists; reconcile issue status separately |
| [#59](https://github.com/SomeSunlight/context-canon/issues/59) | Make onboarding reset discoverable and align onboarding documentation with numbered workflow | Historical implementation checkpoint exists; reconcile issue status separately |
| [#58](https://github.com/SomeSunlight/context-canon/issues/58) | Persist accepted inventory decisions while ignoring transient onboarding workspace | Historical implementation checkpoint exists; reconcile issue status separately |
| [#57](https://github.com/SomeSunlight/context-canon/issues/57) | Handle Git directory entries in inventory and stop mislabeling Errno 13 as WinError 5 | Historical implementation checkpoint exists; reconcile issue status separately |
| [#56](https://github.com/SomeSunlight/context-canon/issues/56) | Harden first-contact onboarding UX after owner walkthrough | Historical implementation checkpoint exists; reconcile issue status separately |
| [#55](https://github.com/SomeSunlight/context-canon/issues/55) | Document uv installation before onboarding | Historical implementation checkpoint exists; reconcile issue status separately |
| [#53](https://github.com/SomeSunlight/context-canon/issues/53) | Add reviewed onboarding inventory before Evidence freeze | Historical implementation checkpoint exists; reconcile issue status separately |
| [#52](https://github.com/SomeSunlight/context-canon/issues/52) | Document install/update command in README | Unscheduled; inspect issue before implementation |
| [#51](https://github.com/SomeSunlight/context-canon/issues/51) | Add post-onboarding .gitignore cleanup guidance | Unscheduled; inspect issue before implementation |
| [#43](https://github.com/SomeSunlight/context-canon/issues/43) | Exclude unresolved findings from review-only Source-edit fallbacks | Unscheduled; inspect issue before implementation |
| [#42](https://github.com/SomeSunlight/context-canon/issues/42) | Extract reusable repository documentation and structure philosophy | Unscheduled; inspect issue before implementation |
| [#41](https://github.com/SomeSunlight/context-canon/issues/41) | Explore explanatory views and documentation-gap findings | Unscheduled; inspect issue before implementation |
| [#40](https://github.com/SomeSunlight/context-canon/issues/40) | Clarify STEP-10 follow-up purpose and out-of-band accepted decisions | Unscheduled; inspect issue before implementation |
| [#39](https://github.com/SomeSunlight/context-canon/issues/39) | Make STEP-09 placement preview IDE-diff friendly | Unscheduled; inspect issue before implementation |

## Unchecked boxes in the historical PLAN

- #75 editable-install finalization: its old merge-gate box is historical; the current reusable workflow already contains CCW-013 and self-hosted 0.3.7-draft. It is not an active PR #108 task.
- PR #13 final ai-workstation readability/owner merge boxes: historical owner-test checkpoints, not present-day merge instructions.
- #66 version 0.9.9/final PR #54 verification box: superseded by the accepted 0.10.0 baseline; the issue remains open and may need status reconciliation.
- Optional semantic contradiction analysis: still a future design question. Preserve explicit human conflict resolution; do not infer Parent precedence. Relate any new block to #41 or create a specific issue before implementation.

The [unchanged historical record](archive/implementation-history-through-pr-105.md) retains all original checkboxes and decisions. The [#107 Phase-2 plan](issue-107-phase-2.md) records completed storage/recovery implementation and owner acceptance; automatic pruning still needs complete reachability accounting, and later onboarding findings belong in new Issues.

## Legacy review-candidate cleanup follow-up (#107)

The owner found old Child-local `.context/parent-candidates/<full-digest>` trees after successful migration. Phase-1 migration relocates accepted `.context/sources` packages and preserves old review candidates so pending reviews remain recoverable; new normal scratch is already scoped at the Git root. Safe cleanup must distinguish pending/retained review and recovery inputs from abandoned candidates, preview what will be removed, and preserve accepted shared versions. This is recorded follow-up work, not a Phase-1 merge blocker or permission to delete every legacy candidate directory.
