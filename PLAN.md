# Plan

## Next vertical slice

- [ ] Review this repository as the first self-hosted ContextCanon node.
- [ ] Walk through creating a new node from several reusable sources plus a small local delta.
- [ ] Walk through a source-context update while a child remains pinned to its accepted version.
- [ ] Walk through deterministic diff review and explicit acceptance of a source update.
- [ ] Walk through a semantic conflict between two composed sources and record an explicit resolution.
- [ ] Walk through a child repository cloned without access to its source repositories and verify that its accepted context remains understandable.
- [ ] Validate visible rule IDs in published parent context and hidden compiler-managed IDs in editable source Markdown.
- [ ] Validate the `Topics` experience with a task that needs one deeper reference and another task that does not.
- [ ] Revisit the specification after those walkthroughs and remove any remaining unnecessary ceremony.

## After the walkthroughs

- [ ] Freeze the smallest useful V1 source syntax.
- [ ] Define the deterministic internal context model.
- [ ] Implement parse, validate, compose, change operations, provenance, and structured diff.
- [ ] Implement offline package build and materialization.
- [ ] Implement source update/acceptance workflow.
- [ ] Generate harness adapters.

Implementation remains intentionally behind product validation.
