# Source Format

`CONTEXT.src.md` is the primary human-editable ContextCanon source for a node.

It is intentionally constrained Markdown: readable without special tooling, but structured enough for deterministic parsing.

Every source file should start with a visible header explaining how to edit it and linking to this documentation.

## Compiler-managed authoring help

The raw Markdown may contain a compiler-managed HTML comment block with copyable templates for common operations.

Rendered Markdown stays clean, while a first-time editor immediately sees valid examples in the source.

The default direction is a compact help block with generic templates once per file. A future user preference may support:

- `compact` — generic templates,
- `expanded` — additional ready-to-edit snippets for imported elements,
- `none` — minimal source for experienced users.

Generating one commented template for every imported rule by default would scale poorly and conflicts with progressive disclosure.

Authoring-help verbosity is tooling/presentation preference, not inherited project governance.

## Sections

### Sources

`## Sources` lists accepted reusable ContextCanon nodes.

A future compiler maintains stable source identity/version/revision metadata in hidden comments while leaving the visible source name and version readable.

Source order is not precedence.

### Rules

`## Rules` contains local rules. `###` headings group related rules.

Example:

```markdown
### Security

- Never commit secrets.
  Why: Version control is not a secret store.
  <!-- ctx:rule id="SEC-001" -->
```

The compiler-managed comment contains the stable local ID. The ID is mandatory in the framework data model even though it need not clutter rendered source Markdown.

### Changes

`## Changes` records explicit operations against accepted sources.

Because titles and wording can change, operations target stable IDs published by the source node. Human-visible source name/title is included for orientation but is not identity.

Conceptual example:

```markdown
## Changes

### Remove

- `Python Development / PY-017` — Require Python 3.13
  Why: This project deliberately supports Python 3.12.
  <!-- ctx:remove target="<stable-node-id>#PY-017" -->
```

The source's published `CONTEXT.md` must make `PY-017` easy to discover.

If a later accepted source package no longer contains the targeted ID, the compiler reports a dangling change operation rather than silently ignoring it.

### Topics

`## Topics` maps task themes to deeper information.

Current design direction:

```markdown
## Topics

### Logging

When changing logging, diagnostics, or structured events:

Required:
- `docs/logging-contract.md`

Optional:
- `docs/logging-history.md`
```

The exact parser syntax remains open until the next vertical POC, but `required` versus `optional` is a semantic requirement.

## IDs

Every addressable ContextCanon element has stable identity independent of title, wording, location, or presentation.

For local authoring, IDs may live in compiler-managed HTML comments. For published official context, IDs that descendants may reference are displayed visibly.
