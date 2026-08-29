# Plan

## How to read "accepted" in this plan

Two different ideas use similar words and should not be confused:

- **Project-owner accepted** means the project owner, acting as ContextCanon's first user/reviewer, reviewed a development stage and approved it as the new project baseline.
- **`source accept` / `onboard accept`** are product operations performed by an explicit human operator on one concrete reviewed Source candidate or onboarding proposal.

No anonymous system, CI job, or LLM "accepts" project truth.

## Project-owner accepted baseline

ContextCanon has passed self-hosted and real external-project validation. The current project-owner accepted `main` baseline is PR #9, squash-merged as:

`f7afe5c82942ecb9e3a04696455f8c960cc9b144`

Validated foundations include:

- [x] Gateway, Foundation, Development Workflow, and Framework Development as real self-hosted Context Nodes.
- [x] Deterministic compiler and generated drift checking.
- [x] `SomeSunlight/teams-chat-exporter` external experiment.
- [x] Real GitHub Copilot entry through generated `AGENTS.md`.
- [x] Ordinary versus Topic-specific progressive disclosure.
- [x] Inherited Rule `Remove`/`Override`, transitive provenance, and diamond-conflict diagnostics.
- [x] Deterministic Context diff and semantic normalization.
- [x] Immutable external Sources, reviewed Source updates, generic Git candidate transport, and atomic publication/recovery.
- [x] Complete first-adoption onboarding from deterministic Evidence preparation through framework-owned LLM assignment, strict proposal validation, human review, explicit acceptance, staged publication, exact Source binding, and rollback-safe canonical adoption.
- [x] Repository orientation, documentation ownership, Tests/CI context, and recoverable LLM-assisted development workflow hardened through PR #9.

The development cadence is deliberately split between human review, mechanical merge finalization, and accepted-baseline closure:

> complete one coherent block → make the large line reviewable and disclose known CI/drift → project-owner review → after approval finalize self-hosted generated packages/cleanup → exact-head fully green + zero drift → squash-merge to `main` → close the post-merge accepted-baseline/state checkpoint → start the next block on a fresh branch.

## Project-owner accepted: Compiler 0.4 — immutable external Sources

Merged through PR #3 as `7fd1aa64fb1f853a2bd4be84a9ed1afaf07d5de9`.

Goal: reusable Sources work across independent repositories without live inheritance or hidden network access during normal build.

### Immutable package boundary

- [x] Define `CompiledPackage` as the common semantic Source boundary.
- [x] Publish a versioned `.context/package.json` alongside `CONTEXT.md` and optional `CONTEXT/`.
- [x] Carry effective Rules, provenance, removals, local Changes/Topics, dependency identities, file hashes, and both digests.
- [x] Verify semantic digest, exact package files, path safety, and package digest on load.
- [x] Round-trip a Source after deleting its original repository.
- [x] Preserve presentation order independently from canonical semantic ordering.
- [x] Route local compiled Sources and loaded external Sources through the same Rule-composition algorithm.

### Exact accepted Source state

- [x] Store accepted Source packages under `<consumer>/.context/sources/<package-digest>/`.
- [x] Treat those packages as reproducible consumer state suitable for offline builds.
- [x] Add exact `normalized-digest` + `package-digest` Source pins.
- [x] Preserve unpinned local Sources as the simple local-development/self-hosting case.
- [x] Make ordinary `build` use only accepted local package state for pinned external Sources.
- [x] Fail clearly on missing/corrupt/mismatched accepted state rather than fetching silently.

### Operator review and `source accept`

Here the actor is the **human/operator using ContextCanon**, not the project milestone process above.

- [x] Diff accepted and candidate immutable packages deterministically.
- [x] Validate the candidate inside the real consumer composition before acceptance.
- [x] Surface dangling local Changes and Rule collisions during review.
- [x] Write a deterministic review receipt bound to exact consumer/candidate state.
- [x] Require that receipt before `contextcanon source accept` can update the accepted Source.
- [x] Reject stale acceptance after consumer/candidate changes.
- [x] Publish accepted package state and Source pins atomically.
- [x] Prove simulated publication failure preserves the old accepted build state.

