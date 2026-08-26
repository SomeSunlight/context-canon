# Current State

ContextCanon has a stable deterministic core and now, on the current review branch, a complete first-adoption path from an existing Git repository to **human-reviewed, explicitly accepted canonical Context**.

The project owner, acting as ContextCanon's first user and reviewer, accepted the latest usability-hardening slice and PR #8 was squash-merged to `main` as:

`1280aa9e763f0588fa06b3e1e98b9e7b52302cdd`

PR #9 / branch `agent/onboarding-review-acceptance` is the current review candidate. It adds the last major onboarding trust step before the larger real-project test: human review plus explicit onboarding acceptance.

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
- bind a proposed reusable Source to the **exact immutable package** the semantic reviewer inspected;
- stage and compile the proposed first Context Node before publication;
- refuse first adoption when it would overwrite existing ContextCanon output paths;
- publish the first canonical `CONTEXT.src.md` only after explicit human acceptance;
- roll back a failed first publication rather than leave a half-adopted repository;
- immediately run the normal deterministic build/check after publication.

The workflow deliberately still does **not**:

- let an LLM publish project truth;
- turn candidate reusable Nodes into library Nodes automatically;
- invent answers for unresolved questions;
- splice state/planning prose into existing human documents by pretending text merging is deterministic semantics;
- replace an existing `CONTEXT.src.md` during first-onboarding acceptance v0;
- silently substitute a different version of a reusable Source after semantic review.

The next major step after project-owner review of PR #9 is therefore no longer another missing onboarding mechanism. It is the **larger real 1:1 onboarding test**.

## How onboarding works now

Onboarding uses a strong reasoning AI as a **semantic sorting assistant** for one bounded step. That is useful because an existing repository rarely presents its context in clean ContextCanon categories: durable rules may be mixed with README prose, configuration, CI, temporary plans, architecture decisions, reusable conventions and contradictions.

Deterministic code is very good at freezing and verifying exact bytes, but it cannot reliably decide what those scattered human artifacts *mean*. The reasoning model therefore proposes a structure: what looks like durable project governance, what belongs in a deeper Topic, what may be reusable across projects, what should remain ordinary documentation, and what is still unresolved. ContextCanon then binds that proposal back to exact evidence, and a human decides what is actually accepted.

```text
[ContextCanon · deterministic]
freeze exact repository evidence
        ↓
[ContextCanon · deterministic]
generate the semantic assignment
        ↓
[External reasoning LLM · semantic]
classify and organize the frozen evidence
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
preflight → stage → compile → publish → build/check
```

The AI is therefore not there merely because ContextCanon is an AI-related tool. It performs the part that benefits from semantic comparison across messy project material; deterministic ContextCanon performs the integrity and publication mechanics around it.

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

Node name/ID/version are human-owned review state rather than something the LLM can silently make canonical. If the human does not provide `--node-id`, ContextCanon creates a fresh UUID once when it creates the review. That identity is stored in `review.json`; it is deliberately not derived from evidence bytes, because unrelated projects can contain identical evidence.

## What explicit acceptance guarantees

`contextcanon onboard accept` refuses publication unless the review is complete and still matches the exact proposal/evidence.

Immediately before publication it rechecks the frozen evidence against the current live repository. If a reviewed README, manifest, CI file, architecture document or other selected evidence changed after review, acceptance stops and a new evidence/review cycle is required.

The proposed Context Node is first compiled in a staging area containing only reviewed evidence. A reviewed Markdown Topic resource therefore cannot use a local link to smuggle an unreviewed file into the eventual Context package. If normal Markdown-resource closure needs a file outside frozen evidence, staging compile fails before canonical source is published.

Accepted local Rules and Topics become canonical authoring. Rejected findings do not. Ordinary documentation stays ordinary documentation.

Accepted candidate reusable Nodes and unresolved questions remain separate reviewed follow-up artifacts instead of being flattened into local Rules or invented answers.

### Reusable Sources stay bound to what was actually reviewed

When a reusable Source catalog is supplied to the semantic review, the generated instruction exposes stable Node ID/name plus exact version, normalized digest and package digest.

