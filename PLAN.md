# Plan

## Completed validation

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

## Next vertical POC

- [ ] Apply ContextCanon Foundation to several real example repositories.
- [ ] Keep at least one tiny repository intentionally tiny and verify that ContextCanon adds more value than ceremony.
- [ ] Add one real reusable Node under `nodes/library/` and verify that its placement and Foundation dependency are obvious to a new contributor.
- [ ] Test direct and transitive Foundation composition inside the ContextCanon Node Library.
- [ ] Test another Gateway-style Node that routes different task families to different deeper Nodes.
- [ ] Test a task that needs only `CONTEXT.md` and no deeper package resource.
- [ ] Test a task that triggers one Topic with Required material and optional deeper links.
- [ ] Verify that source documents remain editable in natural repository locations while published copies are materialized under `CONTEXT/`.
- [ ] Verify that a consumer can use a published package without relying on the Source repository layout.
- [ ] Test a Node composed from several orthogonal Sources plus a small local delta.
- [ ] Simulate a Source update while a child remains pinned to its accepted package.
- [ ] Produce and review a deterministic candidate diff before accepting the update.
- [ ] Test a dangling override/remove after an upstream Rule disappears.
- [ ] Test a semantic conflict between unrelated Source Rules and record an explicit resolution.
- [ ] Test authoring help in `compact` form; decide whether an `expanded` mode is worth keeping.
- [ ] Revisit the specification and remove any remaining unnecessary ceremony.

## Context integration roadmap

The same Topic/package mechanism should be tested beyond Markdown Rules and prose. Add one element type at a time only when a real use case justifies it.

- [ ] Glossaries and domain terminology.
- [ ] Coding patterns and example code.
- [ ] CSV files, schemas, tables, and other structured data.
- [ ] PDFs, images, diagrams, and other reference media.
- [ ] Skills and executable workflows.
- [ ] Test fixtures and worked examples.
- [ ] Operational experience, known pitfalls, and troubleshooting knowledge.
- [ ] Decide which future element types require stable IDs, composition semantics, or special diff behavior.
- [ ] Preserve progressive disclosure for every new type; adding a type must not imply eager prompt loading.

## Before compiler implementation

- [ ] Freeze the smallest useful V1 source syntax.
- [ ] Freeze Topic `Required`/`Optional` representation.
- [ ] Define typed Topic targets, including Context Node targets.
- [ ] Define deterministic node-root discovery and nested-node boundary rules.
- [ ] Define Source locators and immutable package identity, including how a Node move changes location without changing identity.
- [ ] Define multi-node repository addressing.
- [ ] Define stable ID generation/preservation rules.
- [ ] Define deterministic diagnostics, including dangling changes and invalid Topic targets.
- [ ] Define package resource mapping from source paths to `CONTEXT/` paths.
- [ ] Define where non-versioned authoring preferences live.

## Compiler work after product validation

- [ ] Define the deterministic internal context model.
- [ ] Implement parse, validate, Node discovery, compose, change operations, Topic targets, provenance, and structured diff.
- [ ] Implement optional `CONTEXT/` package build and resource materialization.
- [ ] Implement Source update/acceptance workflow.
- [ ] Generate `CONTEXT.md` and harness adapters.

Implementation remains intentionally behind product validation.