### Generic Git candidate transport

- [x] Add explicit `transport="git"`, `ref="..."`, and `node-path="..."` metadata.
- [x] Keep Node ID as identity and `node-path` as repository location.
- [x] Add `contextcanon source fetch` using ordinary Git.
- [x] Keep fetched candidates separate from accepted build state.
- [x] Test nested reusable Nodes, unknown refs, missing paths and interrupted retrieval locally in CI.

## Project-owner accepted: onboarding through validated proposal

The project owner reviewed the onboarding implementation and user-facing documentation as ContextCanon's first user. PR #7 was squash-merged as `275c6b1f121126fb117f4bdbff1efc18218b0528`; the subsequent first-user usability review was accepted and PR #8 was merged as `1280aa9e763f0588fa06b3e1e98b9e7b52302cdd`.

The accepted flow on `main` reaches:

```text
[ContextCanon · deterministic]
existing repository → frozen evidence
        ↓
[ContextCanon · deterministic]
framework-owned semantic assignment
        ↓
[External reasoning LLM · semantic]
proposal.json
        ↓
[ContextCanon · deterministic]
strict proposal/provenance validation
        ↓
validated review artifact
```

### Deterministic bootstrap

- [x] `contextcanon onboard prepare <project>` works without an existing Context Node.
- [x] Inventory likely context carriers without copying the whole repository.
- [x] Preserve exact path/size/hash/selection provenance in content-addressed snapshots.
- [x] Respect Git-ignore while permitting explicit safe additions.
- [x] Bound secret/path/symlink/UTF-8 handling, 1 MiB per file and 16 MiB total evidence.
- [x] Verify/reuse matching snapshots; reject corrupted content-addressed state.

### Framework-owned LLM assignment

- [x] `contextcanon onboard instruction <snapshot>` supplies the semantic task; users do not invent the prompt.
- [x] Bind exact instruction bytes/digest to one verified evidence snapshot and explicit reusable Source catalog.
- [x] Treat evidence/catalog contents as untrusted review data, not as meta-instructions.
- [x] Require exact evidence provenance, rationale and confidence for each proposed item.
- [x] Classify into local Rule, existing Source, candidate reusable Node, Topic/Resource, state/planning, ordinary documentation, or unresolved question.
- [x] Compare likely generic practices against supplied verified Source packages before proposing duplication.
- [x] Preserve useful README/CONTRIBUTING/docs instead of treating onboarding as destructive migration.
- [x] Keep the external harness/model replaceable and outside compiler truth.
- [x] Bound the fully rendered instruction at 4 MiB and reject truncation.

### First-user review hardening

- [x] Make onboarding discoverable from README and repository Gateway.
- [x] Rewrite the user guide as progressive disclosure before technical reference.
- [x] Show clearly which steps are ContextCanon, which single step belongs to the external LLM, and that the LLM returns exactly one `proposal.json`.
- [x] Recommend a strong reasoning-capable model for onboarding rather than implying any general LLM is equally suitable.
- [x] Tell the LLM that README/CONTRIBUTING and other conventional files may be stale.
- [x] Prefer direct implementation/configuration/manifest/CI/test evidence for **current implemented behavior** when it conflicts clearly with descriptive documentation.
- [x] Preserve documentation/source comments as evidence for intent, rationale, constraints, workflow, history and target design.
- [x] Require unresolved current-vs-intended conflicts to remain visible instead of being silently reconciled.
- [x] Add local `Overview` orientation to Official Context without making explanatory prose inherited governance.
- [x] Separate framework contributions from reusable `nodes/library/` contributions in CONTRIBUTING.
- [x] Rewrite STATE for a newcomer rather than as a compressed architecture dump.

### Proposal validation

