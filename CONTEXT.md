# ContextCanon Official Context

> [!CAUTION]
> **GENERATED FILE — DO NOT EDIT.**
> This is the official compiled context for this node. It applies to ContextCanon itself and is the context published to child nodes.
>
> Edit [CONTEXT.src.md](CONTEXT.src.md) instead.

**Node:** ContextCanon  
**Context version:** `0.1.0-draft`

The IDs shown with published rules are stable contract identifiers. Child nodes use them for explicit remove, override, exception, tracing, and diagnostics operations.

## Rules

### Canonical context

#### `CC-001` — One official context

The compiled official context is the single canonical context for a node: it applies to the node itself and is the context the node publishes to children.

Why: Parent and child views must never diverge into two competing truths.

#### `CC-002` — Edit source, not generated context

Human context changes are authored in `CONTEXT.src.md`; generated context and harness adapters are not edited directly.

Why: One editable source prevents drift between equivalent instruction files.

### Machine state

#### `CC-003` — Keep compiler bookkeeping out of the normal workflow

Framework bookkeeping belongs under `.context/` and should not be required reading for normal human or agent work.

Why: IDs, snapshots, provenance, and digests are necessary for the compiler but should not dominate the user experience.

### Composition

#### `CC-004` — No implicit source precedence

Context sources are composed without implicit precedence; conflicts are resolved explicitly through local changes rather than source order.

Why: Hidden first-parent-wins behavior would make composed context difficult to reason about and unsafe to maintain.

### Identity

#### `CC-005` — Stable identity

Every addressable context element has a stable ID independent of its title, wording, file location, and presentation.

Why: Children must be able to remove, override, trace, or debug inherited elements even after their human wording changes.

#### `CC-006` — Publish IDs that children may reference

Published official contexts expose stable IDs for rules and other elements that child nodes may reference.

Why: Users must be able to discover the correct target without searching hidden comments or machine YAML.

### Progressive disclosure

#### `CC-007` — Use Topics for deeper context

Use Topics to direct humans and agents to deeper information only when a task needs it.

Why: Context is scarce; the always-loaded official context should remain compact while deeper project knowledge stays discoverable.

### Project state

#### `CC-008` — State stays local

`STATE.md` describes the current local project situation and is never inherited as governance by child nodes.

Why: Temporary project reality is useful locally but is not a reusable rule of descendants.

### Harness independence

#### `CC-009` — Harness files are adapters

Harness-specific files are thin generated adapters that point to the official context; project truth must not live only in a harness-specific file.

Why: ContextCanon must remain usable across models and agent harnesses.

### Repository conventions

#### `CC-010` — Keep standard repository documents explicit

Keep `README.md`, `CONTRIBUTING.md`, and `CHANGELOG.md` present even when one is intentionally short.

Why: Explicit standard documents make repository intent and history easier to discover.

## Topics

### Concepts

For terminology and the ContextCanon mental model, read `docs/concepts.md`.

### Composition and inheritance

For source composition, dependency graphs, update propagation, conflicts, removes, overrides, or exceptions, read `docs/composition.md`.

### Source and official formats

For authoring syntax, IDs, generated output, and machine representation, read:

- `docs/source-format.md`
- `docs/official-context.md`
- `docs/architecture.md`

### Harness integration

For `AGENTS.md`, `.goosehints`, and other adapters, read `docs/harnesses.md`.

### State and planning

For the boundary between current state, planning, governance, and history, read `docs/state.md`.
