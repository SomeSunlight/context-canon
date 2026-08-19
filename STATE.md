# Current State

ContextCanon has completed two repository-based architecture/UX prototype rounds and repeated mental walkthroughs of critical use cases. The project is deliberately refining the product model before hardening compiler implementation.

## Current design baseline

- Every Context Node has one physical **node-root directory** containing its ContextCanon files; the directory path is location, not identity.
- `CONTEXT.src.md` is the human-editable local delta.
- `CONTEXT.md` is the generated compact official entry view.
- `CONTEXT/` is optional and contains deeper compiled/materialized resources only when a Node needs them.
- Topics provide progressive disclosure with **Required** and **Optional** targets.
- A Topic may navigate to a resource or another Context Node; navigation does not imply inheritance.
- A Node may compose multiple independent Sources without implicit Source precedence.
- Stable IDs are mandatory for addressable elements; published parent contexts expose IDs visibly.
- `.context/` is machine-managed state and normally ignored by humans.
- Harness/model-specific files are adapters only.
- Deterministic operations form the framework skeleton; LLMs assist where semantic interpretation is actually needed.

## ContextCanon dogfoods three Nodes

```text
ContextCanon Gateway ──Topic──> ContextCanon Framework Development
                                      ▲
                                      │ Source
                           ContextCanon Foundation
```

Their physical locations now make their different roles explicit:

- the repository root is **ContextCanon Gateway**, intentionally almost empty,
- `nodes/library/foundation/` is **ContextCanon Foundation**, the common reusable baseline of the ContextCanon Node Library,
- `nodes/internal/framework-development/` is **ContextCanon Framework Development**, which composes Foundation and adds design/compiler context.

The directories `nodes/`, `nodes/library/`, and `nodes/internal/` are organizational containers, not Nodes.

Every reusable Node published in the ContextCanon Node Library must compose Foundation directly or transitively. ContextCanon-internal Nodes are kept separately so contributors do not have to guess whether an internal implementation context is a reusable module.

## Latest POC findings

The Gateway demonstrates that `CONTEXT/` must be optional. A valid useful Node may have zero Sources, zero Rules, one Topic and no materialized resources.

The latest repository reorganization exposed two further contracts:

1. Node organization must be obvious from the filesystem: every actual Node has a node root, while category directories merely organize Nodes.
2. Node identity must survive moves and renames. **ContextCanon Framework Development** keeps the same stable Node ID it had before moving from `nodes/development/` to `nodes/internal/framework-development/`.

A Topic target can also point to another Context Node. The machine model must represent that target explicitly enough for validation and future package/location handling.

No production compiler exists yet. Current generated files and package copies are manually modeled POC output.

## Current focus

Use ContextCanon Foundation against real example repositories, then add at least one further reusable Node to the ContextCanon Node Library to exercise node-root discovery, library placement, Foundation inheritance, package materialization, Source updates and local deltas before freezing the V1 parser/model.

See [PLAN.md](PLAN.md) for the active checklist.
