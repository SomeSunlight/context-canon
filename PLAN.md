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
- Ordinary project documentation remains project-owned during initial placement. `promote` can establish canonical ContextCanon meaning without silently deleting the old prose.
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
- [x] Validate preview/publication vertically on the real materialized `ai-workstation` Nodes with at least one Overview, root Rule, child-local Rule, Topic/Resource, mutable-document follow-up and reusable Development Workflow Source. Keep fixed-authority mapping covered by deterministic framework tests rather than inventing an authority mapping where the real frozen Evidence and human review did not produce one.

Real vertical-validation checkpoint: the corrected pass used `ai-workstation@4106fec3f7726d6c9bfedd70d30d9ed025b7c166`, which reproduced frozen Evidence `2a926bf353b252db4039e5c4b63b39abad6bab46c11982e88b3eb17e19cf203d` exactly. The reviewed v1 placement contained 33 Evidence-based findings plus owner-selected Development Workflow package `1d82c87e4f4140791f354c9d9479df845eb65c13fce1c664ecb05bec9532c8eb`. Publication touched all 8 accepted Context Nodes, retained 6 state/plan/ordinary-documentation follow-ups, preserved the existing root ID and unrelated authored content, kept every frozen Evidence byte unchanged, verified cross-directory Topic routing and exact Git Source provenance, produced zero generated drift across the resulting `ai-workstation` Nodes, and repeated with 0 changed Context sources and the same acceptance digest `a206e3423e9ffaccf7c3f7a1a0e2f140251a834f3c6eaf9764cd952b95e509c4`. The real run also exposed and fixed one trust/UX gap: publication preview now keeps Source name, `owner-selected`/`evidence-derived` origin, version and exact package identity visible alongside Git provenance.

- [x] After the coherent implementation settles, regenerate affected self-hosted Context packages, run the complete deterministic suite and `contextcanon check --all .` on the exact review candidate, inspect the PR diff for temporary/generated drift, and update PR #13 for project-owner review. Do not merge without explicit approval.

Review-candidate checkpoint: the cleaned product tree passed the complete deterministic suite and `contextcanon check --all .` with zero generated drift and no temporary real-test paths. A final qualitative review then removed one dead transaction line, corrected the Fixed Markdown review copy to match its preselected authoritative/imported candidates, and added early validation/regression coverage for invalid or duplicate stable human-side `authoring-id`s. The quality-hardening run again passed focused tests, the complete suite and zero-drift verification. The final repository-authored PLAN/STATE checkpoint exists only to obtain the ordinary exact-current-head PR workflow before presenting PR #13 for explicit project-owner review.

#### Block E — owner-review corrections: semantic shelves, operator guidance, and non-redundant promotion

Purpose: incorporate findings from the project owner's live `ai-workstation` onboarding before PR #13 is accepted. The workflow must remain usable when tired or returning after a pause, must allow conceptual Nodes that require new directories, and must make clear that duplicate prose created by `promote` is transitional rather than an acceptable steady state.

- [x] Make structure discovery explicitly independent from the repository's existing directory taxonomy: a semantic Node may use a new repository-relative directory when that creates the clearest durable landing point, including document-heavy repositories whose current files sit together in one directory.
- [x] Verify and document that structure materialization creates missing accepted Node directories/skeletons safely rather than restricting Nodes to pre-existing directories.
- [x] Turn `contextcanon-onboarding/README.md` into a numbered, end-to-end operator map with the exact artifact/command sequence, clearly marking the two external-LLM handoffs and the human gates.
- [x] Make checkpoint next commands preserve the important invocation context instead of forcing the operator to remember parameters such as repeated `--catalog-package` values or the one-time `--owner-source` decision from prose/chat history.
- [x] Tighten `promote` semantics in the design/docs: ContextCanon becomes the single canonical maintenance surface for the promoted meaning; duplicate source prose is allowed only as a migration transition, and later cleanup must replace true duplicates with a concise orientation/reference (or remove them), not maintain the same rule/meaning twice.
- [x] Define the later duplicate-cleanup contract around reviewed source excerpts plus links to the owning Context Node, keeping semantic summarization/human wording separate from deterministic mutation. Do not implement broad destructive cleanup until that review contract is safe.
- [x] Add focused regression coverage for the changed structure/workspace/promotion semantics, then checkpoint STATE/PR review wording. Full merge-gate regeneration/CI remains deferred until the owner has reviewed the corrected experience.

Owner-review correction checkpoint: the live test clarified three design points. First, the repository path tree is only Evidence; accepted semantic Nodes may introduce missing repository-relative directories, and a focused materialization test proves ContextCanon creates such a path safely. Second, the visible workspace now presents the whole onboarding as an eight-step runbook and records exact `--catalog-package` inputs in placement checkpoints; `--owner-source` is explicitly a one-time review-creation choice. Third, `promote` now means one canonical maintenance surface, with any initial duplicate treated as migration debt. A separate technical cleanup contract defines orientation/reference/removal as the steady-state cleanup outcomes while deliberately deferring destructive implementation. The focused additions brought the deterministic suite to 134 tests. PR workflow #462 / run `33443846928` passed both Unit/repository consistency and generated-output verification with no drift artifact; the remaining repository-authored PLAN checkpoint only records that completed proof and requires one final exact-head PR workflow before owner review continues.


#### Block F — owner-testing UX hardening

Purpose: remove operator reconstruction work exposed by the second live `ai-workstation` onboarding. ContextCanon should make a difficult semantic migration easier to execute, not require the operator to memorize similar CLI spellings, long digests, artifact names, or hidden validation steps.

- [x] Make placement validation an explicit numbered step between LLM placement proposal and human placement review.
- [x] Turn the workspace PLAN into a snapshot-bound copy/paste console with exact commands, persisted Source-catalog arguments, and reset commands for each restart point.
- [x] Prefix workflow artifacts with their step number so alphabetic file order matches the human onboarding flow; migrate unambiguous legacy workspace filenames safely.
- [x] Add safe `onboard reset --from N`: journal ContextCanon-managed project mutations, verify current bytes before rollback, preserve frozen Evidence, and conservatively remove untouched pre-journal onboarding skeleton Nodes.
- [x] Make semantic condensation part of the placement reasoning pass itself: present Overview/State/Plan wording as `Summary`, move volatile compatibility detail out of stable Overview, prefer atomic findings/bullets over snake sentences, and do not preserve architecture documents as Resources when their durable meaning belongs canonically in Nodes.
- [x] Require edited placement review to be revalidated through `placement-review` before advancing to publication preview.
- [x] Add focused regression coverage for runbook numbering/copy-paste commands, reset safety, legacy skeleton cleanup, and the sharper placement instruction.
