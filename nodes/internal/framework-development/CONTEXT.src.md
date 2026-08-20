# ContextCanon Framework Development — Local Context Source
<!-- ctx:node id="8b8f6ad7-2d17-4f9f-9a6c-8cb0bc5d8c2a" version="0.1.0-draft" -->

> [!IMPORTANT]
> **Edit this file to change the context for designing and implementing ContextCanon itself.**
> `CONTEXT.md` and `CONTEXT/` are generated from this source plus accepted Context Sources.
>
> This Node composes [ContextCanon Foundation](../../library/foundation/) and adds only the framework-development delta.
>
> Full format documentation: [../../../docs/source-format.md](../../../docs/source-format.md)

<!--
ContextCanon authoring templates — compiler-managed help, safe to copy.

NEW RULE
### Group
- **Rule title:** Rule statement.
  Why: Reason for the rule.
  [compiler inserts stable ctx:rule ID]

REMOVE IMPORTED RULE
### Remove
- `Source name / RULE-ID` — Current rule title
  Why: Why it does not apply here.
  [compiler binds the stable source-node ID]

OVERRIDE IMPORTED RULE
### Override
- `Source name / RULE-ID` — Current rule title
  New rule: Replacement statement.
  Why: Why this Node differs.
  [compiler binds the stable source-node ID]
-->

## Sources

- [ContextCanon Foundation](../../library/foundation/) — `0.1.0-draft`
  <!-- ctx:source id="4ca9d92c-59f2-4b1f-b7b3-0e2ff91fd001" version="0.1.0-draft" -->

## Rules

### Compiler architecture

- **Deterministic skeleton, semantic intelligence on top:** Prefer deterministic mechanisms whenever behavior can be specified and computed exactly; use LLMs only for work that genuinely requires semantic interpretation.
  Why: Deterministic structure provides reproducibility and auditability, while LLM reasoning is most valuable where meaning rather than mechanics must be understood.
  <!-- ctx:rule id="CCI-001" -->

### Development method

- **Validate vertically before hardening:** Validate ContextCanon through concrete repository use cases before hardening abstractions into compiler code.
  Why: Simple real workflows should shape the framework; implementation convenience must not force unnecessary ceremony on users.
  <!-- ctx:rule id="CCI-002" -->

- **Repository documentation is the design record:** Treat the repository documentation as the canonical design record once a decision is accepted; do not rely on reconstructing architecture from chat history.
  Why: ContextCanon itself should demonstrate durable, reviewable project context.
  <!-- ctx:rule id="CCI-003" -->

### Node library

- **Keep library Nodes on Foundation:** Every reusable Node published in the ContextCanon Node Library must compose ContextCanon Foundation directly or transitively.
  Why: The library needs one common baseline while specialized Nodes should still contain only their own additional context.
  <!-- ctx:rule id="CCI-004" -->

## Topics

### Framework architecture

When changing the compiler boundary, package model, Node structure, deterministic/semantic split, or generated artifacts:

Required:
- Resource: `../../../docs/architecture.md`
- Resource: `../../../docs/use-case-walkthrough.md`

Optional:
- Resource: `../../../docs/concepts.md`
<!-- ctx:topic id="CCI-TOPIC-ARCHITECTURE" -->

### Source and official formats

When changing authoring syntax, IDs, Topics, official entry views, or machine representation:

Required:
- Resource: `../../../docs/source-format.md`
- Resource: `../../../docs/official-context.md`
- Resource: `../../../docs/topics.md`
<!-- ctx:topic id="CCI-TOPIC-FORMATS" -->

### Composition

When changing Source composition, version acceptance, conflicts, removes, overrides, exceptions, or multi-Node repositories:

Required:
- Resource: `../../../docs/composition.md`
- Resource: `../../../docs/use-case-walkthrough.md`
<!-- ctx:topic id="CCI-TOPIC-COMPOSITION" -->

### Harness integration

When changing `AGENTS.md`, `.goosehints`, or another model/harness adapter:

Required:
- Resource: `../../../docs/harnesses.md`
<!-- ctx:topic id="CCI-TOPIC-HARNESSES" -->

### State and planning

When deciding whether information belongs in current state, planning, governance, or history:

Required:
- Resource: `../../../docs/state.md`
<!-- ctx:topic id="CCI-TOPIC-STATE" -->
