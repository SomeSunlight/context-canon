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

Owner-testing UX hardening checkpoint: the nine-step workspace runbook now exposes Placement Validate as Step 6, exact snapshot-bound commands live in the generated PLAN, artifacts sort in workflow order, reset can safely roll back ContextCanon-managed test mutations, and placement performs the semantic condensation while the owner is already reviewing meaning. Final polish also aligns CLI `--help` and the durable onboarding walkthrough with the numbered artifacts and refreshes stale framework-owned PLAN files on upgrade/reset. Focused coverage brings the complete deterministic suite to 141 tests. A self-deleting finalization workflow must pass the full suite plus build/check with zero generated drift before creating the clean product commit; a repository-authored identical-tree checkpoint then exists only to obtain the normal exact-head PR workflow for continued owner testing.

#### Block G — reset must always restore the operator surface

Purpose: close the live-test gap where `onboard reset --from 2` can correctly remove ContextCanon-generated project state but leave the operator with no new `contextcanon-onboarding/PLAN.md` when the visible workspace itself had already been deleted.

- [x] Make reset recreate the default (or explicitly selected) ContextCanon-owned onboarding workspace when it is missing, while retaining the existing refusal to take over a foreign directory.
- [x] Ensure the recreated PLAN is immediately rewritten to the requested reset checkpoint and contains the exact snapshot-bound commands for restarting at that numbered step.
- [x] Add regression coverage for a completely missing workspace, then run the normal PR verification on the resulting head before handing the owner a new install SHA.

Reset operator-surface recovery checkpoint: the live owner test exposed the missing-workspace case after `reset --from 2`. Reset now recreates/refreshes the ContextCanon-owned workspace, rewrites the reset checkpoint, and repopulates the exact snapshot-bound command console. Regression coverage raises the deterministic suite to 142 tests. PR workflow #482 / run `33498482979` passed the product fix with unit/repository consistency and generated-output verification green. This checkpoint records that proof before one final exact-head PR run.

#### Block H — live Step-4 collision and PLAN polish

Purpose: remove the next owner-test blockers without weakening collision safety: make the runbook visually self-explanatory, shorten repeated snapshot paths in commands, and distinguish legitimate ContextCanon-owned root state from project-owned output collisions during structure preview/materialization.

- [x] Add a one-line cue immediately above the checklist that the exact copy/paste commands are below it.
- [x] Render one shell-native snapshot variable once per PLAN and use it in the exact command section instead of repeating the full content-addressed snapshot path in every command.
- [x] Fix structure preview/materialization so an existing ContextCanon-generated `CONTEXT/` namespace and root `.context/onboarding/` state are not mistaken for project-owned collisions, while still refusing concrete foreign output files/namespaces.
- [x] Preserve/recover the established root Node identity when the authoring source is missing but prior ContextCanon acceptance state proves that identity; do not silently allocate a replacement root UUID.
- [x] Add focused regressions for the exact `ai-workstation` Step-4 shape and PLAN rendering, then run full suite/build/check and exact-head PR CI before handing back a new test SHA.

Live Step-4 owner-test checkpoint: the runbook now points visibly from the checklist to the detailed commands and defines one shell-native `SNAPSHOT` variable instead of repeating the full content-addressed path. Structure preview/materialization distinguishes a provably generated root `CONTEXT/`/`.context` namespace from a foreign collision; if the root authoring source is missing, ContextCanon recovers only when generated machine state or prior acceptance proves one stable root identity, and preserves that ID/name/version. Two focused regressions cover the recovered `ai-workstation` shape and continued refusal of a foreign `CONTEXT/`. The complete deterministic suite is now 144 tests; full build/check and zero-drift verification passed in the self-deleting quality run.

#### Block I — recover generated child Nodes during repeated onboarding

Purpose: close the next live `ai-workstation` Step-4 restart gap: a child Node such as `bootstrap` may already have provably generated `.context`/`CONTEXT` state from an earlier onboarding run while its `CONTEXT.src.md` was removed by reset/cleanup. That is established ContextCanon state, not automatically a foreign collision.

