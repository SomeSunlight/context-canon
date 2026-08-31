# Plan

## Accepted baseline

The current accepted `main` baseline is PR #12, squash-merged as `bac1f52048b3d82cedb00b04fccd114607c4c915`.

The structure-first onboarding architecture, reusable Development Workflow Source, two-pass placement semantics and real `ai-workstation` structure materialization are accepted. PR #13 is the active review branch for finishing reviewed placement publication.

## Project-owner accepted block: structure-first onboarding on ai-workstation

Purpose: validate the shelves-before-books onboarding model vertically against the original frozen `ai-workstation` Evidence, while keeping the LLM semantic rather than authoritative.

- [x] Keep the original frozen Evidence snapshot immutable and reuse it as the project-evidence basis for the A/B onboarding test.
- [x] Preserve the already-onboarded root Node identity during structure-first continuation.
- [x] Generate a coarse structure proposal before moving individual Rules/Topics.
- [x] Make the structure review human-editable and treat grouping areas as ordinary Context Nodes rather than inventing `GroupNode`.
- [x] Preserve non-Node knowledge bodies and reusable Source suggestions as first-class structure findings.
- [x] Materialize only the missing owner-accepted Node skeletons after preview; do not publish placement semantics in the structure pass.
- [x] Exercise existing-root identity protection against the real materialized `ai-workstation` root.
- [x] Test Part 1 vertically against the real `ai-workstation` repository and frozen Evidence.
- [x] Complete the project-owner structure review/materialization with the seven missing child/group Nodes.

The accepted owner-edited primary hierarchy is:

```text
AI Workstation (.)
├── Bootstrap (bootstrap)
│   ├── Windows and WSL bootstrap (bootstrap/windows)
│   └── Linux bootstrap (bootstrap/linux)
├── aiw operator interface (bin)
└── Containerized application runtimes (compose)
    ├── Goose (compose/goose)
    └── Open WebUI (compose/open-webui)
```

The proposed `Local model integration` reserved Node was deliberately removed during human review. Frozen Evidence proves that local model integration is deferred, but does not prove its future implementation or whether it belongs below `compose`. That later intent stays a plan, not current structure.

The real operator run then confirmed that `structure-preview.md` made the change understandable, the existing root identity stayed protected, and the seven missing child/group Node skeletons materialized successfully.

## Active development block: reviewed placement publication on ai-workstation

Purpose: distribute the books onto the already accepted shelves using the original frozen Evidence and exact reusable Source catalog, make the human review itself editable, then preview and publish only the reviewed ContextCanon state without destructively cleaning ordinary project documentation.

### Design constraints

- The semantic reviewer receives only the original frozen Evidence plus the accepted structure and exact supplied Source catalog for project claims.
- The human review is allowed to introduce explicit owner decisions that Evidence itself cannot establish; those must remain distinguishable from Evidence-derived findings.
- Ordinary project documentation remains project-owned during initial placement. `move` can establish canonical ContextCanon meaning without silently deleting the old prose.
- Navigation parent does not imply Source inheritance. Source composition remains an independent semantic graph.
- Stable Rule/Topic identities must not be derived from path/title wording and must survive human edits.
- Publication must preserve existing Node identity and unrelated authored content, be previewable, rollback-safe and rerun-safe.
- State/plan/unresolved/ordinary-documentation findings must not disappear merely because current `CONTEXT.src.md` syntax does not safely absorb them.
- Source publication must retain exact reviewed package identity plus durable Git provenance/update metadata, never a transient local developer checkout path.

#### Block A — placement semantics and instruction

- [x] Add `overview` as a distinct placement kind so stable first-contact orientation does not have to masquerade as a Rule or temporary state.
- [x] Tighten action semantics: `promote` for meaning becoming canonical ContextCanon authoring/follow-up state, `reference` for Topic/Resource routing, `keep` for ordinary/unresolved material, and `map` for fixed-authority mappings.
- [x] Let structure review distinguish mutable ordinary Markdown from fixed authoritative Markdown without turning common README/CONTRIBUTING documents into fixed authority by default.
- [x] Update placement instruction to preserve the structure boundary, wording provenance and explicit Source-catalog comparison while refusing hidden/live project evidence.

#### Block B — human-editable placement review