- [x] Define `contextcanon/onboarding-proposal/v0` separately from Proposal and Official Context.
- [x] Require each item to carry rationale, confidence and exact evidence hash/line-range references.
- [x] Strictly validate kinds, payloads, evidence file set, hashes/ranges and deterministic `proposal_digest`.
- [x] Revalidate the Evidence v0 safety policy when consuming a snapshot.

## Project-owner accepted: human review and explicit onboarding acceptance

PR #9 / branch `agent/onboarding-review-acceptance` was project-owner approved, passed the exact-head mechanical merge gate, and was squash-merged to `main` as `f7afe5c82942ecb9e3a04696455f8c960cc9b144`.

Goal: make a proposal inspectable against exact evidence, record explicit human decisions, and allow canonical first adoption only when that exact reviewed state still matches the project.

### Human review representation

- [x] Define `contextcanon/onboarding-review/v0` separately from Proposal and Official Context.
- [x] Bind review state to exact `evidence_digest` and `proposal_digest`.
- [x] Make canonical Node ID/name/version human-owned review state rather than LLM authority.
- [x] Generate a fresh UUID for a newly created Node when the operator does not provide `--node-id`; do not derive independent Node identity from shared Evidence identity.
- [x] Keep that generated/provided Node identity stable by storing it in `review.json`.
- [x] Create every proposal item as `pending` and require exactly one decision per item.
- [x] Support explicit `accept` / `reject` plus human note.
- [x] Render every finding with classification, confidence, rationale, payload, exact evidence references and cited evidence lines.
- [x] Give the normalized review its own deterministic `review_digest`.
- [x] Reject an existing review when the semantic proposal changes.

### Human correction and decision semantics

- [x] Keep semantic corrections in the single `proposal/v0` language: correct `proposal.json`, validate again, then create a fresh review.
- [x] Avoid inventing a second semantic patch language inside the review schema.
- [x] Require every finding to leave `pending` before final acceptance.
- [x] Prove rejected Rules do not enter canonical authoring while the rejection remains recorded.
- [x] Preserve accepted unresolved questions rather than inventing answers.
- [x] Preserve accepted candidate reusable Nodes as separate follow-up artifacts rather than flattening them locally.
- [x] Leave ordinary documentation untouched.
- [x] Keep state/planning findings in reviewed acceptance state rather than deterministically splicing prose into STATE/PLAN.

### Explicit onboarding acceptance

- [x] Add `contextcanon onboard accept` as the explicit operator publication action.
- [x] Reverify frozen evidence against current live repository bytes immediately before publication.
- [x] Refuse stale acceptance when reviewed evidence changed after review.
- [x] Bind a newly generated `existing-source` proposal to exact Source Node ID, name, version, `normalized_digest`, and `package_digest` seen by the LLM.
- [x] Keep legacy v0 proposals structurally readable, but refuse publication of an accepted legacy `existing-source` that lacks exact package identity.
- [x] Require the package supplied at final acceptance to match that exact proposal identity, not merely the same Source Node ID.
- [x] Resolve every accepted `existing-source` to an exact verified immutable package plus explicit visible Source locator.
- [x] Install/pin accepted Source packages exactly and prove normal builds remain offline after the original Source repository is removed.
- [x] Render proposed canonical `CONTEXT.src.md` in a staging Node before publication.
- [x] Stage only frozen reviewed evidence so Topic Markdown closure cannot pull unreviewed local files into the package.
- [x] Compile the staged Node before writing canonical source.
- [x] Preflight the staged compiler's exact first-adoption output paths and refuse to overwrite existing project-owned paths such as `CONTEXT.md` or `CONTEXT/`.
- [x] Create the first canonical `CONTEXT.src.md` only after the staged compile and collision preflight succeed.
- [x] Immediately run normal deterministic build/check after publication.
- [x] Roll back newly created canonical/generated files and newly installed Source packages if first-adoption publication fails before the acceptance record is complete.
- [x] Record `contextcanon/onboarding-acceptance/v0` with evidence/proposal/review identities, decisions, exact Sources and resulting Context/package identities.
- [x] Deliberately refuse replacement when `CONTEXT.src.md` already exists; re-onboarding needs a separate reviewed merge/update contract.