- [x] Generalize safe authoring recovery from the project root to every accepted Node path when that Node's own generated machine/package state proves one stable identity.
- [x] Keep root-only acceptance-record recovery root-only; child recovery must come from the child's own generated state rather than inherited/project-root evidence.
- [x] Preserve strict collision safety: foreign `CONTEXT/` content or unknown child `.context` entries must still abort before mutation.
- [x] Add regressions for a recoverable generated child Node and a child `.context` namespace containing foreign state, then run the complete suite/build/check and normal exact-head PR CI before returning a new test SHA.

Child-node recovery checkpoint: the live `bootstrap` failure proved that restart recovery must be Node-local rather than root-special. Any accepted Node path can now recover a missing `CONTEXT.src.md` only when its own generated package/machine state proves one unambiguous stable Node identity; root acceptance records remain root-only evidence. Foreign child `.context` entries and unverified `CONTEXT/` bytes still abort before mutation. The focused additions raise the deterministic suite from 144 to 146 tests.

#### Block J — placement transformation cockpit and canonical-source cleanup

Purpose: make the human placement gate show the complete reviewed transformation rather than only the destination meaning, so onboarding can actually reduce duplicate canonical knowledge instead of merely creating a second copy.

- [x] Make every promoted finding show the exact editable destination meaning under an honest `Into Node` label when it is actually published into Node authoring; label State/Plan honestly as node-local follow-up until their publication surface is designed.
- [x] Extend the semantic placement contract with reviewed mutable-Markdown source edits: exact frozen range, linked promoted findings, and a proposed concise replacement/orientation that remains close to source wording when meaning is uncertain.
- [x] Render `Source before — frozen Evidence` and editable `Source after promotion` in `STEP-07-placement.md`, with one shared edit owning overlapping/multi-finding source ranges so the same replacement is never edited twice.
- [x] Validate source-edit ranges deterministically: mutable Markdown only, exact frozen hash/range, promoted linked findings only, complete Evidence coverage, and no overlapping edits in one source file.
- [x] Include accepted source-document deltas in publication preview and apply them transactionally with Context Node changes; accept either original frozen bytes or the exact already-published reviewed result for idempotent reruns.
- [x] Persist Source-catalog and owner-selected Source run inputs in machine-owned snapshot state so reset/workspace recreation cannot forget them.
- [x] Tighten placement guidance toward plain source-shaped wording, consolidated Node overviews, and aggressively readable source summaries only when meaning is unambiguous; avoid academic/corporate abstraction and preserve wording when uncertain.
- [x] Add focused regressions for cockpit rendering/edit round-trip, shared source edits, overlap/authority safety, transactional document publication/idempotency, and run-input recovery; then run the complete suite plus build/check.

#### Block K — publish State and Plan as local Node authoring

Purpose: finish onboarding as a real operational starting point by making reviewed current state and future plan first-class local Context content instead of migration follow-up.

- [x] Parse local `## State` and `## Plan` sections from `CONTEXT.src.md` as first-class authored Node content.
- [x] Render State and Plan into generated `CONTEXT.md` and expose them in deterministic local machine state without inheriting them through reusable Sources.
- [x] Publish accepted placement `state` and `plan` findings into placement-managed State/Plan blocks in the destination Node.
- [x] Show State/Plan honestly as `Into Node — editable` in `STEP-07-placement.md`; remove them from publication follow-up once accepted.
- [x] Keep normalized reusable semantics stable when only Overview/State/Plan presentation changes, while exact package identity changes with generated `CONTEXT.md` bytes.
- [x] Cover parser/compiler behavior, onboarding preview/publication, idempotency, and existing reset safety with regressions; then rerun the complete suite plus build/check.

Placement transformation cockpit checkpoint: owner testing showed that showing only a synthesized "maintained meaning" hid the actual migration. `STEP-07-placement.md` now makes the A → Node + A′ transformation explicit: destination wording is editable, frozen source-before Evidence is visible, and shared exact mutable-Markdown Source After edits are editable once and linked to every promoted finding they cover. Accepted source edits are range/hash bound, non-overlapping, previewed as document diffs, and published/rolled back in the same transaction as Context Node changes. Exact already-published A′ bytes are accepted for idempotent reruns; unrelated Evidence drift still stops publication. Run inputs now persist in snapshot-owned `run-inputs.json`, so reset/workspace recreation retains exact catalog and owner-Source choices. The semantic instruction also favors source-shaped plain language, consolidated overviews, and readable orientation over inflated abstraction while remaining conservative under uncertainty.

