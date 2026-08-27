# Current State

ContextCanon has a stable deterministic core and, on PR #9, a complete first-adoption path from an existing Git repository to **human-reviewed, explicitly accepted canonical Context**.

The project-owner accepted baseline on `main` remains PR #8:

`1280aa9e763f0588fa06b3e1e98b9e7b52302cdd`

PR #9 / branch `agent/onboarding-review-acceptance` is the current review candidate. It adds the human review/acceptance mechanics and a substantial self-hosting cleanup around repository orientation, documentation ownership and recoverable LLM-assisted development.

> [!NOTE]
> **Project-owner accepted** means the project owner, acting as ContextCanon's first user/reviewer, reviewed a development stage and approved it as the new project baseline. That is different from `contextcanon source accept` and `contextcanon onboard accept`, where a human operator explicitly accepts one concrete reviewed artifact.

## Where we are now

The current branch is in the final project-owner wording pass before the mechanical merge gate.

The large product/documentation line is present and can be reviewed before every generated package is refreshed. Full green CI and zero generated drift are required for the exact merge candidate **after** project-owner approval.

The latest completed broad authoring verification before the final wording pass was GitHub Actions run #299 on head `ff0372d6217e2352b671b3429d6883c3fd57ea0f`:

- **92/92 deterministic/repository tests passed**;
- the only failure was intentionally stale generated self-hosted package output.

The final wording pass changes authored context again, so generated packages are expected to remain stale until the final regeneration. Unknown test failures would still be a stop signal; understood generated drift is not.

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
- show every finding with rationale, confidence and exact cited evidence;
- require explicit human `accept` or `reject` decisions;
- reject stale review or changed live evidence;
- bind proposed reusable Sources to the exact immutable packages that were reviewed;
- stage and compile the proposed first Context Node before publication;
- refuse first adoption when it would seize existing project-owned ContextCanon paths;
- publish the first canonical `CONTEXT.src.md` only after explicit human acceptance;
- roll back a failed first publication rather than leave a half-adopted repository;
- immediately run normal deterministic build/check after publication.

It deliberately does **not**:

- let an LLM publish project truth;
- invent answers for unresolved questions;
- silently convert candidate reusable Nodes into library Nodes;
- splice planning prose into human documents as if prose merging were deterministic;
- replace an existing `CONTEXT.src.md` through first-onboarding acceptance v0;
- silently substitute another reusable Source package after semantic review.

## Four self-hosted Context Nodes, four different jobs

ContextCanon now uses four real Context Nodes on its own repository.

### 1. ContextCanon Gateway

The repository root is the deliberately small Gateway. It owns first-contact orientation and routes deeper work through Topics.

### 2. ContextCanon Foundation

`nodes/library/foundation/` is the reusable baseline for the ContextCanon Node Library.

Foundation now owns its own reusable authored documentation:

- source/authoring format;
- Official Context package semantics;
- Topics and progressive disclosure;
- Source composition and exact accepted-package semantics;
- harness-adapter principles.

Foundation is therefore independently understandable and publishable. Framework Development may consume those resources, but it is no longer their hidden authoring owner.

### 3. ContextCanon Development Workflow

`nodes/internal/development-workflow/` is an internal self-hosted Node for the development method itself.

Its Rules make the working method explicit:

- put coherent work in `PLAN.md` before editing;
- checkpoint completed steps immediately;
- keep recovery-critical knowledge in the repository;
- after a short explicit continuation with no reported intervening edits, resume from the last established repository state instead of re-proving that nothing changed;
- batch related edits instead of regenerating generated Context packages after every micro-change;
- allow a coherent candidate to reach project-owner review with understood/disclosed CI drift;
- require exact-head full green CI and zero drift only at the final merge gate;
- never merge without explicit project-owner approval.

This Node remains internal until unrelated projects demonstrate that the workflow is genuinely reusable.

### 4. ContextCanon Framework Development

`nodes/internal/framework-development/` composes Foundation plus Development Workflow and adds only ContextCanon-framework-specific context.

It owns compiler implementation, architecture, onboarding internals/reference material, tests/CI documentation, framework state concepts and the project-specific use-case walkthrough.

## Why the extra README files matter

Important physical directories now explain themselves when opened directly in GitHub.

The authored README files are not decorative. They make ownership and purpose visible before a reader has to understand the whole ContextCanon architecture. In particular they distinguish:

```text
owning Node / docs/...              human-authored source documentation
        ↓ deterministic materialization
owning/consuming Node / CONTEXT/... generated self-contained package material
```

Generated non-empty `CONTEXT/` directories also receive a compiler-generated `README.md` explaining that `references/` contains package copies rather than another authoring surface.

