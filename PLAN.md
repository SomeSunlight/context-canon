# Plan

## Completed product validation

- [x] Review the repository as the first self-hosted ContextCanon specification.
- [x] Perform mental walkthroughs of small-project initialization, multi-source composition, inherited changes, Source updates, conflicts, standalone children, harness adapters, and multi-node repositories.
- [x] Define `CONTEXT.md` as the compact entry and `CONTEXT/` as optional deeper package-local material.
- [x] Establish visible published IDs and hidden compiler-managed local IDs.
- [x] Establish `Required` versus `Optional` Topic targets as a design requirement.
- [x] Establish **ContextCanon Foundation** and **ContextCanon Framework Development** with Framework Development composing Foundation.
- [x] Add **ContextCanon Gateway** as a normal minimal root Node with no Sources, Rules, or materialized resources.
- [x] Distinguish Topic navigation from Source composition using the repository's own Node graph.
- [x] Establish the physical rule that every Context Node has one node-root directory while its stable identity remains independent of that path.
- [x] Separate reusable ContextCanon Nodes under `nodes/library/` from ContextCanon-internal Nodes under `nodes/internal/`.
- [x] Require every reusable Node in the ContextCanon Node Library to compose Foundation directly or transitively.
- [x] Demonstrate a Node move/rename while preserving the stable Node ID.
- [x] Define the ContextCanon schema/specification as the structural interface rather than introducing an interface Node.
- [x] Add a public documentation-style Rule for clear, precise technical prose.

See [docs/use-case-walkthrough.md](docs/use-case-walkthrough.md).

## Strategy now: build the walking skeleton

The architecture is coherent enough to stop trying to exhaustively validate it in advance.

From this point, prefer the smallest end-to-end implementation that can run on real repositories. Freeze only contracts required by the next executable slice. Use additional mental walkthroughs narrowly when an implementation decision exposes a concrete ambiguity.

The target feedback loop is:

```text
real repository
      ↓
CONTEXT.src.md
      ↓
deterministic compiler
      ↓
Official Context Package + exact diagnostics/diff
      ↓
LLM uses the compiled context or interprets a Context change
      ↓
real project work
      ↓
feedback into ContextCanon
```

Every compiler change should be testable deterministically across fixture repositories without invoking an LLM.

## Walking Skeleton 1 — minimal deterministic compiler

Build only enough compiler to compile the ContextCanon repository itself and one ordinary example project.

- [ ] Choose the smallest implementation/CLI shape that is easy to run locally and automate in tests.
- [ ] Define only the minimum source grammar needed by Gateway, Foundation, Framework Development, and the first example project.
- [ ] Make Topic targets explicitly distinguish a package resource from another Context Node so Gateway navigation is deterministic.
- [ ] Discover and validate a Node from its node-root directory.
- [ ] Parse local Rules, Topics, Sources, stable IDs, and rationale needed by the current POC.
- [ ] Resolve at least local-path Sources and preserve stable Node identity independently of path.
- [ ] Compose accepted Sources plus Local Context deterministically.
- [ ] Generate `CONTEXT.md`.
- [ ] Materialize referenced resources into optional `CONTEXT/` output.
- [ ] Generate `.context/context.yaml` from compiler state rather than maintaining it manually.
- [ ] Generate thin `AGENTS.md` and `.goosehints` adapters where applicable.
- [ ] Add a deterministic `check` mode that rebuilds/validates generated output and reports drift without an LLM.
- [ ] Turn Gateway, Foundation, and Framework Development into compiler fixtures so every change exercises the current dogfood graph.

The first compiler does **not** need to implement every documented future operation. Unsupported syntax should fail clearly rather than encourage premature complexity.

## Walking Skeleton 2 — first real project with an LLM

- [ ] Select one real existing project as the first external customer of ContextCanon.
- [ ] Use an LLM to inspect that repository and propose only the human-editable ContextCanon source and useful Topic links; generated output remains the compiler's job.
- [ ] Validate and compile the proposal deterministically.
- [ ] Enter the project through a real harness using the generated adapter and compact `CONTEXT.md`.
- [ ] Perform at least one ordinary project task that does not need deeper context.
- [ ] Perform at least one task that triggers Required deeper context.
- [ ] Observe what the LLM actually loads, what it misses, what feels redundant, and where the human model becomes confusing.
- [ ] Compare the experience with the same project before ContextCanon rather than optimizing only synthetic metrics.

## Walking Skeleton 3 — Context change to code impact

Make the first higher-level LLM workflow a direct test of ContextCanon's value.

When a Rule or other authoritative context changes:

```text
old compiled context
        +
new compiled context
        ↓
deterministic Context diff
        ↓
LLM impact review
        ↓
Rule ID → affected files / code / docs → reason → proposed action
```

- [ ] Produce an exact deterministic diff between two compiled Context states using stable IDs and provenance.
- [ ] Emit a compact machine-readable change set plus a human-readable summary suitable for an LLM input.
- [ ] Keep LLM impact analysis outside the deterministic compiler core.
- [ ] Ask the LLM to map each changed Rule to likely affected code, configuration, tests, and documentation in a real repository.
- [ ] Require the LLM to explain why each location is relevant rather than merely listing files.
- [ ] Treat the impact map as semantic advice, not compiler truth.
- [ ] Let a human approve or reject suggested project changes.
- [ ] Later test whether an agent can implement an approved impact set while following the newly compiled Context.

This workflow should remain harness-neutral: Codex, goose, Hermes, a local model, or another agent can consume the same deterministic change set.

## Harden from observed failures

Implement broader semantics when a real scenario requires them, then add deterministic regression fixtures for the discovered case.

Likely next capabilities include:

- [ ] Remove and Override inherited Rules.
- [ ] Protected Rules and authorized exceptions.
- [ ] Multiple orthogonal Sources and dependency-cycle diagnostics.
- [ ] Source update detection, candidate diff, explicit acceptance, and pinned package identity.
- [ ] Dangling change diagnostics after Source updates.
- [ ] External Git/package Source locators and multi-node repository addressing.
- [ ] Resource collision rules and self-contained package guarantees.
- [ ] Authoring assistance such as compact templates and optional richer scaffolding.

## Context integration roadmap

Add new context types only when a concrete end-to-end use case needs them. Reuse the same composition, provenance, package, and progressive-disclosure mechanisms rather than building parallel systems.

- [ ] Glossaries and domain terminology.
- [ ] Coding patterns and example code.
- [ ] CSV files, schemas, tables, and other structured data.
- [ ] PDFs, images, diagrams, and other reference media.
- [ ] Skills and executable workflows.
- [ ] Test fixtures and worked examples.
- [ ] Operational experience, known pitfalls, and troubleshooting knowledge.
- [ ] Decide which new element types require stable IDs or special diff behavior only after using them.

## Working rule

**Do not wait for theoretical completeness before the next executable slice.**

Prefer: implement one deterministic capability, run it across all fixtures, use it in a real project, observe the failure modes, then refine the specification and compiler together.