State/Plan publication checkpoint: reviewed `state` and `plan` findings are now first-class local Node authoring. Placement writes them into managed `## State` / `## Plan` blocks in `CONTEXT.src.md`; generated `CONTEXT.md` carries the same operational content, and machine state exposes it locally. They are no longer placement follow-up. Reusable Sources do not inherit State/Plan, and normalized reusable semantics remain stable when only Overview/State/Plan presentation changes; exact package identity still follows the generated package bytes.

#### Block L — parse multiple shared Source After edits per finding

Purpose: close the live `ai-workstation` Step-7 failure where one promoted finding owns more than one reviewed Source After edit. The renderer already shows each edit once, but the review parser must stop each editable Source-edit block at the next Source-edit boundary rather than consuming all later edits under the same finding.

- [x] Bound Source-edit parsing by the next Source-edit metadata marker as well as the next placement/Source heading.
- [x] Add a regression with two non-overlapping Source After edits owned by the same promoted finding and verify both round-trip independently.
- [x] Run the focused placement-review tests, complete deterministic suite, build/check, diff-check, cleanup, and exact-head PR CI before returning a new test SHA.

Shared Source-edit parser checkpoint: the live `ai-workstation` proposal contains several legitimate cases where one promoted finding owns multiple non-overlapping Source After transformations. Review parsing now treats the next `cc:source-edit` marker as an explicit block boundary, so each edit keeps exactly one decision, note and editable replacement even when two edits are rendered under the same P-item. A focused regression reproduces that shape; the complete deterministic suite and repository build/check are green.

#### Block M — make Source After a real summary and keep the cockpit recoverable

Purpose: correct the next live `ai-workstation` Step-7 review failure. The second semantic pass must leave a useful human summary where promoted prose used to live, not a content-free pointer, and the review cockpit must still let the owner create a safe source rewrite when the LLM omitted one.

- [x] Tighten the placement instruction so stable Overview omits volatile version/platform detail already represented as State, and Overview/State/Plan findings are bullet-sized rather than comma/semicolon snake sentences.
- [x] Require Source After replacements to preserve a real plain-language gist of the moved block plus the Context link; explicitly reject pointer-only replacements such as “details live in Project Context” when the old location still has first-contact value.
- [x] Add a conservative review-only Source After fallback for an unambiguous mutable Markdown range when a promoted finding has no LLM source edit; default it to `reject` so it adds editability without adding publication work.
- [x] Remove self-referential `Linked promoted findings: P-xxx` cockpit noise; show only genuinely shared findings and keep the existing one-edit shared-placement behavior.
- [x] Add focused regressions for the sharper instruction, optional human Source After override, shared-edit presentation and parser round-trip, then run the complete suite plus build/check/diff-check.

Placement summary/cockpit checkpoint: the placement instruction now requires a real A′ summary plus the Context link, explicitly rejects pointer-only Source After prose at still-useful human surfaces, keeps volatile compatibility out of stable Overview, and treats Overview/State/Plan findings as one bullet-sized fact each. STEP-07 hides self-referential linked-finding noise and exposes a deterministic review-only Source edit when a promoted finding has an unambiguous mutable Markdown range but the LLM omitted cleanup; that fallback defaults to reject and therefore cannot mutate the project unless the owner edits and accepts it. Focused regressions cover the instruction and human fallback round-trip; full suite/build/check/diff-check are green before cleanup.

#### Fast-run status — ACTIVE

The project owner has explicitly delegated the current live `ai-workstation` correction sequence as an owner-approved fast-run. This boundary is now recorded durably instead of living only in conversation.

