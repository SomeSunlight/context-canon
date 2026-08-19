# Current State

ContextCanon has completed two repository-based architecture/UX prototype rounds and a first systematic mental walkthrough of critical use cases.

The design baseline is now:

- `CONTEXT.src.md` is the human-editable local delta.
- The **Official Context** is a complete compiled package, not one giant always-loaded file.
- `CONTEXT.md` is the generated compact official entry view.
- Topics provide progressive disclosure and distinguish **Required** from **Optional** deeper material.
- A node may compose multiple independent context sources without implicit source precedence.
- Stable IDs are mandatory for addressable elements; published parent contexts expose IDs visibly.
- `.context/` is machine-managed state and normally ignored by humans; one primary `context.yaml` per node is the current POC shape.
- Harness/model-specific files are adapters only.
- Deterministic operations form the framework skeleton; LLMs assist where semantic interpretation is actually needed.

## ContextCanon now dogfoods two nodes

- `contexts/standard/` is **ContextCanon Standard**, the public baseline intended for managed client nodes.
- the repository root is **ContextCanon Development**, which composes the Standard and adds design/compiler rules.

This validates the architectural rule that node boundaries are independent from Git repository boundaries.

## Use-case walkthrough result

The walkthrough found no need to replace the composition model, but identified bounded questions to settle before compiler V1 is frozen:

- exact package/entry-view boundary,
- Topic syntax for Required/Optional and recursive loading,
- source locators and immutable package identity,
- ID generation/preservation,
- dangling change diagnostics,
- addressing multiple nodes in one repository,
- non-versioned authoring-help preferences.

See [docs/use-case-walkthrough.md](docs/use-case-walkthrough.md) for the scenarios and findings.

No production compiler exists yet. Current generated files are manually modeled POC output.

## Current focus

Run the next vertical POC against real example repositories using ContextCanon Standard, Required/Optional Topics, local deltas, and at least one source-update scenario before freezing the V1 parser/model.

See [PLAN.md](PLAN.md) for the active checklist.
