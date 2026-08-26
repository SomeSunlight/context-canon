# ContextCanon Foundation — Local Context Source
<!-- ctx:node id="4ca9d92c-59f2-4b1f-b7b3-0e2ff91fd001" version="0.1.0-draft" -->

> [!IMPORTANT]
> **Edit this file to change the reusable ContextCanon baseline.**
> `CONTEXT.md` and `CONTEXT/` are generated from this source and its referenced material.
>
> **Source syntax**
> - `## Rules` defines local Foundation Rules.
> - `## Topics` points to deeper framework information loaded only when relevant.
> - `Why:` records human rationale.
> - `<!-- ctx:... -->` comments contain compiler-managed stable IDs. Do not edit them manually.
>
> Full format documentation: [../../internal/framework-development/docs/source-format.md](../../internal/framework-development/docs/source-format.md)

## Rules

### Canonical context

- **One official package:** The compiled Official Context Package is the single canonical context for a Node: it applies to the Node itself and is the package meaning published to child Nodes.
  Why: A Node must not operate under one context while publishing a different truth to descendants.
  <!-- ctx:rule id="CC-001" -->

- **Edit source, not generated output:** Human context changes are authored in `CONTEXT.src.md`; generated context views, package contents, machine state, and harness adapters are not edited directly.
  Why: One editable source prevents drift between equivalent outputs.
  <!-- ctx:rule id="CC-002" -->

### Machine state

- **Keep compiler bookkeeping out of the normal workflow:** Framework bookkeeping belongs under `.context/` and should not be required reading for normal human or agent work.
  Why: IDs, snapshots, provenance, and digests are necessary for the compiler but should not dominate the user experience.
  <!-- ctx:rule id="CC-003" -->

### Composition

- **No implicit Source precedence:** Context Sources are composed without implicit precedence; conflicts are resolved explicitly through local changes rather than Source order.
  Why: Hidden first-source-wins behavior would make composed context difficult to reason about and unsafe to maintain.
  <!-- ctx:rule id="CC-004" -->

### Identity

- **Stable identity:** Every addressable context element has a stable ID independent of its title, wording, file location, and presentation.
  Why: Children must be able to remove, override, trace, or debug inherited elements even after human wording changes.
  <!-- ctx:rule id="CC-005" -->

- **Publish IDs that children may reference:** Published official contexts expose stable IDs for Rules and other elements that child Nodes may reference.
  Why: Users must be able to discover the correct target without searching hidden comments or machine YAML.
  <!-- ctx:rule id="CC-006" -->

### Progressive disclosure

- **Keep entry context small:** Keep the official entry context compact and use Topics to load deeper context only when needed; Topic targets distinguish Required from Optional material.
  Why: Context is scarce working memory and should be spent on information relevant to the current task.
  <!-- ctx:rule id="CC-007" -->

### Project state

- **State stays local:** `STATE.md` describes the current local project situation and is never inherited as governance by child Nodes.
  Why: Temporary project reality is useful locally but is not a reusable Rule of descendants.
  <!-- ctx:rule id="CC-008" -->

### Harness independence

- **Canonical context is model- and harness-neutral:** Project code and canonical project context must not depend on a particular LLM or agent harness; harness-specific files are thin generated adapters at the edge.
  Why: A project should remain portable across models and tools without duplicating its truth.
  <!-- ctx:rule id="CC-009" -->

### Repository conventions

- **Keep familiar repository documents useful:** Keep `README.md`, `CONTRIBUTING.md`, and `CHANGELOG.md` present when they are useful to the repository even when ContextCanon is present.
  Why: ContextCanon should complement familiar project navigation rather than replace it.
  <!-- ctx:rule id="CC-010" -->

### Documentation style

- **Write for intelligent readers:** Write technical documentation in precise, plain prose for intelligent readers; introduce unfamiliar concepts before using specialized terms and avoid unexplained internal shorthand, inflated marketing language, and unnecessary jargon.
  Why: Context should reduce interpretation effort for humans and models rather than create a private vocabulary barrier.
  <!-- ctx:rule id="CC-011" -->

## Topics

### Context authoring

When editing ContextCanon source, IDs, generated views, package resources, or Topics:

Required:
- Resource: `../../internal/framework-development/docs/source-format.md`
- Resource: `../../internal/framework-development/docs/official-context.md`
- Resource: `../../internal/framework-development/docs/topics.md`
<!-- ctx:topic id="CC-TOPIC-AUTHORING" -->

### Context composition

When adding Sources or changing inherited Rules:

Required:
- Resource: `../../internal/framework-development/docs/composition.md`
<!-- ctx:topic id="CC-TOPIC-COMPOSITION" -->

### Harness adapters

When adding or changing a harness-specific entry file:

Required:
- Resource: `../../internal/framework-development/docs/harnesses.md`
<!-- ctx:topic id="CC-TOPIC-HARNESSES" -->
