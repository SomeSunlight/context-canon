# ContextCanon Local Context Source

> [!IMPORTANT]
> **Edit this file to change this node's local context.**
> `CONTEXT.md` is generated from this source plus accepted context sources and is the official context that applies to this node and is published to child nodes.
>
> **Source syntax**
> - `## Sources` lists reusable published ContextCanon nodes to compose. Source order is not precedence.
> - `## Rules` defines local rules. Use `###` headings to group related rules.
> - `## Changes` explicitly removes, overrides, or activates authorized exceptions from imported sources. These operations reference stable published IDs.
> - `## Topics` points to deeper information that should be loaded only when the topic matters.
> - `Why:` is optional but recommended whenever the reason is not obvious.
> - `<!-- ctx:... -->` comments contain compiler-managed stable IDs and package metadata. Do not edit them manually.
>
> Full format documentation: [docs/source-format.md](docs/source-format.md)

## Rules

### Canonical context

- The compiled official context is the single canonical context for a node: it applies to the node itself and is the context the node publishes to children.
  Why: Parent and child views must never diverge into two competing truths.
  <!-- ctx:rule id="CC-001" -->

- Human context changes are authored in `CONTEXT.src.md`; generated context and harness adapters are not edited directly.
  Why: One editable source prevents drift between equivalent instruction files.
  <!-- ctx:rule id="CC-002" -->

### Machine state

- Framework bookkeeping belongs under `.context/` and should not be required reading for normal human or agent work.
  Why: IDs, snapshots, provenance, and digests are necessary for the compiler but should not dominate the user experience.
  <!-- ctx:rule id="CC-003" -->

### Composition

- Context sources are composed without implicit precedence; conflicts are resolved explicitly through local changes rather than source order.
  Why: Hidden first-parent-wins behavior would make composed context difficult to reason about and unsafe to maintain.
  <!-- ctx:rule id="CC-004" -->

### Identity

- Every addressable context element has a stable ID independent of its title, wording, file location, and presentation.
  Why: Children must be able to remove, override, trace, or debug inherited elements even after their human wording changes.
  <!-- ctx:rule id="CC-005" -->

- Published official contexts expose stable IDs for rules and other elements that child nodes may reference.
  Why: Users must be able to discover the correct target without searching hidden comments or machine YAML.
  <!-- ctx:rule id="CC-006" -->

### Progressive disclosure

- Use Topics to direct humans and agents to deeper information only when a task needs it.
  Why: Context is scarce; the always-loaded official context should remain compact while deeper project knowledge stays discoverable.
  <!-- ctx:rule id="CC-007" -->

### Project state

- `STATE.md` describes the current local project situation and is never inherited as governance by child nodes.
  Why: Temporary project reality is useful locally but is not a reusable rule of descendants.
  <!-- ctx:rule id="CC-008" -->

### Harness independence

- Harness-specific files are thin generated adapters that point to the official context; project truth must not live only in a harness-specific file.
  Why: ContextCanon must remain usable across models and agent harnesses.
  <!-- ctx:rule id="CC-009" -->

### Repository conventions

- Keep `README.md`, `CONTRIBUTING.md`, and `CHANGELOG.md` present even when one is intentionally short.
  Why: Explicit standard documents make repository intent and history easier to discover.
  <!-- ctx:rule id="CC-010" -->

## Topics

### Concepts

For terminology and the mental model of ContextCanon, read:
- `docs/concepts.md`
<!-- ctx:topic id="CC-TOPIC-CONCEPTS" -->

### Composition and inheritance

When working on source composition, dependency graphs, update propagation, conflicts, removes, overrides, or exceptions, read:
- `docs/composition.md`
<!-- ctx:topic id="CC-TOPIC-COMPOSITION" -->

### Source and official formats

When changing the human authoring syntax, IDs, generated output, or machine representation, read:
- `docs/source-format.md`
- `docs/official-context.md`
- `docs/architecture.md`
<!-- ctx:topic id="CC-TOPIC-FORMATS" -->

### Harness integration

When changing `AGENTS.md`, `.goosehints`, or another model/harness adapter, read:
- `docs/harnesses.md`
<!-- ctx:topic id="CC-TOPIC-HARNESSES" -->

### State and planning

When deciding whether information belongs in current state, planning, governance, or historical documentation, read:
- `docs/state.md`
<!-- ctx:topic id="CC-TOPIC-STATE" -->
