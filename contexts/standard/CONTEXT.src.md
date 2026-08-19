# ContextCanon Standard — Local Context Source

> [!IMPORTANT]
> **Edit this file to change the public ContextCanon baseline.**
> `CONTEXT.md` is generated and is the published context that managed client nodes may compose.
>
> **Source syntax**
> - `## Rules` defines local Standard rules.
> - `## Topics` points to deeper framework information loaded only when relevant.
> - `Why:` records human rationale.
> - `<!-- ctx:... -->` comments contain compiler-managed stable IDs. Do not edit them manually.
>
> Full format documentation: [../../docs/source-format.md](../../docs/source-format.md)

<!--
ContextCanon authoring templates — compiler-managed help.

NEW RULE
### Group
- Rule statement.
  Why: Reason.
  [compiler inserts stable ctx:rule ID]

TOPIC
### Topic name
When this topic applies...
Required:
- `path/to/must-read.md`
Optional:
- `path/to/deeper-reference.md`
-->

## Rules

### Canonical context

- The compiled Official Context Package is the single canonical context for a node: it applies to the node itself and is the package meaning published to child nodes.
  Why: A node must not operate under one context while publishing a different truth to descendants.
  <!-- ctx:rule id="CC-001" -->

- Human context changes are authored in `CONTEXT.src.md`; generated context views, machine state, and harness adapters are not edited directly.
  Why: One editable source prevents drift between equivalent outputs.
  <!-- ctx:rule id="CC-002" -->

### Machine state

- Framework bookkeeping belongs under `.context/` and should not be required reading for normal human or agent work.
  Why: IDs, snapshots, provenance, and digests are necessary for the compiler but should not dominate the user experience.
  <!-- ctx:rule id="CC-003" -->

### Composition

- Context sources are composed without implicit precedence; conflicts are resolved explicitly through local changes rather than source order.
  Why: Hidden first-source-wins behavior would make composed context difficult to reason about and unsafe to maintain.
  <!-- ctx:rule id="CC-004" -->

### Identity

- Every addressable context element has a stable ID independent of its title, wording, file location, and presentation.
  Why: Children must be able to remove, override, trace, or debug inherited elements even after human wording changes.
  <!-- ctx:rule id="CC-005" -->

- Published official contexts expose stable IDs for rules and other elements that child nodes may reference.
  Why: Users must be able to discover the correct target without searching hidden comments or machine YAML.
  <!-- ctx:rule id="CC-006" -->

### Progressive disclosure

- Keep the official entry context compact and use Topics to load deeper context only when needed; Topic references distinguish required from optional material.
  Why: Context is scarce working memory and should be spent on information relevant to the current task.
  <!-- ctx:rule id="CC-007" -->

### Project state

- `STATE.md` describes the current local project situation and is never inherited as governance by child nodes.
  Why: Temporary project reality is useful locally but is not a reusable rule of descendants.
  <!-- ctx:rule id="CC-008" -->

### Harness independence

- Project code and canonical project context must not depend on a particular LLM or agent harness; harness-specific files are thin generated adapters at the edge.
  Why: A project should remain portable across models and tools without duplicating its truth.
  <!-- ctx:rule id="CC-009" -->

### Repository conventions

- Keep `README.md`, `CONTRIBUTING.md`, and `CHANGELOG.md` present even when one is intentionally short.
  Why: Explicit standard documents make repository intent and history easier to discover.
  <!-- ctx:rule id="CC-010" -->

## Topics

### Context authoring

When editing ContextCanon source, IDs, generated views, or Topics:

Required:
- `../../docs/source-format.md`
- `../../docs/official-context.md`
- `../../docs/topics.md`
<!-- ctx:topic id="CC-TOPIC-AUTHORING" -->

### Context composition

When adding sources or changing inherited rules:

Required:
- `../../docs/composition.md`
<!-- ctx:topic id="CC-TOPIC-COMPOSITION" -->

### Harness adapters

When adding or changing a harness-specific entry file:

Required:
- `../../docs/harnesses.md`
<!-- ctx:topic id="CC-TOPIC-HARNESSES" -->
