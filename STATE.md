# Current State

ContextCanon now has a stable deterministic core and a first complete onboarding path **up to a validated LLM proposal**.

The project owner, acting as ContextCanon's first user and reviewer, accepted the latest onboarding slice after hands-on documentation review. PR #7 was squash-merged to `main` as commit `275c6b1f121126fb117f4bdbff1efc18218b0528`.

> [!NOTE]
> In this file, **project-owner accepted** means that the project owner reviewed a development stage and approved it as the new project baseline. That is not the same operation as `contextcanon source accept`, and it is not the future human acceptance of one onboarding proposal.

## In one minute

Today ContextCanon can:

- compile Context Nodes deterministically;
- compose reusable immutable Sources with exact identities;
- review and explicitly accept Source updates without hidden network access during normal builds;
- keep project entry context small and route deeper context through Topics;
- onboard an existing Git repository through a frozen evidence snapshot;
- generate the exact semantic assignment for an external LLM;
- validate the LLM's returned `proposal.json` against the exact frozen evidence.

Today ContextCanon deliberately **cannot yet**:

- present a validated onboarding proposal in a dedicated human review workflow;
- let a human explicitly accept/correct that proposal into canonical `CONTEXT.src.md`;
- publish a newly suggested reusable Node automatically.

That human review and acceptance step is the active next block.

## How onboarding works today

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
validated review artifact
        ↓
[Human · not implemented yet]
review, correct and explicitly accept
```

ContextCanon does not choose or call the model. The operator supplies the generated assignment and frozen evidence to a suitable external LLM.

The onboarding task is semantically difficult. The documentation now explicitly recommends a **strong reasoning-capable model**. A weak model can return perfectly valid JSON while making poor distinctions between durable Rules, ordinary documentation, temporary state, reusable conventions and unresolved contradictions.

## Evidence is not automatically truth

The first onboarding pass selects likely context carriers such as README, CONTRIBUTING, architecture/development documents, manifests, CI configuration and agent instructions. Ordinary source code is not automatically included.

Those files may disagree or be stale. The generated LLM assignment therefore now says:

- no conventional filename is automatically authoritative;
- for claims about **current implemented behavior**, direct implementation/configuration/manifest/CI/test evidence has more weight when it clearly contradicts descriptive documentation;
- documentation and meaningful source comments remain important evidence for intent, rationale, constraints, workflow, history and target design;
- unclear "is versus should become" conflicts must remain visible as unresolved questions or planning state.

This is implementation-first for current-state claims, not a blanket rule that source code is always correct.

## What the project owner has accepted as stable

The project owner has reviewed and accepted these development stages as the current baseline:

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
- [x] local Node `Overview` for concise orientation without turning prose into inherited governance.

The latest merged review head passed **74 deterministic tests** plus `contextcanon check --all .` with zero generated drift.

## Active next work

The next block is **human review and explicit acceptance of a validated onboarding proposal**.

It should make the LLM's findings easy to inspect rather than merely expose raw JSON. A human must be able to:

- see each proposed classification and its exact evidence;
- correct wrong classifications;
- keep contradictions and unresolved questions visible;
- separate project-local context from candidate reusable Nodes;
- explicitly decide what becomes durable project truth;
- trigger normal deterministic ContextCanon build/validation immediately after acceptance.

Only after that path is stable should the larger real 1:1 onboarding test begin.

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
- [docs/onboarding.md](docs/onboarding.md) — onboarding walkthrough and technical contract.
- [CONTRIBUTING.md](CONTRIBUTING.md) — separate paths for framework work and reusable Node contributions.
- [PLAN.md](PLAN.md) — completed stages and ordered next work.
- [CONTEXT.md](CONTEXT.md) — compact official project context and task routing.
