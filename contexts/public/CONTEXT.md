# ContextCanon Public (`t`) — Official Context

> [!CAUTION]
> **GENERATED FILE — DO NOT EDIT.**
> This is the compact official entry view of the public ContextCanon node.
> Together with the generated `CONTEXT/` directory it forms the human/agent-facing Official Context Package.
>
> Edit [CONTEXT.src.md](CONTEXT.src.md) instead.

**Node:** ContextCanon Public (`t`)  
**Context version:** `0.1.0-draft`

The IDs shown with rules are stable contract identifiers. Child nodes use them for removes, overrides, exceptions, tracing, and diagnostics.

## Rules

### Canonical context

#### `CC-001` — One official package

The compiled Official Context Package is the single canonical context for a node: it applies to the node itself and is the package meaning published to child nodes.

#### `CC-002` — Edit source, not generated output

Human context changes are authored in `CONTEXT.src.md`; generated context views, package contents, machine state, and harness adapters are not edited directly.

### Machine state

#### `CC-003` — Keep compiler bookkeeping out of the normal workflow

Framework bookkeeping belongs under `.context/` and should not be required reading for normal human or agent work.

### Composition

#### `CC-004` — No implicit source precedence

Context sources are composed without implicit precedence; conflicts are resolved explicitly through local changes rather than source order.

### Identity

#### `CC-005` — Stable identity

Every addressable context element has a stable ID independent of its title, wording, file location, and presentation.

#### `CC-006` — Publish IDs that children may reference

Published official contexts expose stable IDs for rules and other elements that child nodes may reference.

### Progressive disclosure

#### `CC-007` — Keep entry context small

Keep the official entry context compact and use Topics to load deeper context only when needed; Topic references distinguish required from optional material.

### Project state

#### `CC-008` — State stays local

`STATE.md` describes the current local project situation and is never inherited as governance by child nodes.

### Harness independence

#### `CC-009` — Canonical context is model- and harness-neutral

Project code and canonical project context must not depend on a particular LLM or agent harness; harness-specific files are thin generated adapters at the edge.

### Repository conventions

#### `CC-010` — Keep standard repository documents explicit

Keep `README.md`, `CONTRIBUTING.md`, and `CHANGELOG.md` present even when one is intentionally short.

### Documentation style

#### `CC-011` — Write for intelligent readers

Write technical documentation in precise, plain prose for intelligent readers; introduce unfamiliar concepts before using specialized terms and avoid unexplained internal shorthand, inflated marketing language, and unnecessary jargon.

## Topics

### Context authoring

When editing ContextCanon source, IDs, generated views, or Topics:

**Required**
- [`CONTEXT/references/docs/source-format.md`](CONTEXT/references/docs/source-format.md)
- [`CONTEXT/references/docs/official-context.md`](CONTEXT/references/docs/official-context.md)
- [`CONTEXT/references/docs/topics.md`](CONTEXT/references/docs/topics.md)

### Context composition

When adding sources or changing inherited rules:

**Required**
- [`CONTEXT/references/docs/composition.md`](CONTEXT/references/docs/composition.md)

### Harness adapters

When adding or changing a harness-specific entry file:

**Required**
- [`CONTEXT/references/docs/harnesses.md`](CONTEXT/references/docs/harnesses.md)