### Regression and documentation completion

- [x] Cover review/acceptance mechanics with focused regression tests.
- [x] Cover stale proposal, stale live evidence, rejected findings, exact reusable Source binding/offline build and unreviewed Markdown closure.
- [x] Cover independent fresh Node identity for identical evidence.
- [x] Cover legacy unbound Source proposals, exact Source-version mismatch, first-adoption output collisions and rollback after acceptance-record publication failure.
- [x] Reach **90 green deterministic tests** before final self-hosted package regeneration; GitHub Actions run #283 confirms the test step is green.
- [x] Update README and onboarding guide through explicit acceptance and final trust-hardening semantics.
- [x] Update STATE/PLAN so the next large step and remaining generated-package/review boundary are explicit.
- [x] Regenerate the affected Gateway and Framework Development self-hosted packages; Foundation remains unchanged.
- [x] Verify the post-regeneration review candidate `22a982d67670444d09d051e4a294785e0a1b5803` with all **90 tests** and `contextcanon check --all .` at zero drift in GitHub Actions run #285.
- [x] Inspect that review candidate against `main`: exactly 21 intended implementation/test/documentation/generated-package paths and no temporary or placeholder files.
- [x] Rewrite the onboarding first-contact section from the user's point of view and introduce Evidence freezing together with its practical benefit.
- [x] Explain the semantic AI step in STATE as useful context sorting rather than leading with an implementation-boundary slogan.
- [x] Promote the four first-adoption trust guarantees into durable Framework Development Rules and architecture documentation.

### Project-owner review correction: repository orientation and development workflow

This block comes directly from the project owner's continuing PR #9 review. Its purpose is to make ContextCanon's own repository demonstrate the same progressive-disclosure and non-duplication principles expected from onboarded projects.

- [x] Record this correction block in `PLAN.md` before changing repository structure or workflow documentation.
- [x] Make authored documentation ownership unambiguous: put reusable/generic guidance with the reusable Node that owns it, framework-internal material with Framework Development, keep generated `CONTEXT/references/` copies clearly identifiable as generated package material, and preserve useful wording/information while removing accidental duplicate maintenance surfaces.
- [x] Correct the reusable Foundation boundary exposed by the first consolidation pass: Foundation-owned Topic resources are authored with Foundation; Framework Development references those resources without becoming their hidden owner or keeping duplicate authored copies.
- [x] Add lightweight in-folder orientation where it materially improves direct browsing, including GitHub-rendered authored-directory READMEs and compiler-generated `CONTEXT/README.md` package orientation without pretending generated files are authored truth.
- [x] Add a Framework Development **Tests and CI** Topic with a short entry summary plus a compact deeper document explaining the deterministic test flow, GitHub Actions runner, generated-drift check/artifact, and how to inspect failures.
- [x] Add an internal development-workflow Context Node for the ContextCanon project and use it to make durable LLM-assisted development rules explicit, including PLAN-before-work and immediate checklist completion as part of each completed step.
- [x] Simplify the correction cadence into separate review-ready and merge-ready gates: coherent authored work may be reviewed with understood/disclosed CI drift; final generated-package regeneration, exact-head green CI and zero drift are required only after project-owner approval and before merge.
- [x] Make short explicit continuations efficient in the current single-developer workflow: when the project owner says to continue after a short pause and reports no intervening repository change, resume from the last established state unless new evidence contradicts it.
- [x] Re-read the moved/consolidated documentation and compare old/new content so no important or especially clear explanation was lost.
- [x] Verify the completed ownership correction before review handoff: exact head `ff0372d6217e2352b671b3429d6883c3fd57ea0f` passed all **92 deterministic/repository tests** in GitHub Actions run #299; the only failure was intentionally stale generated self-hosted package output.
- [x] Prepare PR #9 as a coherent project-owner review candidate without spending another generated-package cycle on a head that may still receive review corrections; known generated drift is explicitly disclosed.
- [x] Update PR #9 description for this project-owner review handoff with the current scope, review order, verification evidence and known technical remainder.

