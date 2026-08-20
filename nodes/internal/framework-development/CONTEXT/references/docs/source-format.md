# Source Format

`CONTEXT.src.md` is the human-editable source of truth for one Context Node. The compiler never needs to reconstruct authored information from generated `CONTEXT.md` or `.context/context.yaml`.

The format is deliberately constrained Markdown: readable without special tooling, but structured enough for deterministic parsing.

## Node header

A source begins with a human-readable H1 and compiler-managed Node metadata:

```markdown
# Example Project — Local Context Source
<!-- ctx:node id="<stable-node-id>" version="0.1.0" -->
```

The stable ID is independent of the Node's directory path or display name. A root Node may additionally declare generated harness adapters, for example `adapters="agents,goose"`.

## Sources

`## Sources` lists accepted Context Nodes. The visible link points to the Source node-root directory; the adjacent comment preserves stable identity and accepted version.

```markdown
## Sources

- [ContextCanon Foundation](../foundation/) — `0.1.0`
  <!-- ctx:source id="<stable-node-id>" version="0.1.0" -->
```

Source order is not precedence. The walking-skeleton compiler currently supports local filesystem Sources inside the same Git repository.

## Rules

`## Rules` contains the Node's local Rules. `###` headings group related Rules. Every Rule has a short visible title, a statement, rationale, and compiler-managed stable ID.

```markdown
### Security

- **Never commit secrets:** Credentials and secret values must stay outside version control.
  Why: Version control is not a secret store.
  <!-- ctx:rule id="SEC-001" -->
```

The title is part of the human presentation, not identity. Descendants address the stable ID.

## Topics

A Topic states when deeper context applies and explicitly types every target.

```markdown
## Topics

### Logging

When changing logging, diagnostics, or structured events:

Required:
- Resource: `docs/logging-contract.md`

Optional:
- Resource: `docs/logging-history.md`
```

A Topic can also navigate to another Context Node without composing it:

```markdown
Required:
- Context Node: `nodes/internal/framework-development`
```

`Resource` targets are materialized into the generated `CONTEXT/` package. `Context Node` targets point to another node root and remain navigation rather than Source composition.

Every Topic ends with a compiler-managed stable ID:

```markdown
<!-- ctx:topic id="LOGGING" -->
```

## Changes

`## Changes` is reserved for explicit operations such as Remove, Override, and authorized exceptions against inherited elements. The specification keeps these concepts, but the first walking-skeleton compiler intentionally rejects unsupported change syntax until a real end-to-end case requires it.

## Compiler-managed authoring help

Raw Markdown may contain compiler-managed HTML comment blocks with copyable examples. These blocks are authoring help only; they do not carry critical human meaning and disappear from rendered Markdown.

## Current compiler contract

The executable walking skeleton freezes only the syntax needed by Gateway, Foundation, Framework Development, and the first external project. See [compiler.md](compiler.md) for supported behavior and deliberate limitations.
