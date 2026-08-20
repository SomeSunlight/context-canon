# Current State

ContextCanon has completed two repository-based architecture/UX prototype rounds and repeated mental walkthroughs of critical use cases. The product model is now coherent and simple enough to move from primarily conceptual validation to an executable end-to-end prototype.

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

Their physical locations make their different roles explicit:

- the repository root is **ContextCanon Gateway**, intentionally almost empty,
- `nodes/library/foundation/` is **ContextCanon Foundation**, the common reusable baseline of the ContextCanon Node Library,
- `nodes/internal/framework-development/` is **ContextCanon Framework Development**, which composes Foundation and adds design/compiler context.

The directories `nodes/`, `nodes/library/`, and `nodes/internal/` are organizational containers, not Nodes.

Every reusable Node published in the ContextCanon Node Library must compose Foundation directly or transitively. ContextCanon-internal Nodes are kept separately so contributors do not have to guess whether an internal implementation context is a reusable module.

## What the POCs established

The current repository demonstrates several contracts strongly enough to implement them rather than continue validating them only in prose:

1. A useful Node may be almost empty: Gateway has zero Sources, zero Rules, one Topic, and no `CONTEXT/` directory.
2. Node organization must be obvious from the filesystem: every actual Node has a node root, while category directories merely organize Nodes.
3. Node identity must survive moves and renames. ContextCanon Framework Development kept its stable Node ID when its name and path changed.
4. Topic navigation and Source composition are different relationships.
5. Topic targets must be explicit enough for deterministic validation because a target may be a resource or another Context Node.
6. Generated package resources must be synchronized deterministically with their source material.

No production compiler exists yet. Current generated files and package copies are manually modeled POC output.

## Development strategy has changed

ContextCanon will no longer postpone implementation until every planned use case has been exhaustively explored mentally.

The next goal is a **walking skeleton**: the smallest deterministic compiler that can compile the ContextCanon dogfood graph and one real external project, validate its generated output without an LLM, and expose exact Context changes to a separate LLM layer.

Mental walkthroughs remain useful, but they become targeted tools for concrete ambiguities found while implementing or operating the prototype rather than a gate before implementation.

The intended end-to-end loop is:

```text
real project
    ↓
human/LLM-authored CONTEXT.src.md
    ↓
deterministic compiler
    ↓
Official Context Package + exact diff/diagnostics
    ↓
LLM project work or Context-impact review
    ↓
observed value and failure modes
    ↓
framework refinement
```

## First high-level LLM experiment

A particularly valuable first semantic workflow is already identified: when a compiled Rule changes, the compiler should produce the exact Context delta; an LLM can then inspect a real project and answer:

> Which code, configuration, tests, or documentation are likely affected by this Rule change, why, and what should change?

The compiler owns the exact Rule identity, provenance, and diff. The LLM owns semantic impact analysis. The impact map remains advice until reviewed.

This separation preserves harness independence and allows the same deterministic change set to be consumed by Codex, goose, Hermes, a local model, or another future agent.

## Current focus

Implement **Walking Skeleton 1** from [PLAN.md](PLAN.md): the minimal deterministic compiler, deterministic fixtures for Gateway/Foundation/Framework Development, and enough generated output to apply ContextCanon to the first real external project.