### Final project-owner wording pass before the merge gate

This final review pass polishes the product story and records one additional onboarding-lifecycle use case before the merge candidate is mechanically finalized.

- [x] Record this wording/lifecycle pass in `PLAN.md` before editing the reviewed texts.
- [x] Replace the misleading root Gateway story about "using a bigger context window" with the real observed problem: manually assembled static context drifts, misses details, triggers opportunistic repository searching, and becomes expensive to update across duplicated context copies.
- [x] State the positive ContextCanon model just as briefly: a small dependable overview, deeper detail available on demand, reusable/inherited context with one maintained source, and deterministic propagation to children when rebuilt.
- [x] Replace "dogfood" jargon in current user/developer-facing documentation with plain language such as **self-hosted Context Nodes**, **ContextCanon's own Context**, or **generated self-hosted packages**, while preserving historical meaning.
- [x] Add one short top-level benefit of the README/Node structure: details can live close to the narrow context where they belong without bloating every higher-level overview, while humans and agents still get immediate landing points.
- [x] Record a later **onboarding cleanup / strip-down** workflow: preview exactly which transient ContextCanon onboarding/review artifacts are safe to remove, require explicit human confirmation, and preserve useful canonical/generated Context by default rather than pretending `git reset` is the right recovery mechanism.
- [x] Return the updated authored PR #9 to the project owner for the final large-line check before mechanical merge finalization.

The project owner approved the large-line review and asked for the mechanical completion. Final regeneration had to include all four self-hosted Nodes after the ownership correction; GitHub Actions run #329 on `896d79dd2661b957794fbadf10912de42482d0ef` passed all **92 tests** and `contextcanon check --all .` at zero drift for Gateway, Development Workflow, Framework Development, and Foundation.

- [x] Project-owner review PR #9.
- [x] After explicit project-owner approval, apply any final approved corrections and regenerate only the compiler-owned self-hosted package outputs affected by the final authored state.
- [x] Prove the exact merge candidate with the complete deterministic suite and `contextcanon check --all .` at zero generated drift; GitHub Actions run #330 on `25afc961caab545802e98c42f1716299696816e1` passed all **92 tests** and skipped drift-artifact upload because no drift was found.
- [x] Inspect the final merge candidate against `main` for intended paths and accidental temporary/placeholder files; the 93-path ownership/onboarding diff contains no temporary marker or placeholder path.
- [x] Update PR #9 description with the exact merge-ready head, final test count and self-hosted package identities.
- [x] Squash-merge PR #9 to `main` after project-owner approval and the green merge gate; GitHub records merge commit `f7afe5c82942ecb9e3a04696455f8c960cc9b144`.

## Immediate correction after PR #9 merge: accepted-baseline checkpoint

PR #9 was squash-merged to `main` as `f7afe5c82942ecb9e3a04696455f8c960cc9b144` after the documented green merge gate. The merge exposed a lifecycle gap: the development workflow ended at `squash-merge to main` but did not require an immediate accepted-baseline/state reconciliation. As a result, several repository status surfaces and the historical PR description still described the pre-merge state.

Purpose: restore `main` as a coherent reference point and add the smallest durable procedural guard against repeating this failure. Do not invent a larger product mechanism unless later use proves one necessary.

- [x] Record the post-merge lifecycle finding and this correction block before changing other status/workflow surfaces.
- [x] Reconcile the accepted baseline and post-merge status across `STATE.md`, `PLAN.md`, root `README.md`, and `CHANGELOG.md`, and correct PR #9's description so it reads coherently as a merged historical record.
- [x] Extend ContextCanon Development Workflow with an explicit post-merge accepted-baseline/state checkpoint before the next development block begins; keep the correction procedural unless real use proves deterministic tooling necessary.
- [x] Record for the later real onboarding test the distinction between a project-owned Node-root `README.md`, authored folder landing/orientation README files, and compiler-generated `CONTEXT/README.md`; observe whether folder landing pages should later become an onboarding recommendation or managed feature without overwriting existing project README files.
- [x] After authored context settles, regenerate affected self-hosted Context packages, run the complete deterministic suite and zero-drift check on the exact review head, inspect the diff, and open a review PR without merging; exact head `74489182ce359703a00d821eeb61cc05657f0dd5` passed all **92 tests** and `contextcanon check --all .` at zero drift in GitHub Actions run #336, and the diff against `main` contained exactly 16 intended paths: 9 authored/status surfaces plus 7 deterministic generated-package updates, with no compiler or test-code changes.

