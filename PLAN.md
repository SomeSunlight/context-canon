# Plan

## Completed product validation

- [x] Review the repository as the first self-hosted ContextCanon specification.
- [x] Perform mental walkthroughs of small-project initialization, multi-source composition, inherited changes, Source updates, conflicts, standalone children, harness adapters, and multi-node repositories.
- [x] Define `CONTEXT.md` as the compact entry and `CONTEXT/` as optional deeper package-local material.
- [x] Establish visible published IDs and hidden compiler-managed local IDs.
- [x] Establish Required versus Optional Topic targets.
- [x] Establish ContextCanon Foundation and ContextCanon Framework Development with Framework Development composing Foundation.
- [x] Add ContextCanon Gateway as a normal minimal root Node.
- [x] Distinguish Topic navigation from Source composition.
- [x] Establish one node-root directory per Context Node while keeping stable identity independent of path.
- [x] Separate reusable ContextCanon Nodes under `nodes/library/` from ContextCanon-internal Nodes under `nodes/internal/`.
- [x] Define the ContextCanon schema/specification as the structural interface rather than introducing an interface Node.

See [docs/use-case-walkthrough.md](docs/use-case-walkthrough.md).

## Strategy: executable walking skeleton

Prefer the smallest end-to-end implementation that can run on real repositories. Freeze only contracts required by the next executable slice. Use mental walkthroughs selectively when implementation exposes a concrete ambiguity.

```text
real repository
      ↓
CONTEXT.src.md
      ↓
deterministic compiler
      ↓
Official Context Package + exact diagnostics/diff
      ↓
LLM uses compiled context or interprets a Context change
      ↓
real project work
      ↓
feedback into ContextCanon
```

Every compiler change should remain testable deterministically without invoking an LLM.

## Walking Skeleton 1 — deterministic compiler

The first compiler slice is now executable and dogfooded by this repository.

- [x] Use a small dependency-free Python CLI that is easy to run locally and in CI.
- [x] Define the minimum source grammar needed by Gateway, Foundation, and Framework Development.
- [x] Make Topic targets explicitly distinguish Resource from Context Node.
- [x] Discover and validate Nodes from their node-root directories.
- [x] Parse Node metadata, Sources, local Rules, Topics, stable IDs, titles, and rationale.
- [x] Resolve local-path Sources and validate stable Node identity and accepted version.
- [x] Detect local Source dependency cycles.
- [x] Compose inherited and local Rules deterministically without Source precedence.
- [x] Generate `CONTEXT.md`.
- [x] Materialize Topic Resource targets into optional `CONTEXT/` output.
- [x] Compute recursive materialization closure for local links from materialized Markdown resources.
- [x] Generate `.context/context.yaml` with provenance and exact SHA-256 digests.
- [x] Generate thin `AGENTS.md` and `.goosehints` adapters when requested by Node metadata.
- [x] Add `check` mode to detect missing, changed, or extra generated output.
- [x] Turn Gateway, Foundation, and Framework Development into deterministic compiler fixtures.
- [x] Add CI that runs unit tests and `contextcanon check --all .`.
- [ ] Run the compiler against one deliberately simple external Hello-World-style repository.
- [ ] Confirm that the first external project can be rebuilt and checked without depending on the ContextCanon repository layout.

Unsupported syntax must fail clearly rather than encourage premature complexity.

## Walking Skeleton 2 — first external project with an LLM

Use a small real repository first so every relationship between source, generated context, project files, and LLM behavior is obvious.

The active experiment is `SomeSunlight/teams-chat-exporter` on branch `agent/contextcanon-hello-world`. It intentionally starts before compilation so the first generated filesystem diff remains visible and reviewable.

- [x] Select a simple existing repository as the first external customer.
- [x] Create a dedicated ContextCanon experiment branch; do not alter its main branch.
- [x] Bootstrap only human-editable `CONTEXT.src.md` and genuinely useful Topic resources.
- [ ] Compile all generated output deterministically.
- [ ] Enter the project through a real harness using the generated adapter and compact `CONTEXT.md`.
- [ ] Perform one ordinary project task that needs no deeper Topic material.
- [ ] Perform one task that must load a Required Topic resource.
- [ ] Observe what the LLM actually loads, what it misses, what feels redundant, and what is confusing to a human reviewer.
- [ ] Compare the experience with the same project without ContextCanon.

## Walking Skeleton 3 — Context change to code impact

Make the first higher-level LLM workflow a direct test of ContextCanon's value.

```text
old compiled Context
        +
new compiled Context
        ↓
deterministic Context diff
        ↓
LLM impact review
        ↓
Rule ID → affected files / code / docs → reason → proposed action
```

- [ ] Produce an exact deterministic diff between two compiled Context states using stable IDs and provenance.
- [ ] Emit a compact machine-readable change set plus a human-readable summary suitable for LLM input.
- [ ] Keep LLM impact analysis outside the deterministic compiler core.
- [ ] Ask the LLM to map each changed Rule to likely affected code, configuration, tests, and documentation in a real repository.
- [ ] Require a reason for each suggested location.
- [ ] Treat the impact map as semantic advice, not compiler truth.
- [ ] Let a human approve or reject suggested project changes.
- [ ] Later test whether an agent can implement an approved impact set while following the newly compiled Context.

The semantic workflow must remain harness-neutral: Codex, goose, Hermes, a local model, or another agent should consume the same deterministic change set.

## Harden from observed failures

Implement broader semantics only when a real scenario needs them, then preserve the discovered case as a deterministic regression fixture.

Likely next capabilities include:

- [ ] Topic inheritance/materialization across Source package boundaries.
- [ ] Remove and Override inherited Rules.
- [ ] Protected Rules and authorized exceptions.
- [ ] Multiple orthogonal Sources and broader structural conflict diagnostics.
- [ ] Source update detection, candidate diff, explicit acceptance, and pinned package identity.
- [ ] Dangling change diagnostics after Source updates.
- [ ] External Git/package Source locators and multi-node repository addressing.
- [ ] Resource collision rules and self-contained package guarantees.
- [ ] Nested Git repository boundary behavior.
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

## Working rule

**Do not wait for theoretical completeness before the next executable slice.**

Prefer: implement one deterministic capability, run it across all fixtures, use it in a real project, observe the failure modes, then refine the specification and compiler together.
