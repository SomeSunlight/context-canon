# Current State

ContextCanon now has a stable deterministic core and, on PR #9, a complete first-adoption path from an existing Git repository to **human-reviewed, explicitly accepted canonical Context**.

The project-owner accepted baseline on `main` remains PR #8:

`1280aa9e763f0588fa06b3e1e98b9e7b52302cdd`

PR #9 / branch `agent/onboarding-review-acceptance` is the current review candidate. Its onboarding review/acceptance mechanics are implemented. The project-owner review then triggered a second hardening pass around repository orientation, documentation ownership and the way long LLM-assisted development work is checkpointed.

That correction is now through its **authoring gate**: exact head `ff0372d6217e2352b671b3429d6883c3fd57ea0f` passed all **92 deterministic/repository tests** in GitHub Actions run #299. The only failure was the expected generated-package drift. The remaining technical closing step is therefore one deliberate dogfood regeneration followed by exact-head zero-drift CI.

> [!NOTE]
> **Project-owner accepted** means the project owner, acting as ContextCanon's first user/reviewer, reviewed a development stage and approved it as the new project baseline. That is different from `contextcanon source accept` and `contextcanon onboard accept`, where a human operator explicitly accepts one concrete reviewed artifact.

## In one minute

The current PR candidate can:

- compile Context Nodes deterministically;
- compose reusable immutable Sources with exact identities and offline accepted state;
- review and explicitly accept Source updates;
- keep entry context small and route deeper context through Topics;
- freeze exact onboarding evidence from an existing Git repository;
- generate the semantic assignment for an external reasoning LLM;
- validate the returned `proposal.json` against exact frozen evidence;
- create a human review bound to that exact proposal and evidence;
- show every finding with classification, rationale, confidence and cited evidence lines;
- require an explicit human `accept` or `reject` decision for every finding;
- reject stale review or changed live evidence;
- bind a proposed reusable Source to the exact immutable package the semantic reviewer inspected;
- stage and compile the proposed first Context Node before publication;
- refuse first adoption when it would seize existing project-owned ContextCanon paths;
- publish the first canonical `CONTEXT.src.md` only after explicit human acceptance;
- roll back a failed first publication rather than leave a half-adopted repository;
- immediately run normal deterministic build/check after publication.

It deliberately does **not**:

- let an LLM publish project truth;
- turn candidate reusable Nodes into library Nodes automatically;
- invent answers for unresolved questions;
- splice state/planning prose into human documents as if prose merging were deterministic;
- replace an existing `CONTEXT.src.md` through first-onboarding acceptance v0;
- silently substitute another reusable Source package after semantic review.

## Four dogfood Nodes, four different jobs

ContextCanon now dogfoods four real Context Nodes in its own repository.

### 1. ContextCanon Gateway

The repository root is the deliberately small Gateway.

It owns the first user entry and the ordinary onboarding walkthrough. It contains almost no governance itself; Topics route work to deeper material only when needed.

### 2. ContextCanon Foundation

`nodes/library/foundation/` is the reusable baseline for the ContextCanon Node Library.

Foundation now also owns its **authored reusable documentation**:

- source/authoring format;
- Official Context package semantics;
- Topics and progressive disclosure;
- Source composition and exact accepted-package semantics;
- harness-adapter principles.

This matters architecturally. Foundation must be independently understandable and publishable as a reusable Node; it must not depend on Framework Development as a hidden authoring owner.

### 3. ContextCanon Development Workflow

`nodes/internal/development-workflow/` is an internal dogfood Node for the development method itself.

Its durable Rules make long LLM-assisted work recoverable: record coherent work in `PLAN.md` before editing, checkpoint completed steps immediately, keep recovery-critical decisions in the repository, preserve failed-verification evidence, batch related edits before dogfood, and require exact-head CI before review completion.

It is intentionally internal for now. If unrelated projects later prove the same method reusable, it can be reviewed for promotion instead of being declared generic prematurely.

### 4. ContextCanon Framework Development

`nodes/internal/framework-development/` composes Foundation plus Development Workflow and adds only ContextCanon-framework-specific context.

It owns compiler implementation, architecture, onboarding internals/reference material, tests/CI documentation, framework state concepts and the project-specific use-case walkthrough.

Framework Development may reference Foundation-owned reusable resources, but it no longer maintains duplicate authored copies.

## Authored documentation versus generated package material

