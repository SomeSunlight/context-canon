# ContextCanon Development — Local Context Source

> [!IMPORTANT]
> **Edit this file to change the context for developing ContextCanon itself.**
> `CONTEXT.md` and `CONTEXT/` are generated from this source plus accepted Context Sources.
>
> This node composes [ContextCanon Foundation](../foundation/CONTEXT.md) and adds only the Development delta.
>
> Full format documentation: [../../docs/source-format.md](../../docs/source-format.md)

<!--
ContextCanon authoring templates — compiler-managed help, safe to copy.

NEW RULE
### Group
- Rule statement.
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
  Why: Why this node differs.
  [compiler binds the stable source-node ID]
-->

## Sources

- [ContextCanon Foundation](../foundation/CONTEXT.md) — `0.1.0-draft`
  <!-- ctx:source id="4ca9d92c-59f2-4b1f-b7b3-0e2ff91fd001" version="0.1.0-draft" revision="POC-UNPINNED" -->

## Rules

### Compiler architecture

- Prefer deterministic mechanisms whenever behavior can be specified and computed exactly; use LLMs only for work that genuinely requires semantic interpretation.
  Why: Deterministic structure provides reproducibility and auditability, while LLM reasoning is most valuable where meaning rather than mechanics must be understood.
  <!-- ctx:rule id="CCI-001" -->

### Development method

- Validate ContextCanon through concrete repository use cases before hardening abstractions into compiler code.
  Why: Simple real workflows should shape the framework; implementation convenience must not force unnecessary ceremony on users.
  <!-- ctx:rule id="CCI-002" -->

- Treat the repository documentation as the canonical design record once a decision is accepted; do not rely on reconstructing architecture from chat history.
  Why: ContextCanon itself should demonstrate durable, reviewable project context.
  <!-- ctx:rule id="CCI-003" -->

## Topics

### Framework architecture

When changing the compiler boundary, package model, node structure, deterministic/semantic split, or generated artifacts:

Required:
- `../../docs/architecture.md`
- `../../docs/use-case-walkthrough.md`

Optional:
- `../../docs/concepts.md`
<!-- ctx:topic id="CCI-TOPIC-ARCHITECTURE" -->

### Source and official formats

When changing authoring syntax, IDs, Topics, official entry views, or machine representation:

Required:
- `../../docs/source-format.md`
- `../../docs/official-context.md`
- `../../docs/topics.md`
<!-- ctx:topic id="CCI-TOPIC-FORMATS" -->

### Composition

When changing Source composition, version acceptance, conflicts, removes, overrides, exceptions, or multi-node repositories:

Required:
- `../../docs/composition.md`
- `../../docs/use-case-walkthrough.md`
<!-- ctx:topic id="CCI-TOPIC-COMPOSITION" -->

### Harness integration

When changing `AGENTS.md`, `.goosehints`, or another model/harness adapter:

Required:
- `../../docs/harnesses.md`
<!-- ctx:topic id="CCI-TOPIC-HARNESSES" -->

### State and planning

When deciding whether information belongs in current state, planning, governance, or history:

Required:
- `../../docs/state.md`
<!-- ctx:topic id="CCI-TOPIC-STATE" -->