New `existing-source` findings must carry that exact package identity. Final acceptance requires the operator to supply the same immutable package again. ContextCanon compares Node ID, name, version and both digests; another version of the same Node is rejected rather than silently replacing what the LLM and human reviewed.

Historical `proposal/v0` files without those exact identity fields remain structurally readable, but an unbound `existing-source` cannot be accepted into canonical context. It must be corrected/regenerated and reviewed again.

After successful acceptance, the package is installed in accepted local state and pinned exactly. The resulting project continues to build offline after the original Source repository disappears.

### First adoption does not seize existing project files

Before live publication, ContextCanon uses the staged compile to determine the exact generated output set for the proposed Node.

If one of those output paths already exists, first adoption refuses to overwrite it. Any existing `CONTEXT/` path is also a hard stop because that tree is compiler-owned resource output and normal builds may clean stale generated resources from it.

This is based on actual outputs, not a blanket filename blacklist. An existing `AGENTS.md`, for example, may remain normal project evidence when the proposed Node does not generate an `AGENTS.md` target.

An existing `CONTEXT.src.md` remains a separate hard stop: re-onboarding needs its own reviewed merge/update contract.

### Failed first publication is rolled back

After the preflight, acceptance may need to install Source packages, write canonical source, generate outputs and publish the acceptance record.

If that post-preflight publication fails, ContextCanon removes the new canonical source, generated outputs, partial onboarding acceptance artifacts and Source packages newly installed by that failed attempt. Pre-existing Source packages are preserved.

A dedicated regression test simulates failure while writing the final `acceptance.json` and verifies that the repository returns to its pre-adoption canonical state.

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

The executable path currently passes **90 deterministic tests**. Coverage includes:

- pending review decisions and exact evidence rendering;
- fresh default Node identity independent of evidence identity;
- stale proposal/review and changed-live-evidence rejection;
- first canonical Rule/Topic publication;
- rejected findings remaining rejected and recorded;
- candidate reusable Node and unresolved-question preservation;
- historical unbound Source proposals remaining readable but not publishable;
- exact reusable Source version/digest binding and offline post-accept build;
- refusal to overwrite existing `CONTEXT.src.md` and generated-output collisions;
- refusal to package Markdown-linked material that was outside frozen review evidence;
- rollback after simulated final acceptance-record publication failure.

The executable acceptance path has already reached **90 green deterministic tests**. The current project-owner review has now triggered another documentation/architecture hardening pass: the onboarding entry is being rewritten from the user's viewpoint, the semantic-AI step is being explained by its benefit, and four first-adoption trust guarantees are being promoted from implementation/status knowledge into durable Framework Development Rules and architecture documentation.

After those review corrections, the branch must again follow the normal closing sequence: regenerate only compiler-reported dogfood drift, then run the **exact new PR head** through all 90 tests plus `contextcanon check --all .` at zero drift. Until that succeeds, the previous green review head is evidence about the implementation, not the final state of this corrected review candidate.

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

That real-project exercise is deliberately two tests at once. First, it tests the onboarding workflow itself: evidence selection, semantic sorting, review, correction and explicit acceptance. Second, it tests whether ContextCanon is genuinely useful after onboarding: can messy project knowledge be cleaned up into sensible local Rules, Topics and reusable Nodes without the distribution work becoming awkward? The mechanics for stable identities and location-independent Nodes exist; the human experience of reorganizing a real project has not yet been validated.

The interesting questions should now be semantic/product questions rather than missing trust mechanics: What did the LLM classify badly? Which context was stale? Which information should become shared Sources? How natural did it feel to distribute guidance between Nodes, Sources, Rules and Topics? Which state/planning findings need better authoring assistance? Was the review representation pleasant enough on a real-sized proposal?

## Later refinement: context hidden in source code

A later refinement should investigate a **second-pass source scan after initial ContextCanon adoption**.

Human-written comments and docstrings can contain unusually valuable design information: module invariants, reasons for strange constraints, compatibility decisions, and warnings that never made it into README or architecture documents.

The preferred direction is not to feed all source code into the first bootstrap. Instead:

1. establish the coarse ContextCanon structure first;
2. scan source in bounded Node/directory-sized areas;
3. use already accepted Rules, Topics and Sources as context for interpreting comments;
4. propose only high-value context that should be centralized;
5. keep exact source provenance and human review;
