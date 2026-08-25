# Current State

ContextCanon now has a stable deterministic core and an onboarding workflow that reaches from an existing Git repository to **human-reviewed, explicitly accepted canonical Context**.

The project owner, acting as ContextCanon's first user and reviewer, accepted the latest usability-hardening slice and PR #8 was squash-merged to `main` as:

`1280aa9e763f0588fa06b3e1e98b9e7b52302cdd`

The current branch / PR #9 adds the last major onboarding trust step before the larger real-project test: human review plus explicit onboarding acceptance.

> [!NOTE]
> In this file, **project-owner accepted** means that the project owner reviewed a development stage and approved it as the new project baseline. That is different from the product operations `contextcanon source accept` and `contextcanon onboard accept`, where a human operator explicitly accepts one concrete reviewed artifact.

## In one minute

Today the current development branch can:

- compile Context Nodes deterministically;
- compose reusable immutable Sources with exact identities;
- review and explicitly accept Source updates without hidden network access during normal builds;
- keep project entry context small and route deeper context through Topics;
- freeze exact evidence from an existing Git repository;
- generate the exact semantic assignment for an external reasoning LLM;
- validate the LLM's returned `proposal.json` against exact frozen evidence;
- create a human review bound to that exact proposal;
- show each finding together with rationale, confidence and exact cited evidence lines;
- require an explicit `accept` or `reject` decision for every finding;
- reject stale review when the proposal or live evidence changed;
- stage and compile the proposed first Context Node before publication;
- publish the first canonical `CONTEXT.src.md` only after explicit human acceptance;
- immediately run the normal deterministic build/check after publication.

The workflow deliberately still does **not**:

- let an LLM publish project truth;
- turn candidate reusable Nodes into library Nodes automatically;
- invent answers for unresolved questions;
- splice state/planning prose into existing human documents by pretending text merging is deterministic semantics;
- overwrite an existing `CONTEXT.src.md` during first-onboarding acceptance v0.

The next major step after project-owner review of PR #9 is therefore no longer another missing onboarding mechanism. It is the **larger real 1:1 onboarding test**.

## How onboarding works now

Only one step requires semantic AI:

```text
[ContextCanon · deterministic]
freeze exact repository evidence
        ↓
[ContextCanon · deterministic]
generate the semantic assignment
        ↓
[External reasoning LLM · semantic]
classify the frozen evidence
return one proposal.json
        ↓
[ContextCanon · deterministic]
validate JSON structure and provenance
        ↓
[ContextCanon + Human]
render each finding with exact evidence
record accept/reject decisions
        ↓
[Human · explicit action]
contextcanon onboard accept
        ↓
[ContextCanon · deterministic]
stage → compile → publish → build/check
```

ContextCanon does not choose or call the model. The operator supplies the generated assignment and frozen evidence to a suitable external LLM.

The onboarding task is semantically difficult. The documentation explicitly recommends a **strong reasoning-capable model**. A weak model can return perfectly valid JSON while making poor distinctions between durable Rules, ordinary documentation, temporary state, reusable conventions and unresolved contradictions.

## What human review adds

A validated LLM proposal is still untrusted semantic interpretation.

`contextcanon onboard review` creates a separate `contextcanon/onboarding-review/v0` artifact bound to the exact `proposal_digest` and `evidence_digest`. Every proposal item starts `pending`.

The reviewer sees each item together with:

- classification and confidence;
- LLM rationale and proposed payload;
- exact evidence path/hash/line range;
- the cited evidence lines themselves.

The human must change every decision to `accept` or `reject`. If the semantic finding itself is wrong, the proposal is corrected and validated again. Because that changes `proposal_digest`, the old review no longer applies.

Node name/ID/version are human-owned review state rather than something the LLM can silently make canonical.

## What explicit acceptance guarantees

`contextcanon onboard accept` refuses publication unless the review is complete and still matches the exact proposal/evidence.

Immediately before publication it also rechecks the frozen evidence against the current live repository. If a reviewed README, manifest, CI file, architecture document or other selected evidence changed after review, acceptance stops and a new evidence/review cycle is required.

The proposed Context Node is first compiled in a staging area containing only reviewed evidence. This has an important consequence: a reviewed Markdown Topic resource cannot use a local link to smuggle an unreviewed file into the eventual Context package. If the normal Markdown-resource closure needs a file outside frozen evidence, staging compile fails before canonical source is published.

Accepted local Rules and Topics become canonical authoring. Rejected findings do not. Ordinary documentation stays ordinary documentation.

Accepted candidate reusable Nodes and unresolved questions remain separate reviewed follow-up artifacts instead of being flattened into local Rules or invented answers.

Accepted `existing-source` findings must be resolved again at final acceptance to exact immutable Source packages plus explicit visible locators. The packages are verified, installed in accepted local state and pinned by both digests; the resulting project continues to build offline after the original Source repository disappears.