- [x] Replace the static placement report with a destination-first editable `contextcanon/onboarding-placement-review/v1` surface while keeping `placement-proposal.json` as the strict LLM/machine artifact.
- [x] Parse only a deliberately small editable Markdown control surface; keep Evidence/provenance rendering outside the editable contract.
- [x] Allocate canonical Rule/Topic identities once in human review state and preserve them across repeated load/preview; titles and wording remain editable presentation.
- [x] Preserve an existing human-edited placement review instead of overwriting it; fail clearly when a changed proposal requires a new candidate/review decision.
- [x] Support explicit owner-selected reusable Sources independently of LLM-derived `source_reuses`, while retaining exact immutable package identity and project-specific local deltas.

#### Block C — deterministic placement preview and publication

- [x] Add deterministic `placement-preview` that shows exact per-Node `CONTEXT.src.md` deltas, Source install/pin changes, and findings that intentionally remain outside Node authoring before mutation.
- [x] Materialize accepted Overview, local Rules, Topics/Resources and Source state without replacing Node identity or unrelated authored content; repeated preview/publication must be safe.
- [x] Carry accepted `state`, `plan`, `ordinary-documentation`, authority mappings and unresolved findings durably even when they are not automatically spliced into arbitrary repository prose.
- [x] Keep existing mutable Markdown untouched during initial placement publication. A later cleanup preview may propose removing duplicate promoted text and leaving orientation/references, but that remains a distinct operation.
- [x] Preserve exact Source package identity plus durable Git provenance/update metadata without writing a transient developer checkout path into project truth.

#### Block D — resumable onboarding UX and final real-project validation

- [x] Make the visible onboarding workspace self-describing enough that a human or capable LLM can enter through one local file and reconstruct Evidence identity, accepted structure, current placement-review stage and next command without chat history.
- [x] Document the distinction between one-time migration onboarding and ContextCanon-native project growth/maintenance; keep future context-audit ideas separate from initial onboarding.
- [x] Record reusable Node distribution as an explicit later UX decision without selecting a repository/registry architecture in this block.
- [x] Re-run the corrected placement pass against the real frozen `ai-workstation` Evidence and owner-edited structure, including owner-selected Development Workflow, and inspect the new editable review before publication.
- [x] Validate preview/publication vertically on the real materialized `ai-workstation` Nodes with at least one Overview, root Rule, child-local Rule, Topic/Resource, fixed-authority mapping, mutable-document follow-up and reusable Development Workflow Source.

Real vertical-validation checkpoint: the corrected pass used `ai-workstation@4106fec3f7726d6c9bfedd70d30d9ed025b7c166`, which reproduced frozen Evidence `2a926bf353b252db4039e5c4b63b39abad6bab46c11982e88b3eb17e19cf203d` exactly. The reviewed v1 placement contained 33 Evidence-based findings plus owner-selected Development Workflow package `1d82c87e4f4140791f354c9d9479df845eb65c13fce1c664ecb05bec9532c8eb`. Publication touched all 8 accepted Context Nodes, retained 6 state/plan/ordinary-documentation follow-ups, preserved the existing root ID and unrelated authored content, kept every frozen Evidence byte unchanged, verified cross-directory Topic routing and exact Git Source provenance, produced zero generated drift across the resulting `ai-workstation` Nodes, and repeated with 0 changed Context sources and the same acceptance digest `a206e3423e9ffaccf7c3f7a1a0e2f140251a834f3c6eaf9764cd952b95e509c4`. The real run also exposed and fixed one trust/UX gap: publication preview now keeps Source name, `owner-selected`/`evidence-derived` origin, version and exact package identity visible alongside Git provenance.

- [x] After the coherent implementation settles, regenerate affected self-hosted Context packages, run the complete deterministic suite and `contextcanon check --all .` on the exact review candidate, inspect the PR diff for temporary/generated drift, and update PR #13 for project-owner review. Do not merge without explicit approval.

Review-candidate checkpoint: the cleaned tree passed 129/129 tests, `contextcanon check --all .` for all four self-hosted Nodes, and a final net-diff hygiene check with no temporary real-test workflow/harness/report/diagnostic paths. PR #13 was updated with the real validation and exact package/evidence identities. A normal human-authored checkpoint follows solely to obtain an ordinary exact-head GitHub PR workflow because GitHub marked the bot-authored finalizer synchronization `action_required` without creating a job.