This preserves a self-contained immutable package without creating a second place where humans are expected to maintain the same documentation. It also lets precise detail live close to the narrow context where it belongs while higher-level overviews stay compact.

## How onboarding works now

Onboarding uses a strong reasoning AI as a **semantic sorting assistant** for one bounded step.

An existing repository rarely presents its useful context in clean categories. Durable Rules may be mixed with README prose, configuration, CI, architecture decisions, temporary plans, reusable conventions and contradictory descriptions.

The workflow is deliberately split by actor:

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
validate structure and provenance
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

ContextCanon does not choose or call the model. The operator supplies the framework-generated instruction and frozen evidence to a suitable model or harness.

A strong reasoning-capable model is recommended because deterministic validation proves JSON structure and provenance, not whether semantic classification was intelligent.

## What explicit onboarding acceptance protects

A valid LLM proposal is still untrusted semantic interpretation.

`contextcanon onboard review` binds human review state to exact proposal/evidence identity. Every finding starts pending and must become explicit `accept` or `reject` before publication.

`contextcanon onboard accept` then protects four important first-adoption boundaries:

1. **Live evidence must still match review.** Changed reviewed files stop acceptance.
2. **Reusable Source identity stays exact.** The accepted package must be the same immutable package that semantic review and human review saw.
3. **First adoption does not seize project files.** ContextCanon stages the proposed Node and derives its real generated outputs before touching canonical project state.
4. **Failed first publication is rolled back.** Newly created canonical/generated state and newly installed Source packages from a failed attempt are removed while pre-existing accepted state is preserved.

## Evidence is not automatically truth

Onboarding selects likely high-value context carriers such as README, CONTRIBUTING, architecture/development documentation, manifests, CI configuration and agent instructions. Ordinary source code is not blindly added to the first semantic pass.

Those files may disagree or be stale. The generated assignment therefore tells the reasoning model:

- no familiar filename is automatically authoritative;
- for **currently implemented behavior**, direct implementation/configuration/manifest/CI/test evidence has more weight when it clearly contradicts descriptive documentation;
- documentation and meaningful source comments remain important evidence for intent, rationale, constraints, workflow, history and target design;
- unclear "is versus should become" conflicts stay visible as unresolved questions or planning state.

## What is already stable on main

The merged baseline through PR #8 includes:

- deterministic Context Node compilation and generated drift checking;
- compact Gateway context plus Topic-based progressive disclosure;
- stable Node/Rule identity and inherited Rule Remove/Override;
- immutable external Source packages and offline normal builds;
- deterministic Source review and explicit operator acceptance;
- generic Git candidate transport;
- deterministic onboarding evidence preparation;
- framework-owned, harness-neutral semantic assignment;
- strict provenance-rich onboarding proposal validation;
- user-facing onboarding walkthrough and first-user usability hardening.

PR #9 is **not yet project-owner accepted** and remains open.

## What remains before PR #9 can merge

Finish the final wording pass, then create the exact mechanical merge candidate:

1. regenerate only compiler-owned self-hosted Context packages affected by the final authored state;
2. run the exact merge candidate through the complete deterministic suite;
3. require `contextcanon check --all .` at zero generated drift;
4. inspect the final diff against `main` for accidental temporary/placeholder files;
5. update PR #9 with the exact merge-ready head, test count and package identities;
6. squash-merge only after explicit project-owner approval.

No merge happens without explicit project-owner approval.

## What comes next after PR #9

After PR #9 is accepted and merged, ContextCanon should be used on a **materially larger existing project** with no pre-curated ContextCanon files.

That exercise is deliberately two tests at once:

1. **Onboarding usability and trust:** Does prepare → semantic proposal → review → explicit acceptance remain understandable and comfortable at real size?
2. **ContextCanon in actual use:** Once accepted, does the resulting structure genuinely help humans and agents clean up scattered project knowledge into sensible local Nodes, reusable Sources, Rules and Topics?

The real test should also answer the intentionally open baseline question: should normal first onboarding offer/recommend ContextCanon Foundation as a reusable starting Source, remain fully opt-in, or use another convention? The repository Gateway is not the reusable baseline.

A separate later lifecycle question is how to **clean up or strip down onboarding state without throwing away useful Context**. The intended direction is a deterministic preview of transient artifacts that are ready to delete, explicit human confirmation, and preservation of canonical/generated Context and useful nested Nodes by default.

## Later refinement: important context hidden in source code

Do **not** turn first bootstrap into a blind whole-repository source scan.

After coarse ContextCanon structure exists, investigate a second bounded semantic pass over human-written comments/docstrings. Look for high-value invariants, non-obvious constraints, compatibility reasons, architectural decisions and warnings; compare them against accepted Rules/Topics/Sources; preserve exact source provenance; and require human review before centralizing anything.
