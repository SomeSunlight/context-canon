# Plan

## Completed validation

- [x] Review the repository as the first self-hosted ContextCanon specification.
- [x] Perform mental walkthroughs of small-project initialization, multi-source composition, inherited changes, source updates, conflicts, standalone children, harness adapters, and multi-node repositories.
- [x] Define `CONTEXT.md` as the compact entry and `CONTEXT/` as deeper package-local material.
- [x] Establish visible published IDs and hidden compiler-managed local IDs.
- [x] Establish `Required` versus `Optional` Topic material as a design requirement.
- [x] Split ContextCanon into public `t` and internal `t-intern` nodes.
- [x] Define the ContextCanon schema/specification as the structural interface rather than introducing a third interface node.
- [x] Add a public documentation-style rule for clear, precise technical prose.

See [docs/use-case-walkthrough.md](docs/use-case-walkthrough.md).

## Next vertical POC

- [ ] Apply ContextCanon Public (`t`) to several real example repositories.
- [ ] Keep at least one tiny repository intentionally tiny and verify that ContextCanon adds more value than ceremony.
- [ ] Test a task that needs only `CONTEXT.md` and no deeper package resource.
- [ ] Test a task that triggers one Topic with Required material and optional deeper links.
- [ ] Verify that source documents remain editable in natural repository locations while published copies are materialized under `CONTEXT/`.
- [ ] Verify that a consumer can use the published package without relying on the source repository layout.
- [ ] Test a node composed from several orthogonal sources plus a small local delta.
- [ ] Simulate a source update while a child remains pinned to its accepted package.
- [ ] Produce and review a deterministic candidate diff before accepting the update.
- [ ] Test a dangling override/remove after an upstream rule disappears.
- [ ] Test a semantic conflict between unrelated source rules and record an explicit resolution.
- [ ] Test authoring help in `compact` form; decide whether an `expanded` mode is worth keeping.
- [ ] Revisit the specification and remove any remaining unnecessary ceremony.

## Context integration roadmap

The same Topic/package mechanism should be tested beyond Markdown rules and prose. Add one element type at a time only when a real use case justifies it.

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
- [ ] Define source locator and immutable package identity.
- [ ] Define multi-node repository addressing.
- [ ] Define stable ID generation/preservation rules.
- [ ] Define deterministic diagnostics, including dangling changes.
- [ ] Define package resource mapping from source paths to `CONTEXT/` paths.
- [ ] Define where non-versioned authoring preferences live.

## Compiler work after product validation

- [ ] Define the deterministic internal context model.
- [ ] Implement parse, validate, compose, change operations, provenance, and structured diff.
- [ ] Implement `CONTEXT/` package build and resource materialization.
- [ ] Implement source update/acceptance workflow.
- [ ] Generate `CONTEXT.md` and harness adapters.

Implementation remains intentionally behind product validation.
