# Current State

ContextCanon has completed two repository-based architecture/UX prototype rounds and repeated mental walkthroughs of critical use cases. The project is deliberately refining the product model before hardening compiler implementation.

## Current design baseline

- `CONTEXT.src.md` is the human-editable local delta.
- `CONTEXT.md` is the generated compact official entry view.
- `CONTEXT/` is optional and contains deeper compiled/materialized resources only when a node needs them.
- Topics provide progressive disclosure with **Required** and **Optional** targets.
- A Topic may navigate to a resource or another Context Node; navigation does not imply inheritance.
- A node may compose multiple independent Sources without implicit source precedence.
- Stable IDs are mandatory for addressable elements; published parent contexts expose IDs visibly.
- `.context/` is machine-managed state and normally ignored by humans.
- Harness/model-specific files are adapters only.
- Deterministic operations form the framework skeleton; LLMs assist where semantic interpretation is actually needed.

## ContextCanon now dogfoods three nodes

```text
ContextCanon Gateway ──Topic──> ContextCanon Development
                                      ▲
                                      │ Source
                           ContextCanon Foundation
```

- the repository root is **ContextCanon Gateway**, intentionally almost empty,
- `nodes/foundation/` is **ContextCanon Foundation**, the reusable baseline,
- `nodes/development/` is **ContextCanon Development**, which composes Foundation and adds design/compiler context.

This makes two important distinctions concrete: a Context Node is not a Git repository, and Topic navigation is not Source composition.

The ContextCanon schema/specification remains the structural interface implemented by all nodes; no separate interface node is needed merely to describe the schema.

## Latest POC finding

The Gateway demonstrates that `CONTEXT/` must be optional. A valid useful node may have zero Sources, zero Rules, one Topic and no materialized resources.

It also exposes one V1 contract that still needs to be frozen: a Topic target can point to another Context Node. The machine model must represent that target explicitly enough for validation and future package/location handling.

No production compiler exists yet. Current generated files and package copies are manually modeled POC output.

## Current focus

Use ContextCanon Foundation against real example repositories, then exercise Gateway routing, package materialization, source updates and local deltas before freezing the V1 parser/model.

See [PLAN.md](PLAN.md) for the active checklist.
