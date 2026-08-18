# Source Format

`CONTEXT.src.md` is the primary human-editable ContextCanon source for a node.

It is intentionally constrained Markdown: readable without special tooling, but structured enough for deterministic parsing.

Every generated source file should start with a visible header explaining how to edit it and linking to this documentation.

## Sections

### Sources

`## Sources` lists accepted reusable ContextCanon nodes.

A future compiler will maintain package identity/version/revision metadata in hidden comments while leaving the visible source name and version readable.

Source order is not precedence.

### Rules

`## Rules` contains local rules. `###` headings group related rules by topic.

Example:

```markdown
### Security

- Never commit secrets.
  Why: Version control is not a secret store.
  <!-- ctx:rule id="SEC-001" -->
```

The `ctx:rule` comment contains the stable ID. POC direction: the compiler inserts and maintains these IDs automatically so a human normally does not manage them.

The ID is mandatory in the framework data model even though it is visually hidden in the editable Markdown rendering.

### Changes

`## Changes` records explicit operations against accepted sources.

Because titles and wording can change, operations must target the stable ID published by the source node. The human-visible text should also show the current source title/description so the operation remains understandable.

Conceptual example:

```markdown
## Changes

### Remove

- `python-context#PY-017` — Require Python 3.13
  Why: This project deliberately supports Python 3.12.
  <!-- ctx:remove target="<stable-node-id>#PY-017" -->
```

The visible reference is not merely decoration: a user must be able to identify the exact inherited element being changed.

### Topics

`## Topics` maps task themes to deeper information.

Example:

```markdown
## Topics

### Logging

When changing logging, diagnostics, or structured events, read:
- `docs/logging.md`
```

The human concept is **Topics**. A compiler may internally model this as routing, but that implementation vocabulary should not leak into normal authoring.

## IDs

Every addressable ContextCanon element has stable identity independent of title, wording, location, or presentation.

For local authoring, IDs may live in compiler-managed HTML comments. For published official context, IDs that descendants may reference are displayed visibly.