## Next major block after PR #9: larger real 1:1 onboarding test

This real-project exercise is deliberately **two tests at once**:

1. **Onboarding process:** Is the prepare → semantic proposal → review → acceptance workflow understandable, comfortable and trustworthy on a materially larger repository?
2. **ContextCanon in actual use:** Once the repository has been onboarded, does the resulting context structure genuinely help humans and agents, and how natural does it feel to clean up scattered project knowledge into the right Nodes, Sources, Rules and Topics?

The second part matters as much as the first. Stable IDs and location-independent Node identity give us the mechanics for reorganizing context, but we have not yet tested the human experience of taking a messy real project and distributing its rules and knowledge into a clean context structure.

### Baseline Source question to test explicitly

**Current behavior:** first onboarding adds no Source automatically. A Source enters the new `CONTEXT.src.md` only when the semantic proposal contains an `existing-source` finding and the human accepts that exact package.

The repository-root **ContextCanon Gateway is not the reusable baseline**: it is intentionally repository-local navigation for the ContextCanon project itself and contains no Sources or Rules. ContextCanon Foundation is the plausible reusable baseline because it contains the common ContextCanon rules and the Node Library already builds on it.

We should not silently turn that plausibility into a framework-wide default immediately before the real test. The test should answer whether a normal onboarding should explicitly offer/recommend Foundation as the starting Source, whether projects should remain fully opt-in, or whether another baseline convention is needed.

Only after the human review/acceptance path is stable and project-owner accepted:

- [ ] Choose a materially larger existing project with meaningful README/CONTRIBUTING/docs and no pre-curated ContextCanon files.
- [ ] Run the framework-generated onboarding assignment through a strong reasoning LLM with access only to frozen evidence plus explicit Source catalog.
- [ ] Do not pre-author the structure from conversation memory.
- [ ] Review especially the split between project-local context and reusable generic Nodes.
- [ ] Explicitly test whether Foundation should be offered/recommended as the default reusable baseline; do not treat the repository Gateway as a reusable Source.
- [ ] Test the practical "cleanup" operation: move/distribute real project guidance into sensible local Nodes, reusable Sources, Rules and Topics while preserving stable identities.
- [ ] Observe whether stable IDs and location-independent Nodes are enough ergonomically when context is split, moved or consolidated, or whether authoring/move assistance is needed.
- [ ] Record where standard documentation was stale or contradicted current implementation.
- [ ] Correct and explicitly accept the proposal through the human workflow.
- [ ] Observe whether `review.json` + rendered evidence is comfortable at real proposal size.
- [ ] Observe whether state/planning findings need additional authoring assistance rather than deterministic prose merge.
- [ ] Build the accepted Node and test ordinary plus Topic-specific tasks through a real harness.
- [ ] Evaluate whether the resulting Context actually improves ordinary work: discoverability, prompt relevance, progressive disclosure and the ability of smaller/local models to work with the right context.
- [ ] Record where the model classified correctly, where humans corrected/rejected it, whether Source reuse reduced duplication, and which context-distribution decisions felt awkward.

## Public repository README hotfix before the real onboarding baseline

GitHub gives `.github/README.md` precedence over the repository-root `README.md` on the repository landing page. The folder-orientation README added for `.github/` therefore hides ContextCanon's actual public project introduction from visitors.

Purpose: remove only that GitHub-specific presentation conflict before tagging/using the accepted baseline for the first materially larger real onboarding test. Keep the broader folder-landing-page question as an empirical finding for that test rather than turning this hosting-specific workaround into a Foundation rule.