The repository now makes this distinction explicit when browsing directories directly:

```text
owning Node / docs/...              human-authored source documentation
        ↓ deterministic materialization
owning/consuming Node / CONTEXT/... generated self-contained package material
```

Short `README.md` files explain important physical directory boundaries. Generated non-empty `CONTEXT/` directories also receive a compiler-generated `README.md` explaining that `references/` contains package copies rather than another authoring surface.

The explicit generated paths are useful rather than accidental duplication: a published immutable package may later exist without the original source repository, so the package needs exact copies of the Topic resources it exposes.

## How onboarding works now

Onboarding uses a strong reasoning AI as a **semantic sorting assistant** for one bounded step.

An existing repository rarely presents its useful context in clean categories. Durable Rules may be mixed with README prose, configuration, CI, architecture decisions, temporary plans, reusable conventions and contradictory descriptions. Deterministic code can freeze and verify those bytes exactly, but it cannot reliably decide what the scattered human material means.

The workflow is therefore deliberately split by actor:

```text
[ContextCanon · deterministic]
freeze exact repository evidence
        ↓
[ContextCanon · deterministic]
generate the semantic assignment
        ↓
[External strong reasoning LLM · semantic]
classify and organize the frozen evidence
return exactly one proposal.json
        ↓
[ContextCanon · deterministic]
validate JSON structure and provenance
        ↓
[ContextCanon + Human]
show each finding beside exact evidence
record accept/reject decisions
        ↓
[Human · explicit action]
contextcanon onboard accept
        ↓
[ContextCanon · deterministic]
preflight → stage → compile → publish → build/check
```

ContextCanon does not choose or call the model. The operator supplies the framework-generated instruction and frozen evidence to a suitable external model or harness.

The documentation explicitly recommends a **strong reasoning-capable model**. A weak model can return perfectly valid JSON while making poor distinctions between durable governance, ordinary documentation, temporary state, reusable knowledge and unresolved contradictions. Deterministic validation proves structure and provenance, not semantic judgment quality.

## What human review adds

A valid LLM proposal is still untrusted semantic interpretation.

`contextcanon onboard review` creates `contextcanon/onboarding-review/v0`, bound to the exact `proposal_digest` and `evidence_digest`. Every item starts `pending`.

The reviewer sees:

- classification and confidence;
- rationale and proposed payload;
- exact evidence path/hash/line range;
- the cited evidence lines themselves.

Every item must become `accept` or `reject` before publication. If the semantic finding itself is wrong, the operator corrects `proposal.json`, validates again and creates a fresh review. The changed proposal digest makes the old review inapplicable.

Node name, ID and version are human-owned review state. When the operator does not provide `--node-id`, ContextCanon creates one fresh UUID and stores it in `review.json`; Node identity is deliberately not derived from Evidence identity.

## What explicit acceptance guarantees

`contextcanon onboard accept` refuses publication unless review state is complete and still bound to the exact proposal/evidence.

Immediately before publication it rechecks frozen evidence against the current live repository. Changed reviewed evidence stops acceptance.

The proposed Context Node is first compiled in staging using only reviewed evidence. Markdown resource closure therefore cannot quietly pull an unreviewed local file into the accepted package.

Accepted Rules and Topics become canonical authoring. Rejected findings remain rejected. Ordinary documentation remains ordinary documentation. Candidate reusable Nodes and unresolved questions stay separate reviewed follow-up artifacts.

### Reusable Sources stay exact

An `existing-source` finding is bound to the Source Node ID, name, version, `normalized_digest` and `package_digest` inspected by the semantic reviewer.

Final acceptance requires that same immutable package. A newer package with the same stable Source Node ID is a different review object and is rejected until explicitly reviewed.

After acceptance, the package is installed into accepted local state and pinned exactly. Normal builds remain offline even if the original Source repository disappears.

### First adoption does not seize project files

ContextCanon stages the proposed Node and derives its real compiler-owned output set before touching canonical project state.

If those output paths already exist, first adoption refuses to overwrite them. Existing `CONTEXT/` and existing `CONTEXT.src.md` are explicit stops. Re-onboarding an already adopted project needs a separate reviewed merge/update workflow.

### Failed publication is rolled back

If first publication fails after preflight but before the final acceptance record is complete, ContextCanon removes only the canonical/generated state and Source packages newly created by that failed attempt. Pre-existing accepted Source state is preserved.

