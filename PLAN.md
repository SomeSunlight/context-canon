# Plan

## How to read "accepted" in this plan

Two different ideas use similar words and should not be confused:

- **Project-owner accepted** means the project owner, acting as ContextCanon's first user/reviewer, reviewed a development stage and approved it as the new project baseline.
- **`source accept` / `onboard accept`** are product operations performed by an explicit human operator on one concrete reviewed Source candidate or onboarding proposal.

No anonymous system, CI job, or LLM "accepts" project truth.

## Project-owner accepted baseline

ContextCanon has passed self-hosted and real external-project validation. The current accepted `main` baseline includes Compiler 0.4 plus the first user-reviewed onboarding and usability-hardening slices through PR #8:

`1280aa9e763f0588fa06b3e1e98b9e7b52302cdd`

Validated foundations include:

- [x] Gateway, Foundation, and Framework Development as real self-hosted Context Nodes.
- [x] Deterministic compiler and generated drift checking.
- [x] `SomeSunlight/teams-chat-exporter` external experiment.
- [x] Real GitHub Copilot entry through generated `AGENTS.md`.
- [x] Ordinary versus Topic-specific progressive disclosure.
- [x] Inherited Rule `Remove`/`Override`, transitive provenance, and diamond-conflict diagnostics.
- [x] Deterministic Context diff and semantic normalization.
- [x] Immutable external Sources, reviewed Source updates, generic Git candidate transport, and atomic publication/recovery.
- [x] Deterministic onboarding evidence preparation, framework-owned LLM assignment and strict proposal validation.
- [x] First-user onboarding documentation hardening, explicit actors, strong-reasoning-model guidance and stale-evidence handling.

The development cadence is now deliberately split between human review and mechanical merge finalization:

> complete one coherent block → make the large line reviewable and disclose known CI/drift → project-owner review → after approval finalize self-hosted generated packages/cleanup → exact-head fully green + zero drift → squash-merge to `main` → start the next block on a fresh branch.

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

- [x] Define `contextcanon/onboarding-proposal/v0` separately from Official Context.
- [x] Require each item to carry rationale, confidence and exact evidence hash/line-range references.
- [x] Strictly validate kinds, payloads, evidence file set, hashes/ranges and deterministic `proposal_digest`.
- [x] Revalidate the Evidence v0 safety policy when consuming a snapshot.

## Current review candidate: human review and explicit onboarding acceptance

PR #9 / branch `agent/onboarding-review-acceptance` implements the next actor: the **human reviewer/operator**. A validated LLM proposal is not yet project truth.

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
- [x] Stage only frozen reviewed evidence so Topic Markdown closure cannot pull unreviewed local files into the accepted package.
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
- [ ] Replace the misleading root Gateway story about "using a bigger context window" with the real observed problem: manually assembled static context drifts, misses details, triggers opportunistic repository searching, and becomes expensive to update across duplicated context copies.
- [ ] State the positive ContextCanon model just as briefly: a small dependable overview, deeper detail available on demand, reusable/inherited context with one maintained source, and deterministic propagation to children when rebuilt.
- [ ] Replace "dogfood" jargon in current user/developer-facing documentation with plain language such as **self-hosted Context Nodes**, **ContextCanon's own Context**, or **generated self-hosted packages**, while preserving historical meaning.
- [ ] Add one short top-level benefit of the README/Node structure: details can live close to the narrow context where they belong without bloating every higher-level overview, while humans and agents still get immediate landing points.
- [ ] Record a later **onboarding cleanup / strip-down** workflow: preview exactly which transient ContextCanon onboarding/review artifacts are safe to remove, require explicit human confirmation, and preserve useful canonical/generated Context by default rather than pretending `git reset` is the right recovery mechanism.
- [ ] Return the updated authored PR #9 to the project owner for the final large-line check before mechanical merge finalization.

- [ ] Project-owner review PR #9.
- [ ] After explicit project-owner approval, apply any final approved corrections and regenerate only the compiler-owned self-hosted package outputs affected by the final authored state.
- [ ] Prove the exact merge candidate with the complete deterministic suite and `contextcanon check --all .` at zero generated drift.
- [ ] Inspect the final merge candidate against `main` for intended paths and accidental temporary/placeholder files.
- [ ] Update PR #9 description with the exact merge-ready head, final test count and self-hosted package identities.
- [ ] Squash-merge PR #9 to `main` only after project-owner approval and the green merge gate.

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

## Later semantic refinement: important context hidden in source code

Do **not** expand the first bootstrap into a blind whole-repository source scan.

Instead, after a project already has coarse accepted ContextCanon context, investigate a second semantic pass that can use that context to find high-value information hidden in human-written source comments/docstrings.

- [ ] Scan source in bounded Node/directory-sized areas rather than whole large repositories at once.
- [ ] Look specifically for design invariants, non-obvious constraints, compatibility reasons, architectural decisions and warnings — not routine implementation comments.
- [ ] Evaluate findings against already accepted local Rules, Topics and reusable Sources so duplicates can be discarded.
- [ ] Keep exact source path/hash/line provenance for every proposed extraction.
- [ ] Require human review before centralizing any discovered context.
- [ ] Consider optional stable references from source comments back to ContextCanon Rule/Topic IDs after those identities exist.
- [ ] Test whether this second pass improves documentation freshness without turning ContextCanon into source-code indexing or indiscriminate prompt expansion.

## Later onboarding/update refinement

The first acceptance path deliberately creates a new Node only.

- [ ] Design a reviewed re-onboarding/update workflow for repositories that already contain canonical ContextCanon context.
- [ ] Compare new semantic findings against existing Rules/Sources/Topics/state instead of replacing `CONTEXT.src.md` wholesale.
- [ ] Preserve stable identities across reviewed updates.
- [ ] Make conflicts between current canonical context and new evidence visible before publication.
- [ ] Design a non-destructive onboarding cleanup/strip-down command for experiments, retries and version upgrades: show a deterministic **Ready to delete** list of transient onboarding/review artifacts, require explicit human confirmation, and preserve useful canonical/generated Context and nested Context Nodes by default. A deeper destructive reset, if ever added, must be a separate explicit operation.

## Later deterministic layers

### Protected Rules and authorized exceptions

- [ ] Mark selected Rules protected at their owner.
- [ ] Reject ordinary Remove/Override against protected Rules.
- [ ] Define stable authorized exceptions and explicit `Use Exception` in consumers.
- [ ] Preserve exception provenance and reject dangling/invalid exception use.

### Broader hardening

- [ ] Topic composition/materialization across Source package boundaries.
- [ ] Resource collision policy across composed packages.
- [ ] Richer nested Git/repository boundary cases.
- [ ] Safe compiler-owned generated-file manifests where needed.
- [ ] Authoring assistance beyond the reviewed onboarding workflow.

## Semantic layers above exact compiler artifacts

A later high-level impact workflow remains:

```text
exact Context / Source diff
        ↓
external reasoning LLM impact review
        ↓
Rule ID → affected code / config / tests / docs
        ↓
reason → proposed action → explicit human approval
```

This remains harness-neutral and outside deterministic compiler truth.

## Working rule

**Build exact mechanics deterministically, make semantic AI steps explicit and replaceable, name the human who decides durable truth, then use each stable stage aggressively.**