- [x] Record this isolated public-README hotfix before changing repository files.
- [x] Rename `.github/README.md` to `.github/ABOUT.md` with identical content so GitHub can render the repository-root `README.md` again.
- [x] Verify `.github/workflows/README.md` remains useful and repository search finds no links depending on `.github/README.md`.
- [x] Run the complete deterministic suite and zero-drift check, inspect the tiny diff, and open a focused review PR without merging; GitHub Actions run #339 on `c61f0f40860366b99dcba5a945c33648ee9fc395` passed all **92 tests** and `contextcanon check --all .` at zero drift, and PR #11 contains only the content-identical rename plus this PLAN checkpoint.

## Active development block: structure-first onboarding on `ai-workstation`

The first materially larger onboarding run on `SomeSunlight/ai-workstation` exposed a more fundamental problem than wording polish: the current onboarding proposal starts at individual semantic findings before the project owner and the model have agreed on the coarse Context structure that should organize those findings. The result can be semantically valid while still feeling flat, over-abstracted and awkward to evolve.

Purpose: keep the existing frozen-Evidence and human-trust boundaries, but split semantic onboarding into two passes. **Pass 1 discovers and reviews the coarse knowledge/context structure; Pass 2 later places existing project knowledge into that accepted structure.** The project owner's mental model is authoritative for the coarse structure. The LLM proposes and explains; it does not get to impose a taxonomy. Good existing wording should normally survive placement rather than being gratuitously rewritten.

This block uses `ai-workstation` as the concrete design pressure. Do not generalize beyond what this repository needs until a second unrelated real project shows the same requirement.

### Part 1 — discover and materialize the coarse structure

- [x] Record the structure-first pivot, concrete `ai-workstation` motivation, human ownership boundary and two-pass intent in `PLAN.md` before implementation changes.
- [x] Define the smallest structure-proposal contract needed for the experiment: candidate local Nodes/grouping Nodes, matches to existing reusable Nodes/Sources when a supplied catalog supports them, non-Node knowledge bodies that should remain Resources/authoritative corpora, parent/child placement, rationale, confidence and exact frozen-Evidence provenance.
- [x] Reuse the existing frozen Evidence and Source-catalog boundary; add a framework-owned **structure-discovery instruction** that asks the strong reasoning LLM to find coarse groups before classifying or rewriting individual Rules.
- [x] Add deterministic validation and digesting for the structure proposal without making semantic correctness a compiler decision.
- [ ] Produce a deliberately simple, human-editable `structure.md` review artifact bound to exact Evidence/proposal identity. Make the hierarchy obvious, keep existing Nodes stable/protected by identity, and allow the project owner to add/rearrange proposed or future/reserved Nodes without editing a large JSON document.
  - [x] Prototype the hierarchy-first Markdown surface with evidence excerpts below it, proposal/evidence binding, re-parenting by indentation, and human-added `[reserved]` Nodes; exact head `fb293b2e472eba48905a7d0c17d218149d0a14d9` passed all **99 tests** and zero generated drift in GitHub Actions run #344.
  - [ ] Exercise existing-Node identity protection against the real already-onboarded `ai-workstation` root before declaring the Markdown review contract complete.
- [ ] Define a narrow deterministic import/normalization contract for edited `structure.md`; avoid a general Markdown AST/editor language. Preserve stable IDs for existing Nodes and allocate fresh human-side identity for newly accepted Nodes only once.
- [ ] Add a preview step that shows exactly which missing Node directories/files would be created from the edited structure before touching the project.
- [ ] Materialize only the accepted **Node skeletons** needed by the structure: minimal `CONTEXT.src.md`/identity plus short human orientation such as a Node-root `README.md` where useful. Future/reserved Nodes may explicitly say that the area is planned and not yet implemented. Do not distribute individual project Rules/Resources in Part 1.
- [ ] Make the structure iteration cheap: if the owner dislikes the result, edit `structure.md` again and regenerate the not-yet-populated missing skeletons deterministically rather than repeating semantic content analysis.
- [ ] Test Part 1 vertically against the real `ai-workstation` shape, including independently deployable/containerized tool areas and at least one grouping Node, and record where the proposed tree needs human correction.

