# Plan

## Completed validation

- [x] Review the repository as the first self-hosted ContextCanon specification.
- [x] Perform a mental walkthrough of small-project initialization, multi-source composition, inherited changes, source updates, conflicts, standalone children, harness adapters, and multi-node repositories.
- [x] Identify the Official Context Package versus compact `CONTEXT.md` entry-view distinction.
- [x] Establish visible published IDs and hidden compiler-managed local IDs.
- [x] Establish `Required` versus `Optional` Topic material as a design requirement.
- [x] Split ContextCanon conceptually into a public Standard node and an internal Development node.

See [docs/use-case-walkthrough.md](docs/use-case-walkthrough.md).

## Next vertical POC

- [ ] Apply ContextCanon Standard to several real example repositories.
- [ ] Keep at least one tiny repository intentionally tiny and verify that ContextCanon adds more value than ceremony.
- [ ] Test a task that needs only the entry context and confirm no Topic document is needed.
- [ ] Test a task that triggers one Topic with Required material and optional deeper links.
- [ ] Test a node composed from several orthogonal sources plus a small local delta.
- [ ] Simulate a source update while a child remains pinned to its accepted package.
- [ ] Produce and review a deterministic candidate diff before accepting the update.
- [ ] Test a dangling override/remove after an upstream rule disappears.
- [ ] Test a semantic conflict between unrelated source rules and record an explicit resolution.
- [ ] Verify a standalone child remains understandable without live access to source repositories.
- [ ] Test authoring help in `compact` form; decide whether an `expanded` mode is worth keeping.
- [ ] Revisit the specification and remove any remaining unnecessary ceremony.

## Before compiler implementation

- [ ] Freeze the smallest useful V1 source syntax.
- [ ] Freeze Topic `Required`/`Optional` representation.
- [ ] Define source locator and immutable package identity.
- [ ] Define multi-node repository addressing.
- [ ] Define stable ID generation/preservation rules.
- [ ] Define deterministic diagnostics, including dangling changes.
- [ ] Define where non-versioned authoring preferences live.

## Compiler work after product validation

- [ ] Define the deterministic internal context model.
- [ ] Implement parse, validate, compose, change operations, provenance, and structured diff.
- [ ] Implement offline package build and materialization.
- [ ] Implement source update/acceptance workflow.
- [ ] Generate official entry views and harness adapters.

Implementation remains intentionally behind product validation.