The operator should be able to fix the failure and retry, not reverse-engineer a half-adopted repository.

## Evidence is not automatically truth

Onboarding selects likely high-value context carriers such as README, CONTRIBUTING, architecture/development documentation, manifests, CI configuration and agent instructions. Ordinary source code is not blindly added to the first semantic pass.

Those files may disagree or be stale. The generated assignment therefore tells the reasoning model:

- no familiar filename is automatically authoritative;
- for claims about **currently implemented behavior**, direct implementation/configuration/manifest/CI/test evidence has more weight when it clearly contradicts descriptive documentation;
- documentation and meaningful source comments remain important evidence for intent, rationale, constraints, workflow, history and target design;
- unclear "is versus should become" conflicts stay visible as unresolved questions or planning state.

This is implementation-first only for current-state claims, not a blanket rule that source code is always correct.

## What the project owner has accepted as stable

The currently merged baseline through PR #8 includes:

- [x] deterministic Context Node compiler and generated drift checking;
- [x] compact `CONTEXT.md` plus Topic-based progressive disclosure;
- [x] stable Node/Rule identity and inherited Rule Remove/Override;
- [x] immutable external Source packages and offline normal builds;
- [x] deterministic Source candidate review and explicit operator acceptance;
- [x] generic Git candidate transport;
- [x] deterministic onboarding evidence preparation;
- [x] framework-owned, harness-neutral semantic assignment;
- [x] strict provenance-rich onboarding proposal validation;
- [x] user-facing onboarding walkthrough and Gateway discoverability;
- [x] concise local Node Overview presentation;
- [x] first-user usability hardening: explicit actors, strong-model guidance, stale-document handling, readable STATE and separate contribution paths.

PR #9 is **not yet project-owner accepted** and remains open.

## Current review candidate: PR #9

PR #9 adds the human review/explicit acceptance block and the review-correction work described above.

The deterministic suite has grown from the earlier 90-test implementation checkpoint to **92 tests**. The additional repository-orientation regression coverage includes the generated `CONTEXT/README.md` package orientation and repository link/ownership consistency.

The latest completed authoring-gate evidence is:

- exact authoring head: `ff0372d6217e2352b671b3429d6883c3fd57ea0f`;
- GitHub Actions run #299;
- **92/92 tests green**;
- generated drift intentionally still present because the final dogfood regeneration has not yet been committed.

The next closing sequence is therefore narrow:

1. regenerate only the compiler-reported dogfood output for the completed correction block;
2. commit that exact generated state once;
3. run the exact new head through all 92 tests plus `contextcanon check --all .` at zero drift;
4. inspect the final diff against `main` for intended paths and accidental temporary files;
5. update PR #9 with exact final identities and CI evidence;
6. return the still-open PR to the project owner for review.

No merge happens without explicit project-owner approval.

## What comes next after PR #9

After this block is complete and project-owner accepted, ContextCanon should be used on a **materially larger existing project** with no pre-curated ContextCanon files.

That exercise is deliberately two tests at once:

1. **Onboarding usability and trust:** Does prepare → semantic proposal → review → explicit acceptance remain understandable and comfortable at real size?
2. **ContextCanon in actual use:** Once accepted, does the resulting structure genuinely help humans and agents clean up scattered project knowledge into sensible local Nodes, reusable Sources, Rules and Topics?

The real test should also answer an intentionally open baseline question: should normal first onboarding explicitly offer/recommend ContextCanon Foundation as a reusable starting Source, remain fully opt-in, or use another convention? The repository Gateway is not the reusable baseline.

The interesting findings should now be semantic/product questions rather than missing trust mechanics: what the reasoning model classified badly, which documents were stale, which information should become reusable, how natural context distribution feels, and whether the accepted structure actually improves ordinary model/human work.

## Later refinement: important context hidden in source code

Do **not** turn first bootstrap into a blind whole-repository source scan.

After coarse ContextCanon structure already exists, investigate a second bounded semantic pass over human-written comments/docstrings. Look for high-value invariants, non-obvious constraints, compatibility reasons, architectural decisions and warnings; compare them against accepted Rules/Topics/Sources; preserve exact source provenance; and require human review before centralizing anything.

Optional stable references from source comments back to established ContextCanon Rule/Topic IDs may be useful later. The goal is fresher central context without turning ContextCanon into indiscriminate source-code indexing or prompt expansion.
