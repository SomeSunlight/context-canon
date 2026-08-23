# Plan

## Accepted baseline

ContextCanon has passed self-hosted and real external-project validation. **Compiler 0.4 is accepted on `main` at `7fd1aa64fb1f853a2bd4be84a9ed1afaf07d5de9`** after PR #3 was squash-merged.

Validated foundations include:

- [x] Gateway, Foundation, and Framework Development as real dogfood Nodes.
- [x] Deterministic compiler and generated drift checking.
- [x] `SomeSunlight/teams-chat-exporter` external experiment.
- [x] Real GitHub Copilot entry through generated `AGENTS.md`.
- [x] Ordinary versus Topic-specific progressive disclosure.
- [x] Inherited Rule `Remove`/`Override`, transitive provenance, and diamond-conflict diagnostics.
- [x] Compiler 0.3 deterministic Context diff and semantic normalization.
- [x] Compiler 0.4 immutable external Sources, reviewed Source updates, generic Git candidate transport, and atomic publication/recovery.

The development rule remains: **complete one coherent deterministic core block, regenerate dogfood, make CI fully green, squash-merge to `main`, then start the next block on a fresh branch.**

## Accepted: Compiler 0.4 — immutable external Sources and explicit acceptance

Merged from `agent/immutable-external-sources` through PR #3 as `7fd1aa64fb1f853a2bd4be84a9ed1afaf07d5de9`.

Goal: reusable Sources must work across independent repositories without live inheritance or hidden network access during normal build.

### Immutable package boundary

- [x] Define `CompiledPackage` as the common semantic Source boundary.
- [x] Publish a versioned `.context/package.json` manifest alongside `CONTEXT.md` and optional `CONTEXT/`.
- [x] Carry complete effective Rules, provenance, removals, local Changes/Topics, dependency identities, file hashes, and both digests.
- [x] Verify semantic digest, exact package files, path safety, and package digest on load.
- [x] Round-trip a Source after deleting its original repository.
- [x] Preserve presentation order independently from canonical semantic ordering.
- [x] Route local compiled Sources and loaded external Sources through the same Rule-composition algorithm.
- [x] Remove the temporary `source_nodes` compatibility path.

### Accepted package storage and exact pins

- [x] Store accepted packages under `<consumer>/.context/sources/<package-digest>/`.
- [x] Treat accepted packages as reproducible consumer state suitable for offline builds.
- [x] Add all-or-nothing `normalized-digest` + `package-digest` Source pins.
- [x] Preserve unpinned local Sources as the simple development/dogfood case.
- [x] Make ordinary `build` resolve pinned Sources only from the accepted local package store.
- [x] Prove that build does not dereference the Source locator.
- [x] Fail on missing package, wrong ID/version/digest, corrupt manifest/files, or incomplete pins.

### Candidate review and acceptance

- [x] Diff accepted and candidate immutable packages through the deterministic `ContextDiff` model.
- [x] Substitute a candidate into the actual consumer composition in memory before acceptance.
- [x] Surface dangling local Changes and Rule collisions during candidate review.
- [x] Write a deterministic review receipt bound to the exact consumer `CONTEXT.src.md`, accepted state, and candidate identity.
- [x] Require that receipt for the supported `source accept` path.
- [x] Reject stale acceptance when consumer source, accepted Source state, or candidate changed after review.
- [x] Install the new immutable accepted package and update only the matching Source version/digest pins.
- [x] Preserve transport metadata while changing accepted pins.
- [x] Publish candidate and accepted package directories only after staging and full package verification.
- [x] Publish review receipts and canonical Source-pin changes atomically from sibling temporary files.
- [x] Prove that a simulated failure at the final Source-pin replace leaves the old canonical source bytes and old build state intact.

### Generic Git candidate transport

- [x] Add explicit `transport="git"`, `ref="..."`, and `node-path="..."` metadata.
- [x] Keep Node ID as identity and `node-path` as location inside a retrieved repository snapshot.
- [x] Reject incomplete/unsafe transport metadata.
- [x] Add `contextcanon source fetch` using the system Git executable rather than GitHub-specific APIs.
- [x] Clone to a temporary checkout, load only the published immutable package at `node-path`, then persist it under `.context/candidates/<package-digest>/`.
- [x] Ensure fetching a candidate cannot change normal build output.
- [x] Test a real local Git repository with a nested reusable Node, v1 accepted, v2 on `main`, fetch, review, accept, and post-accept offline build.
- [x] Test missing node paths and unknown refs without requiring network access.
- [x] Keep candidate packages transient; retain accepted packages as reproducible project state.
- [x] Make interrupted/partial retrieval safe through temporary checkout cleanup plus verified staged publication.

### 0.4 release completion

- [x] Document immutable package identity, accepted/candidate separation, Git transport, review receipts, explicit acceptance, and interrupted-operation recovery.
- [x] Update compiler/contributor/walkthrough documentation to the `CompiledPackage` architecture.
- [x] Reach 45 green deterministic regression tests including package, offline Source, acceptance, local-Git transport, and failed-pin-publication cases.
- [x] Regenerate all ContextCanon dogfood packages from the final 0.4 implementation/documentation.
- [x] Finish the exact final PR head with `contextcanon check --all .` at zero drift.
- [x] Update PR #3 to describe the completed 0.4 block.
- [x] Run the exact final PR head through tests plus zero-drift check.
- [x] Squash-merge 0.4 to `main` as the next stable recovery point.