### Part 2 — place the books after the shelves are accepted

Do not implement the full placement/migration semantics before Part 1 has produced a structure the project owner actually likes. The intended next pass is already explicit so Part 1 does not accidentally hard-code the old leaf-first model.

- [ ] Bind the second semantic assignment to both the exact frozen Evidence and the accepted structure identity.
- [ ] Ask the LLM primarily **where existing information belongs**, not to restyle it: distinguish at least keep, move, reference and authority/compliance mapping; preserve good source language by default and record when synthesis is genuinely necessary.
- [ ] Carry every accepted finding durably according to its semantic class; fix the current gap where accepted state/planning semantics can disappear when the original proposal artifact is removed.
- [ ] Let ordinary documentation and larger corpora remain at natural/authoritative locations while Nodes provide progressive-disclosure entry points and mappings into them.
- [ ] Use stable IDs so moved/localized context can be referenced without making file location the semantic identity.
- [ ] Only after a reviewed placement proposal exists, design the cleanup step that removes true duplicate rule text from old locations and leaves useful references/orientation behind.

### Questions this experiment must answer, not assume

- [ ] Does a normal ContextCanon-managed root explicitly offer/recommend Foundation as its baseline Source, and how should that self-explanation appear without mixing ContextCanon infrastructure into the project's domain tree?
- [ ] Is a normal Node sufficient for grouping/"directory" Nodes, including nodes with little local governance, or does real use expose a missing semantic distinction?
- [ ] How should cross-cutting graph relationships be represented without making the human primary navigation cease to look like a simple hierarchy?
- [ ] Which non-Node knowledge-body concepts need first-class representation, if any, beyond today's Resources and Sources? In particular test authoritative standards/policies and large imported documentation corpora before inventing a universal type system.
- [ ] Is constrained Markdown the right human review/edit surface for coarse structure, with JSON remaining the deterministic machine form underneath, or does the round-trip become too fragile?
- [ ] Which atomic CLI commands should remain as the stable automation API, and which repeated onboarding steps later deserve a thin orchestration command or local browser UI? Do not build the UI before the structure workflow has been used end to end.

### Pre-test operator UX hardening from the first `ai-workstation` run

The first real operator run exposed two practical issues that are worth fixing before asking the project owner to repeat the structure experiment: the project development instructions did not preserve the established `uv` installation workflow across chats, and important onboarding Markdown was being created by shell redirection, which is brittle on Windows PowerShell because encoding behavior can make the resulting file unusable in editors.

- [x] Record these operator findings in PLAN before changing development guidance or onboarding output behavior.
- [ ] Make `uv` the preferred ContextCanon development/tool installation path when practical, with `uv tool install --force "git+https://github.com/SomeSunlight/context-canon.git@<ref>"` as the normal Windows/PowerShell development pattern; keep the guidance cross-platform and do not make PowerShell or Windows a framework requirement.
- [ ] Add one visible human-facing onboarding workspace with a collision-safe ContextCanon marker and standard filenames instead of mixing editable LLM/review artifacts into the repository root or hiding them under `.context/`.
- [ ] Keep `.context/onboarding/<digest>/` as the immutable machine Evidence/review anchor, while explaining in the visible workspace README why frozen Evidence lets semantic/review work resume and iterate without silently changing its project basis.
- [ ] Make the structure-discovery instruction write UTF-8 directly to its standard workspace file by default, avoiding shell capture; retain an explicit stdout mode for scripting/harnesses.
- [ ] Let the new structure validate/review commands use standard workspace paths by default while retaining explicit path overrides for automation and unusual layouts.
- [ ] Cover workspace ownership/collision behavior, exact UTF-8 writes, standard-path CLI flow, and explicit stdout/path overrides with deterministic tests on the platform-independent Python layer.