Initial acceptance v0 deliberately refuses to replace an existing `CONTEXT.src.md`. Re-onboarding an already adopted project needs its own reviewed merge/update contract.

## Evidence is not automatically truth

The first onboarding pass selects likely context carriers such as README, CONTRIBUTING, architecture/development documents, manifests, CI configuration and agent instructions. Ordinary source code is not automatically included.

Those files may disagree or be stale. The generated LLM assignment therefore says:

- no conventional filename is automatically authoritative;
- for claims about **current implemented behavior**, direct implementation/configuration/manifest/CI/test evidence has more weight when it clearly contradicts descriptive documentation;
- documentation and meaningful source comments remain important evidence for intent, rationale, constraints, workflow, history and target design;
- unclear "is versus should become" conflicts must remain visible as unresolved questions or planning state.

This is implementation-first for current-state claims, not a blanket rule that source code is always correct.

## What the project owner has accepted as stable

The project owner has reviewed and accepted these development stages as the current `main` baseline:

- [x] deterministic Context Node compiler and generated drift checking;
- [x] progressive disclosure through compact `CONTEXT.md` plus Topics;
- [x] stable Node/Rule identity and inherited Rule Remove/Override;
- [x] immutable external Source packages and offline normal builds;
- [x] deterministic Source candidate diff/review plus explicit operator acceptance;
- [x] generic Git candidate transport;
- [x] deterministic onboarding evidence preparation;
- [x] framework-owned, harness-neutral onboarding instruction;
- [x] strict provenance-rich onboarding proposal validation;
- [x] user-facing onboarding walkthrough and Gateway discoverability;
- [x] local Node `Overview` for concise orientation without turning prose into inherited governance;
- [x] first-user review hardening: explicit actors, strong-LLM guidance, stale-document handling, readable STATE and separate contribution paths.

The currently merged baseline is PR #8 at `1280aa9e763f0588fa06b3e1e98b9e7b52302cdd`.

## Current review candidate: explicit onboarding acceptance

PR #9 implements the human review/acceptance block above the merged baseline.

The executable path currently passes **84 deterministic tests**. Coverage includes:

- pending review decisions;
- exact evidence rendering;
- stale proposal/review rejection;
- changed live evidence rejection;
- first canonical Rule/Topic publication;
- rejected findings remaining rejected and recorded;
- candidate reusable Node and unresolved-question preservation;
- exact reusable Source package binding and offline post-accept build;
- refusal to overwrite existing `CONTEXT.src.md`;
- refusal to package Markdown-linked material that was outside frozen review evidence.

Before the documentation changes in this branch, GitHub Actions run #267 also passed `contextcanon check --all .` with zero drift. The final branch still needs its normal documentation dogfood regeneration and exact-head green CI before project-owner review.

## What comes next

After this block is complete and project-owner accepted, ContextCanon should be used on a **materially larger existing project** with no pre-curated ContextCanon files.

That test should exercise the whole real path:

1. deterministic evidence preparation;
2. framework-owned assignment;
3. strong reasoning LLM;
4. deterministic proposal validation;
5. human review with real corrections/rejections;
6. explicit acceptance;
7. normal ContextCanon build;
8. ordinary and Topic-specific work through a real harness.

The interesting questions should now be semantic/product questions rather than missing trust mechanics: What did the LLM classify badly? Which context was stale? Which information should become shared Sources? Which state/planning findings need better authoring assistance? Was the review representation pleasant enough on a real-sized proposal?

## Later refinement: context hidden in source code

A later refinement should investigate a **second-pass source scan after initial ContextCanon adoption**.

Human-written comments and docstrings can contain unusually valuable design information: module invariants, reasons for strange constraints, compatibility decisions, and warnings that never made it into README or architecture documents.

The preferred direction is not to feed all source code into the first bootstrap. Instead:

1. establish the coarse ContextCanon structure first;
2. scan source in bounded Node/directory-sized areas;
3. use already accepted Rules, Topics and Sources as context for interpreting comments;
4. propose only high-value context that should be centralized;
5. keep exact source provenance and human review;
6. later consider explicit references from source comments back to stable ContextCanon Rule/Topic IDs where that improves traceability.

This should remain a semantic refinement workflow, not a new reason to preload an entire repository.

## Where to look next

- [README.md](README.md) — product overview and first-user entry.
- [docs/onboarding.md](docs/onboarding.md) — complete onboarding walkthrough and technical contract.
- [CONTRIBUTING.md](CONTRIBUTING.md) — separate paths for framework work and reusable Node contributions.
- [PLAN.md](PLAN.md) — completed stages and ordered next work.
- [CONTEXT.md](CONTEXT.md) — compact official project context and task routing.