- **Scope:** corrections discovered while vertically reviewing the real onboarding placement, through the next coherent owner-review candidate.
- **Reduced intermediate ceremony:** repeated PR-description polish, full CI and generated-output refresh may be deferred between small related corrections; focused verification and recovery checkpoints remain required.
- **Exit condition:** the project owner explicitly ends the fast-run, or the current placement line reaches a coherent owner-review candidate. At exit, record **Fast-run status — CLOSED** in PLAN before returning to ordinary review cadence.
- **Authority is unchanged:** fast-run changes cadence only. PR #13 remains review-only and must not be merged without explicit owner approval and the normal exact-head merge gate.

The exact historical instant at which this already-running cadence began is intentionally not invented retroactively; this checkpoint makes the active boundary explicit from here forward.

#### Block N — preserve semantic integrity and make the placement cockpit visibly editable

Purpose: incorporate the next real `ai-workstation` placement-review findings without making the semantic pass brittle. Source cleanup must never silently discard facts, open questions must survive onboarding in the owning Node, and the Markdown cockpit must show human-editable regions even in rendered views.

- [x] Require a per-Source-edit zero-loss audit: every substantive fact removed from the frozen range must remain in A′ or be carried by linked promoted findings that cite that source range; a duplicate elsewhere may not accidentally rescue an incomplete move.
- [x] Make `unresolved` a destination-bearing promoted local open question and publish it into the destination Node's State so investigation can happen after onboarding without blocking it.
- [x] Tighten the one-finding/one-fact guidance enough that lists and three-or-more independently maintainable clauses cannot be hidden inside one `includes A, B, C` or semicolon-heavy bullet.
- [x] Keep review-only H-fallback cleanup away from retained Topic/Resource documents and release-history/patch documents.
- [x] Make optional source cleanup explicitly independent from accepting the promoted finding, and add visible rendered Markdown markers around every human-editable control/content region.
- [x] Clarify historical evidence for volatile State: when only changelog/history supports a value, say `last documented` or leave it unresolved rather than presenting it as proven current state.
- [x] Record the bounded fast-run start/scope/exit contract in the reusable Development Workflow while leaving this currently active fast-run open.
- [x] Add focused regressions, run the complete deterministic suite, rebuild/check generated ContextCanon output, and leave PR #13 draft/unmerged for continued owner testing.

Placement semantic-integrity checkpoint: the second semantic pass now audits every proposed Source After transformation for zero semantic loss against its exact frozen range; splitting volatile detail out of Overview requires destination State findings to cite that same mixed source. Unresolved findings are destination-bearing promoted open questions and publish into local Node State instead of disappearing into follow-up. The review-only H-fallback no longer offers cleanup for retained Topic/Resource documents or release-history/patch documents, optional cleanup explicitly says it is independent from accepting the finding, and rendered Markdown shows visible ✏️ boundaries around editable controls/content. The Development Workflow now requires an explicit fast-run ACTIVE scope/exit boundary and later CLOSED checkpoint; the current owner-approved fast-run remains ACTIVE. Focused placement regressions, the complete deterministic suite, full build/check and diff hygiene passed before this checkpoint.

### Later documentation follow-up

- [ ] Document the observed onboarding effect that book placement itself surfaces previously hidden responsibilities, boundaries and unresolved questions; concise finding titles become a useful project index before the reader even opens the deeper material.

#### Block O — allow blank Markdown separators inside reviewed Source edits

Purpose: fix the live `ai-workstation` Step-6 validation failure where one coherent `docs/architecture.md` Source After edit spans a blank separator line between two Evidence-backed semantic blocks.

- [x] Keep Source-edit provenance strict for every non-blank line while allowing blank/whitespace-only Markdown separators inside a contiguous reviewed edit range.
- [x] Align the placement instruction with that deterministic rule so the LLM is not asked to invent semantic Evidence for formatting-only blank lines.
- [x] Add a regression proving blank separators are ignored and a substantive uncovered line still fails with its exact missing line number.
- [x] Run the focused placement test, complete deterministic suite, build/check and diff hygiene, then remove the temporary verification harness.

Blank-separator checkpoint: the live proposal was semantically sound. Its architecture edit covers lines 3–13 while linked findings cover the table (3–10) and source-of-truth statement (12–13); line 11 is only the Markdown separator between them. Validation now requires provenance for every non-blank edited line, not for formatting-only blank separators, while substantive uncovered lines remain a hard error.
