# Plan

## How to read "accepted" in this plan

Two different ideas use similar words and should not be confused:

- **Project-owner accepted** means the project owner, acting as ContextCanon's first user/reviewer, reviewed a development stage and approved it as the new project baseline.
- **`source accept` / onboarding acceptance** are product operations performed by an explicit human operator on one candidate Source or one reviewed onboarding proposal.

No anonymous system, CI job, or LLM "accepts" project truth.

## Project-owner accepted baseline

ContextCanon has passed self-hosted and real external-project validation. The project owner accepted **Compiler 0.4** as the deterministic compiler baseline after review and squash-merge.

Validated foundations include:

- [x] Gateway, Foundation, and Framework Development as real dogfood Nodes.
- [x] Deterministic compiler and generated drift checking.
- [x] `SomeSunlight/teams-chat-exporter` external experiment.
- [x] Real GitHub Copilot entry through generated `AGENTS.md`.
- [x] Ordinary versus Topic-specific progressive disclosure.
- [x] Inherited Rule `Remove`/`Override`, transitive provenance, and diamond-conflict diagnostics.
- [x] Deterministic Context diff and semantic normalization.
- [x] Immutable external Sources, reviewed Source updates, generic Git candidate transport, and atomic publication/recovery.

The development cadence remains:

> complete one coherent block → regenerate dogfood → make CI fully green → project-owner review → squash-merge to `main` → start the next block on a fresh branch.

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
- [x] Preserve unpinned local Sources as the simple development/dogfood case.
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

The project owner reviewed the onboarding implementation and user-facing documentation as ContextCanon's first user. PR #7 was then squash-merged to `main` as:

`275c6b1f121126fb117f4bdbff1efc18218b0528`

The implemented flow is:

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

## Active next block: human review and explicit onboarding acceptance

The next actor is the **human reviewer/operator**. A validated LLM proposal is not yet project truth.

Goal: turn `proposal.json` into an inspectable, correctable review experience and require an explicit human decision before canonical ContextCanon authoring changes.

- [ ] Design the human-readable review representation for a validated proposal.
- [ ] Show every proposed classification next to its exact evidence and confidence.
- [ ] Allow a human reviewer to correct or reject classifications without editing raw JSON blindly.
- [ ] Preserve unresolved questions and candidate reusable Nodes rather than flattening them.
- [ ] Require explicit human acceptance before canonical `CONTEXT.src.md` or related authored context is created/replaced.
- [ ] Bind acceptance to the exact validated proposal/evidence state so stale approval cannot apply to changed input.
- [ ] Immediately run normal deterministic ContextCanon validation/build after accepted authoring is produced.
- [ ] Keep candidate reusable-Node extraction separately reviewable/versioned; onboarding must never auto-publish it.

## Larger real 1:1 onboarding test

Only after the human review/acceptance path is stable:

- [ ] Choose a materially larger existing project with meaningful README/CONTRIBUTING/docs and no pre-curated ContextCanon files.
- [ ] Run the framework-generated onboarding assignment through a strong reasoning LLM with access only to frozen evidence plus explicit Source catalog.
- [ ] Do not pre-author the structure from conversation memory.
- [ ] Review especially the split between project-local context and reusable generic Nodes.
- [ ] Record where standard documentation was stale or contradicted current implementation.
- [ ] Correct and explicitly accept the proposal through the new human workflow.
- [ ] Build it and test ordinary plus Topic-specific tasks through a real harness.
- [ ] Record where the model classified correctly, where humans corrected it, and whether Source reuse reduced duplication.

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