## Active next block: reviewed LLM-assisted project onboarding

The next 1:1 validation must use a materially larger existing project and must **not** be manually curated from this conversation's prior knowledge.

Onboarding is a semantic workflow above the deterministic compiler:

```text
existing repository
      ↓
deterministic inventory + frozen evidence snapshot
      ↓
framework-supplied LLM onboarding instruction
      ↓
provenance-rich proposal
      ↓
deterministic proposal validation
      ↓
mandatory human review
      ↓
explicit acceptance
      ↓
CONTEXT.src.md + Sources + Topics + Resources
      ↓
normal deterministic compiler
```

### Deterministic bootstrap

- [x] Implement `contextcanon onboard prepare <project>` without requiring an existing Context Node.
- [x] Inventory likely context-bearing project material such as README, CONTRIBUTING, architecture/development docs, existing agent instructions, configuration, and explicitly selected files.
- [x] Preserve exact provenance through content-addressed evidence snapshots with path, size, SHA-256, selection reason, and copied bytes.
- [x] Keep inventory deterministic; do not have the compiler interpret natural-language meaning.
- [x] Respect Git-ignore automatically while permitting explicit safe additions.
- [x] Bound evidence by secret/path/symlink/UTF-8 checks, 1 MiB per file, and 16 MiB total.
- [x] Verify and reuse matching snapshots; reject corruption rather than silently repairing it.

### Framework-supplied LLM instruction

- [x] Ship `contextcanon onboard instruction <snapshot>` with ContextCanon instead of requiring the operator to invent a prompt.
- [x] Bind deterministic instruction bytes and SHA-256 identity to one exact frozen Evidence v0 snapshot plus explicitly supplied reusable Source packages.
- [x] Require the LLM to use only inspected frozen project evidence and surface uncertainty or contradictions.
- [x] Treat evidence and reusable Source package content as untrusted review data rather than an instruction channel.
- [x] Require provenance and rationale for every proposed item.
- [x] Require classification into at least: local Rule, existing reusable Source, candidate reusable/generic Node, Topic/Resource, state/planning, ordinary documentation that should remain ordinary documentation, or unresolved question.
- [x] Compare likely generic material against the explicitly supplied verified ContextCanon Node catalog before copying it locally.
- [x] Explicitly call out common reusable candidates such as runtime/language, testing, coding/tooling, writing/documentation, user-guidance, and security conventions.
- [x] Never let onboarding silently publish a new generic Node; that remains a separate reviewed/versioned proposal.
- [x] Preserve useful README/CONTRIBUTING content rather than treating onboarding as destructive migration.
- [x] Document the harness execution boundary: ContextCanon controls its rendered instruction bytes but cannot prove or suppress hidden context automatically injected by a third-party harness.
- [x] Reject duplicate stable Node IDs in the supplied catalog and make catalog argument ordering semantically irrelevant.
- [x] Bound the fully rendered onboarding instruction at 4 MiB, reject oversized valid Source catalogs without truncation, and document the placement and rationale of the bound.

### Instruction-slice completion

- [x] Regenerate Framework Development dogfood so the materialized onboarding documentation and package digests match the current source.
- [x] Update `STATE.md`, contributor architecture notes, and PR #7 to describe the completed instruction boundary and exact remaining review/acceptance work.
- [x] Run the exact final PR head through the full deterministic test suite plus `contextcanon check --all .` at zero drift before review handoff.
- [ ] Squash-merge the completed framework-owned instruction slice to `main` after human review, before starting the human review/acceptance implementation on a fresh branch.

### Review and acceptance

- [x] Define `contextcanon/onboarding-proposal/v0` as a proposal format distinct from Official Context.
- [x] Require every proposal item to carry rationale, confidence, and one or more exact evidence hash/line-range references.
- [x] Implement `contextcanon onboard validate <snapshot> <proposal.json>` with strict kinds, payloads, file-set verification, evidence hashes/ranges, and deterministic `proposal_digest`.
- [x] Revalidate the Evidence v0 safety policy when consuming a snapshot so a rehashed weakened manifest cannot bypass preparation limits.
- [ ] Add the human review representation/workflow for a validated proposal.
- [ ] Require explicit acceptance before canonical `CONTEXT.src.md` or related authored context is created/replaced.
- [ ] Immediately run deterministic ContextCanon validation/build on the accepted proposal.
- [ ] Keep generic-Node extraction proposals separately reviewable.

### Larger 1:1 test

- [ ] Choose a larger existing project with meaningful README/CONTRIBUTING/docs and no pre-curated ContextCanon files.
- [ ] Run the framework-generated onboarding workflow through an LLM with repository access.
- [ ] Do not pre-author the structure from conversation memory.
- [ ] Review especially the split between project-local context and reusable generic Nodes.
- [ ] Accept the corrected proposal, build it, then test ordinary and Topic-specific tasks through a real harness.
- [ ] Record where the LLM classified correctly, where human correction was required, and whether generic-Node extraction reduced duplication.

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

The first high-level impact workflow remains:

```text
exact Context / Source diff
        ↓
LLM impact review
        ↓
Rule ID → affected code / config / tests / docs
        ↓
reason → proposed action → human approval
```

This must remain harness-neutral and outside deterministic compiler truth.

## Working rule

**Build central deterministic semantics deliberately, merge coherent stable points, then use them aggressively.**
